# comprehensive_test_achievements.py
import django
import os
import sys

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laurierboom_chess.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg, Max, Min
from chess.models import Tournament, User, Match, Round, TournamentStanding, Achievement
from chess.utils import update_tournament_standings
from chess.achievement_service import check_achievements

User = get_user_model()

def test_all_achievements():
    """
    Test all achievement types to check they're functioning properly
    """
    print("====== TESTING ALL ACHIEVEMENT TYPES ======\n")
    
    # Get all achievement types from the Achievement model
    all_achievement_types = dict(Achievement.ACHIEVEMENT_TYPES)
    print(f"Found {len(all_achievement_types)} achievement types defined in the model\n")
    
    # Group achievements by category for testing
    achievement_categories = {
        "Tournament Victories": ['tournament_win_1', 'tournament_win_3', 'tournament_win_5', 'tournament_win_10'],
        "Tournament Medals": ['silver_medal_3', 'silver_medal_5', 'bronze_medal_3', 'bronze_medal_5'],
        "Streaks": ['hat_trick', 'winning_streak_5', 'winning_streak_10', 'white_dominator', 'black_defender'],
        "Perfect Performance": ['clean_sweep', 'perfect_score', 'undefeated'],
        "Experience-based": ['tournament_veteran_10', 'tournament_veteran_25', 'tournament_veteran_50'],
        "Special Game Outcomes": ['comeback_kid', 'underdog', 'giant_slayer'],
        "Format Specialists": ['swiss_master', 'round_robin_champion', 'double_round_robin_king'],
        "Time Control Specialists": ['bullet_blitzer', 'blitz_boss', 'rapid_ruler', 'classical_conqueror'],
        "Rating Milestones": ['rating_1600', 'rating_1800', 'rating_2000', 'rating_2200'],
        "Special Trophies": ['support_bear', 'dummies', 'goat', 'truce_seeker'],
        "Community Trophies": ['social_butterfly', 'rival_nemesis', 'kingmaker', 'bar_legend'],
        "Milestone Trophies": ['century_club', 'blitz_marathon'],
        "Whimsical Trophies": ['phoenix_rising', 'draw_magnet', 'the_spoiler', 'last_stand'],
        "Achievement Trophies": ['grand_slam', 'format_master', 'seasonal_champion', 'the_perfectionist'],
        "Unconventional Trophies": ['comeback_king', 'late_bloomer', 'score_maximizer', 'early_departure']
    }
    
    # Get counts of all achievements by type
    achievement_counts = dict(Achievement.objects.values('achievement_type')
                             .annotate(count=Count('id'))
                             .values_list('achievement_type', 'count'))
    
    # Function to test tournament victory achievements
    def test_tournament_victories():
        print("\n------ Testing Tournament Victory Achievements ------")
        
        # Get users with tournament wins
        winners = User.objects.annotate(
            wins=Count('standings', filter=Q(standings__rank=1, standings__tournament__is_completed=True))
        ).filter(wins__gt=0).order_by('-wins')
        
        print(f"Found {winners.count()} users with tournament wins")
        
        for winner in winners[:5]:  # Limit to 5 users to avoid too much output
            win_count = winner.wins
            print(f"\nUser: {winner.username}, Tournament Wins: {win_count}")
            
            # Test each tournament victory achievement
            for achievement_type in ['tournament_win_1', 'tournament_win_3', 'tournament_win_5', 'tournament_win_10']:
                threshold = int(achievement_type.split('_')[-1])
                
                # Check if user should have this achievement
                should_have = win_count >= threshold
                
                # Check if user actually has this achievement
                has_achievement = Achievement.objects.filter(
                    user=winner,
                    achievement_type=achievement_type
                ).exists()
                
                if should_have and has_achievement:
                    achievement = Achievement.objects.get(user=winner, achievement_type=achievement_type)
                    print(f"✓ Has {achievement_type} (Expected for {win_count} wins, count: {achievement.count})")
                elif should_have and not has_achievement:
                    print(f"❌ Missing {achievement_type} (Expected for {win_count} wins)")
                elif not should_have and has_achievement:
                    achievement = Achievement.objects.get(user=winner, achievement_type=achievement_type)
                    print(f"⚠️ Unexpected {achievement_type} (Not expected for {win_count} wins, count: {achievement.count})")
                else:
                    print(f"✓ Correctly does not have {achievement_type} (Not expected for {win_count} wins)")
    
    # Function to test medal achievements (silver, bronze)
    def test_medal_achievements():
        print("\n------ Testing Medal Achievements ------")
        
        # Get users with 2nd place finishes
        silver_winners = User.objects.annotate(
            silver_count=Count('standings', filter=Q(standings__rank=2, standings__tournament__is_completed=True))
        ).filter(silver_count__gt=0).order_by('-silver_count')
        
        print(f"Found {silver_winners.count()} users with silver medals")
        
        for user in silver_winners[:3]:  # Limit to 3 users
            silver_count = user.silver_count
            print(f"\nUser: {user.username}, Silver Medals: {silver_count}")
            
            # Test silver medal achievements
            for achievement_type in ['silver_medal_3', 'silver_medal_5']:
                threshold = int(achievement_type.split('_')[-1])
                
                # Check if user should have this achievement
                should_have = silver_count >= threshold
                
                # Check if user actually has this achievement
                has_achievement = Achievement.objects.filter(
                    user=user,
                    achievement_type=achievement_type
                ).exists()
                
                if should_have and has_achievement:
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    print(f"✓ Has {achievement_type} (Expected for {silver_count} silver medals, count: {achievement.count})")
                elif should_have and not has_achievement:
                    print(f"❌ Missing {achievement_type} (Expected for {silver_count} silver medals)")
                elif not should_have and has_achievement:
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    print(f"⚠️ Unexpected {achievement_type} (Not expected for {silver_count} silver medals, count: {achievement.count})")
                else:
                    print(f"✓ Correctly does not have {achievement_type} (Not expected for {silver_count} silver medals)")
        
        # Get users with 3rd place finishes
        bronze_winners = User.objects.annotate(
            bronze_count=Count('standings', filter=Q(standings__rank=3, standings__tournament__is_completed=True))
        ).filter(bronze_count__gt=0).order_by('-bronze_count')
        
        print(f"\nFound {bronze_winners.count()} users with bronze medals")
        
        for user in bronze_winners[:3]:  # Limit to 3 users
            bronze_count = user.bronze_count
            print(f"\nUser: {user.username}, Bronze Medals: {bronze_count}")
            
            # Test bronze medal achievements
            for achievement_type in ['bronze_medal_3', 'bronze_medal_5']:
                threshold = int(achievement_type.split('_')[-1])
                
                # Check if user should have this achievement
                should_have = bronze_count >= threshold
                
                # Check if user actually has this achievement
                has_achievement = Achievement.objects.filter(
                    user=user,
                    achievement_type=achievement_type
                ).exists()
                
                if should_have and has_achievement:
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    print(f"✓ Has {achievement_type} (Expected for {bronze_count} bronze medals, count: {achievement.count})")
                elif should_have and not has_achievement:
                    print(f"❌ Missing {achievement_type} (Expected for {bronze_count} bronze medals)")
                elif not should_have and has_achievement:
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    print(f"⚠️ Unexpected {achievement_type} (Not expected for {bronze_count} bronze medals, count: {achievement.count})")
                else:
                    print(f"✓ Correctly does not have {achievement_type} (Not expected for {bronze_count} bronze medals)")
    
    # Function to test streak-based achievements
    def test_streak_achievements():
        print("\n------ Testing Streak Achievements ------")
        
        # Get users with streak achievements
        users_with_streaks = User.objects.filter(
            achievements__achievement_type__in=['hat_trick', 'winning_streak_5', 'winning_streak_10', 'white_dominator', 'black_defender']
        ).distinct()
        
        print(f"Found {users_with_streaks.count()} users with streak achievements")
        
        for user in users_with_streaks:
            print(f"\nUser: {user.username}")
            
            streak_achievements = Achievement.objects.filter(
                user=user,
                achievement_type__in=['hat_trick', 'winning_streak_5', 'winning_streak_10', 'white_dominator', 'black_defender']
            )
            
            for achievement in streak_achievements:
                print(f"✓ Has {achievement.achievement_type} (count: {achievement.count})")
    
    # Function to test perfect performance achievements
    def test_perfect_performance():
        print("\n------ Testing Perfect Performance Achievements ------")
        
        # Get users with perfect performance achievements
        users_with_perfect = User.objects.filter(
            achievements__achievement_type__in=['clean_sweep', 'perfect_score', 'undefeated']
        ).distinct()
        
        print(f"Found {users_with_perfect.count()} users with perfect performance achievements")
        
        for user in users_with_perfect:
            print(f"\nUser: {user.username}")
            
            perfect_achievements = Achievement.objects.filter(
                user=user,
                achievement_type__in=['clean_sweep', 'perfect_score', 'undefeated']
            )
            
            for achievement in perfect_achievements:
                # Get the associated tournament if it exists
                tournament_name = "Unknown tournament"
                if achievement.tournament:
                    tournament_name = achievement.tournament.name
                
                print(f"✓ Has {achievement.achievement_type} in tournament: {tournament_name}")
    
    # Function to test format specialist achievements
    def test_format_specialists():
        print("\n------ Testing Format Specialist Achievements ------")
        
        # Get users with format specialist achievements
        users_with_format = User.objects.filter(
            achievements__achievement_type__in=['swiss_master', 'round_robin_champion', 'double_round_robin_king']
        ).distinct()
        
        print(f"Found {users_with_format.count()} users with format specialist achievements")
        
        for user in users_with_format:
            print(f"\nUser: {user.username}")
            
            format_achievements = Achievement.objects.filter(
                user=user,
                achievement_type__in=['swiss_master', 'round_robin_champion', 'double_round_robin_king']
            )
            
            for achievement in format_achievements:
                print(f"✓ Has {achievement.achievement_type} (count: {achievement.count})")
            
            # Check if they've won tournaments of these types
            won_swiss = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__tournament_type='swiss',
                tournament__is_completed=True
            ).exists()
            
            won_round_robin = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__tournament_type='round_robin',
                tournament__is_completed=True
            ).exists()
            
            won_double_round_robin = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__tournament_type='double_round_robin',
                tournament__is_completed=True
            ).exists()
            
            # Check for potential missing achievements
            if won_swiss and not Achievement.objects.filter(user=user, achievement_type='swiss_master').exists():
                print(f"❌ Missing swiss_master achievement despite winning Swiss tournaments")
            
            if won_round_robin and not Achievement.objects.filter(user=user, achievement_type='round_robin_champion').exists():
                print(f"❌ Missing round_robin_champion achievement despite winning Round Robin tournaments")
            
            if won_double_round_robin and not Achievement.objects.filter(user=user, achievement_type='double_round_robin_king').exists():
                print(f"❌ Missing double_round_robin_king achievement despite winning Double Round Robin tournaments")
    
    # Function to test time control specialist achievements
    def test_time_control_specialists():
        print("\n------ Testing Time Control Specialist Achievements ------")
        
        # Get users with time control specialist achievements
        users_with_timecontrol = User.objects.filter(
            achievements__achievement_type__in=['bullet_blitzer', 'blitz_boss', 'rapid_ruler', 'classical_conqueror']
        ).distinct()
        
        print(f"Found {users_with_timecontrol.count()} users with time control specialist achievements")
        
        for user in users_with_timecontrol:
            print(f"\nUser: {user.username}")
            
            timecontrol_achievements = Achievement.objects.filter(
                user=user,
                achievement_type__in=['bullet_blitzer', 'blitz_boss', 'rapid_ruler', 'classical_conqueror']
            )
            
            for achievement in timecontrol_achievements:
                print(f"✓ Has {achievement.achievement_type} (count: {achievement.count})")
            
            # Check if they've won tournaments of these time controls
            won_bullet = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__time_control='bullet',
                tournament__is_completed=True
            ).exists()
            
            won_blitz = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__time_control='blitz',
                tournament__is_completed=True
            ).exists()
            
            won_rapid = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__time_control='rapid',
                tournament__is_completed=True
            ).exists()
            
            won_classical = TournamentStanding.objects.filter(
                player=user,
                rank=1,
                tournament__time_control='classical',
                tournament__is_completed=True
            ).exists()
            
            # Check for potential missing achievements
            if won_bullet and not Achievement.objects.filter(user=user, achievement_type='bullet_blitzer').exists():
                print(f"❌ Missing bullet_blitzer achievement despite winning Bullet tournaments")
            
            if won_blitz and not Achievement.objects.filter(user=user, achievement_type='blitz_boss').exists():
                print(f"❌ Missing blitz_boss achievement despite winning Blitz tournaments")
            
            if won_rapid and not Achievement.objects.filter(user=user, achievement_type='rapid_ruler').exists():
                print(f"❌ Missing rapid_ruler achievement despite winning Rapid tournaments")
            
            if won_classical and not Achievement.objects.filter(user=user, achievement_type='classical_conqueror').exists():
                print(f"❌ Missing classical_conqueror achievement despite winning Classical tournaments")
    
    # Function to test rating milestone achievements
    def test_rating_milestones():
        print("\n------ Testing Rating Milestone Achievements ------")
        
        # Get users with rating milestone achievements
        users_with_rating = User.objects.filter(
            achievements__achievement_type__in=['rating_1600', 'rating_1800', 'rating_2000', 'rating_2200']
        ).distinct()
        
        print(f"Found {users_with_rating.count()} users with rating milestone achievements")
        
        for user in users_with_rating:
            print(f"\nUser: {user.username}")
            print(f"Current ratings: Blitz: {user.blitz_elo}, Bullet: {user.bullet_elo}, Rapid: {user.rapid_elo}, Classical: {user.classical_elo}")
            
            rating_achievements = Achievement.objects.filter(
                user=user,
                achievement_type__in=['rating_1600', 'rating_1800', 'rating_2000', 'rating_2200']
            )
            
            for achievement in rating_achievements:
                print(f"✓ Has {achievement.achievement_type}")
            
            # Check for potential missing or incorrect achievements
            rating = max(user.blitz_elo, user.bullet_elo, user.rapid_elo, user.classical_elo, user.elo)
            
            if rating >= 1600 and not Achievement.objects.filter(user=user, achievement_type='rating_1600').exists():
                print(f"❌ Missing rating_1600 achievement despite having rating {rating}")
            
            if rating >= 1800 and not Achievement.objects.filter(user=user, achievement_type='rating_1800').exists():
                print(f"❌ Missing rating_1800 achievement despite having rating {rating}")
            
            if rating >= 2000 and not Achievement.objects.filter(user=user, achievement_type='rating_2000').exists():
                print(f"❌ Missing rating_2000 achievement despite having rating {rating}")
            
            if rating >= 2200 and not Achievement.objects.filter(user=user, achievement_type='rating_2200').exists():
                print(f"❌ Missing rating_2200 achievement despite having rating {rating}")
    
    # Function to test milestone/quantity-based achievements
    def test_milestone_achievements():
        print("\n------ Testing Milestone/Quantity-based Achievements ------")
        
        # Get users with tournament participation milestones
        users_by_tournament_count = User.objects.annotate(
            tournament_count=Count('tournaments', filter=Q(tournaments__is_completed=True))
        ).filter(tournament_count__gt=0).order_by('-tournament_count')[:5]
        
        print(f"Top users by tournament participation:")
        for user in users_by_tournament_count:
            print(f"\nUser: {user.username}, Tournaments: {user.tournament_count}")
            
            # Check for tournament veteran achievements
            for achievement_type in ['tournament_veteran_10', 'tournament_veteran_25', 'tournament_veteran_50']:
                threshold = int(achievement_type.split('_')[-1])
                
                # Check if user should have this achievement
                should_have = user.tournament_count >= threshold
                
                # Check if user actually has this achievement
                has_achievement = Achievement.objects.filter(
                    user=user,
                    achievement_type=achievement_type
                ).exists()
                
                if should_have and has_achievement:
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    print(f"✓ Has {achievement_type} (Expected for {user.tournament_count} tournaments, count: {achievement.count})")
                elif should_have and not has_achievement:
                    print(f"❌ Missing {achievement_type} (Expected for {user.tournament_count} tournaments)")
                elif not should_have and has_achievement:
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    print(f"⚠️ Unexpected {achievement_type} (Not expected for {user.tournament_count} tournaments, count: {achievement.count})")
                else:
                    print(f"✓ Correctly does not have {achievement_type} (Not expected for {user.tournament_count} tournaments)")
        
        # Users with blitz marathon achievement
        blitz_marathon_users = User.objects.filter(
            achievements__achievement_type='blitz_marathon'
        )
        
        print(f"\nFound {blitz_marathon_users.count()} users with blitz_marathon achievement")
        for user in blitz_marathon_users[:3]:  # Limit to 3
            achievement = Achievement.objects.get(user=user, achievement_type='blitz_marathon')
            print(f"User: {user.username} has blitz_marathon (count: {achievement.count})")
    
    # Function to test special achievements
    def test_special_achievements():
        print("\n------ Testing Special Achievements ------")
        
        # List of special achievements to check
        special_achievements = [
            'comeback_kid', 'underdog', 'giant_slayer', 'support_bear', 
            'dummies', 'goat', 'truce_seeker', 'phoenix_rising', 
            'draw_magnet', 'social_butterfly', 'rival_nemesis'
        ]
        
        # Check each special achievement
        for achievement_type in special_achievements:
            users_with_achievement = User.objects.filter(
                achievements__achievement_type=achievement_type
            )
            
            count = users_with_achievement.count()
            
            if count > 0:
                print(f"\nAchievement: {achievement_type}")
                print(f"Found {count} users with this achievement")
                
                # Show a few examples
                for user in users_with_achievement[:2]:  # Limit to 2
                    achievement = Achievement.objects.get(user=user, achievement_type=achievement_type)
                    tournament_info = f" in tournament {achievement.tournament.name}" if achievement.tournament else ""
                    print(f"User: {user.username} (count: {achievement.count}){tournament_info}")
    
    # Function to test all achievements in general
    def test_all_achievement_types():
        print("\n------ Testing All Achievement Types ------")
        
        # Get count of each achievement type
        achievement_stats = []
        for achievement_type, achievement_name in all_achievement_types.items():
            count = Achievement.objects.filter(achievement_type=achievement_type).count()
            users_count = User.objects.filter(achievements__achievement_type=achievement_type).distinct().count()
            achievement_stats.append((achievement_type, achievement_name, count, users_count))
        
        # Sort by count (most common first)
        achievement_stats.sort(key=lambda x: x[2], reverse=True)
        
        print("Achievement statistics (sorted by frequency):")
        print(f"{'Type':<25} {'Name':<30} {'Count':<10} {'Users':<10}")
        print("-" * 75)
        
        for achievement_type, achievement_name, count, users_count in achievement_stats:
            print(f"{achievement_type:<25} {achievement_name:<30} {count:<10} {users_count:<10}")
    
    # Function to test achievement checking process
    def test_achievement_checking_process():
        print("\n------ Testing Achievement Checking Process ------")
        
        # Find a recent tournament winner
        recent_winner = TournamentStanding.objects.filter(
            rank=1,
            tournament__is_completed=True
        ).order_by('-tournament__date').first()
        
        if not recent_winner:
            print("No tournament winners found to test")
            return
        
        winner = recent_winner.player
        tournament = recent_winner.tournament
        
        print(f"Testing achievement check for {winner.username} who won tournament {tournament.name}")
        
        # Testing the tournament_win_1 achievement
        achievement = Achievement.objects.filter(
            user=winner,
            achievement_type='tournament_win_1'
        ).first()
        
        if achievement:
            print(f"✓ User has tournament_win_1 achievement (count: {achievement.count})")
            
            # Delete the achievement to test recreation
            achievement.delete()
            print(f"Deleted tournament_win_1 achievement for testing")
            
            # Run the achievement check
            new_achievements = check_achievements(winner)
            
            # Check if the achievement was recreated
            achievement = Achievement.objects.filter(
                user=winner,
                achievement_type='tournament_win_1'
            ).first()
            
            if achievement:
                print(f"✓ Achievement was successfully re-created with count: {achievement.count}")
            else:
                print(f"❌ Achievement was NOT re-created!")
        else:
            print(f"❌ User does not have tournament_win_1 achievement despite winning tournaments")
            
            # Try to create it
            new_achievements = check_achievements(winner)
            
            # Check if the achievement was created
            achievement = Achievement.objects.filter(
                user=winner,
                achievement_type='tournament_win_1'
            ).first()
            
            if achievement:
                print(f"✓ Achievement was successfully created with count: {achievement.count}")
            else:
                print(f"❌ Achievement was NOT created!")

    # Run all the test functions
    test_tournament_victories()
    test_medal_achievements()
    test_streak_achievements()
    test_perfect_performance()
    test_format_specialists()
    test_time_control_specialists()
    test_rating_milestones()
    test_milestone_achievements()
    test_special_achievements()
    test_all_achievement_types()
    test_achievement_checking_process()

    print("\n====== ACHIEVEMENT TESTING COMPLETE ======")

if __name__ == '__main__':
    test_all_achievements()