# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import math

from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated
from allauth.socialaccount.models import SocialAccount

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
    start_time = models.TimeField(null=True, blank=True)  
    location = models.CharField(max_length=200, default="De Laurierboom, Amsterdam")
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES, blank=True, null=True)
    num_rounds = models.IntegerField(validators=[MinValueValidator(1)], null=True, blank=True)
    description = models.TextField(blank=True)
    participants = models.ManyToManyField(User, related_name='tournaments')
    is_completed = models.BooleanField(default=False)
    has_started = models.BooleanField(default=False)
    time_control = models.CharField(max_length=20, choices=TIME_CONTROL_CHOICES, default='blitz')
    max_participants = models.IntegerField(default=20, validators=[MinValueValidator(2)])
    
    def __str__(self):
        return self.name
    
    def num_participants(self):
        return self.participants.count()
    
    def is_full(self):
        """Check if tournament has reached maximum participants"""
        return self.participants.count() >= self.max_participants
    
    def spots_left(self):
        """Return number of spots left in tournament"""
        return max(0, self.max_participants - self.participants.count())
    
    def is_swiss_type(self):
        """Check if tournament is Swiss type"""
        return self.tournament_type == 'swiss'

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
        ('bye', 'Bye'),
        ('white_forfeit', 'White Forfeit'),  # White player didn't show
        ('black_forfeit', 'Black Forfeit'),  # Black player didn't show
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='matches')
    white_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='white_matches')
    black_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='black_matches', null=True, blank=True)  # Allow null for byes
    result = models.CharField(max_length=13, choices=RESULT_CHOICES, default='pending')
    
    def __str__(self):
        if self.black_player:
            return f"{self.white_player.username} vs {self.black_player.username}"
        else:
            return f"{self.white_player.username} - Bye"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update Glicko2 ratings only for actual matches (not byes)
        # Only if result is set and not pending
        if not is_new and self.result not in ['pending', 'bye'] and self.black_player is not None:
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

class PlayerRatingHistory(models.Model):
    """
    Model to track player rating history after each tournament
    """
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rating_history')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    date = models.DateField()
    rating = models.FloatField()
    time_control = models.CharField(max_length=20, choices=Tournament.TIME_CONTROL_CHOICES)
    
    def __str__(self):
        return f"{self.player.username} - {self.tournament.name} - {self.rating}"
    
    class Meta:
        unique_together = ('player', 'tournament')
        ordering = ['date']

