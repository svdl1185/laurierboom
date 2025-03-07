# views.py
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import F, Count, Sum, Q
from django.http import HttpResponseRedirect

from .models import Tournament, User, Match, Round, TournamentStanding
from .forms import EmptyForm, MatchResultForm, SimplePlayerRegistrationForm, StartTournamentSettingsForm, TournamentForm, UserEditForm, UserRegistrationForm, AddPlayerToTournamentForm
from .utils import generate_swiss_pairings, generate_round_robin_pairings, update_tournament_standings


class HomeView(ListView):
    """Homepage view showing the top rated players"""
    model = User
    template_name = 'chess/home.html'
    context_object_name = 'players'
    
    def get_queryset(self):
        # Get users ordered by Elo rating, excluding superusers/staff
        return User.objects.filter(is_active=True, is_staff=False, is_superuser=False).order_by('-elo')[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upcoming_tournaments'] = Tournament.objects.filter(
            is_completed=False
        ).order_by('date')[:5]
        context['recent_tournaments'] = Tournament.objects.filter(
            is_completed=True
        ).order_by('-date')[:5]
        return context

class PlayerDetailView(DetailView):
    """View for player profiles"""
    model = User
    template_name = 'chess/player_detail.html'
    context_object_name = 'player'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player = self.get_object()
        
        # Get player's tournaments
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
        
        # Recent match history
        context['recent_matches'] = (list(white_matches) + list(black_matches))[-10:]
        
        return context

class TournamentListView(ListView):
    """View for listing all tournaments"""
    model = Tournament
    template_name = 'chess/tournament_list.html'
    context_object_name = 'tournaments'
    ordering = ['-date']

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
        
        # Get rounds and matches
        rounds = tournament.rounds.all().order_by('number')
        context['rounds'] = rounds
        
        # Get completed matches
        completed_matches = tournament.matches.exclude(result='pending')
        context['completed_matches'] = completed_matches
        
        # Get current round's matches
        try:
            current_round = rounds.filter(is_completed=False).earliest('number')
            context['current_round'] = current_round
            context['current_matches'] = current_round.matches.all()
        except Round.DoesNotExist:
            context['current_round'] = None
            
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
        return self.request.user.is_staff
    
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
            if tournament.tournament_type == 'round_robin' or tournament.tournament_type == 'double_round_robin':
                generate_round_robin_pairings(tournament, round_obj)
            else:  # Swiss or Double Swiss
                generate_swiss_pairings(tournament, round_obj)
            
            # Initialize tournament standings
            for player in tournament.participants.all():
                TournamentStanding.objects.create(tournament=tournament, player=player)
            
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
    
    if tournament.is_completed:
        messages.error(request, "Cannot add players to completed tournaments")
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
        planned_rounds = participant_count - 1
    elif tournament.tournament_type == 'double_round_robin':
        planned_rounds = 2 * (participant_count - 1)
    else:  # Swiss only now
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
            else:  # Swiss or Double Swiss
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