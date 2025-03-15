# views.py
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import F, Count, Sum, Q, Avg
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Tournament, User, Match, Round, TournamentStanding
from .forms import EmptyForm, MatchResultForm, ProfileEditForm, SimplePlayerRegistrationForm, StartTournamentSettingsForm, TournamentForm, UserEditForm, UserRegistrationForm, AddPlayerToTournamentForm
from .utils import generate_swiss_pairings, generate_round_robin_pairings, update_tournament_standings


class HomeView(ListView):
    """Homepage view showing the top rated players and upcoming tournaments"""
    model = User
    template_name = 'chess/home.html'
    context_object_name = 'players'
    
    def get_queryset(self):
        # Get users ordered by Elo rating, excluding superusers/staff
        players = list(User.objects.filter(
            is_active=True, 
            is_staff=False, 
            is_superuser=False
        ).order_by('-elo')[:20])
        
        # Calculate match statistics for each player
        for player in players:
            # Get player's match history
            white_matches = player.white_matches.exclude(result='pending')
            black_matches = player.black_matches.exclude(result='pending')
            
            # Calculate win/loss/draw stats
            wins = white_matches.filter(result='white_win').count() + black_matches.filter(result='black_win').count()
            losses = white_matches.filter(result='black_win').count() + black_matches.filter(result='white_win').count()
            draws = white_matches.filter(result='draw').count() + black_matches.filter(result='draw').count()
            
            player.wins = wins
            player.losses = losses
            player.draws = draws
            player.total_games = wins + losses + draws
        
        return players

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Sort players by each time control rating
        context['bullet_players'] = list(User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).order_by('-bullet_elo')[:20])
        
        context['blitz_players'] = list(User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).order_by('-blitz_elo')[:20])
        
        context['rapid_players'] = list(User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).order_by('-rapid_elo')[:20])
        
        context['classical_players'] = list(User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).order_by('-classical_elo')[:20])
        
        # Make sure we're getting tournaments from today onward and they're not completed
        from django.utils import timezone
        today = timezone.now().date()
        
        context['upcoming_tournaments'] = Tournament.objects.filter(
            is_completed=False,
            date__gte=today
        ).order_by('date')[:5]
        
        return context

