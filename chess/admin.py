# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Tournament, Round, Match, TournamentStanding

# Register the custom User model with the UserAdmin
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Chess Profile', {'fields': ('lichess_account', 'chesscom_account', 'fide_rating', 'elo', 'rd', 'volatility')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'elo', 'is_staff')
    list_filter = UserAdmin.list_filter + ('elo',)
    search_fields = UserAdmin.search_fields + ('lichess_account', 'chesscom_account')

# Register Tournament with custom admin
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'tournament_type', 'num_rounds', 'is_completed')
    list_filter = ('tournament_type', 'is_completed', 'date')
    search_fields = ('name', 'description')
    filter_horizontal = ('participants',)

# Register Round with custom admin
class RoundAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'number', 'is_completed')
    list_filter = ('is_completed', 'tournament')

# Register Match with custom admin
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'round', 'result')
    list_filter = ('result', 'tournament', 'round')
    search_fields = ('white_player__username', 'black_player__username')

# Register TournamentStanding with custom admin
class TournamentStandingAdmin(admin.ModelAdmin):
    list_display = ('player', 'tournament', 'score', 'rank')
    list_filter = ('tournament',)
    search_fields = ('player__username',)

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(TournamentStanding, TournamentStandingAdmin)