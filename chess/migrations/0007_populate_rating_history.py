# chess/migrations/0014_populate_rating_history.py

from django.db import migrations

def populate_rating_history(apps, schema_editor):
    """
    Populate rating history for completed tournaments
    """
    User = apps.get_model('chess', 'User')
    Tournament = apps.get_model('chess', 'Tournament')
    PlayerRatingHistory = apps.get_model('chess', 'PlayerRatingHistory')
    
    # Get all completed tournaments
    completed_tournaments = Tournament.objects.filter(is_completed=True).order_by('date')
    
    for tournament in completed_tournaments:
        # For each participant in the tournament
        for player in tournament.participants.all():
            # Determine which rating to use based on time control
            time_control = tournament.time_control or 'blitz'
            
            if time_control == 'bullet':
                rating = player.bullet_elo
            elif time_control == 'blitz':
                rating = player.blitz_elo
            elif time_control == 'rapid':
                rating = player.rapid_elo
            elif time_control == 'classical':
                rating = player.classical_elo
            else:
                rating = player.elo
                
            # Create the rating history entry
            PlayerRatingHistory.objects.create(
                player=player,
                tournament=tournament,
                date=tournament.date,
                rating=round(rating),  # Store as rounded integer
                time_control=time_control
            )

class Migration(migrations.Migration):
    dependencies = [
        ('chess', '0006_playerratinghistory'),  # Reference the previous migration
    ]

    operations = [
        migrations.RunPython(populate_rating_history),
    ]