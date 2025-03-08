# utils.py
from django.db.models import Q, F, Sum, Count, Case, When, Value, FloatField
import random
import math

def generate_swiss_pairings(tournament, round_obj):
    """
    Generate pairings for a Swiss tournament round
    
    In Swiss tournaments, players are paired with others who have the same or similar scores.
    For the first round, players are typically paired randomly or by rating.
    """
    from .models import Match, TournamentStanding
    
    participants = list(tournament.participants.all())
    
    # Special case for exactly two players - alternate colors each round
    if len(participants) == 2:
        # Get previous matches between these players
        previous_matches = Match.objects.filter(
            tournament=tournament,
            white_player__in=participants,
            black_player__in=participants
        ).order_by('round__number')
        
        # If there's an odd round number, reverse the colors from the latest match
        if previous_matches.exists() and round_obj.number % 2 == 0:
            latest_match = previous_matches.last()
            white_player = latest_match.black_player
            black_player = latest_match.white_player
        else:
            # First round or odd-numbered round, sort by rating
            participants.sort(key=lambda x: x.elo, reverse=True)
            white_player = participants[0]
            black_player = participants[1]
        
        Match.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=white_player,
            black_player=black_player,
            result='pending'
        )
        return [(white_player, black_player)]
    
    # If it's the first round, pair by rating or randomly
    if round_obj.number == 1:
        # Sort players by rating
        participants.sort(key=lambda x: x.elo, reverse=True)
    else:
        # Sort players by tournament score
        standings = {
            standing.player.id: standing.score 
            for standing in TournamentStanding.objects.filter(tournament=tournament)
        }
        participants.sort(key=lambda x: (standings.get(x.id, 0), x.elo), reverse=True)
    
    # Track already played matches to avoid duplicates
    already_played = set()
    for match in tournament.matches.all():
        player_pair = frozenset([match.white_player.id, match.black_player.id])
        already_played.add(player_pair)
    
    # Create pairings
    pairings = []
    unpaired = participants.copy()
    
    while len(unpaired) >= 2:
        player1 = unpaired.pop(0)
        
        # Find the best opponent for player1
        for i, player2 in enumerate(unpaired):
            player_pair = frozenset([player1.id, player2.id])
            
            # Check if these players have already played
            if player_pair not in already_played:
                unpaired.pop(i)
                pairings.append((player1, player2))
                break
        else:
            # If all potential pairings would be rematches, pick the first available player
            player2 = unpaired.pop(0)
            pairings.append((player1, player2))
    
    # If there's an odd number of players, the last one gets a bye
    # For simplicity, we're not implementing byes here, but would need to in a real system
    
    # Create match objects for the generated pairings
    for white, black in pairings:
        Match.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=white,
            black_player=black,
            result='pending'
        )
    
    return pairings

def generate_round_robin_pairings(tournament, round_obj):
    """
    Generate pairings for a Round Robin tournament
    
    In Round Robin tournaments, each player plays against all other players.
    For Double Round Robin, each player faces all others twice (once with white, once with black).
    """
    from .models import Match
    
    participants = list(tournament.participants.all())
    n = len(participants)
    
    # Special case for exactly two players
    if n == 2:
        # For two players, alternate colors in each round
        # In round robin with 2 players, we should have exactly 2 rounds (or 4 for double round robin)
        if round_obj.number % 2 == 1:  # Odd round number
            white_player, black_player = participants[0], participants[1]
        else:  # Even round number
            white_player, black_player = participants[1], participants[0]
            
        Match.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=white_player,
            black_player=black_player,
            result='pending'
        )
        
        return [(white_player, black_player)]
    
    # Standard round robin algorithm for more than 2 players
    # If odd number of players, add a "dummy" player for byes
    if n % 2 == 1:
        participants.append(None)
        n += 1
    
    # Apply the "polygon method" for round robin scheduling
    round_number = round_obj.number
    
    # For double round robin, we have 2*(n-1) rounds total
    # For rounds n through 2*(n-1), we reverse colors
    is_double_round_robin = tournament.tournament_type == 'double_round_robin'
    is_second_cycle = is_double_round_robin and round_number > (n - 1)
    
    # Adjust round number for second cycle
    effective_round = round_number if not is_second_cycle else round_number - (n - 1)
    
    # The first player is fixed, others rotate clockwise
    pairings = []
    
    # Calculate positions for this round
    positions = [0]  # First player stays at position 0
    for i in range(1, n):
        new_pos = (i + effective_round - 1) % (n - 1)
        if new_pos == 0:
            new_pos = n - 1
        positions.append(new_pos)
    
    # Generate pairings for this round
    for i in range(n // 2):
        player1_idx = positions[i]
        player2_idx = positions[n - 1 - i]
        
        player1 = participants[player1_idx]
        player2 = participants[player2_idx]
        
        # Skip if one is dummy player (for odd number of original participants)
        if player1 is None or player2 is None:
            continue
        
        # For second cycle in double round robin, reverse colors
        if is_second_cycle:
            white_player, black_player = player2, player1
        else:
            white_player, black_player = player1, player2
        
        # Create match
        Match.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=white_player,
            black_player=black_player,
            result='pending'
        )
        pairings.append((white_player, black_player))
    
    return pairings

def update_tournament_standings(tournament):
    """
    Update standings for a tournament based on match results
    """
    from .models import TournamentStanding, Match
    
    # Get all completed matches in this tournament
    matches = Match.objects.filter(
        tournament=tournament
    ).exclude(result='pending')
    
    # Dictionary to track scores
    scores = {}
    
    # Calculate scores based on match results
    for match in matches:
        white_id = match.white_player.id
        black_id = match.black_player.id
        
        # Initialize scores if needed
        if white_id not in scores:
            scores[white_id] = 0
        if black_id not in scores:
            scores[black_id] = 0
        
        # Update scores based on match result
        if match.result == 'white_win':
            scores[white_id] += 1
        elif match.result == 'black_win':
            scores[black_id] += 1
        else:  # Draw
            scores[white_id] += 0.5
            scores[black_id] += 0.5
    
    # Update standings table
    for player_id, score in scores.items():
        standing, created = TournamentStanding.objects.get_or_create(
            tournament=tournament,
            player_id=player_id,
            defaults={'score': 0}
        )
        standing.score = score
        standing.save()
    
    # Calculate and update ranks
    standings = TournamentStanding.objects.filter(
        tournament=tournament
    ).order_by('-score')
    
    current_rank = 1
    current_score = None
    count_at_current_score = 0
    
    for i, standing in enumerate(standings):
        if standing.score != current_score:
            current_rank = i + 1
            current_score = standing.score
            count_at_current_score = 1
        else:
            count_at_current_score += 1
        
        standing.rank = current_rank
        standing.save()