class PlayerDetailView(DetailView):
    """View for player profiles"""
    model = User
    template_name = 'chess/player_detail.html'
    context_object_name = 'player'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player = self.get_object()
        
        # Get player's tournaments (most recent first)
        context['tournaments'] = player.tournaments.all().order_by('-date')
        
        # Get player's match history
        white_matches = player.white_matches.exclude(result='pending')
        black_matches = player.black_matches.exclude(result='pending')
        
        # Calculate win/loss/draw stats
        wins = white_matches.filter(result='white_win').count() + black_matches.filter(result='black_win').count()
        losses = white_matches.filter(result='black_win').count() + black_matches.filter(result='white_win').count()
        draws = white_matches.filter(result='draw').count() + black_matches.filter(result='draw').count()
        
        context['wins'] = wins
        context['losses'] = losses
        context['draws'] = draws
        context['total_games'] = wins + losses + draws
        
        # Add performance by color stats
        white_wins = white_matches.filter(result='white_win').count()
        white_losses = white_matches.filter(result='black_win').count()
        white_draws = white_matches.filter(result='draw').count()
        
        black_wins = black_matches.filter(result='black_win').count()
        black_losses = black_matches.filter(result='white_win').count()
        black_draws = black_matches.filter(result='draw').count()
        
        context['white_wins'] = white_wins
        context['white_losses'] = white_losses
        context['white_draws'] = white_draws
        context['black_wins'] = black_wins
        context['black_losses'] = black_losses
        context['black_draws'] = black_draws

        # Calculate win rates by color
        white_win_rate = 0
        black_win_rate = 0

        if (white_wins + white_draws + white_losses) > 0:
            white_win_rate = (white_wins / (white_wins + white_draws + white_losses)) * 100

        if (black_wins + black_draws + black_losses) > 0:
            black_win_rate = (black_wins / (black_wins + black_draws + black_losses)) * 100

        context['white_win_rate'] = white_win_rate
        context['black_win_rate'] = black_win_rate
        
        # Recent match history (most recent first - reversed order)
        combined_matches = list(white_matches) + list(black_matches)
        combined_matches.sort(key=lambda x: (x.round.tournament.date, x.round.number), reverse=True)
        context['recent_matches'] = combined_matches[:10]  # Keep only the 10 most recent
        
        # Calculate blitz rating change over last month
        from django.utils import timezone
        import datetime
        one_month_ago = timezone.now() - datetime.timedelta(days=30)
        
        # Get blitz matches from tournaments in the last month
        blitz_matches = Match.objects.filter(
            (Q(white_player=player) | Q(black_player=player)),
            tournament__time_control='blitz',
            tournament__date__gte=one_month_ago,
            result__in=['white_win', 'black_win', 'draw']
        ).order_by('tournament__date', 'round__number')
        
        # Get the earliest blitz match from more than a month ago to establish baseline
        earliest_match = Match.objects.filter(
            (Q(white_player=player) | Q(black_player=player)),
            tournament__time_control='blitz',
            tournament__date__lt=one_month_ago,
            result__in=['white_win', 'black_win', 'draw']
        ).order_by('-tournament__date', '-round__number').first()
        
        # Calculate rating change
        blitz_rating_month_ago = 1500  # Default starting rating
        
        if earliest_match:
            # This is a simplified approximation - in reality you'd need a rating history table
            # to accurately track historical ratings
            blitz_rating_month_ago = player.blitz_elo - (10 * len(blitz_matches))
        
        context['blitz_rating_change'] = player.blitz_elo - blitz_rating_month_ago
        
        # Add tournament placements chart data
        tournaments_participated = player.tournaments.filter(is_completed=True).order_by('date')
        placements = []
        
        for tournament in tournaments_participated:
            try:
                standing = tournament.standings.get(player=player)
                placements.append({
                    'tournament': tournament.name,
                    'round': tournament.id,  # Using ID as a simple round number for the chart
                    'position': standing.rank,
                    'total_players': tournament.participants.count()
                })
            except:
                continue
        
        context['placements'] = placements

        # Calculate average position and points from tournaments
        avg_position = 0
        avg_total_players = 0
        if placements:
            avg_position = sum(p['position'] for p in placements) / len(placements)
            avg_total_players = sum(p['total_players'] for p in placements) / len(placements)
            
        context['avg_position'] = avg_position
        context['avg_total_players'] = avg_total_players

        # Calculate average points per tournament
        from django.utils import timezone
        one_month_ago = timezone.now() - datetime.timedelta(days=30)
        
        # Get the standings from tournaments in the last month
        recent_tournaments = player.tournaments.filter(date__gte=one_month_ago).order_by('date')
        recent_standings = []
        for tournament in recent_tournaments:
            try:
                standing = tournament.standings.get(player=player)
                recent_standings.append({
                    'tournament': tournament.name,
                    'date': tournament.date,
                    'position': standing.rank,
                    'score': standing.score
                })
            except:
                pass
        
        context['recent_standings'] = recent_standings
        
        avg_points = 0
        if recent_standings:
            avg_points = sum(s['score'] for s in recent_standings) / len(recent_standings)
            
        context['avg_points'] = avg_points
        context['tournament_count'] = len(placements)

        one_month_ago = timezone.now() - datetime.timedelta(days=30)

        # Get blitz matches from tournaments in the last month
        blitz_matches = Match.objects.filter(
            (Q(white_player=player) | Q(black_player=player)),
            tournament__time_control='blitz',
            tournament__date__gte=one_month_ago,
            result__in=['white_win', 'black_win', 'draw']
        ).order_by('tournament__date', 'round__number')

        # Get the earliest blitz match from more than a month ago to establish baseline
        earliest_match = Match.objects.filter(
            (Q(white_player=player) | Q(black_player=player)),
            tournament__time_control='blitz',
            tournament__date__lt=one_month_ago,
            result__in=['white_win', 'black_win', 'draw']
        ).order_by('-tournament__date', '-round__number').first()

        # Calculate rating change
        blitz_rating_month_ago = 1500  # Default starting rating

        if earliest_match:
            # This is a simplified approximation - in reality you'd need a rating history table
            blitz_rating_month_ago = player.blitz_elo - (10 * len(blitz_matches))

        context['blitz_rating_change'] = player.blitz_elo - blitz_rating_month_ago

        # Calculate number of tournaments won
        tournaments_won = 0
        tournaments_participated = player.tournaments.filter(is_completed=True).order_by('date')

        for tournament in tournaments_participated:
            try:
                # Check if player has rank 1 in the standings (winner)
                standing = tournament.standings.get(player=player, rank=1)
                if standing:
                    tournaments_won += 1
            except:
                pass

        context['tournaments_won'] = tournaments_won
        
        return context