class Achievement(models.Model):
    """Model to track player achievements and trophies"""
    ACHIEVEMENT_TYPES = [
        # Tournament win milestones
        ('tournament_win_1', 'Tournament Champion'),
        ('tournament_win_3', 'Triple Crown'),
        ('tournament_win_5', 'Dominator'),
        ('tournament_win_10', 'Dynasty Builder'),
        
        # Tournament placements
        ('silver_medal_3', 'Silver Collector'),
        ('silver_medal_5', 'Silver Hoarder'),
        ('bronze_medal_3', 'Bronze Collector'),
        ('bronze_medal_5', 'Bronze Hoarder'),
        
        # Streaks and special performance
        ('hat_trick', 'Hat Trick'),
        ('winning_streak_5', 'Winning Streak'),
        ('winning_streak_10', 'Unstoppable'),
        ('white_dominator', 'White Dominator'),
        ('black_defender', 'Black Defender'),
        
        # Perfect performance
        ('clean_sweep', 'Clean Sweep'),
        ('perfect_score', 'Perfect Score'),
        ('undefeated', 'Undefeated'),
        
        # Experience-based
        ('tournament_veteran_10', 'Tournament Veteran'),
        ('tournament_veteran_25', 'Tournament Master'),
        ('tournament_veteran_50', 'Tournament Legend'),
        
        # Special game outcomes
        ('comeback_kid', 'Comeback Kid'),
        ('underdog', 'Underdog'),
        ('giant_slayer', 'Giant Slayer'),
        
        # Format specialists
        ('swiss_master', 'Swiss Master'),
        ('round_robin_champion', 'Round Robin Champion'),
        ('double_round_robin_king', 'Double Round Robin King'),
        
        # Time control specialists
        ('bullet_blitzer', 'Bullet Blitzer'),
        ('blitz_boss', 'Blitz Boss'),
        ('rapid_ruler', 'Rapid Ruler'),
        ('classical_conqueror', 'Classical Conqueror'),
        
        # Rating-based
        ('rating_1600', 'Rising Star'),
        ('rating_1800', 'Advanced Player'),
        ('rating_2000', 'Expert Player'),
        ('rating_2200', 'Master Player'),
        
        # Existing achievements
        ('support_bear', 'Emotional Support Bear'),
        ('dummies', 'Chess for Dummies'),
        ('goat', 'The Ace'),
        ('truce_seeker', 'Truce Seeker'),

        # Community Trophies
        ('social_butterfly', 'Social Butterfly'),
        ('rival_nemesis', 'Rival Nemesis'),
        ('kingmaker', 'Kingmaker'),
        ('bar_legend', 'Bar Legend'),

        # Milestone Trophies
        ('century_club', 'Century Club'),
        ('blitz_marathon', 'Blitz Marathon'),

        # Whimsical Trophies
        ('phoenix_rising', 'Phoenix Rising'),
        ('draw_magnet', 'Draw Magnet'),
        ('the_spoiler', 'The Spoiler'),
        ('last_stand', 'Last Stand'),

        # Achievement Trophies
        ('grand_slam', 'Grand Slam'),
        ('format_master', 'Format Master'),
        ('seasonal_champion', 'Seasonal Champion'),
        ('the_perfectionist', 'The Perfectionist'),

        # Unconventional Trophies
        ('comeback_king', 'Comeback King/Queen'),
        ('late_bloomer', 'Late Bloomer'),
        ('score_maximizer', 'Score Maximizer'),
        ('early_departure', 'Missing Poster'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    date_achieved = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default=1)  # For counting achievements (e.g. "3 tournament wins")
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True, blank=True)  # Optional link to specific tournament
    
    class Meta:
        unique_together = ('user', 'achievement_type')
        ordering = ['-date_achieved']
    
    def __str__(self):
        achievement_name = dict(self.ACHIEVEMENT_TYPES).get(self.achievement_type, self.achievement_type)
        if self.count > 1:
            return f"{self.user.username} - {achievement_name} (x{self.count})"
        return f"{self.user.username} - {achievement_name}"
    
    @property
    def icon(self):
        """Return the appropriate Font Awesome icon class for this achievement"""
        icons = {
            # Tournament victories
            'tournament_win_1': 'fa-trophy',
            'tournament_win_3': 'fa-trophy',
            'tournament_win_5': 'fa-trophy',
            'tournament_win_10': 'fa-crown',
            
            # Medals
            'silver_medal_3': 'fa-medal',
            'silver_medal_5': 'fa-medal',
            'bronze_medal_3': 'fa-medal',
            'bronze_medal_5': 'fa-medal',
            
            # Streaks
            'hat_trick': 'fa-bolt',
            'winning_streak_5': 'fa-bolt',
            'winning_streak_10': 'fa-bolt-lightning',
            'white_dominator': 'fa-chess-pawn',
            'black_defender': 'fa-chess-pawn',
            
            # Perfect performance
            'clean_sweep': 'fa-broom',
            'perfect_score': 'fa-star',
            'undefeated': 'fa-shield',
            
            # Experience
            'tournament_veteran_10': 'fa-chess',
            'tournament_veteran_25': 'fa-chess-board',
            'tournament_veteran_50': 'fa-chess-king',
            
            # Special outcomes
            'comeback_kid': 'fa-arrow-up',
            'underdog': 'fa-dog',
            'giant_slayer': 'fa-dragon',
            
            # Format specialists
            'swiss_master': 'fa-sitemap',
            'round_robin_champion': 'fa-circle',
            'double_round_robin_king': 'fa-circle-notch',
            
            # Time control
            'bullet_blitzer': 'fa-bolt',
            'blitz_boss': 'fa-rocket',
            'rapid_ruler': 'fa-stopwatch',
            'classical_conqueror': 'fa-hourglass',
            
            # Rating
            'rating_1600': 'fa-chart-line',
            'rating_1800': 'fa-chart-line',
            'rating_2000': 'fa-chart-line',
            'rating_2200': 'fa-chess-king',
            
            # Existing
            'support_bear': 'fa-paw',
            'dummies': 'fa-book',
            'goat': 'fa-trophy',
            'truce_seeker': 'fa-handshake',

            # Community Trophies
            'social_butterfly': 'fa-users',
            'rival_nemesis': 'fa-user-secret',
            'kingmaker': 'fa-chess-king',
            'bar_legend': 'fa-glass-cheers',
            
            # Milestone Trophies
            'century_club': 'fa-hundred-points',
            'blitz_marathon': 'fa-running',
            
            # Whimsical Trophies
            'phoenix_rising': 'fa-phoenix-framework',
            'draw_magnet': 'fa-magnet',
            'the_spoiler': 'fa-ban',
            'last_stand': 'fa-flag',
            
            # Achievement Trophies
            'grand_slam': 'fa-award',
            'format_master': 'fa-certificate',
            'seasonal_champion': 'fa-sun',
            'the_perfectionist': 'fa-check-double',
            
            # Unconventional Trophies
            'comeback_king': 'fa-arrow-up',
            'late_bloomer': 'fa-hourglass-end',
            'score_maximizer': 'fa-percentage',
        }
        return icons.get(self.achievement_type, 'fa-award')
    
    @property
    def description(self):
        """Return a description of how to earn this achievement"""
        descriptions = {
            # Tournament victories
            'tournament_win_1': 'Win your first tournament',
            'tournament_win_3': 'Win 3 tournaments',
            'tournament_win_5': 'Win 5 tournaments',
            'tournament_win_10': 'Win 10 tournaments',
            
            # Medals
            'silver_medal_3': 'Finish 2nd place in 3 tournaments',
            'silver_medal_5': 'Finish 2nd place in 5 tournaments',
            'bronze_medal_3': 'Finish 3rd place in 3 tournaments',
            'bronze_medal_5': 'Finish 3rd place in 5 tournaments',
            
            # Streaks
            'hat_trick': 'Win 3 consecutive games',
            'winning_streak_5': 'Win 5 consecutive games',
            'winning_streak_10': 'Win 10 consecutive games',
            'white_dominator': 'Win 5 consecutive games as White',
            'black_defender': 'Win 5 consecutive games as Black',
            
            # Perfect performance
            'clean_sweep': 'Win all games in a tournament round',
            'perfect_score': 'Win all games in a tournament',
            'undefeated': 'Complete a tournament without losing',
            
            # Experience
            'tournament_veteran_10': 'Participate in 10 tournaments',
            'tournament_veteran_25': 'Participate in 25 tournaments',
            'tournament_veteran_50': 'Participate in 50 tournaments',
            
            # Special outcomes
            'comeback_kid': 'Win a tournament after losing the first game',
            'underdog': 'Beat a player rated 200+ points above you',
            'giant_slayer': 'Beat the top-rated player in a tournament',
            
            # Format specialists
            'swiss_master': 'Win a Swiss format tournament',
            'round_robin_champion': 'Win a Round Robin tournament',
            'double_round_robin_king': 'Win a Double Round Robin tournament',
            
            # Time control
            'bullet_blitzer': 'Win a Bullet tournament',
            'blitz_boss': 'Win a Blitz tournament',
            'rapid_ruler': 'Win a Rapid tournament',
            'classical_conqueror': 'Win a Classical tournament',
            
            # Rating
            'rating_1600': 'Reach a rating of 1600',
            'rating_1800': 'Reach a rating of 1800',
            'rating_2000': 'Reach a rating of 2000', 
            'rating_2200': 'Reach a rating of 2200',
            
            # Existing
            'support_bear': 'No wins in a tournament',
            'dummies': 'Last place in a tournament',
            'goat': 'Won all games in a tournament',
            'truce_seeker': '50%+ draws in a tournament',

            # Community Trophies
            'social_butterfly': 'Play against 15 different opponents',
            'rival_nemesis': 'Win 3 consecutive games against the same opponent',
            'kingmaker': 'Beat a tournament leader in the final round, changing who wins',
            'bar_legend': 'Participate in 10 consecutive weekly tournaments',
            
            # Milestone Trophies
            'century_club': 'Play 100 rated games',
            'blitz_marathon': 'Play 10 games in a single day',
            
            # Whimsical Trophies
            'phoenix_rising': 'Lose 3 consecutive games then win the next 3',
            'draw_magnet': 'Draw 3 consecutive games',
            'the_spoiler': 'Defeat a player on a 5+ game winning streak',
            'last_stand': 'Win your final game after losing all previous games in a tournament',
            
            # Achievement Trophies
            'grand_slam': 'Win tournaments in all four time controls',
            'format_master': 'Win tournaments in all three formats',
            'seasonal_champion': 'Win tournaments in Spring, Summer, Fall, and Winter',
            'the_perfectionist': 'Complete 5 tournaments without a single loss',
            
            # Unconventional Trophies
            'comeback_king': 'Win a tournament after being in bottom half before final round',
            'late_bloomer': 'Win your first tournament after playing in 10+ tournaments',
            'score_maximizer': 'Score 90%+ of possible points in a tournament with 5+ rounds',
        }
        return descriptions.get(self.achievement_type, 'Achievement unlocked!')
    
    @property
    def color(self):
        """Return appropriate color class for this achievement"""
        colors = {
            # Color groups by achievement type
            'tournament_win_1': 'gold',
            'tournament_win_3': 'gold',
            'tournament_win_5': 'gold', 
            'tournament_win_10': 'gold',
            
            'silver_medal_3': 'silver',
            'silver_medal_5': 'silver',
            
            'bronze_medal_3': 'bronze',
            'bronze_medal_5': 'bronze',
            
            'rating_1600': 'green',
            'rating_1800': 'blue',
            'rating_2000': 'purple',
            'rating_2200': 'red',

            # Community Trophies
            'social_butterfly': 'purple',
            'rival_nemesis': 'red',
            'kingmaker': 'gold',
            'bar_legend': 'blue',
            
            # Milestone Trophies
            'century_club': 'silver',
            'blitz_marathon': 'green',
            
            # Whimsical Trophies
            'phoenix_rising': 'red',
            'draw_magnet': 'silver',
            'the_spoiler': 'green',
            'last_stand': 'gold',
            
            # Achievement Trophies
            'grand_slam': 'gold',
            'format_master': 'purple',
            'seasonal_champion': 'green',
            'the_perfectionist': 'blue',
            
            # Unconventional Trophies
            'comeback_king': 'gold',
            'late_bloomer': 'green',
            'score_maximizer': 'purple',
        }
        return colors.get(self.achievement_type, 'teal')  # Default color

# Glicko-2 implementation functions
def update_glicko2_ratings(match):

    if match.result in ['white_forfeit', 'black_forfeit']:
        return  # Exit the function early - no rating changes
    
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

@receiver(social_account_added)
def social_account_added_handler(request, sociallogin, **kwargs):
    """Handle new social account connections"""
    process_social_data(sociallogin)

@receiver(social_account_updated)
def social_account_updated_handler(request, sociallogin, **kwargs):
    """Handle updates to social accounts"""
    process_social_data(sociallogin)

def process_social_data(sociallogin):
    """Process data from social account and update user profile"""
    user = sociallogin.user
    account = sociallogin.account
    
    # Get data from social account
    data = account.extra_data
    
    # Example: Update user fields if blank
    if not user.first_name and 'given_name' in data:
        user.first_name = data['given_name']
    
    if not user.last_name and 'family_name' in data:
        user.last_name = data['family_name']
    
    user.save()