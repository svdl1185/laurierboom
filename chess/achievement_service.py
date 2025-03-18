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


    # --- COMMUNITY ACHIEVEMENTS ---
    
    # Social Butterfly - Play against 15 different opponents
    opponents = set()
    for match in all_matches:
        if match.white_player == user:
            opponents.add(match.black_player.id)
        else:
            opponents.add(match.white_player.id)
    
    if len(opponents) >= 15:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='social_butterfly'
        )
        if created:
            new_achievements.append(achievement)
    
    # Rival Nemesis - Win 3 consecutive games against the same opponent
    # Group matches by opponent
    opponent_matches = {}
    for match in all_matches:
        if match.white_player == user and match.result == 'white_win':
            opponent_id = match.black_player.id
            if opponent_id not in opponent_matches:
                opponent_matches[opponent_id] = []
            opponent_matches[opponent_id].append((match.tournament.date, match.round.number, 'win'))
        elif match.black_player == user and match.result == 'black_win':
            opponent_id = match.white_player.id
            if opponent_id not in opponent_matches:
                opponent_matches[opponent_id] = []
            opponent_matches[opponent_id].append((match.tournament.date, match.round.number, 'win'))
        elif match.white_player == user and match.result != 'white_win':
            opponent_id = match.black_player.id
            if opponent_id not in opponent_matches:
                opponent_matches[opponent_id] = []
            opponent_matches[opponent_id].append((match.tournament.date, match.round.number, 'not_win'))
        elif match.black_player == user and match.result != 'black_win':
            opponent_id = match.white_player.id
            if opponent_id not in opponent_matches:
                opponent_matches[opponent_id] = []
            opponent_matches[opponent_id].append((match.tournament.date, match.round.number, 'not_win'))
    
    # Check for 3 consecutive wins against any opponent
    for opponent_id, matches in opponent_matches.items():
        # Sort by date and round
        matches.sort()
        consecutive_wins = 0
        max_consecutive_wins = 0
        
        for _, _, result in matches:
            if result == 'win':
                consecutive_wins += 1
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_wins = 0
        
        if max_consecutive_wins >= 3:
            achievement, created = Achievement.objects.get_or_create(
                user=user, 
                achievement_type='rival_nemesis'
            )
            if created:
                new_achievements.append(achievement)
            break
    
    # Bar Legend - Participate in 10 consecutive weekly tournaments
    all_tournaments = user.tournaments.order_by('date')
    if all_tournaments.count() >= 10:
        # Convert to list for easier manipulation
        tournament_dates = list(all_tournaments.values_list('date', flat=True))
        
        # Check for consecutive weekly tournaments
        consecutive_weeks = 1
        max_consecutive_weeks = 1
        
        for i in range(1, len(tournament_dates)):
            # If the difference between tournaments is 5-9 days, consider it weekly
            days_diff = (tournament_dates[i] - tournament_dates[i-1]).days
            if 5 <= days_diff <= 9:
                consecutive_weeks += 1
                max_consecutive_weeks = max(max_consecutive_weeks, consecutive_weeks)
            else:
                consecutive_weeks = 1
        
        if max_consecutive_weeks >= 10:
            achievement, created = Achievement.objects.get_or_create(
                user=user,
                achievement_type='bar_legend'
            )
            if created:
                new_achievements.append(achievement)
    
    # --- MILESTONE ACHIEVEMENTS ---
    
    # Century Club - Play 100 rated games
    total_games = all_matches.count()
    if total_games >= 100:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='century_club'
        )
        if created:
            new_achievements.append(achievement)
    
    # Blitz Marathon - Play 10 games in a single day
    # Group matches by date
    matches_by_date = {}
    for match in all_matches:
        match_date = match.tournament.date
        if match_date not in matches_by_date:
            matches_by_date[match_date] = 0
        matches_by_date[match_date] += 1
    
    # Check if any date has 10+ games
    for date, count in matches_by_date.items():
        if count >= 10:
            achievement, created = Achievement.objects.get_or_create(
                user=user,
                achievement_type='blitz_marathon'
            )
            if created:
                new_achievements.append(achievement)
            break
    
    # --- WHIMSICAL ACHIEVEMENTS ---
    
    # Phoenix Rising - Lose 3 consecutive games then win the next 3
    if all_matches.count() >= 6:
        results = []
        for match in all_matches.order_by('tournament__date', 'round__number'):
            if (match.white_player == user and match.result == 'white_win') or \
               (match.black_player == user and match.result == 'black_win'):
                results.append('win')
            elif match.result != 'draw':  # Only count definite losses
                results.append('loss')
        
        # Look for pattern: loss, loss, loss, win, win, win
        for i in range(len(results) - 5):
            if results[i:i+6] == ['loss', 'loss', 'loss', 'win', 'win', 'win']:
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type='phoenix_rising'
                )
                if created:
                    new_achievements.append(achievement)
                break
    
    # Draw Magnet - Draw 3 consecutive games
    if all_matches.count() >= 3:
        consecutive_draws = 0
        max_consecutive_draws = 0
        
        for match in all_matches.order_by('tournament__date', 'round__number'):
            if match.result == 'draw':
                consecutive_draws += 1
                max_consecutive_draws = max(max_consecutive_draws, consecutive_draws)
            else:
                consecutive_draws = 0
        
        if max_consecutive_draws >= 3:
            achievement, created = Achievement.objects.get_or_create(
                user=user,
                achievement_type='draw_magnet'
            )
            if created:
                new_achievements.append(achievement)
    
    # Last Stand - Win your final game after losing all previous games in a tournament
    for tournament in tournaments:
        tournament_matches = Match.objects.filter(
            tournament=tournament
        ).filter(
            Q(white_player=user) | Q(black_player=user)
        ).exclude(result='pending').order_by('round__number')
        
        if tournament_matches.count() >= 2:
            # Get only the user's results
            results = []
            for match in tournament_matches:
                if (match.white_player == user and match.result == 'white_win') or \
                   (match.black_player == user and match.result == 'black_win'):
                    results.append('win')
                elif match.result == 'draw':
                    results.append('draw')
                else:
                    results.append('loss')
            
            # Check if all games were losses except the last one which was a win
            if all(result == 'loss' for result in results[:-1]) and results[-1] == 'win':
                achievement, created = Achievement.objects.get_or_create(
                    user=user,
                    achievement_type='last_stand',
                    tournament=tournament
                )
                if created:
                    new_achievements.append(achievement)
    
    # --- ACHIEVEMENT TROPHIES ---
    
    # Grand Slam - Win tournaments in all four time controls
    time_control_wins = set()
    for tournament in tournaments:
        try:
            standing = TournamentStanding.objects.get(
                tournament=tournament,
                player=user,
                rank=1
            )
            time_control_wins.add(tournament.time_control)
        except TournamentStanding.DoesNotExist:
            pass
    
    # Check if all 4 time controls have been won
    if len(time_control_wins) >= 4:  # bullet, blitz, rapid, classical
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='grand_slam'
        )
        if created:
            new_achievements.append(achievement)
    
    # Format Master - Win tournaments in all three formats
    format_wins = set()
    for tournament in tournaments:
        if tournament.tournament_type:  # Skip tournaments with no defined type
            try:
                standing = TournamentStanding.objects.get(
                    tournament=tournament,
                    player=user,
                    rank=1
                )
                format_wins.add(tournament.tournament_type)
            except TournamentStanding.DoesNotExist:
                pass
    
    # Check if all 3 formats have been won
    all_formats = {'swiss', 'round_robin', 'double_round_robin'}
    if format_wins >= all_formats:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='format_master'
        )
        if created:
            new_achievements.append(achievement)
    
    # Seasonal Champion - Win tournaments in Spring, Summer, Fall, and Winter
    season_wins = set()
    for tournament in tournaments:
        try:
            standing = TournamentStanding.objects.get(
                tournament=tournament,
                player=user,
                rank=1
            )
            # Determine season based on month
            month = tournament.date.month
            if 3 <= month <= 5:
                season_wins.add('spring')
            elif 6 <= month <= 8:
                season_wins.add('summer')
            elif 9 <= month <= 11:
                season_wins.add('fall')
            else:  # 12, 1, 2
                season_wins.add('winter')
        except TournamentStanding.DoesNotExist:
            pass
    
    # Check if all 4 seasons have been won
    if len(season_wins) >= 4:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='seasonal_champion'
        )
        if created:
            new_achievements.append(achievement)
    
    # The Perfectionist - Complete 5 tournaments without a single loss
    perfect_tournaments = 0
    for tournament in tournaments:
        tournament_matches = Match.objects.filter(
            tournament=tournament
        ).filter(
            Q(white_player=user) | Q(black_player=user)
        ).exclude(result='pending')
        
        # Check if there are any losses
        has_loss = False
        for match in tournament_matches:
            if (match.white_player == user and match.result == 'black_win') or \
               (match.black_player == user and match.result == 'white_win'):
                has_loss = True
                break
        
        if not has_loss and tournament_matches.exists():
            perfect_tournaments += 1
    
    if perfect_tournaments >= 5:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            achievement_type='the_perfectionist'
        )
        if created:
            new_achievements.append(achievement)
    
    # --- UNCONVENTIONAL ACHIEVEMENTS ---
    
    # Comeback King/Queen - Win a tournament after being in bottom half before final round
    for tournament in tournaments:
        # Check if user won this tournament
        try:
            standing = TournamentStanding.objects.get(
                tournament=tournament,
                player=user,
                rank=1
            )
            
            # If tournament had at least 2 rounds, check standing before final round
            rounds = tournament.rounds.order_by('number')
            if rounds.count() >= 2:
                penultimate_round = rounds.order_by('-number')[1]  # Second to last round
                
                # Calculate standings after penultimate round
                # This is simplified - ideally we would get historical standings
                matches_before_final = Match.objects.filter(
                    tournament=tournament,
                    round__number__lte=penultimate_round.number
                ).exclude(result='pending')
                
                # Count points for each player
                player_points = {}
                for match in matches_before_final:
                    if match.result == 'white_win':
                        if match.white_player.id not in player_points:
                            player_points[match.white_player.id] = 0
                        player_points[match.white_player.id] += 1
                    elif match.result == 'black_win':
                        if match.black_player.id not in player_points:
                            player_points[match.black_player.id] = 0
                        player_points[match.black_player.id] += 1
                    elif match.result == 'draw':
                        if match.white_player.id not in player_points:
                            player_points[match.white_player.id] = 0
                        if match.black_player.id not in player_points:
                            player_points[match.black_player.id] = 0
                        player_points[match.white_player.id] += 0.5
                        player_points[match.black_player.id] += 0.5
                
                # Sort players by points
                sorted_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)
                
                # Check if user was in bottom half
                player_position = next((i for i, (pid, _) in enumerate(sorted_players) if pid == user.id), -1)
                if player_position >= len(sorted_players) / 2:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user,
                        achievement_type='comeback_king',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
        except TournamentStanding.DoesNotExist:
            continue
    
    # Late Bloomer - Win your first tournament after playing in 10+ tournaments
    first_win = None
    for tournament in tournaments.order_by('date'):
        try:
            standing = TournamentStanding.objects.get(
                tournament=tournament,
                player=user,
                rank=1
            )
            first_win = tournament
            break
        except TournamentStanding.DoesNotExist:
            continue
    
    if first_win:
        # Count tournaments before this win
        tournaments_before_win = tournaments.filter(date__lt=first_win.date).count()
        if tournaments_before_win >= 10:
            achievement, created = Achievement.objects.get_or_create(
                user=user,
                achievement_type='late_bloomer',
                tournament=first_win
            )
            if created:
                new_achievements.append(achievement)
    
    # Score Maximizer - Score 90%+ of possible points in a tournament with 5+ rounds
    for tournament in tournaments:
        rounds = tournament.rounds.count()
        if rounds >= 5:
            try:
                standing = TournamentStanding.objects.get(
                    tournament=tournament,
                    player=user
                )
                
                # Calculate maximum possible points
                # In a tournament with n rounds, max points is n
                max_points = rounds
                
                # Check if scored 90%+ of possible points
                if standing.score >= 0.9 * max_points:
                    achievement, created = Achievement.objects.get_or_create(
                        user=user,
                        achievement_type='score_maximizer',
                        tournament=tournament
                    )
                    if created:
                        new_achievements.append(achievement)
            except TournamentStanding.DoesNotExist:
                continue

    # Count forfeits for a player
    forfeited_matches = Match.objects.filter(
        (Q(white_player=user) & Q(result='white_forfeit')) | 
        (Q(black_player=user) & Q(result='black_forfeit'))
    ).count()

    if forfeited_matches >= 3:
        achievement, created = Achievement.objects.get_or_create(
            user=user, 
            achievement_type='early_departure',
            defaults={'count': forfeited_matches}
        )
        if created:
            new_achievements.append(achievement)
        else:
            achievement.count = forfeited_matches
            achievement.save()
    
    return new_achievements