class TournamentListView(ListView):
    """View for listing all tournaments"""
    model = Tournament
    template_name = 'chess/tournament_list.html'
    context_object_name = 'tournaments'
    
    def get_queryset(self):
        """Get tournaments and pre-calculate winners"""
        tournaments = Tournament.objects.all().order_by('-date')
        
        # For each tournament, find the winner and runner-up
        result = []
        for tournament in tournaments:
            # Manually execute updated standings calculation for completed tournaments
            if tournament.is_completed:
                from .utils import update_tournament_standings
                update_tournament_standings(tournament)
                
                # Get standings sorted by score
                standings = list(tournament.standings.all().order_by('-score'))
                
                # Find winner and runner-up
                if standings:
                    tournament.winner = standings[0].player
                    tournament.runner_up = standings[1].player if len(standings) > 1 else None
                else:
                    tournament.winner = None
                    tournament.runner_up = None
            
            result.append(tournament)
        
        return result
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        today = timezone.now().date()
        
        # Add upcoming tournaments to context
        upcoming_tournaments = Tournament.objects.filter(
            is_completed=False,
            date__gte=today
        ).order_by('date')
        
        # Process upcoming tournaments to attach winners (should be None for upcoming)
        processed_upcoming = []
        for tournament in upcoming_tournaments:
            tournament.winner = None
            tournament.runner_up = None
            processed_upcoming.append(tournament)
        
        context['upcoming_tournaments'] = processed_upcoming
        
        # Add past tournaments to context
        past_tournaments = Tournament.objects.filter(
            is_completed=True
        ).order_by('-date')
        
        # Process past tournaments to attach winners (CLEAN VERSION)
        processed_past = []
        for tournament in past_tournaments:
            # Get standings sorted by score
            standings = list(tournament.standings.all().order_by('-score'))
            
            # Find winner and runner-up WITHOUT adding emoji
            if standings and len(standings) > 0:
                tournament.winner = standings[0].player  # Just assign the player object
                tournament.runner_up = standings[1].player if len(standings) > 1 else None
            else:
                tournament.winner = None
                tournament.runner_up = None
            
            processed_past.append(tournament)
        
        context['past_tournaments'] = processed_past
        
        return context

class TournamentDetailView(DetailView):
    """View for tournament details"""
    model = Tournament
    template_name = 'chess/tournament_detail.html'
    context_object_name = 'tournament'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_object()
        
        # Get tournament standings
        standings = tournament.standings.all().order_by('-score', 'rank')
        context['standings'] = standings
        
        # Get all rounds in order
        rounds = tournament.rounds.all().order_by('number')
        context['rounds'] = rounds
        
        # Get all matches organized by round number
        rounds_matches = {}
        for round_obj in rounds:
            rounds_matches[round_obj.number] = round_obj.matches.all()
        
        context['rounds_matches'] = rounds_matches
        
        # Get current round (first incomplete round)
        try:
            current_round = rounds.filter(is_completed=False).earliest('number')
            context['current_round'] = current_round
            context['current_matches'] = current_round.matches.all()
        except Round.DoesNotExist:
            # If all rounds are completed, set the last round as current
            if rounds.exists():
                context['current_round'] = rounds.latest('number')
                context['current_matches'] = context['current_round'].matches.all()
            else:
                context['current_round'] = None
                context['current_matches'] = []
        
        # Check if this is the final round for admin controls visibility
        if tournament.num_rounds and rounds.exists():
            context['is_final_round'] = rounds.latest('number').number >= tournament.num_rounds
        else:
            context['is_final_round'] = False
        
        # Add available players for dropdown
        if self.request.user.is_staff and not tournament.is_completed:
            # Get already registered player IDs
            registered_player_ids = tournament.participants.values_list('id', flat=True)
            
            # Get available players (not registered, not staff/superuser)
            available_players = User.objects.filter(
                is_active=True, 
                is_staff=False, 
                is_superuser=False
            ).exclude(id__in=registered_player_ids).order_by('first_name', 'last_name')
            
            context['available_players'] = available_players
        
        # For board numbers assignment:
        if context['current_round'] and context['current_matches']:
            current_matches = list(context['current_matches'])
            
            # Get player rankings from standings
            player_rankings = {}
            for standing in context['standings']:
                player_rankings[standing.player.id] = standing.rank or 999
            
            # Calculate board values and assign board numbers
            for match in current_matches:
                white_rank = player_rankings.get(match.white_player.id, 999)
                black_rank = player_rankings.get(match.black_player.id, 999)
                match.board_value = white_rank + black_rank
            
            # Sort matches by board value and assign board numbers
            current_matches.sort(key=lambda m: m.board_value)
            for i, match in enumerate(current_matches):
                match.board_number = i + 1
            
            context['current_matches'] = current_matches
        
        return context
    
