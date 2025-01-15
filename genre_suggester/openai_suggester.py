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
            {"role": "system", "content": f"""You are a movie expert who can clean up movie filenames and determine genres.
Given a movie filename, first extract the actual title and year, then determine its genre.

Your primary goal is to categorize movies using these existing genres whenever possible: {genres_list}
Only suggest a new genre if absolutely none of the existing genres could work.

Format your response EXACTLY like this:
TITLE: [cleaned movie title]
YEAR: [year if found, or N/A if not found]
SELECTED_GENRE: [Use one of the provided genres if suitable, otherwise suggest a new genre]
CONFIDENCE: [High/Medium/Low]

Here are examples of using broader existing genres:

Input: "Spider.Man.2002.1080p.BluRay.x264"
TITLE: Spider-Man
YEAR: 2002
SELECTED_GENRE: Action
CONFIDENCE: High
Explanation: While this could be "Superhero", we use the broader "Action" genre that exists

Input: "Lord.of.the.Rings.2001.BluRay"
TITLE: The Lord of the Rings
YEAR: 2001
SELECTED_GENRE: Fantasy
CONFIDENCE: High
Explanation: While this could be "Epic Fantasy", we use the broader "Fantasy" genre that exists

Input: "The.Conjuring.2013.WEBRip"
TITLE: The Conjuring
YEAR: 2013
SELECTED_GENRE: Horror
CONFIDENCE: High
Explanation: While this could be "Supernatural Horror", we use the broader "Horror" genre that exists

Input: "Some.Unknown.Movie.2024.WEBRip"
TITLE: Some Unknown Movie
YEAR: 2024
SELECTED_GENRE: Drama
CONFIDENCE: Low
Explanation: When uncertain, use a broader existing genre rather than creating a new one

IMPORTANT RULES:
1. ALWAYS prefer an existing genre, even if it's broader than the specific sub-genre you have in mind
2. A movie fitting multiple genres is normal - pick the most relevant existing genre
3. It's better to use a broader existing genre than to create a new specific one
4. Only suggest a new genre if the movie absolutely cannot fit into any existing genre"""},
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
