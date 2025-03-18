from django.db.models import Count, Q, Max, Avg
from django.utils import timezone
import datetime

def check_achievements(user):
    from .models import Match
    """
    Check for all possible achievements for a user and update the database.
    Returns a list of newly earned achievements.
    """
    from django.db.models import Q
    from .models import Tournament, TournamentStanding, Match, Achievement
    
    # Track newly earned achievements to report back
    new_achievements = []
    
    # --- TOURNAMENT MILESTONE ACHIEVEMENTS ---
    
    # Get all completed tournaments for this user
    tournaments = Tournament.objects.filter(
        participants=user,
        is_completed=True
    )
    
    # Count total tournaments participation
    tournament_count = tournaments.count()
    
    # --- TOURNAMENT WIN ACHIEVEMENTS ---
    first_places = TournamentStanding.objects.filter(
        tournament__in=tournaments,
        player=user,
        rank=1
    )
    
    # Tournament win milestones
    first_place_count = first_places.count()
    
    # Tournament win achievements
    win_milestones = [
        (1, 'tournament_win_1'),
        (3, 'tournament_win_3'),
        (5, 'tournament_win_5'),
        (10, 'tournament_win_10')
    ]
    
    for milestone, achievement_type in win_milestones:
        if first_place_count >= milestone:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type=achievement_type,
                defaults={'count': first_place_count}
            )
            if created or achievement.count != first_place_count:
                achievement.count = first_place_count
                achievement.save()
                new_achievements.append(achievement)
    
    # Tournament participation milestones
    participation_milestones = [
        (10, 'tournament_veteran_10'),
        (25, 'tournament_veteran_25'),
        (50, 'tournament_veteran_50')
    ]
    
    for milestone, achievement_type in participation_milestones:
        if tournament_count >= milestone:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type=achievement_type,
                defaults={'count': tournament_count}
            )
            if created or achievement.count != tournament_count:
                achievement.count = tournament_count
                achievement.save()
                new_achievements.append(achievement)
    
    # --- TOURNAMENT SPECIAL ACHIEVEMENTS ---
    for tournament in tournaments:
        try:
            # Get tournament standings for this specific tournament
            tournament_standing = TournamentStanding.objects.get(
                tournament=tournament,
                player=user
            )
            
            # Tournament matches for this user in this tournament
            tournament_matches = Match.objects.filter(
                Q(white_player=user) | Q(black_player=user),
                tournament=tournament
            ).exclude(result='pending')
            
            # Winner-specific achievements
            if tournament_standing.rank == 1:
                # Tournament type achievements
                if tournament.tournament_type == 'swiss':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='swiss_master'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                elif tournament.tournament_type == 'round_robin':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='round_robin_champion'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                elif tournament.tournament_type == 'double_round_robin':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='double_round_robin_king'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Time control achievements
                if tournament.time_control == 'bullet':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='bullet_blitzer'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                elif tournament.time_control == 'blitz':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='blitz_boss'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                elif tournament.time_control == 'rapid':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='rapid_ruler'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                elif tournament.time_control == 'classical':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='classical_conqueror'
                    )
                    if created:
                        new_achievements.append(achievement)
            
            # Perfect Tournament Achievement
            if tournament_standing.rank == 1:
                # Check if all matches were wins
                if all(
                    (match.white_player == user and match.result == 'white_win') or
                    (match.black_player == user and match.result == 'black_win')
                    for match in tournament_matches
                ):
                    achievement, created = Achievement.objects.get_or_create(
                        user=user,
                        achievement_type='perfect_score',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
            
            # Undefeated Tournament Achievement
            undefeated = tournament_matches.filter(
                Q(white_player=user, result='black_win') | 
                Q(black_player=user, result='white_win')
            ).count() == 0
            
            if undefeated:
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type='undefeated',
                    tournament=tournament
                )
                if created:
                    new_achievements.append(achievement)
            
            # Comeback Kid - Lose first round, win tournament
            first_match = tournament_matches.order_by('round__number').first()
            if (first_match and tournament_standing.rank == 1 and 
                ((first_match.white_player == user and first_match.result == 'black_win') or 
                 (first_match.black_player == user and first_match.result == 'white_win'))):
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type='comeback_kid',
                    tournament=tournament
                )
                if created:
                    new_achievements.append(achievement)
        
        except TournamentStanding.DoesNotExist:
            # Skip if no standing exists for this tournament
            continue
    
    # --- MATCH-BASED ACHIEVEMENTS ---
    
    # Get all user's matches
    all_matches = Match.objects.filter(
        Q(white_player=user) | Q(black_player=user)
    ).exclude(result='pending').order_by('tournament__date', 'round__number')
    
    # Consecutive match pattern achievements
    achievements_patterns = [
        (['loss', 'loss', 'loss', 'win', 'win', 'win'], 'phoenix_rising'),
        (['draw', 'draw', 'draw'], 'draw_magnet'),
        (['win', 'win', 'win'], 'hat_trick'),
        (['win', 'win', 'win', 'win', 'win'], 'winning_streak_5'),
        (['win'] * 10, 'winning_streak_10')
    ]
    
    for pattern, achievement_type in achievements_patterns:
        # Exclude pending matches, byes, and draws from the result tracking
        exclude_results = ['pending', 'bye', 'draw', 'white_forfeit', 'black_forfeit']
        
        # Filter matches and convert to win/loss results
        results = []
        for match in all_matches:
            # Determine if the match is a win for the user
            is_win = (
                (match.white_player == user and match.result == 'white_win') or 
                (match.black_player == user and match.result == 'black_win')
            )
            
            # Determine if the match is a loss for the user
            is_loss = (
                (match.white_player == user and match.result == 'black_win') or 
                (match.black_player == user and match.result == 'white_win')
            )
            
            # Categorize the result
            if is_win:
                results.append('win')
            elif is_loss:
                results.append('loss')
        
        # Look for the specific pattern in the results
        for i in range(len(results) - len(pattern) + 1):
            if results[i:i+len(pattern)] == pattern:
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type=achievement_type
                )
                if created:
                    new_achievements.append(achievement)
                break
    
    # --- RATING-BASED ACHIEVEMENTS ---
    
    # Check rating milestones
    rating = user.blitz_elo  # Using blitz rating as the primary rating
    
    rating_milestones = [
        (1600, 'rating_1600'),
        (1800, 'rating_1800'),
        (2000, 'rating_2000'),
        (2200, 'rating_2200')
    ]
    
    for milestone, achievement_type in rating_milestones:
        if rating >= milestone:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type=achievement_type
            )
            if created:
                new_achievements.append(achievement)
    
    # --- UNDERDOG ACHIEVEMENT ---
    
    # Count wins against significantly higher-rated opponents
    underdog_count = 0
    for match in all_matches:
        try:
            if match.white_player == user and match.result == 'white_win' and \
               match.black_player.elo >= (match.white_player.elo + 200):
                underdog_count += 1
            elif match.black_player == user and match.result == 'black_win' and \
                 match.white_player.elo >= (match.black_player.elo + 200):
                underdog_count += 1
        except Exception:
            # Skip if there are any issues accessing player ratings
            continue
    
    if underdog_count > 0:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='underdog',
            defaults={'count': underdog_count}
        )
        if created or achievement.count != underdog_count:
            achievement.count = underdog_count
            achievement.save()
            new_achievements.append(achievement)
    
    return new_achievements