class CreateTournamentView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating new tournaments (admin only)"""
    model = Tournament
    form_class = TournamentForm
    template_name = 'chess/tournament_form.html'
    success_url = reverse_lazy('tournament_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, "Tournament created successfully!")
        return super().form_valid(form)

class UpdateTournamentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating tournaments (admin only)"""
    model = Tournament
    form_class = TournamentForm
    template_name = 'chess/tournament_form.html'
    
    def test_func(self):
        # Only staff can update tournaments
        if not self.request.user.is_staff:
            return False
        
        # Check if tournament has started - prevent editing if it has
        tournament = self.get_object()
        return not tournament.has_started
    
    def handle_no_permission(self):
        tournament = self.get_object()
        if tournament.has_started:
            messages.error(self.request, "Cannot edit tournament after it has started")
        return super().handle_no_permission()
    
    def get_success_url(self):
        return reverse_lazy('tournament_detail', kwargs={'pk': self.object.pk})

class StartTournamentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for starting a tournament and generating first round (admin only)"""
    model = Tournament
    template_name = 'chess/start_tournament.html'
    form_class = StartTournamentSettingsForm
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_object()
        context['participants'] = self.get_object().participants.all()
        return context
    
    def form_valid(self, form):
        tournament = self.get_object()
        
        # Ensure we have enough participants
        if tournament.participants.count() < 2:
            messages.error(self.request, "Need at least 2 participants to start tournament")
            return self.form_invalid(form)
        
        # Save tournament settings (tournament type and num_rounds)
        tournament = form.save(commit=False)
        tournament.has_started = True
        tournament.save()
        
        # Create first round
        round_obj = Round.objects.create(tournament=tournament, number=1)
        
        # Generate pairings based on tournament type
        try:
            # Generate the pairings for the first round!
            if tournament.tournament_type in ['round_robin', 'double_round_robin']:
                generate_round_robin_pairings(tournament, round_obj)
            else:  # Swiss
                generate_swiss_pairings(tournament, round_obj)
            
            # Calculate total planned rounds for this tournament type
            participant_count = tournament.participants.count()
            if tournament.tournament_type == 'round_robin':
                if participant_count % 2 == 1:
                    planned_rounds = participant_count
                else:
                    planned_rounds = participant_count - 1
            elif tournament.tournament_type == 'double_round_robin':
                if participant_count % 2 == 1:
                    planned_rounds = participant_count * 2
                else:
                    planned_rounds = (participant_count - 1) * 2
            else:  # Swiss
                planned_rounds = tournament.num_rounds
            
            # Initialize tournament standings
            for player in tournament.participants.all():
                TournamentStanding.objects.create(tournament=tournament, player=player, score=0)
            
            messages.success(self.request, f"Tournament started! Round 1 pairings generated.")
        except Exception as e:
            messages.error(self.request, f"Error starting tournament: {str(e)}")
            # Delete the round if there was an error
            round_obj.delete()
            tournament.has_started = False
            tournament.save()
            return self.form_invalid(form)
        
        return HttpResponseRedirect(reverse_lazy('tournament_detail', kwargs={'pk': tournament.pk}))

class EnterMatchResultView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for entering match results (admin only)"""
    model = Match
    form_class = MatchResultForm
    template_name = 'chess/match_result_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        match = form.save()
        tournament = match.tournament
        round_obj = match.round
        
        # Check if all matches in this round are completed
        pending_matches = round_obj.matches.filter(result='pending')
        
        if not pending_matches.exists():
            # Mark round as completed if not already
            if not round_obj.is_completed:
                round_obj.is_completed = True
                round_obj.save()
                
                # Update tournament standings
                update_tournament_standings(tournament)
                
                # Calculate the planned total rounds based on tournament type
                participant_count = tournament.participants.count()
                if tournament.tournament_type == 'round_robin':
                    planned_rounds = participant_count - 1
                elif tournament.tournament_type == 'double_round_robin':
                    planned_rounds = 2 * (participant_count - 1)
                else:  # Swiss only now
                    planned_rounds = tournament.num_rounds
                
                # Check if there are more rounds to be played and if the next round doesn't already exist
                if round_obj.number < planned_rounds:
                    # Check if the next round already exists
                    next_round_exists = Round.objects.filter(
                        tournament=tournament,
                        number=round_obj.number + 1
                    ).exists()
                    
                    if not next_round_exists:
                        # Create next round
                        next_round = Round.objects.create(
                            tournament=tournament,
                            number=round_obj.number + 1
                        )
                        
                        # Generate pairings for next round
                        if tournament.tournament_type in ['round_robin', 'double_round_robin']:
                            generate_round_robin_pairings(tournament, next_round)
                        else:  # Swiss or Double Swiss
                            generate_swiss_pairings(tournament, next_round)
                        
                        messages.success(self.request, f"Round {round_obj.number} completed. Round {next_round.number} pairings generated.")
                    else:
                        messages.info(self.request, f"Match result updated. Round {round_obj.number} is already completed.")
                else:
                    # The tournament continues until manually ended
                    messages.success(self.request, f"Round {round_obj.number} completed. All planned rounds are now finished.")
            else:
                messages.info(self.request, "Match result updated.")
        
        return HttpResponseRedirect(reverse_lazy('tournament_detail', kwargs={'pk': tournament.pk}))

