# In chess/management/commands/update_fide_ratings.py
from django.core.management.base import BaseCommand
from chess.utils import update_fide_ratings

class Command(BaseCommand):
    help = 'Fetch and update FIDE ratings for all users'

    def handle(self, *args, **options):
        self.stdout.write("Updating FIDE ratings...")
        update_fide_ratings()
        self.stdout.write(self.style.SUCCESS("Successfully updated FIDE ratings"))