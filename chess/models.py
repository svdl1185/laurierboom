# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import math

class User(AbstractUser):
    # Add additional field to identify users who don't need login
    is_player_only = models.BooleanField(default=True)
    lichess_account = models.CharField(max_length=100, blank=True, null=True)
    chesscom_account = models.CharField(max_length=100, blank=True, null=True)
    
    fide_id = models.CharField(max_length=20, blank=True, null=True)
    fide_rating = models.IntegerField(blank=True, null=True)

    bullet_elo = models.FloatField(default=1500)
    bullet_rd = models.FloatField(default=350)
    bullet_volatility = models.FloatField(default=0.06)
    
    blitz_elo = models.FloatField(default=1500)
    blitz_rd = models.FloatField(default=350)
    blitz_volatility = models.FloatField(default=0.06)
    
    rapid_elo = models.FloatField(default=1500)
    rapid_rd = models.FloatField(default=350)
    rapid_volatility = models.FloatField(default=0.06)
    
    classical_elo = models.FloatField(default=1500)
    classical_rd = models.FloatField(default=350)
    classical_volatility = models.FloatField(default=0.06)
    
    # Keep the original elo field as an overall rating or fallback
    elo = models.FloatField(default=1500)
    rd = models.FloatField(default=350)
    volatility = models.FloatField(default=0.06)
    last_played = models.DateTimeField(auto_now=True)

    def get_rating_for_time_control(self, time_control):
        if time_control == 'bullet':
            return self.bullet_elo
        elif time_control == 'blitz':
            return self.blitz_elo
        elif time_control == 'rapid':
            return self.rapid_elo
        elif time_control == 'classical':
            return self.classical_elo
        return self.elo  # Fallback to general rating
    
    def save(self, *args, **kwargs):
        # If it's a new player-only user without a username, create one
        if not self.pk and self.is_player_only and not self.username:
            base = f"{self.first_name.lower()}{self.last_name.lower()}"
            base = ''.join(c for c in base if c.isalnum())  # Remove special chars
            username = base
            counter = 1
            
            # Ensure uniqueness
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1
                
            self.username = username
            
        super().save(*args, **kwargs)
    
    # This allows users to be identified by name if they don't have a username
    def __str__(self):
        if self.get_full_name():
            return self.get_full_name()
        return self.username

class Tournament(models.Model):
    TIME_CONTROL_CHOICES = [
        ('bullet', 'Bullet'),
        ('blitz', 'Blitz'),
        ('rapid', 'Rapid'),
        ('classical', 'Classical'),
    ]

    TOURNAMENT_TYPES = [
        ('swiss', 'Swiss'),
        ('round_robin', 'Round Robin'),
        ('double_round_robin', 'Double Round Robin'),
    ]
    
    name = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)  # Add this field
    location = models.CharField(max_length=200, default="De Laurierboom, Amsterdam")
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES, blank=True, null=True)  # Make optional initially
    num_rounds = models.IntegerField(validators=[MinValueValidator(1)], null=True, blank=True)  # Make optional initially
    description = models.TextField(blank=True)
    participants = models.ManyToManyField(User, related_name='tournaments')
    is_completed = models.BooleanField(default=False)
    has_started = models.BooleanField(default=False)  # Add this field to track if tournament has started
    time_control = models.CharField(max_length=20, choices=TIME_CONTROL_CHOICES, default='blitz')
    
    def __str__(self):
        return self.name
    
    def num_participants(self):
        return self.participants.count()
    
    def is_swiss_type(self):
        """Check if tournament is Swiss type"""
        return self.tournament_type == 'swiss'

    # And the is_round_robin_type method 
    def is_round_robin_type(self):
        """Check if tournament is Round Robin type"""
        return self.tournament_type in ['round_robin', 'double_round_robin']
    
    def get_tournament_type_display(self):
        """Return a properly formatted tournament type for display"""
        if not self.tournament_type:
            return "Type TBD"
        elif self.tournament_type == 'round_robin':
            return "Round Robin"
        elif self.tournament_type == 'double_round_robin':
            return "Double Round Robin"
        elif self.tournament_type == 'swiss':
            return "Swiss"
        else:
            return self.tournament_type.replace('_', ' ').title()

class Round(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    number = models.IntegerField()
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('tournament', 'number')
    
    def __str__(self):
        return f"{self.tournament.name} - Round {self.number}"

class Match(models.Model):
    RESULT_CHOICES = [
        ('white_win', 'White Win'),
        ('black_win', 'Black Win'),
        ('draw', 'Draw'),
        ('pending', 'Pending'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='matches')
    white_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='white_matches')
    black_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='black_matches')
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.white_player.username} vs {self.black_player.username}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update Glicko2 ratings if result is set and not pending
        if not is_new and self.result != 'pending':
            update_glicko2_ratings(self)

class TournamentStanding(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='standings')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='standings')
    score = models.FloatField(default=0)
    rank = models.IntegerField(null=True, blank=True)
    previous_rank = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('tournament', 'player')
    
    def __str__(self):
        return f"{self.player.username} - {self.score} points"