class UserRegistrationView(CreateView):
    """View for user registration"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'chess/register.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.save()
        messages.success(self.request, "Registration successful! You can now log in.")
        return HttpResponseRedirect(self.success_url)

def register_for_tournament(request, tournament_id):
    """View for players to register for tournaments"""
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to register for tournaments")
        return redirect('login')
    
    # Prevent superusers/staff from registering
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Administrators cannot participate in tournaments")
        return redirect('tournament_detail', pk=tournament_id)
    
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    
    if tournament.is_completed:
        messages.error(request, "This tournament is already completed")
    elif request.user in tournament.participants.all():
        messages.info(request, "You are already registered for this tournament")
    else:
        tournament.participants.add(request.user)
        messages.success(request, f"You have successfully registered for {tournament.name}")
    
    return redirect('tournament_detail', pk=tournament_id)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for superusers to list all users"""
    model = User
    template_name = 'chess/user_list.html'
    context_object_name = 'users'
    ordering = ['username']
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return User.objects.order_by('-is_active', 'username')

class UserEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for superusers to edit user details"""
    model = User
    form_class = UserEditForm
    template_name = 'chess/user_edit.html'
    success_url = reverse_lazy('user_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, f"User {form.instance.username} updated successfully")
        return super().form_valid(form)

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for superusers to create new users"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'chess/user_create.html'
    success_url = reverse_lazy('user_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        user = form.save(commit=False)
        # Set password directly since we're an admin
        user.set_password(form.cleaned_data['password1'])
        user.save()
        messages.success(self.request, f"User {user.username} created successfully")
        return HttpResponseRedirect(self.success_url)

class ProfileView(TemplateView):
    """View for user profiles - can show own profile or others' profiles"""
    template_name = 'chess/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Determine which user's profile to show
        if 'pk' in kwargs:
            # If a specific user ID is provided, show their profile
            profile_user = get_object_or_404(User, pk=kwargs['pk'])
            context['is_own_profile'] = self.request.user.is_authenticated and self.request.user.id == profile_user.id
        else:
            # If no user ID provided, show the current user's profile
            if not self.request.user.is_authenticated:
                # Redirect to login if trying to see own profile while not logged in
                return redirect('login')
            profile_user = self.request.user
            context['is_own_profile'] = True
            
        context['profile_user'] = profile_user
        
        # Get upcoming tournaments the user is registered for
        today = timezone.now().date()
        context['upcoming_tournaments'] = Tournament.objects.filter(
            participants=profile_user,
            date__gte=today,
            is_completed=False
        ).order_by('date')
        
        # Get past tournaments the user participated in
        past_tournaments = Tournament.objects.filter(
            participants=profile_user,
            is_completed=True
        ).order_by('-date')
        
        # Process tournaments and their standings separately
        processed_past_tournaments = []
        for tournament in past_tournaments:
            # Create a temporary copy of the tournament for display purposes
            tournament_info = {
                'id': tournament.id,
                'name': tournament.name,
                'date': tournament.date,
                'standings': None
            }
            
            # Try to find the user's standing for this tournament
            try:
                standing = TournamentStanding.objects.get(
                    tournament=tournament,
                    player=profile_user
                )
                tournament_info['standings'] = standing
            except TournamentStanding.DoesNotExist:
                pass
            
            processed_past_tournaments.append(tournament_info)
        
        context['past_tournaments'] = processed_past_tournaments
        
        # Calculate match statistics
        white_matches = profile_user.white_matches.exclude(result='pending')
        black_matches = profile_user.black_matches.exclude(result='pending')
        
        # Total matches
        context['total_matches'] = white_matches.count() + black_matches.count()
        
        # Wins calculation
        white_wins = white_matches.filter(result='white_win').count()
        black_wins = black_matches.filter(result='black_win').count()
        context['wins'] = white_wins + black_wins
        context['white_wins'] = white_wins
        context['black_wins'] = black_wins
        
        # Losses calculation
        white_losses = white_matches.filter(result='black_win').count()
        black_losses = black_matches.filter(result='white_win').count()
        context['losses'] = white_losses + black_losses
        context['white_losses'] = white_losses
        context['black_losses'] = black_losses
        
        # Draws calculation
        white_draws = white_matches.filter(result='draw').count()
        black_draws = black_matches.filter(result='draw').count()
        context['draws'] = white_draws + black_draws
        context['white_draws'] = white_draws
        context['black_draws'] = black_draws
        
        # Total games and win percentage
        total_games = context['wins'] + context['losses'] + context['draws']
        context['total_games'] = total_games
        
        if total_games > 0:
            context['win_percentage'] = round((context['wins'] / total_games) * 100)
        else:
            context['win_percentage'] = 0
        
        # Win rates by color
        total_white_games = white_wins + white_losses + white_draws
        total_black_games = black_wins + black_losses + black_draws
        
        if total_white_games > 0:
            context['white_win_rate'] = round((white_wins / total_white_games) * 100)
        else:
            context['white_win_rate'] = 0
            
        if total_black_games > 0:
            context['black_win_rate'] = round((black_wins / total_black_games) * 100)
        else:
            context['black_win_rate'] = 0
        
        # Recent match history
        combined_matches = list(white_matches) + list(black_matches)
        combined_matches.sort(key=lambda x: (x.round.tournament.date, x.round.number), reverse=True)
        context['recent_matches'] = combined_matches[:10]  # Keep only the 10 most recent
        
        # Calculate accolades for the user based on their tournament performance
        context['accolades'] = self.calculate_accolades(profile_user)
        
        # Tournament statistics
        # Calculate number of tournaments played
        tournaments_participated = profile_user.tournaments.filter(is_completed=True)
        context['tournament_count'] = tournaments_participated.count()
        
        # Calculate number of tournaments won
        tournaments_won = 0
        avg_position = 0
        avg_points = 0
        
        if context['tournament_count'] > 0:
            # Count tournaments where the user was ranked 1st
            for tournament in tournaments_participated:
                try:
                    standing = tournament.standings.get(player=profile_user, rank=1)
                    if standing:
                        tournaments_won += 1
                except:
                    pass
                
            # Calculate average position and points
            standings = TournamentStanding.objects.filter(
                tournament__in=tournaments_participated,
                player=profile_user
            )
            
            if standings.exists():
                avg_position = standings.aggregate(Avg('rank'))['rank__avg']
                avg_points = standings.aggregate(Avg('score'))['score__avg']
        
        context['tournaments_won'] = tournaments_won
        context['avg_position'] = avg_position if avg_position else 0
        context['avg_points'] = avg_points if avg_points else 0
        
        return context
    
    def calculate_accolades(self, user):
        """Calculate accolades for the user based on their tournament performance"""
        accolades = {
            'support_bear': 0,  # No wins in a tournament
            'dummies': 0,       # Last place in a tournament
            'goat': 0,          # Perfect score in a tournament
            'truce_seeker': 0,  # 50%+ draws
        }
        
        # Get all completed tournaments the user participated in
        tournaments = Tournament.objects.filter(
            participants=user,
            is_completed=True
        )
        
        for tournament in tournaments:
            # Get user's matches in this tournament
            user_matches = Match.objects.filter(
                Q(white_player=user) | Q(black_player=user),
                tournament=tournament
            ).exclude(result='pending')
            
            if not user_matches.exists():
                continue
                
            # Count wins, losses, draws
            wins = 0
            draws = 0
            total = user_matches.count()
            
            for match in user_matches:
                if (match.white_player == user and match.result == 'white_win') or \
                   (match.black_player == user and match.result == 'black_win'):
                    wins += 1
                elif match.result == 'draw':
                    draws += 1
            
            # Calculate accolades
            if wins == 0 and total > 0:
                accolades['support_bear'] += 1
                
            # Check if user was last place
            try:
                standing = TournamentStanding.objects.get(
                    tournament=tournament,
                    player=user
                )
                participants_count = tournament.participants.count()
                
                if standing.rank == participants_count:
                    accolades['dummies'] += 1
                    
                if standing.rank == 1 and wins == total:
                    accolades['goat'] += 1
            except TournamentStanding.DoesNotExist:
                pass
                
            # Check for truce seeker
            if total > 0 and (draws / total) >= 0.5:
                accolades['truce_seeker'] += 1
                
        return accolades

