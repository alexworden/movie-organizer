# Movie Organizer

This is a web application for organizing movies based on genre. Users can configure movie folders and genre categories, and the application will suggest moving movies into the correct folders based on their genres.

## Requirements

- Python 3.x
- Flask
- Requests
- Hugging Face Hub

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a Hugging Face API Token:
   - Go to https://huggingface.co/settings/tokens
   - Sign up for a free account if you don't have one
   - Create a new token with read access
   - Export the token as an environment variable:
     ```bash
     export HUGGINGFACE_API_TOKEN='your-token-here'
     ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and go to `http://localhost:5001` to access the application.

## Usage

1. Configuration:
   - Add movie folders where your movies are stored
   - Configure genre categories (comma-separated)
   - Save the configuration

2. Movies:
   - View all movies in the configured folders
   - Get genre suggestions for each movie
   - Approve suggestions to move movies to appropriate genre folders

## Features

- Automatic genre detection using AI
- Support for multiple movie folders
- Custom genre categories
- Movie file organization
- Clean movie title parsing
