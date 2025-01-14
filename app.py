from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
import os
import json
import logging
import shutil
from pathlib import Path
from genre_suggester.base_suggester import GenreSuggestion
from genre_suggester.openai_suggester import OpenAIGenreSuggester
from genre_suggester.tmdb_suggester import TMDBGenreSuggester
import requests
from rich.logging import RichHandler
from rich.console import Console
from rich import print as rprint
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

# Configure rich console logging
console = Console(force_terminal=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s %(message)s'
)
logger = logging.getLogger("movie_organizer")

# Set OpenAI logger to debug as well
logging.getLogger('genre_suggester.openai_suggester').setLevel(logging.DEBUG)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get API tokens from environment
OPENAI_API_TOKEN = os.getenv('MOVIE_ORGANIZER_OPENAI_API_TOKEN')
TMDB_API_KEY = os.getenv('MOVIE_ORGANIZER_TMDB_API_KEY')

# Initialize genre suggester
if OPENAI_API_TOKEN:
    logger.info("Using OpenAI for genre suggestions")
    # Create TMDB suggester as fallback if API key is available
    tmdb_suggester = TMDBGenreSuggester(TMDB_API_KEY) if TMDB_API_KEY else None
    if tmdb_suggester:
        try:
            tmdb_suggester.initialize()
            logger.info("Initialized TMDB suggester as fallback")
        except Exception as e:
            logger.error(f"Failed to initialize TMDB suggester: {e}")
            tmdb_suggester = None
    
    # Create OpenAI suggester with optional TMDB fallback
    genre_suggester = OpenAIGenreSuggester(OPENAI_API_TOKEN, tmdb_suggester=tmdb_suggester)
    try:
        genre_suggester.initialize()
        logger.info("Successfully initialized OpenAI genre suggester")
    except Exception as e:
        logger.error(f"Failed to initialize genre suggester: {e}", exc_info=True)
        genre_suggester = None
else:
    logger.error("OpenAI API token not configured")
    genre_suggester = None

# Create a thread pool for handling LLM requests
llm_executor = ThreadPoolExecutor(max_workers=3)

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'movie_folders': [], 'genres': []}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)

def check_folder_access(folder_path):
    """Check if we have access to the folder and provide guidance if we don't"""
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True, None
    except PermissionError as e:
        error_message = f"""Cannot access folder: {folder_path}

To fix this, you need to grant Full Disk Access to your Terminal app:
1. Open System Preferences
2. Go to Security & Privacy > Privacy
3. Select "Full Disk Access" from the left sidebar
4. Click the lock icon to make changes
5. Add your Terminal app (or iTerm if you're using that)
6. Restart your Terminal and the Flask application

Error details: {str(e)}"""
        logger.error(error_message, exc_info=True)
        return False, error_message

def get_relative_path(file_path, base_folder):
    """Get the relative path of a file from its base folder"""
    try:
        return str(Path(file_path).relative_to(base_folder))
    except ValueError:
        return str(file_path)

def get_movie_files(folder_path):
    """Get all movie files from the folder and subfolders"""
    movies = []
    try:
        # First check if we have access to the folder
        has_access, error_message = check_folder_access(folder_path)
        if not has_access:
            logger.error(error_message, exc_info=True)
            return []

        # Get the configured genres
        config = load_config()
        genres = config.get('genres', [])

        # Walk through the folder and its subfolders
        for root, _, files in os.walk(folder_path):
            # Skip #recycle folders
            if '#recycle' in root.lower():
                continue
                
            for file in files:
                if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    full_path = os.path.join(root, file)
                    relative_path = get_relative_path(full_path, folder_path)
                    current_genre = os.path.basename(os.path.dirname(relative_path))
                    
                    # Skip if the immediate parent folder is #recycle
                    if current_genre.lower() == '#recycle':
                        continue
                        
                    # Only consider it a genre if it's in our configured genres
                    if current_genre not in genres:
                        current_genre = "Uncategorized"
                    
                    movies.append({
                        'title': os.path.splitext(file)[0],
                        'path': relative_path,
                        'base_folder': folder_path,
                        'current_genre': current_genre,
                        'suggested_genre': None
                    })
        
        return sorted(movies, key=lambda x: x['title'].lower())
    except PermissionError as e:
        logger.error(f"Permission denied accessing {folder_path}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error getting movie files: {str(e)}", exc_info=True)
        raise