@login_required
def profile_edit(request):
    """View for users to edit their own profile"""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully")
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'chess/profile_edit.html', {'form': form})

def user_toggle_active(request, pk):
    """Toggle user active status (enable/disable account)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('home')
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} {status} successfully")
    return redirect('user_list')

# Tournament player management views

def add_player_to_tournament(request, tournament_id):
    """Admin view to add a player to a tournament"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('tournament_detail', pk=tournament_id)
    
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    
    if tournament.is_completed or tournament.has_started:
        messages.error(request, "Cannot add players after tournament has started")
        return redirect('tournament_detail', pk=tournament_id)
    
    if request.method == 'POST':
        player_id = request.POST.get('player')
        if player_id:
            try:
                player = User.objects.get(id=player_id)
                # Double check that player is not a superuser or staff
                if player.is_superuser or player.is_staff:
                    messages.error(request, "Cannot add superuser or staff to tournaments")
                elif player in tournament.participants.all():
                    messages.info(request, f"{player.get_full_name() or player.username} is already registered for this tournament")
                else:
                    tournament.participants.add(player)
                    messages.success(request, f"{player.get_full_name() or player.username} added to tournament successfully")
            except User.DoesNotExist:
                messages.error(request, "Player not found")
        else:
            messages.error(request, "No player selected")
    
    return redirect('tournament_detail', pk=tournament_id)

