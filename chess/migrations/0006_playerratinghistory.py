# chess/migrations/0013_playerratinghistory.py

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('chess', '0005_tournament_max_participants'),  # Replace with your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerRatingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('rating', models.FloatField()),
                ('time_control', models.CharField(choices=[('bullet', 'Bullet'), ('blitz', 'Blitz'), ('rapid', 'Rapid'), ('classical', 'Classical')], max_length=20)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating_history', to='chess.user')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chess.tournament')),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('player', 'tournament')},
            },
        ),
    ]