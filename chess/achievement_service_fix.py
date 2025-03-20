# achievement_service_fix.py
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

def check_missing_tournament_win_achievements():
    """
    Run this function to fix missing tournament win achievements
    """
    from django.db.models import Count
    from chess.models import User, TournamentStanding, Achievement
    
    # Find all users who have won at least one tournament
    winners = User.objects.filter(
        standings__rank=1,
        standings__tournament__is_completed=True
    ).distinct()
    
    print(f"Found {winners.count()} tournament winners")
    fixed_users = 0
    
    for winner in winners:
        # Count actual tournament wins
        win_count = TournamentStanding.objects.filter(
            player=winner,
            rank=1,
            tournament__is_completed=True
        ).count()
        
        # Check if they have the achievement
        achievement = Achievement.objects.filter(
            user=winner,
            achievement_type='tournament_win_1'
        ).first()
        
        if not achievement:
            # Create the achievement
            Achievement.objects.create(
                user=winner,
                achievement_type='tournament_win_1',
                count=win_count
            )
            print(f"Created tournament_win_1 achievement for {winner.username} with count {win_count}")
            fixed_users += 1
        elif achievement.count != win_count:
            # Update count
            achievement.count = win_count
            achievement.save()
            print(f"Updated tournament_win_1 count for {winner.username} from {achievement.count} to {win_count}")
            fixed_users += 1
    
    print(f"Fixed achievements for {fixed_users} users")
    return fixed_users

def check_other_missing_achievements():
    """
    Check for other missing achievements based on tournament standings
    """
    from chess.models import User, TournamentStanding, Achievement
    from django.db.models import Count, Q
    
    # Finding users with 3+ tournament wins for 'tournament_win_3'
    print("\nChecking for missing tournament_win_3 achievements:")
    silver_users = User.objects.annotate(
        wins=Count('standings', filter=Q(standings__rank=1, standings__tournament__is_completed=True))
    ).filter(wins__gte=3)
    
    for user in silver_users:
        achievement = Achievement.objects.filter(
            user=user,
            achievement_type='tournament_win_3'
        ).first()
        
        if not achievement:
            Achievement.objects.create(
                user=user,
                achievement_type='tournament_win_3',
                count=user.wins
            )
            print(f"Created tournament_win_3 achievement for {user.username} with count {user.wins}")
    
    # Finding users with 5+ tournament wins for 'tournament_win_5'
    print("\nChecking for missing tournament_win_5 achievements:")
    gold_users = User.objects.annotate(
        wins=Count('standings', filter=Q(standings__rank=1, standings__tournament__is_completed=True))
    ).filter(wins__gte=5)
    
    for user in gold_users:
        achievement = Achievement.objects.filter(
            user=user,
            achievement_type='tournament_win_5'
        ).first()
        
        if not achievement:
            Achievement.objects.create(
                user=user,
                achievement_type='tournament_win_5',
                count=user.wins
            )
            print(f"Created tournament_win_5 achievement for {user.username} with count {user.wins}")
    
    # Finding users with 2nd place finishes for silver medals
    print("\nChecking for missing silver_medal_3 achievements:")
    silver_medal_users = User.objects.annotate(
        silver_count=Count('standings', filter=Q(standings__rank=2, standings__tournament__is_completed=True))
    ).filter(silver_count__gte=3)
    
    for user in silver_medal_users:
        achievement = Achievement.objects.filter(
            user=user,
            achievement_type='silver_medal_3'
        ).first()
        
        if not achievement:
            Achievement.objects.create(
                user=user,
                achievement_type='silver_medal_3',
                count=user.silver_count
            )
            print(f"Created silver_medal_3 achievement for {user.username} with count {user.silver_count}")
    
    # Finding users with 3rd place finishes for bronze medals
    print("\nChecking for missing bronze_medal_3 achievements:")
    bronze_medal_users = User.objects.annotate(
        bronze_count=Count('standings', filter=Q(standings__rank=3, standings__tournament__is_completed=True))
    ).filter(bronze_count__gte=3)
    
    for user in bronze_medal_users:
        achievement = Achievement.objects.filter(
            user=user,
            achievement_type='bronze_medal_3'
        ).first()
        
        if not achievement:
            Achievement.objects.create(
                user=user,
                achievement_type='bronze_medal_3',
                count=user.bronze_count
            )
            print(f"Created bronze_medal_3 achievement for {user.username} with count {user.bronze_count}")

def run_all_fixes():
    """Run all fixes for achievements"""
    print("====== FIXING MISSING ACHIEVEMENTS ======")
    fixed_count = check_missing_tournament_win_achievements()
    check_other_missing_achievements()
    print(f"\nCompleted all fixes. Fixed {fixed_count} tournament win achievements.")

if __name__ == "__main__":
    run_all_fixes()