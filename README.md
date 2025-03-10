# De Laurierboom Chess Club Management System

This project is a comprehensive chess tournament management system built for De Laurierboom Chess Club in Amsterdam. It's a Django-based web application that helps manage players, tournaments, matches, and ratings.

## Features

### Player Management
- Player profiles with personal details and chess platform accounts (Lichess, Chess.com)
- Different rating categories (Bullet, Blitz, Rapid, Classical)
- Rating history tracking and visualization
- Player search functionality

### Tournament Management
- Multiple tournament formats (Swiss, Round Robin, Double Round Robin)
- Different time controls (Bullet, Blitz, Rapid, Classical)
- Automatic pairing generation for each round
- Result tracking and standings calculation
- Cross-table view of tournament results

### Rating System
- Glicko-2 rating implementation for accurate ratings
- Separate ratings for different time controls
- Rating adjustments based on match results

### User Interface
- Responsive design that works on desktop and mobile
- Intuitive navigation and player/tournament discovery
- Beautiful styling with Bootstrap and custom CSS

## Technical Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQL (supports SQLite, PostgreSQL via settings)
- **Deployment**: Ready for Heroku deployment

## Project Structure

The project follows a standard Django application structure:

- **`models.py`**: Database models for User, Tournament, Round, Match, and TournamentStanding
- **`views.py`**: View functions and classes for handling HTTP requests
- **`urls.py`**: URL routing configuration
- **`forms.py`**: Form classes for data input and validation
- **`utils.py`**: Utility functions including Swiss/Round Robin pairing algorithms
- **`templates/`**: HTML templates for rendering pages
- **`static/`**: Static assets including CSS and JavaScript

## Key Components

- **Custom User Model**: Extended Django's user model to include chess-specific fields
- **Pairing Algorithms**: Implementations of Swiss and Round Robin tournament pairings
- **Glicko-2 Rating System**: For accurate player ratings across different time controls
- **Tournament Standings**: Automatic calculation of scores and rankings
- **Rating History Chart**: Visualization of player rating progression

## Getting Started

1. Clone the repository
2. Install dependencies using `pip install -r requirements.txt`
3. Run migrations with `python manage.py migrate`
4. Create a superuser with `python manage.py createsuperuser`
5. Run the development server with `python manage.py runserver`

## Development Mode vs Production

The project includes separate settings files:
- `settings.py`: For local development (SQLite)
- `production_settings.py`: For production deployment (PostgreSQL, security settings)

## License

This project is designed specifically for De Laurierboom Chess Club but can be adapted for use by other chess clubs or tournament organizers.

## Contributors

This project was developed for the De Laurierboom Chess Club in Amsterdam.