from django.db.models import Count, Q, Max, Avg
from django.utils import timezone
import datetime

from .models import Match

def check_consecutive_match_pattern(user, pattern):
    """
    Check for a specific consecutive match pattern for a user.
    
    Args:
    - user: User object
    - pattern: List of match result types to look for
    
    Returns:
    - Boolean indicating if the pattern was found
    """
    # Exclude pending matches, byes, and draws from the result tracking
    exclude_results = ['pending', 'bye', 'draw', 'white_forfeit', 'black_forfeit']
    
    # Get all matches ordered by tournament date and round number
    all_matches = Match.objects.filter(
        Q(white_player=user) | Q(black_player=user)
    ).exclude(result__in=exclude_results).order_by('tournament__date', 'round__number')
    
    # If not enough matches, return False
    if all_matches.count() < len(pattern):
        return False
    
    # Track match results
    results = []
    for match in all_matches:
        # Determine if the match is a win for the user
        is_win = (
            (match.white_player == user and match.result == 'white_win') or 
            (match.black_player == user and match.result == 'black_win')
        )
        
        # Determine if the match is a loss for the user
        is_loss = (
            (match.white_player == user and match.result == 'black_win') or 
            (match.black_player == user and match.result == 'white_win')
        )
        
        # Categorize the result
        if is_win:
            results.append('win')
        elif is_loss:
            results.append('loss')
    
    # Look for the specific pattern in the results
    for i in range(len(results) - len(pattern) + 1):
        if results[i:i+len(pattern)] == pattern:
            return True
    
    return False