# Business Logic Methods
def clean_movie_title(filename: str) -> str:
    """Clean up movie title from filename"""
    # Remove file extension
    title = Path(filename).stem
    
    # Extract year if present
    year_match = re.search(r'(?:^|\D)(\d{4})(?:\D|$)', title)
    year = year_match.group(1) if year_match else None
    
    # Remove common video quality and source patterns
    patterns = [
        r'\b\d{3,4}p\b',           # Resolution (e.g., 720p, 1080p)
        r'\bHDTV\b',
        r'\bDVDRip\b',
        r'\bBluRay\b',
        r'\bWEB-?DL\b',            # Handle both WEB-DL and WEBDL
        r'\bWEBRip\b',
        r'\bx\d{3}\b',             # x264, x265
        r'\bAAC\d*\b',             # AAC, AAC5.1
        r'\bHEVC\b',
        r'\bDD5\.1\b',             # Audio format
        r'\d+MB\b',              # File size
        r'\[.*?\]',                # Anything in brackets
        r'\(.*?\)',                # Anything in parentheses
    ]
    
    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Replace dots and underscores with spaces
    title = title.replace('.', ' ').replace('_', ' ')
    
    # Remove multiple spaces
    title = ' '.join(title.split())
    
    # Add year back if found
    if year:
        title = f"{title} ({year})"
    
    return title.strip()

def suggest_genre_for_movie(movie_path):
    """Get genre suggestion for a movie"""
    if not genre_suggester:
        logger.error("No genre suggester configured. Check if OpenAI API token is set.")
        return GenreSuggestion(
            genre=None,
            confidence="Low",
            status="error",
            message="Genre suggester not configured. Check if OpenAI API token is set."
        )
        
    clean_title = clean_movie_title(movie_path)
    logger.info(f"Processing movie: '{clean_title}'")
    
    config = load_config()
    return genre_suggester.suggest_genre(clean_title, config.get('genres', []))

def ensure_genre_folder(base_folder, genre):
    """Create genre folder if it doesn't exist"""
    genre_folder = Path(base_folder) / genre
    if not genre_folder.exists():
        genre_folder.mkdir(parents=True, exist_ok=True)
    return str(genre_folder)

def has_movies_or_subdirs(directory: Path) -> bool:
    """Check if directory contains any movie files or subdirectories"""
    try:
        for item in directory.iterdir():
            if item.is_dir():
                return True  # Has subdirectory
            if item.is_file() and item.suffix.lower() in ('.mp4', '.mkv', '.avi', '.mov'):
                return True  # Has movie file
        return False
    except Exception as e:
        logger.error(f"Error checking directory {directory}: {e}", exc_info=True)
        return True  # Assume it has content if we can't check

def move_movie_file(src_path, dest_folder):
    """Move a movie file to destination folder and clean up empty source directory"""
    # Convert relative path to absolute path if needed
    src = Path(src_path)
    if not src.is_absolute():
        # Get the base folder from the path components before the movie file
        # e.g., "Evil.Dead.Rise.2023.../movie.mkv" -> need to prepend base folder
        base_folder = Path(dest_folder).parent
        src = base_folder / src
    
    src_dir = src.parent
    dest = Path(dest_folder) / src.name
    
    logger.info(f"Moving movie from '{src}' to '{dest}'")
    
    # Ensure source file exists
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    # Move the movie file
    shutil.move(str(src), str(dest))
    
    # Check if source directory should be cleaned up
    if src_dir.exists() and src_dir != Path(dest_folder):
        if not has_movies_or_subdirs(src_dir):
            try:
                logger.info(f"Removing directory and contents: {src_dir}")
                shutil.rmtree(str(src_dir))
            except Exception as e:
                logger.error(f"Error removing directory {src_dir}: {e}", exc_info=True)
    
    return dest

