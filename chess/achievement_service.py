from django.db.models import Count, Q, Max, Avg
from django.utils import timezone
import datetime

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
    
    # Check tournament participation milestones
    if tournament_count >= 10:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_veteran_10',
            defaults={'count': tournament_count}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = tournament_count
            achievement.save()
            
    if tournament_count >= 25:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_veteran_25',
            defaults={'count': tournament_count}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = tournament_count
            achievement.save()
            
    if tournament_count >= 50:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_veteran_50',
            defaults={'count': tournament_count}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = tournament_count
            achievement.save()
    
    # --- TOURNAMENT RANKINGS ACHIEVEMENTS ---
    
    # Count first, second, and third place finishes
    first_places = TournamentStanding.objects.filter(
        tournament__in=tournaments,
        player=user,
        rank=1
    ).count()
    
    second_places = TournamentStanding.objects.filter(
        tournament__in=tournaments,
        player=user,
        rank=2
    ).count()
    
    third_places = TournamentStanding.objects.filter(
        tournament__in=tournaments,
        player=user,
        rank=3
    ).count()
    
    # Tournament win milestones
    if first_places >= 1:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_win_1',
            defaults={'count': first_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = first_places
            achievement.save()
            
    if first_places >= 3:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_win_3',
            defaults={'count': first_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = first_places
            achievement.save()
            
    if first_places >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_win_5',
            defaults={'count': first_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = first_places
            achievement.save()
            
    if first_places >= 10:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='tournament_win_10',
            defaults={'count': first_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = first_places
            achievement.save()
    
    # Second place achievements
    if second_places >= 3:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='silver_medal_3',
            defaults={'count': second_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = second_places
            achievement.save()
            
    if second_places >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='silver_medal_5',
            defaults={'count': second_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = second_places
            achievement.save()
    
    # Third place achievements
    if third_places >= 3:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='bronze_medal_3',
            defaults={'count': third_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = third_places
            achievement.save()
            
    if third_places >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='bronze_medal_5',
            defaults={'count': third_places}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = third_places
            achievement.save()
    
    # --- SPECIAL TOURNAMENT ACHIEVEMENTS ---
    
    for tournament in tournaments:
        # Get tournament type and time control
        tournament_type = tournament.tournament_type
        time_control = tournament.time_control
        
        # Check if user won this tournament
        try:
            user_standing = tournament.standings.get(player=user)
            is_winner = user_standing.rank == 1
            
            # Check for tournament format specific achievements
            if is_winner:
                # Format specific achievements
                if tournament_type == 'swiss':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='swiss_master'
                    )
                    if created:
                        new_achievements.append(achievement)
                    
                elif tournament_type == 'round_robin':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='round_robin_champion'
                    )
                    if created:
                        new_achievements.append(achievement)
                    
                elif tournament_type == 'double_round_robin':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='double_round_robin_king'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Time control specific achievements
                if time_control == 'bullet':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='bullet_blitzer'
                    )
                    if created:
                        new_achievements.append(achievement)
                    
                elif time_control == 'blitz':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='blitz_boss'
                    )
                    if created:
                        new_achievements.append(achievement)
                    
                elif time_control == 'rapid':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='rapid_ruler'
                    )
                    if created:
                        new_achievements.append(achievement)
                    
                elif time_control == 'classical':
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='classical_conqueror'
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Check for "Comeback Kid" achievement
                # Get user's first match in this tournament
                first_match = Match.objects.filter(
                    tournament=tournament,
                    round__number=1
                ).filter(
                    Q(white_player=user) | Q(black_player=user)
                ).first()
                
                if first_match:
                    # Check if user lost their first match
                    lost_first_match = (first_match.white_player == user and first_match.result == 'black_win') or \
                                      (first_match.black_player == user and first_match.result == 'white_win')
                    
                    if lost_first_match:
                        achievement, created = Achievement.objects.get_or_create(
                            user=user, 
                            achievement_type='comeback_kid',
                            tournament=tournament
                        )
                        if created:
                            new_achievements.append(achievement)
            
            # Check for "Perfect Score" achievement
            # Get all user's matches in this tournament
            user_matches = Match.objects.filter(
                tournament=tournament
            ).filter(
                Q(white_player=user) | Q(black_player=user)
            ).exclude(result='pending')
            
            if user_matches.exists():
                wins = 0
                losses = 0
                draws = 0
                
                for match in user_matches:
                    if (match.white_player == user and match.result == 'white_win') or \
                       (match.black_player == user and match.result == 'black_win'):
                        wins += 1
                    elif (match.white_player == user and match.result == 'black_win') or \
                         (match.black_player == user and match.result == 'white_win'):
                        losses += 1
                    else:
                        draws += 1
                
                # Check for various achievement patterns
                total_games = wins + losses + draws
                
                # Perfect Score
                if total_games > 0 and wins == total_games:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='perfect_score',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Undefeated
                if total_games > 0 and losses == 0:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='undefeated',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Support Bear (No wins)
                if total_games > 0 and wins == 0:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='support_bear',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Chess for Dummies (Last place)
                if user_standing.rank == tournament.participants.count():
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='dummies',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # The Ace (Win all games)
                if is_winner and wins == total_games:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='goat',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Truce Seeker (50%+ draws)
                if total_games > 0 and draws / total_games >= 0.5:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user, 
                        achievement_type='truce_seeker',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
                
                # Giant Slayer
                highest_rated_player = tournament.participants.order_by('-elo').first()
                if highest_rated_player and highest_rated_player != user:
                    # Look for matches against the highest rated player
                    highest_rated_matches = user_matches.filter(
                        Q(white_player=highest_rated_player, black_player=user) |
                        Q(white_player=user, black_player=highest_rated_player)
                    )
                    
                    for match in highest_rated_matches:
                        # Check if user won against the highest rated player
                        if (match.white_player == user and match.result == 'white_win') or \
                           (match.black_player == user and match.result == 'black_win'):
                            achievement, created = Achievement.objects.get_or_create(
                                user=user, 
                                achievement_type='giant_slayer',
                                tournament=tournament
                            )
                            if created:
                                new_achievements.append(achievement)
                            break
                            
        except TournamentStanding.DoesNotExist:
            # User doesn't have standings in this tournament
            continue
    
    # --- MATCH-BASED ACHIEVEMENTS ---
    
    # Get all user's matches
    all_matches = Match.objects.filter(
        Q(white_player=user) | Q(black_player=user)
    ).exclude(result='pending').order_by('tournament__date', 'round__number')
    
    # Check for streaks
    current_streak = 0
    max_streak = 0
    
    white_streak = 0
    max_white_streak = 0
    
    black_streak = 0
    max_black_streak = 0
    
    for match in all_matches:
        # Check overall streak
        if (match.white_player == user and match.result == 'white_win') or \
           (match.black_player == user and match.result == 'black_win'):
            # Win
            current_streak += 1
            max_streak = max(max_streak, current_streak)
            
            # Check color-specific streaks
            if match.white_player == user:
                white_streak += 1
                max_white_streak = max(max_white_streak, white_streak)
                black_streak = 0  # Reset other color streak
            else:
                black_streak += 1
                max_black_streak = max(max_black_streak, black_streak)
                white_streak = 0  # Reset other color streak
                
        else:
            # Loss or draw
            current_streak = 0
            
            # Reset color-specific streaks
            if match.white_player == user:
                white_streak = 0
            else:
                black_streak = 0
    
    # Hat Trick (3 consecutive wins)
    if max_streak >= 3:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='hat_trick'
        )
        if created:
            new_achievements.append(achievement)
    
    # Winning Streak (5 consecutive wins)
    if max_streak >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='winning_streak_5'
        )
        if created:
            new_achievements.append(achievement)
    
    # Unstoppable (10 consecutive wins)
    if max_streak >= 10:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='winning_streak_10'
        )
        if created:
            new_achievements.append(achievement)
    
    # White Dominator (5 consecutive wins as White)
    if max_white_streak >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='white_dominator'
        )
        if created:
            new_achievements.append(achievement)
    
    # Black Defender (5 consecutive wins as Black)
    if max_black_streak >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='black_defender'
        )
        if created:
            new_achievements.append(achievement)
    
    # Check for Underdog achievement
    underdog_count = 0
    for match in all_matches:
        if match.white_player == user and match.result == 'white_win' and \
           match.black_player.elo >= (match.white_player.elo + 200):
            underdog_count += 1
            
        elif match.black_player == user and match.result == 'black_win' and \
             match.white_player.elo >= (match.black_player.elo + 200):
            underdog_count += 1
    
    if underdog_count > 0:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='underdog',
            defaults={'count': underdog_count}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = underdog_count
            achievement.save()
    
    # --- RATING-BASED ACHIEVEMENTS ---
    
    # Check rating milestones
    rating = user.blitz_elo  # Using blitz rating as the primary rating
    
    if rating >= 1600:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='rating_1600'
        )
        if created:
            new_achievements.append(achievement)
    
    if rating >= 1800:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='rating_1800'
        )
        if created:
            new_achievements.append(achievement)
    
    if rating >= 2000:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='rating_2000'
        )
        if created:
            new_achievements.append(achievement)
    
    if rating >= 2200:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='rating_2200'
        )
        if created:
            new_achievements.append(achievement)
    
    return new_achievements