def check_achievements(user):
    """
    Check for all possible achievements for a user and update the database.
    Returns a list of newly earned achievements.
    """
    from .models import Tournament, TournamentStanding, Match, Achievement
    
    # Track newly earned achievements to report back
    new_achievements = []
    
    # --- TOURNAMENT MILESTONE ACHIEVEMENTS ---
    
    # Get all completed tournaments for this user
    tournaments = Tournament.objects.filter(
        participants=user,
        is_completed=True
    )
    
    # Count total tournaments participation
    tournament_count = tournaments.count()
    
    # --- TOURNAMENT WIN ACHIEVEMENTS ---
    first_places = TournamentStanding.objects.filter(
        tournament__in=tournaments,
        player=user,
        rank=1
    )
    
    # Tournament win milestones
    first_place_count = first_places.count()
    
    # Debugging print
    print(f"User: {user.username}, Total Tournaments: {tournament_count}, First Place Count: {first_place_count}")
    
    # Tournament win achievements (revised logic)
    win_milestones = [
        (1, 'tournament_win_1'),
        (3, 'tournament_win_3'),
        (5, 'tournament_win_5'),
        (10, 'tournament_win_10')
    ]
    
    for milestone, achievement_type in win_milestones:
        if first_place_count >= milestone:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type=achievement_type,
                defaults={'count': first_place_count}
            )
            if created or achievement.count != first_place_count:
                achievement.count = first_place_count
                achievement.save()
                new_achievements.append(achievement)
    
    # --- TOURNAMENT PARTICIPATION MILESTONES ---
    participation_milestones = [
        (10, 'tournament_veteran_10'),
        (25, 'tournament_veteran_25'),
        (50, 'tournament_veteran_50')
    ]
    
    for milestone, achievement_type in participation_milestones:
        if tournament_count >= milestone:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type=achievement_type,
                defaults={'count': tournament_count}
            )
            if created or achievement.count != tournament_count:
                achievement.count = tournament_count
                achievement.save()
                new_achievements.append(achievement)
    
    # --- MATCH-BASED ACHIEVEMENTS ---
    
    # Get all user's matches
    all_matches = Match.objects.filter(
        Q(white_player=user) | Q(black_player=user)
    ).exclude(result='pending').order_by('tournament__date', 'round__number')
    
    # Phoenix Rising - Lose 3 consecutive games then win the next 3
    if check_consecutive_match_pattern(user, ['loss', 'loss', 'loss', 'win', 'win', 'win']):
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='phoenix_rising'
        )
        if created:
            new_achievements.append(achievement)
    
    # Draw Magnet - 3 consecutive draws
    if check_consecutive_match_pattern(user, ['draw', 'draw', 'draw']):
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='draw_magnet'
        )
        if created:
            new_achievements.append(achievement)
    
    # Hat Trick - 3 consecutive wins
    if check_consecutive_match_pattern(user, ['win', 'win', 'win']):
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='hat_trick'
        )
        if created:
            new_achievements.append(achievement)
    
    # Winning Streak (5 consecutive wins)
    if check_consecutive_match_pattern(user, ['win', 'win', 'win', 'win', 'win']):
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='winning_streak_5'
        )
        if created:
            new_achievements.append(achievement)
    
    # Unstoppable (10 consecutive wins)
    if check_consecutive_match_pattern(user, ['win']*10):
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='winning_streak_10'
        )
        if created:
            new_achievements.append(achievement)
    
    # --- TOURNAMENT SPECIFIC ACHIEVEMENTS ---
    
    for tournament in tournaments:
        # Get tournament standings for this specific tournament
        try:
            tournament_standing = TournamentStanding.objects.get(
                tournament=tournament,
                player=user
            )
            
            # All matches in this specific tournament
            tournament_matches = Match.objects.filter(
                Q(white_player=user) | Q(black_player=user),
                tournament=tournament
            )
            
            # Perfect Tournament (Win all games)
            if tournament_standing.rank == 1 and all(
                (match.white_player == user and match.result == 'white_win') or
                (match.black_player == user and match.result == 'black_win')
                for match in tournament_matches
            ):
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type='perfect_score',
                    tournament=tournament
                )
                if created:
                    new_achievements.append(achievement)
            
            # Undefeated Tournament
            if tournament_matches.exclude(
                Q(white_player=user, result='black_win') | 
                Q(black_player=user, result='white_win')
            ).count() == tournament_matches.count():
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type='undefeated',
                    tournament=tournament
                )
                if created:
                    new_achievements.append(achievement)
        
        except TournamentStanding.DoesNotExist:
            # If no standing exists for this tournament, skip
            continue
    
    # --- RATING-BASED ACHIEVEMENTS ---
    
    # Check rating milestones
    rating = user.blitz_elo  # Using blitz rating as the primary rating
    
    rating_milestones = [
        (1600, 'rating_1600'),
        (1800, 'rating_1800'),
        (2000, 'rating_2000'),
        (2200, 'rating_2200')
    ]
    
    for milestone, achievement_type in rating_milestones:
        if rating >= milestone:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type=achievement_type
            )
            if created:
                new_achievements.append(achievement)
    
    # Return list of newly earned achievements
    return new_achievements