# HTTP Request Handlers
@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/movies')
def movies():
    try:
        config = load_config()
        movie_folders = config.get('movie_folders', [])
        selected_folder = request.args.get('selected_folder', movie_folders[0] if movie_folders else None)
        
        if not selected_folder:
            return render_template('movies.html', error_message="No movie folders configured", 
                                movie_folders=[], movies=[], config=config)
        
        # Check folder access before proceeding
        has_access, error_message = check_folder_access(selected_folder)
        if not has_access:
            return render_template('movies.html', error_message=error_message,
                                movie_folders=movie_folders, movies=[], 
                                selected_folder=selected_folder, config=config)
        
        movies = get_movie_files(selected_folder)
        return render_template('movies.html', movies=movies, movie_folders=movie_folders,
                             selected_folder=selected_folder, config=config)
    except Exception as e:
        logger.error(f"Error in movies route: {str(e)}", exc_info=True)
        return render_template('movies.html', error_message=str(e), 
                             movie_folders=[], movies=[], config=load_config())

@app.route('/configure', methods=['POST'])
def configure():
    config = load_config()
    config['movie_folders'] = [folder.strip() for folder in request.form.get('movie_folders', '').split('\n') if folder.strip()]
    # Split genres by comma and strip whitespace, then split any that contain newlines
    genres_text = request.form.get('genres', '').strip()
    raw_genres = [genre.strip() for genre in genres_text.split(',') if genre.strip()]
    # Handle any genres that might contain newlines
    genres = []
    for genre in raw_genres:
        genres.extend([g.strip() for g in genre.split('\n') if g.strip()])
    # Remove duplicates and sort alphabetically
    config['genres'] = sorted(set(genres))
    save_config(config)
    return redirect(url_for('index'))

@app.route('/suggest_genre', methods=['POST'])
def suggest_genre():
    """Handle genre suggestion request"""
    try:
        data = request.get_json()
        logger.info(f"Received genre suggestion request: {data}")  # Debug log
        
        movie_path = data.get('title')
        if not movie_path:
            logger.error("No movie path provided in request")  # Debug log
            return jsonify({'error': 'No movie path provided'}), 400
            
        logger.info(f"Processing movie path: {movie_path}")  # Debug log
        suggestion = suggest_genre_for_movie(movie_path)
        logger.info(f"Got genre suggestion: {suggestion}")  # Debug log
        
        # Convert GenreSuggestion object to response format
        response = {
            'genre': suggestion.genre,
            'status': suggestion.status
        }
        if suggestion.message:
            response['message'] = suggestion.message
            
        return jsonify(response)
            
    except Exception as e:
        logger.error(f"Error in genre suggestion: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/move_movie', methods=['POST'])
def move_movie():
    """Handle movie move request"""
    try:
        data = request.get_json()
        movie_path = data.get('movie_path')
        base_folder = data.get('base_folder')
        genre = data.get('genre')
        
        if not all([movie_path, base_folder, genre]):
            missing = [k for k, v in {'movie_path': movie_path, 'base_folder': base_folder, 'genre': genre}.items() if not v]
            return jsonify({'error': f'Missing required parameters: {", ".join(missing)}'}), 400
            
        genre_folder = ensure_genre_folder(base_folder, genre)
        dest_path = move_movie_file(movie_path, genre_folder)
        
        return jsonify({'success': True, 'new_path': str(dest_path)})
        
    except Exception as e:
        logger.error("Error moving movie", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/add_genre', methods=['POST'])
def add_genre():
    """Handle new genre addition request"""
    try:
        data = request.get_json()
        new_genre = data.get('genre')
        if not new_genre:
            return jsonify({'error': 'No genre provided'}), 400
            
        config = load_config()
        if new_genre not in config['genres']:
            config['genres'].append(new_genre)
            save_config(config)
            
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error("Error adding genre", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check environment variables on startup
    token_status = "not set" if not OPENAI_API_TOKEN else "set"
    logger.info(f"Starting app with OpenAI API token status: {token_status}")
    
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=True)