def remove_player_from_tournament(request, tournament_id, player_id):
    """Admin view to remove a player from a tournament"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('tournament_detail', pk=tournament_id)
    
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    player = get_object_or_404(User, pk=player_id)
    
    if tournament.is_completed:
        messages.error(request, "Cannot remove players from completed tournaments")
    elif tournament.rounds.exists():
        messages.error(request, "Cannot remove players after tournament has started")
    else:
        tournament.participants.remove(player)
        messages.success(request, f"{player.username} removed from tournament successfully")
    
    return redirect('tournament_detail', pk=tournament_id)

def complete_round(request, tournament_id, round_id):
    """Admin view to manually complete a round and generate the next round"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('tournament_detail', pk=tournament_id)
    
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    round_obj = get_object_or_404(Round, pk=round_id)
    
    if tournament.is_completed:
        messages.error(request, "This tournament is already completed")
        return redirect('tournament_detail', pk=tournament_id)
    
    if round_obj.tournament_id != tournament.id:
        messages.error(request, "Round doesn't belong to this tournament")
        return redirect('tournament_detail', pk=tournament_id)
    
    # Check if any matches are still pending
    pending_matches = round_obj.matches.filter(result='pending')
    if pending_matches.exists():
        messages.warning(request, f"There are still {pending_matches.count()} pending matches in this round")
        return redirect('tournament_detail', pk=tournament_id)
    
    # Mark round as completed
    round_obj.is_completed = True
    round_obj.save()
    
    # Update tournament standings
    update_tournament_standings(tournament)
    
    # Calculate the planned total rounds based on tournament type
    participant_count = tournament.participants.count()
    if tournament.tournament_type == 'round_robin':
        if participant_count % 2 == 1:
            planned_rounds = participant_count
        else:
            planned_rounds = participant_count - 1
    elif tournament.tournament_type == 'double_round_robin':
        if participant_count % 2 == 1:
            planned_rounds = participant_count * 2
        else:
            planned_rounds = (participant_count - 1) * 2
    else:  # Swiss
        planned_rounds = tournament.num_rounds
    
    # Check if there are more rounds to be played
    if round_obj.number < planned_rounds:
        # Check if the next round already exists
        next_round_exists = Round.objects.filter(
            tournament=tournament,
            number=round_obj.number + 1
        ).exists()
        
        if not next_round_exists:
            # Create next round
            next_round = Round.objects.create(
                tournament=tournament,
                number=round_obj.number + 1
            )
            
            # Generate pairings for next round
            if tournament.tournament_type in ['round_robin', 'double_round_robin']:
                generate_round_robin_pairings(tournament, next_round)
            else:  # Swiss
                generate_swiss_pairings(tournament, next_round)
            
            messages.success(request, f"Round {round_obj.number} completed. Round {next_round.number} pairings generated.")
        else:
            messages.info(request, f"Round {round_obj.number} completed. Round {round_obj.number + 1} already exists.")
    else:
        # All planned rounds are done
        messages.success(request, f"Round {round_obj.number} completed. All planned rounds are now finished.")
    
    return redirect('tournament_detail', pk=tournament_id)

