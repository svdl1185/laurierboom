# utils.py
from django.db.models import Q, F, Sum, Count, Case, When, Value, FloatField
import random
import math
import requests
from bs4 import BeautifulSoup
import logging
from .models import TournamentStanding, User, Match

def generate_swiss_pairings(tournament, round_obj):
    """
    Generate pairings for a Swiss tournament round following FIDE Dutch Swiss System rules
    with proper handling for an odd number of players (byes)
    """
    from .models import Match, TournamentStanding
    import math
    
    participants = list(tournament.participants.all())
    
    # Check if we have an odd number of players
    has_odd_players = len(participants) % 2 == 1
    
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
    
    # First round pairing with bye handling - split players into top and bottom half by rating
    if round_obj.number == 1:
        # Sort players by rating (highest to lowest)
        participants.sort(key=lambda x: x.elo, reverse=True)
        
        # Handle bye for odd number of players
        if has_odd_players:
            # The lowest-rated player gets a bye in the first round
            bye_player = participants.pop()  # Remove the last player (lowest rated)
            
            # Create a bye match
            Match.objects.create(
                tournament=tournament,
                round=round_obj,
                white_player=bye_player,
                black_player=None,  # No opponent indicates a bye
                result='bye'  # Special result type for byes
            )
            
            # Award 1 point for the bye
            standing, created = TournamentStanding.objects.get_or_create(
                tournament=tournament,
                player=bye_player,
                defaults={'score': 0}
            )
            standing.score += 1
            standing.save()
        
        # Calculate midpoint - with the bye player already removed for odd count
        midpoint = len(participants) // 2
        
        # Split remaining players into top and bottom half
        top_half = participants[:midpoint]
        bottom_half = participants[midpoint:]
        
        # Match players from top half with players from bottom half
        pairings = []
        for i in range(min(len(top_half), len(bottom_half))):
            white_player = top_half[i]
            black_player = bottom_half[i]
            
            match = Match.objects.create(
                tournament=tournament,
                round=round_obj,
                white_player=white_player,
                black_player=black_player,
                result='pending'
            )
            
            pairings.append((white_player, black_player))
        
        # Sort pairings by the combined score of the players (highest first)
        # This ensures board 1 has the most important match
        sorted_pairings = sorted(pairings, 
                              key=lambda p: max(p[0].elo, p[1].elo), 
                              reverse=True)
        
        return sorted_pairings
    
    # For rounds after the first, use the FIDE Dutch Swiss System with bye handling
    
    # Get all previous tournament matches
    previous_matches = Match.objects.filter(
        tournament=tournament
    ).order_by('round__number')
    
    # Get all previous byes
    bye_matches = previous_matches.filter(
        black_player=None,
        result='bye'
    )
    
    # Get players who have already received a bye
    players_with_bye = bye_matches.values_list('white_player_id', flat=True)
    
    # --- STEP 1: Prepare Player Data ---
    
    # Create player info dictionary with all relevant pairing information
    player_info = {}
    
    for player in participants:
        player_info[player.id] = {
            'player': player,
            'score': 0,  # Will be populated from standings
            'opponents': set(),  # IDs of previous opponents
            'colors': [],  # List of previous colors ('W' or 'B')
            'color_diff': 0,  # #White - #Black
            'color_pref': 0,  # 0=neutral, +ve=white preference, -ve=black preference
            # Magnitude: 1=mild, 2=strong (2 same in row), 3=absolute (CD >= |2|)
            'float_history': [],  # History of up/down floats (not used in basic implementation)
            'received_bye': player.id in players_with_bye  # Whether player has received a bye
        }
    
    # --- STEP 2: Calculate Standings ---
    
    # Get scores from tournament standings
    standings = TournamentStanding.objects.filter(tournament=tournament)
    
    for standing in standings:
        if standing.player_id in player_info:
            player_info[standing.player_id]['score'] = standing.score
    
    # --- STEP 3: Process Previous Match History ---
    
    # Process previous matches to gather color and opponent history
    for match in previous_matches:
        # Skip bye matches for this part
        if match.black_player is None:
            continue
            
        # Record opponent for white player
        white_id = match.white_player.id
        black_id = match.black_player.id
        
        if white_id in player_info and black_id in player_info:
            # Record opponents
            player_info[white_id]['opponents'].add(black_id)
            player_info[black_id]['opponents'].add(white_id)
            
            # Record colors
            player_info[white_id]['colors'].append('W')
            player_info[black_id]['colors'].append('B')
            
            # Update color difference
            player_info[white_id]['color_diff'] += 1
            player_info[black_id]['color_diff'] -= 1
    
    # --- STEP 4: Calculate Color Preferences (FIDE Rules) ---
    
    for player_id, info in player_info.items():
        # Calculate color preference according to FIDE
        colors = info['colors']
        color_diff = info['color_diff']
        
        # Start with absolute preference based on color difference
        if color_diff >= 2:
            info['color_pref'] = -3  # Strong black preference
        elif color_diff <= -2:
            info['color_pref'] = 3   # Strong white preference
        elif color_diff == 1:
            info['color_pref'] = -1  # Mild black preference
        elif color_diff == -1:
            info['color_pref'] = 1   # Mild white preference
        
        # Then consider consecutive same colors (takes precedence)
        if len(colors) >= 2:
            if colors[-1] == colors[-2] == 'W':
                info['color_pref'] = -2  # Strong black preference
            elif colors[-1] == colors[-2] == 'B':
                info['color_pref'] = 2   # Strong white preference
    
    # --- STEP 5: Group Players by Score ---
    
    # Group players by score (descending order)
    score_groups = {}
    for player_id, info in player_info.items():
        score = info['score']
        if score not in score_groups:
            score_groups[score] = []
        score_groups[score].append(info)
    
    # Sort players within each score group by rating (for consistent results)
    for score, players in score_groups.items():
        players.sort(key=lambda x: x['player'].elo, reverse=True)
    
    # --- STEP 6: Handle Bye for Odd Number of Players ---
    if has_odd_players:
        # Find eligible players for a bye (players who haven't had a bye yet)
        eligible_for_bye = [
            info for player_id, info in player_info.items() 
            if not info['received_bye']
        ]
        
        # If no eligible players (everyone has had a bye), consider all players
        if not eligible_for_bye:
            eligible_for_bye = list(player_info.values())
        
        # Sort eligible players by score (ascending), then by rating (ascending)
        eligible_for_bye.sort(key=lambda x: (x['score'], x['player'].elo))
        
        # Assign bye to the lowest scoring eligible player
        bye_player = eligible_for_bye[0]['player']
        
        # Create a bye match
        Match.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=bye_player,
            black_player=None,
            result='bye'
        )
        
        # Award 1 point for the bye
        standing = TournamentStanding.objects.get(
            tournament=tournament,
            player=bye_player
        )
        standing.score += 1
        standing.save()
        
        # Remove the bye player from the participants for pairing
        for score, players in score_groups.items():
            players[:] = [p for p in players if p['player'].id != bye_player.id]
            
            # If the score group is now empty, remove it
            if not players:
                score_groups.pop(score, None)
    
    # --- STEP 7: Generate Pairings (FIDE Dutch Swiss) ---
    
    pairings = []
    remaining_players = []
    
    # Start with highest score group, work down to lowest
    for score in sorted(score_groups.keys(), reverse=True):
        group = score_groups[score]
        
        # Add any players that floated down from previous groups
        group = remaining_players + group
        remaining_players = []
        
        # While there are at least 2 players in the group
        while len(group) >= 2:
            # Start with the highest rated player in the group
            s1 = group[0]
            player1 = s1['player']
            
            # Try to find a compatible pairing
            pair_found = False
            for i in range(1, len(group)):
                s2 = group[i]
                player2 = s2['player']
                
                # Check if they've already played
                if player2.id in s1['opponents']:
                    continue
                
                # Try to determine colors
                white_player, black_player = determine_colors(s1, s2)
                
                if white_player and black_player:
                    # Valid pairing found
                    pairings.append((white_player, black_player))
                    # Remove these players from the group
                    group.remove(s1)
                    group.remove(s2)
                    pair_found = True
                    break
            
            # If no valid pairing found, float player to next group
            if not pair_found:
                remaining_players.append(s1)
                group.remove(s1)
        
        # If one player remains, add to next group
        if len(group) == 1:
            remaining_players.append(group[0])
    
    # Handle any players that couldn't be paired
    # In a proper implementation, these would get byes
    # But since we already handled byes earlier, we'll just pair them sub-optimally
    if len(remaining_players) >= 2:
        while len(remaining_players) >= 2:
            s1 = remaining_players[0]
            s2 = remaining_players[1]
            white_player, black_player = determine_colors(s1, s2)
            
            # If colors can't be determined, just assign arbitrarily
            if not white_player or not black_player:
                white_player = s1['player']
                black_player = s2['player']
                
            pairings.append((white_player, black_player))
            remaining_players.remove(s1)
            remaining_players.remove(s2)
    
    # --- STEP 8: Sort Pairings by Importance ---
    
    # Sort pairings by the combined score of the players (highest first)
    # This ensures that board 1 has the most important match (highest scoring players)
    scored_pairings = []
    
    for white, black in pairings:
        # Get the scores of both players
        white_score = 0
        black_score = 0
        
        for player_id, info in player_info.items():
            if info['player'] == white:
                white_score = info['score']
            elif info['player'] == black:
                black_score = info['score']
        
        # Calculate the importance of this pairing
        # Primary sort: Combined score (higher = more important)
        # Secondary sort: Highest player rating (higher = more important)
        combined_score = white_score + black_score
        max_rating = max(white.elo, black.elo)
        
        scored_pairings.append({
            'white': white,
            'black': black,
            'combined_score': combined_score,
            'max_rating': max_rating
        })
    
    # Sort the pairings by importance (highest combined score first, then by highest rating)
    sorted_pairings = sorted(scored_pairings, 
                          key=lambda p: (p['combined_score'], p['max_rating']), 
                          reverse=True)
    
    # --- STEP 9: Create Match Objects With Board Numbers ---
    
    # Create match objects for the sorted pairings
    pairings_result = []
    for board_number, pairing in enumerate(sorted_pairings, 1):
        white = pairing['white']
        black = pairing['black']
        
        match = Match.objects.create(
            tournament=tournament,
            round=round_obj,
            white_player=white,
            black_player=black,
            result='pending'
        )
        
        pairings_result.append((white, black))
    
    return pairings_result

