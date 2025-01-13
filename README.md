# MovieOrg - AI-Powered Movie Library Organizer

🎬 AI-powered movie library organizer that automatically categorizes your movies by genre. Uses OpenAI's GPT-4 and TMDB to intelligently analyze titles, clean up filenames, and organize files into genre folders. Perfect for keeping your movie collection tidy and well-structured.

## Features

- 🤖 **Smart Genre Detection**
  - Uses OpenAI GPT-4 to understand movie titles and suggest genres
  - Falls back to TMDB for additional movie information
  - Handles various filename formats and quality indicators

- 📁 **Intelligent File Management**
  - Automatically organizes movies into genre-based folders
  - Cleans up empty source directories after moving files
  - Preserves movie years in filenames

- 🌐 **Web Interface**
  - Easy-to-use web UI for managing your movie collection
  - Real-time genre suggestions
  - Configurable genre categories

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/alexworden/movie-organizer.git
   cd movie-organizer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**
   ```bash
   export MOVIE_ORGANIZER_OPENAI_API_TOKEN="your-openai-api-key"
   export MOVIE_ORGANIZER_TMDB_API_KEY="your-tmdb-api-key"
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

   Visit `http://localhost:5000` in your browser.

## Configuration

1. **Movie Folders**: Add paths to your movie directories in the web interface
2. **Genres**: Configure your preferred genre categories
3. **API Keys**:
   - Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com)
   - Get a TMDB API key from [TMDB](https://www.themoviedb.org/settings/api)

## How It Works

1. When you select a movie, MovieOrg:
   - Cleans up the filename (removes quality indicators, etc.)
   - Uses GPT-4 to analyze the movie title and suggest a genre
   - If GPT-4 can't determine the genre, uses TMDB as a fallback
   - Moves the file to the appropriate genre folder
   - Cleans up empty source directories

2. The application maintains a clean directory structure by:
   - Creating genre folders as needed
   - Moving movie files to their genre folders
   - Removing empty source directories (preserving non-movie files)

## Requirements

- Python 3.8+
- OpenAI API key
- TMDB API key (optional, but recommended)
- Modern web browser

## License

MIT License - See LICENSE file for details