# Glicko-2 implementation functions
def update_glicko2_ratings(match):
    """Update Glicko-2 ratings based on match result and time control"""
    white_player = match.white_player
    black_player = match.black_player
    time_control = match.tournament.time_control
    
    # Determine which rating fields to use
    if time_control == 'bullet':
        white_rating = (white_player.bullet_elo - 1500) / 173.7178
        white_rd = white_player.bullet_rd / 173.7178
        black_rating = (black_player.bullet_elo - 1500) / 173.7178
        black_rd = black_player.bullet_rd / 173.7178
    elif time_control == 'blitz':
        white_rating = (white_player.blitz_elo - 1500) / 173.7178
        white_rd = white_player.blitz_rd / 173.7178
        black_rating = (black_player.blitz_elo - 1500) / 173.7178
        black_rd = black_player.blitz_rd / 173.7178
    elif time_control == 'rapid':
        white_rating = (white_player.rapid_elo - 1500) / 173.7178
        white_rd = white_player.rapid_rd / 173.7178
        black_rating = (black_player.rapid_elo - 1500) / 173.7178
        black_rd = black_player.rapid_rd / 173.7178
    elif time_control == 'classical':
        white_rating = (white_player.classical_elo - 1500) / 173.7178
        white_rd = white_player.classical_rd / 173.7178
        black_rating = (black_player.classical_elo - 1500) / 173.7178
        black_rd = black_player.classical_rd / 173.7178
    else:
        # Fallback to general rating
        white_rating = (white_player.elo - 1500) / 173.7178
        white_rd = white_player.rd / 173.7178
        black_rating = (black_player.elo - 1500) / 173.7178
        black_rd = black_player.rd / 173.7178
    
    # System constants
    tau = 0.5  # Volatility parameter
    
    # Determine white_outcome and black_outcome based on match result
    if match.result == 'white_win':
        white_outcome = 1
        black_outcome = 0
    elif match.result == 'black_win':
        white_outcome = 0
        black_outcome = 1
    else:  # Draw
        white_outcome = 0.5
        black_outcome = 0.5
    
    # Function to calculate g(RD)
    def g(rd):
        return 1 / math.sqrt(1 + (3 * rd ** 2) / (math.pi ** 2))
    
    # Function to calculate E (expected outcome)
    def E(player_rating, opponent_rating, opponent_rd):
        return 1 / (1 + math.exp(-g(opponent_rd) * (player_rating - opponent_rating)))
    
    # Calculate new white player rating
    g_black_rd = g(black_rd)
    E_white = E(white_rating, black_rating, black_rd)
    v_white = 1 / (g_black_rd**2 * E_white * (1 - E_white))
    
    # Calculate delta for white
    delta_white = v_white * g_black_rd * (white_outcome - E_white)
    
    # Calculate new volatility for white
    # ... (this part is complex and requires implementation of the volatility update algorithm)
    # For simplicity, we'll use a fixed volatility here, but a complete implementation would update it
    new_white_volatility = white_player.volatility
    
    # Calculate new RD for white
    new_white_rd = math.sqrt(1 / ((1 / (white_rd**2)) + (1 / v_white)))
    
    # Calculate new rating for white
    new_white_rating = white_rating + new_white_rd**2 * g_black_rd * (white_outcome - E_white)
    
    # Calculate new black player rating
    g_white_rd = g(white_rd)
    E_black = E(black_rating, white_rating, white_rd)
    v_black = 1 / (g_white_rd**2 * E_black * (1 - E_black))
    
    # Calculate delta for black
    delta_black = v_black * g_white_rd * (black_outcome - E_black)
    
    # Calculate new volatility for black
    # ... (volatility update would go here)
    new_black_volatility = black_player.volatility
    
    # Calculate new RD for black
    new_black_rd = math.sqrt(1 / ((1 / (black_rd**2)) + (1 / v_black)))
    
    # Calculate new rating for black
    new_black_rating = black_rating + new_black_rd**2 * g_white_rd * (black_outcome - E_black)
    
    # Update the appropriate rating fields based on time control
    if time_control == 'bullet':
        white_player.bullet_elo = (new_white_rating * 173.7178) + 1500
        white_player.bullet_rd = new_white_rd * 173.7178
        white_player.bullet_volatility = new_white_volatility
        
        black_player.bullet_elo = (new_black_rating * 173.7178) + 1500
        black_player.bullet_rd = new_black_rd * 173.7178
        black_player.bullet_volatility = new_black_volatility
    elif time_control == 'blitz':
        white_player.blitz_elo = (new_white_rating * 173.7178) + 1500
        white_player.blitz_rd = new_white_rd * 173.7178
        white_player.blitz_volatility = new_white_volatility
        
        black_player.blitz_elo = (new_black_rating * 173.7178) + 1500
        black_player.blitz_rd = new_black_rd * 173.7178
        black_player.bullet_volatility = new_black_volatility
    elif time_control == 'rapid':
        white_player.rapid_elo = (new_white_rating * 173.7178) + 1500
        white_player.rapid_rd = new_white_rd * 173.7178
        white_player.rapid_volatility = new_white_volatility

        black_player.rapid_elo = (new_black_rating * 173.7178) + 1500
        black_player.rapid_rd = new_black_rd * 173.7178
        black_player.rapid_volatility = new_black_volatility
    elif time_control == 'classical':
        white_player.classical_elo = (new_white_rating * 173.7178) + 1500
        white_player.classical_rd = new_white_rd * 173.7178
        white_player.classical_volatility = new_white_volatility

        black_player.classical_elo = (new_black_rating * 173.7178) + 1500
        black_player.classical_rd = new_black_rd * 173.7178
        black_player.classical_volatility = new_black_volatility

    
    # Also update the general rating for backward compatibility
    white_player.elo = (new_white_rating * 173.7178) + 1500
    white_player.rd = new_white_rd * 173.7178
    white_player.volatility = new_white_volatility
    
    black_player.elo = (new_black_rating * 173.7178) + 1500
    black_player.rd = new_black_rd * 173.7178
    black_player.volatility = new_black_volatility
    
    white_player.save()
    black_player.save()