def determine_colors(s1, s2):
    """
    Determine the color allocation for two players following FIDE rules.
    Returns (white_player, black_player) or (None, None) if colors can't be determined.
    
    s1, s2: Dictionaries containing player info
    """
    p1 = s1['player']
    p2 = s2['player']
    
    # Rule C.04.1.h.1: If both players have a strong color preference, and these 
    # preferences are for opposite colors, the higher ranked player should receive
    # their preference
    if abs(s1['color_pref']) >= 2 and abs(s2['color_pref']) >= 2 and s1['color_pref'] * s2['color_pref'] < 0:
        if s1['color_pref'] > 0:  # s1 prefers white
            return p1, p2
        else:  # s1 prefers black
            return p2, p1
    
    # Rule C.04.1.h.2: If both players have opposite color preferences
    # (one preferring white, the other black), satisfy both
    if s1['color_pref'] * s2['color_pref'] < 0:
        if s1['color_pref'] > 0:  # s1 prefers white
            return p1, p2
        else:  # s1 prefers black
            return p2, p1
    
    # Rule C.04.1.h.3: If one player has a color preference and the other is neutral
    # (no preference), satisfy the player with a preference
    if s1['color_pref'] != 0 and s2['color_pref'] == 0:
        if s1['color_pref'] > 0:  # s1 prefers white
            return p1, p2
        else:  # s1 prefers black
            return p2, p1
    elif s1['color_pref'] == 0 and s2['color_pref'] != 0:
        if s2['color_pref'] > 0:  # s2 prefers white
            return p2, p1
        else:  # s2 prefers black
            return p1, p2
    
    # Rule C.04.1.h.4: If both players have the same color preference, alternate
    # colors from the most recent game where they had different colors
    if s1['color_pref'] != 0 and s2['color_pref'] != 0:
        # In this case, we'll just assign based on who has the stronger color imbalance
        if abs(s1['color_diff']) > abs(s2['color_diff']):
            if s1['color_diff'] > 0:  # s1 has had more whites
                return p2, p1
            else:  # s1 has had more blacks
                return p1, p2
        else:
            if s2['color_diff'] > 0:  # s2 has had more whites
                return p1, p2
            else:  # s2 has had more blacks
                return p2, p1
    
    # Rule C.04.1.h.5: If both players are neutral, alternate colors from the most recent
    # game where they had different colors
    if s1['color_pref'] == 0 and s2['color_pref'] == 0:
        # Alternate from the previous round for the highest-ranked player
        if len(s1['colors']) > 0:
            if s1['colors'][-1] == 'W':
                return p2, p1
            else:
                return p1, p2
        elif len(s2['colors']) > 0:
            if s2['colors'][-1] == 'W':
                return p1, p2
            else:
                return p2, p1
        else:
            # If neither has played before, higher ranked gets white
            return p1, p2
    
    # Fallback
    return p1, p2

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
    # Before calculating new rankings, store current ranks as previous ranks
    current_standings = TournamentStanding.objects.filter(tournament=tournament)
    for standing in current_standings:
        # Only save previous_rank if it doesn't already have one or if rank has actually changed
        if standing.previous_rank is None or standing.rank != standing.previous_rank:
            standing.previous_rank = standing.rank
            standing.save()
    
    # Get all completed matches in this tournament
    matches = Match.objects.filter(
        tournament=tournament
    ).exclude(result='pending')
    
    # Dictionary to track scores
    scores = {}
    
    # Calculate scores based on match results
    for match in matches:
        white_id = match.white_player.id
        
        # Initialize white player score if needed
        if white_id not in scores:
            scores[white_id] = 0
            
        # Check if this is a bye or has black player
        if match.black_player is None:
            # Handle byes - just award point to white player
            if match.result == 'bye':
                scores[white_id] += 1
            # Handle white forfeit with no black player (unusual edge case)
            elif match.result == 'white_forfeit':
                pass  # No points awarded to anyone
            continue  # Skip rest of loop for byes
        
        # For normal matches with two players
        black_id = match.black_player.id
        
        # Initialize black player score if needed  
        if black_id not in scores:
            scores[black_id] = 0
        
        # Update scores based on match result
        if match.result == 'white_win' or match.result == 'black_forfeit':
            scores[white_id] += 1
        elif match.result == 'black_win' or match.result == 'white_forfeit':
            scores[black_id] += 1
        elif match.result == 'draw':
            scores[white_id] += 0.5
            scores[black_id] += 0.5
    
    # Make sure all participants have a standing entry, even if they have no score
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
    count_at_current_score = 0
    
    for i, standing in enumerate(standings):
        if standing.score != current_score:
            current_rank = i + 1
            current_score = standing.score
            count_at_current_score = 1
        else:
            count_at_current_score += 1
        
        # Only save rank if it has changed
        if standing.rank != current_rank:
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
