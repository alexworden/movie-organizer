import logging
from typing import List, Optional, Dict, Tuple
from openai import OpenAI
from .base_suggester import GenreSuggesterInterface, GenreSuggestion
from .tmdb_suggester import TMDBGenreSuggester

logger = logging.getLogger(__name__)

class OpenAIGenreSuggester(GenreSuggesterInterface):
    """Genre suggester that uses OpenAI's GPT-4"""
    
    def __init__(self, api_key: str, tmdb_suggester: Optional[TMDBGenreSuggester] = None, model: str = "gpt-4-1106-preview"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self.tmdb_suggester = tmdb_suggester
        
    def initialize(self) -> None:
        """Initialize OpenAI client"""
        if not self.api_key:
            raise ValueError("No OpenAI API key provided")
        self.client = OpenAI(api_key=self.api_key)
        
    def cleanup(self) -> None:
        """Clean up resources"""
        self.client = None
        
    def suggest_genre(self, title: str, valid_genres: List[str]) -> GenreSuggestion:
        """Get genre suggestion using OpenAI"""
        if not self.client:
            raise ValueError("Client not initialized. Call initialize() first")
            
        # Create the prompt for both title extraction and genre suggestion
        genres_list = ', '.join(valid_genres)
        messages = [
            {"role": "system", "content": """You are a movie expert who can clean up movie filenames and determine genres.
Given a movie filename, first extract the actual title and year, then determine its genre.

Format your response EXACTLY like this:
TITLE: [cleaned movie title]
YEAR: [year if found, or N/A if not found]
SELECTED_GENRE: [Use one of the provided genres if suitable, otherwise suggest a new genre]
CONFIDENCE: [High/Medium/Low]

Example outputs:
For "The.Matrix.1999.1080p.BluRay.x264":
TITLE: The Matrix
YEAR: 1999
SELECTED_GENRE: SciFi
CONFIDENCE: High

For "Some.Unknown.Movie.2024.WEBRip":
TITLE: Some Unknown Movie
YEAR: 2024
SELECTED_GENRE: Documentary
CONFIDENCE: Low

For "The.Godfather.1972.BluRay":
TITLE: The Godfather
YEAR: 1972
SELECTED_GENRE: Drama
CONFIDENCE: High

IMPORTANT: For SELECTED_GENRE, prefer using these existing genres when they fit well: {genres_list}
If none of these genres are a good match, you may suggest a new genre. When suggesting a new genre, be specific and consistent.
"""},
            {"role": "user", "content": f"""Movie filename: "{title}"

Please clean up this movie title and determine its genre from the available genres."""}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=250
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response: {response_text}")
            
            # Parse response
            clean_title = None
            year = None
            genre = None
            confidence = "Low"
            message = None
            
            for line in response_text.split('\n'):
                if line.startswith('TITLE:'):
                    clean_title = line.replace('TITLE:', '').strip()
                elif line.startswith('YEAR:'):
                    year_str = line.replace('YEAR:', '').strip()
                    year = year_str if year_str != 'N/A' else None
                elif line.startswith('SELECTED_GENRE:'):
                    genre = line.replace('SELECTED_GENRE:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    confidence = line.replace('CONFIDENCE:', '').strip()
            
            # If OpenAI couldn't determine genre but gave us a clean title, try TMDB
            if (not genre or genre.upper() == 'N/A') and self.tmdb_suggester and clean_title:
                logger.debug(f"Trying TMDB with cleaned title: {clean_title}")
                tmdb_suggestion = self.tmdb_suggester.suggest_genre(clean_title, valid_genres)
                if tmdb_suggestion.genre:
                    # Add the clean title info to TMDB's message
                    title_info = f"'{clean_title}" + (f" ({year})" if year else "") + "'"
                    tmdb_suggestion.message = f"Using TMDB data for {title_info}: " + (tmdb_suggestion.message or "")
                    return tmdb_suggestion
            
            if not genre or genre.upper() == 'N/A':
                title_info = f"'{clean_title}" + (f" ({year})" if year else "") + "'"
                return GenreSuggestion(
                    genre=None,
                    confidence=confidence,
                    status="undetermined",
                    message=message or f"Unable to determine genre for {title_info}"
                )
                
            # Check if the suggested genre matches any of our valid genres (case-insensitive)
            for valid_genre in valid_genres:
                if valid_genre.lower() == genre.lower():
                    return GenreSuggestion(
                        genre=valid_genre,  # Use our casing
                        confidence=confidence,
                        status="success",
                        message=message
                    )
                    
            # If no match, return the suggested genre as a new genre
            return GenreSuggestion(
                genre=genre,
                confidence=confidence,
                status="success",
                message=message
            )
            
        except Exception as e:
            logger.error("Error in OpenAI API call", exc_info=True)
            return GenreSuggestion(
                genre=None,
                confidence="Low",
                status="error",
                message=str(e)
            )
