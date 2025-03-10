# utils.py
from django.db.models import Q, F, Sum, Count, Case, When, Value, FloatField
import random
import math
import requests
from bs4 import BeautifulSoup
import logging
from .models import User

def generate_swiss_pairings(tournament, round_obj):
    """
    Generate pairings for a Swiss tournament round with improved color balancing
    
    This implementation:
    1. Pairs players with similar scores
    2. Balances colors (players alternate white/black when possible)
    3. Avoids rematches
    4. Follows FIDE Swiss pairing principles more closely
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
    
    # For tournaments with more than 2 players
    # Get player color history and pairing history
    color_history = {}
    pairing_history = {}
    
    # Initialize the structures
    for player in participants:
        color_history[player.id] = {'white': 0, 'black': 0, 'last_color': None}
        pairing_history[player.id] = set()
    
    # Populate color history and pairing history from previous matches
    previous_matches = Match.objects.filter(
        tournament=tournament
    ).order_by('round__number')
    
    for match in previous_matches:
        # Record the colors
        color_history[match.white_player.id]['white'] += 1
        color_history[match.white_player.id]['last_color'] = 'white'
        
        color_history[match.black_player.id]['black'] += 1
        color_history[match.black_player.id]['last_color'] = 'black'
        
        # Record that these players have played each other
        pairing_history[match.white_player.id].add(match.black_player.id)
        pairing_history[match.black_player.id].add(match.white_player.id)
    
    # If it's the first round, pair by rating or randomly
    if round_obj.number == 1:
        # Sort players by rating
        participants.sort(key=lambda x: x.elo, reverse=True)
        
        # For first round, simply pair adjacent players in the rating list
        pairings = []
        for i in range(0, len(participants), 2):
            if i + 1 < len(participants):
                # Higher rated player gets white for first game
                white_player = participants[i]
                black_player = participants[i+1]
                
                pairings.append((white_player, black_player))
        
        # Handle odd number of players (bye)
        if len(participants) % 2 == 1:
            # The last player gets a bye
            # In a real system, you'd implement proper byes here
            pass
    else:
        # Sort players by score (and then by rating as tiebreaker)
        standings = {
            standing.player.id: standing.score 
            for standing in TournamentStanding.objects.filter(tournament=tournament)
        }
        
        participants.sort(key=lambda x: (standings.get(x.id, 0), x.elo), reverse=True)
        
        # Group players by score
        score_groups = {}
        for player in participants:
            score = standings.get(player.id, 0)
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(player)
        
        # Process groups from highest score to lowest
        pairings = []
        for score in sorted(score_groups.keys(), reverse=True):
            group = score_groups[score][:]  # Make a copy to avoid modifying the original
            
            while len(group) >= 2:
                player1 = group[0]
                
                # Try to find the best opponent for player1 in this score group
                best_match_found = False
                
                # First try to find an opponent with different last color
                for i, player2 in enumerate(group[1:], 1):
                    # Skip if they've already played
                    if player2.id in pairing_history[player1.id]:
                        continue
                    
                    # Check if colors would be balanced
                    p1_last = color_history[player1.id]['last_color']
                    p2_last = color_history[player2.id]['last_color']
                    
                    # Ideal: players had different colors last time, so they can alternate
                    if p1_last != p2_last and p1_last is not None and p2_last is not None:
                        group.pop(i)  # Remove player2
                        group.pop(0)  # Remove player1
                        
                        # Assign colors - player who was black gets white
                        if p1_last == 'black':
                            white_player, black_player = player1, player2
                        else:
                            white_player, black_player = player2, player1
                        
                        pairings.append((white_player, black_player))
                        best_match_found = True
                        break
                
                # If no balanced color match, try to find any valid opponent
                if not best_match_found:
                    for i, player2 in enumerate(group[1:], 1):
                        # Skip if they've already played
                        if player2.id in pairing_history[player1.id]:
                            continue
                        
                        # Get color balance stats
                        p1_white = color_history[player1.id]['white']
                        p1_black = color_history[player1.id]['black']
                        p2_white = color_history[player2.id]['white']
                        p2_black = color_history[player2.id]['black']
                        
                        # Assign colors based on color balance
                        # Player with more games as black should get white
                        if p1_black - p1_white > p2_black - p2_white:
                            white_player, black_player = player1, player2
                        else:
                            white_player, black_player = player2, player1
                        
                        group.pop(i)  # Remove player2
                        group.pop(0)  # Remove player1
                        pairings.append((white_player, black_player))
                        best_match_found = True
                        break
                
                # If still no match, allow a rematch with balanced colors
                if not best_match_found:
                    # Just pair with the next available player
                    player2 = group[1]
                    group.pop(1)  # Remove player2
                    group.pop(0)  # Remove player1
                    
                    # Determine colors to at least maintain balance
                    p1_white = color_history[player1.id]['white']
                    p1_black = color_history[player1.id]['black']
                    p2_white = color_history[player2.id]['white']
                    p2_black = color_history[player2.id]['black']
                    
                    if p1_black - p1_white > p2_black - p2_white:
                        white_player, black_player = player1, player2
                    else:
                        white_player, black_player = player2, player1
                    
                    pairings.append((white_player, black_player))
            
            # If there's one player left in this score group, move them to the next group
            if len(group) == 1:
                leftover = group[0]
                next_score = next((s for s in sorted(score_groups.keys(), reverse=True) if s < score), None)
                if next_score is not None:
                    score_groups[next_score].insert(0, leftover)
    
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
    """Update standings for a tournament based on match results"""
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
    
    # Make sure all participants have a standing entry
    for player in tournament.participants.all():
        if player.id not in scores:
            scores[player.id] = 0
    
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
    
    for i, standing in enumerate(standings):
        if standing.score != current_score:
            current_rank = i + 1
            current_score = standing.score
        
        standing.rank = current_rank
        standing.save()
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

def update_fide_ratings():
    """Fetch and update FIDE ratings for all users with a FIDE ID"""
    users_with_fide_id = User.objects.filter(fide_id__isnull=False).exclude(fide_id='')
    
    for user in users_with_fide_id:
        try:
            # Example using a hypothetical FIDE API service
            response = requests.get(f"https://ratings.fide.com/profile/{user.fide_id}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract the rating from the page - this would depend on the specific HTML structure
                rating_element = soup.select_one('div.profile-top-rating-data')
                if rating_element:
                    try:
                        rating = int(rating_element.text.strip())
                        user.fide_rating = rating
                        user.save()
                        logging.info(f"Updated FIDE rating for {user.username}: {rating}")
                    except ValueError:
                        logging.error(f"Could not parse FIDE rating for {user.username}")
            else:
                logging.error(f"Failed to fetch FIDE rating for {user.username}: Status code {response.status_code}")
        except Exception as e:
            logging.error(f"Error updating FIDE rating for {user.username}: {str(e)}")
