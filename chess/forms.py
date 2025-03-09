# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator
from .models import Tournament, Match, User
from django.utils.crypto import get_random_string

class TournamentForm(forms.ModelForm):
    """Form for creating and updating tournaments"""
    class Meta:
        model = Tournament
        fields = ['name', 'date', 'start_time', 'location', 'tournament_type', 'time_control', 'num_rounds', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'tournament_type': forms.Select(attrs={'class': 'form-select', 'required': False}),
            'num_rounds': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_control': forms.Select(attrs={'class': 'form-select', 'required': True}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        tournament_type = cleaned_data.get('tournament_type')
        num_rounds = cleaned_data.get('num_rounds')
        
        # If tournament_type is provided, validate it
        if tournament_type:
            # Only validate if tournament_type is provided and is Swiss type
            if tournament_type == 'swiss' and not num_rounds:
                self.add_error('num_rounds', 'Number of rounds is required for Swiss tournaments')
            
            # For round robin types, num_rounds is automatically calculated
            if tournament_type in ['round_robin', 'double_round_robin'] and num_rounds:
                # Clear the num_rounds as it's calculated automatically
                cleaned_data['num_rounds'] = None
        
        return cleaned_data

class StartTournamentSettingsForm(forms.ModelForm):
    """Form for configuring tournament settings just before starting"""
    class Meta:
        model = Tournament
        fields = ['tournament_type', 'num_rounds']
        widgets = {
            'tournament_type': forms.Select(attrs={'class': 'form-select'}),
            'num_rounds': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        tournament_type = cleaned_data.get('tournament_type')
        num_rounds = cleaned_data.get('num_rounds')
        
        # Only validate if tournament_type is provided and is Swiss type
        if tournament_type == 'swiss' and not num_rounds:
            self.add_error('num_rounds', 'Number of rounds is required for Swiss tournaments')
        
        # For round robin types, num_rounds is automatically calculated
        if tournament_type in ['round_robin', 'double_round_robin'] and num_rounds:
            # Clear the num_rounds as it's calculated automatically
            cleaned_data['num_rounds'] = None
        
        return cleaned_data

class MatchResultForm(forms.ModelForm):
    """Form for entering match results"""
    class Meta:
        model = Match
        fields = ['result']
        widgets = {
            'result': forms.Select(attrs={'class': 'form-control'})
        }

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    first_name = forms.CharField(required=True, help_text="Required")
    last_name = forms.CharField(required=True, help_text="Required")
    email = forms.EmailField(required=False, help_text="Optional")
    lichess_account = forms.CharField(required=False, help_text="Your Lichess username (optional)")
    chesscom_account = forms.CharField(required=False, help_text="Your Chess.com username (optional)")
    fide_rating = forms.IntegerField(required=False, help_text="Your FIDE rating, if you have one (optional)")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'lichess_account', 'chesscom_account', 'fide_rating', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # If no username provided, create one
        if not user.username:
            # Create username from first and last name
            base_username = f"{user.first_name.lower()}{user.last_name.lower()}"
            username = base_username
            # Make sure username is unique
            count = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{count}"
                count += 1
            user.username = username
        user.lichess_account = self.cleaned_data['lichess_account']
        user.chesscom_account = self.cleaned_data['chesscom_account']
        user.fide_rating = self.cleaned_data['fide_rating']
        
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    """Form for admins to edit user details"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'lichess_account', 'chesscom_account', 'fide_rating', 'elo', 'is_active']
        widgets = {
            'elo': forms.NumberInput(attrs={'step': '0.1'}),
        }

class TournamentRegistrationForm(forms.Form):
    """Form for players to register for tournaments"""
    confirm = forms.BooleanField(
        required=True,
        label="I confirm my participation in this tournament",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class AddPlayerToTournamentForm(forms.Form):
    """Form for admins to add players to a tournament"""
    player = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True, is_staff=False, is_superuser=False).order_by('username'),
        label="Select Player",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class SimplePlayerRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'lichess_account', 'chesscom_account', 'fide_id']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_player_only = True
        
        # Generate a random password since Django requires one
        random_password = get_random_string(length=12)
        user.set_password(random_password)
        
        if commit:
            user.save()
        return user



class EmptyForm(forms.Form):
    """Form with no fields, used for CSRF protection only"""
    pass