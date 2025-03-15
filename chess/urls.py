# chess/urls.py
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # Home and player views
    path('', views.HomeView.as_view(), name='home'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Tournament views
    path('tournaments/', views.TournamentListView.as_view(), name='tournament_list'),
    path('tournament/<int:pk>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
    path('tournament/new/', views.CreateTournamentView.as_view(), name='tournament_create'),
    path('tournament/<int:pk>/edit/', views.UpdateTournamentView.as_view(), name='tournament_update'),
    path('tournament/<int:pk>/start/', views.StartTournamentView.as_view(), name='tournament_start'),
    path('tournament/<int:tournament_id>/register/', views.register_for_tournament, name='tournament_register'),
    path('tournament/<int:tournament_id>/add-player/', views.add_player_to_tournament, name='add_player_to_tournament'),
    path('tournament/<int:tournament_id>/remove-player/<int:player_id>/', views.remove_player_from_tournament, name='remove_player_from_tournament'),
    path('tournament/<int:tournament_id>/complete/', views.complete_tournament, name='complete_tournament'),
    path('tournament/<int:tournament_id>/round/<int:round_id>/complete/', views.complete_round, name='complete_round'),

    path('tournament/<int:tournament_id>/register/', views.register_for_tournament, name='tournament_register'),
    path('tournament/<int:tournament_id>/unregister/', views.unregister_from_tournament, name='tournament_unregister'),
    
    # Match views
    path('match/<int:pk>/result/', views.EnterMatchResultView.as_view(), name='match_result'),
    path('match/<int:match_id>/inline-result/', views.inline_match_result, name='inline_match_result'),
    
    # User management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/new/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    
    # User authentication
    path('accounts/', include('allauth.urls')),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('register/simple/', views.simple_register, name='simple_register'),
    path('login/', LoginView.as_view(template_name='chess/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    
    # Player search
    path('players/search/', views.player_search, name='player_search'),
    path('player/<int:player_id>/rating-history/', views.player_rating_history, name='player_rating_history'),
]