def complete_tournament(request, tournament_id):
    """Admin view to manually complete a tournament"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('tournament_detail', pk=tournament_id)
    
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    
    if tournament.is_completed:
        messages.error(request, "This tournament is already completed")
        return redirect('tournament_detail', pk=tournament_id)
    
    # Ensure all matches have results before completing
    pending_matches = tournament.matches.filter(result='pending')
    if pending_matches.exists():
        for match in pending_matches:
            # Set any pending matches to draws to ensure all matches have a result
            match.result = 'draw'
            match.save()
            messages.warning(request, f"Set pending match between {match.white_player.username} and {match.black_player.username} to a draw")
    
    # Update tournament standings one last time
    update_tournament_standings(tournament)
    
    # Mark the tournament as completed
    tournament.is_completed = True
    tournament.save()
    
    messages.success(request, "Tournament has been marked as completed")
    return redirect('tournament_detail', pk=tournament_id)

def player_search(request):
    query = request.GET.get('q', '')
    if query:
        players = User.objects.filter(
            is_active=True, 
            is_staff=False, 
            is_superuser=False
        ).filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(lichess_account__icontains=query) |
            Q(chesscom_account__icontains=query)
        ).order_by('-elo')
    else:
        players = User.objects.none()
    
    return render(request, 'chess/player_search.html', {
        'players': players,
        'query': query
    })

def simple_register(request):
    if request.method == 'POST':
        form = SimplePlayerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Player registration successful! You've been added to our player database.")
            return redirect('home')
    else:
        form = SimplePlayerRegistrationForm()
    
    return render(request, 'chess/simple_register.html', {'form': form})

def inline_match_result(request, match_id):
    """AJAX view to update match results inline from the tournament page"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    # Add debug logging
    print(f"Request method: {request.method}")
    print(f"POST data: {request.POST}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    match = get_object_or_404(Match, pk=match_id)
    tournament = match.tournament
    
    # Check if tournament is completed
    if tournament.is_completed:
        return JsonResponse({'success': False, 'error': 'Tournament is already completed'})
    
    # Get the new result from the form
    result = request.POST.get('result')
    print(f"Received result: {result}")
    
    # Validate the result more explicitly
    valid_results = ['white_win', 'black_win', 'draw', 'pending']
    if result not in valid_results:
        return JsonResponse({'success': False, 'error': f'Invalid result: {result}. Expected one of {valid_results}'})
    
    # Update the match
    match.result = result
    match.save()
    
    # Update tournament standings
    update_tournament_standings(tournament)
    
    return JsonResponse({'success': True})

def player_rating_history(request, player_id):
    """API view to get rating history data for a player chart"""
    try:
        player = User.objects.get(pk=player_id)
        
        # Get all completed tournaments where this player participated
        tournaments = Tournament.objects.filter(
            participants=player,
            is_completed=True
        ).order_by('date')
        
        data = []
        
        for tournament in tournaments:
            time_control = tournament.time_control or 'blitz'
            
            # Get player's standing in this tournament
            try:
                standing = TournamentStanding.objects.get(
                    tournament=tournament,
                    player=player
                )
                
                # Determine which rating field to use based on time control
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
                
                # Add tournament data point
                data.append({
                    'date': tournament.date.strftime('%b %d, %Y'),
                    'rating': rating,
                    'time_control': time_control,
                    'tournament': tournament.name,
                    'standing': standing.score
                })
            except TournamentStanding.DoesNotExist:
                pass
        
        return JsonResponse(data, safe=False)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)