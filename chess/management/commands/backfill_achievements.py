from django.core.management.base import BaseCommand
from chess.models import User
from chess.achievement_service import check_achievements

class Command(BaseCommand):
    help = 'Backfills the newly added achievements for all users'

    def handle(self, *args, **options):
        users = User.objects.all()
        total_users = users.count()
        
        self.stdout.write(f"Starting new achievement backfill for {total_users} users")
        
        total_achievements = 0
        
        for i, user in enumerate(users):
            self.stdout.write(f"Processing user {i+1}/{total_users}: {user.username}")
            new_achievements = check_achievements(user)
            
            if new_achievements:
                achievement_names = [a.get_achievement_type_display() for a in new_achievements]
                total_achievements += len(new_achievements)
                self.stdout.write(self.style.SUCCESS(
                    f"  Added {len(new_achievements)} achievements: {', '.join(achievement_names)}"
                ))
            else:
                self.stdout.write("  No new achievements found")
        
        self.stdout.write(self.style.SUCCESS(
            f'Achievement backfill completed! Added {total_achievements} new achievements.'
        ))