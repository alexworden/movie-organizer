import logging
from typing import List, Optional
import requests
from .base_suggester import GenreSuggesterInterface, GenreSuggestion

logger = logging.getLogger(__name__)

class TMDBGenreSuggester(GenreSuggesterInterface):
    """Genre suggester that uses TMDB API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        
    def initialize(self) -> None:
        """Verify API key works"""
        if not self.api_key:
            raise ValueError("No TMDB API key provided")
        
    def cleanup(self) -> None:
        """Nothing to clean up"""
        pass
        
    def suggest_genre(self, title: str, valid_genres: List[str]) -> GenreSuggestion:
        """Get genre suggestion using TMDB API"""
        try:
            # Search for the movie
            response = requests.get(
                f"{self.base_url}/search/movie",
                params={
                    "api_key": self.api_key,
                    "query": title,
                    "include_adult": False
                }
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            if not results:
                return GenreSuggestion(
                    genre=None,
                    confidence="Low",
                    status="undetermined",
                    message=f"No movies found matching '{title}'"
                )
                
            # Get the first result's details
            movie = results[0]
            
            # Get full movie details which includes genres as strings
            movie_response = requests.get(
                f"{self.base_url}/movie/{movie['id']}",
                params={"api_key": self.api_key}
            )
            movie_response.raise_for_status()
            movie_details = movie_response.json()
            
            # Get genres as strings
            movie_genres = [g["name"] for g in movie_details.get("genres", [])]
            
            if not movie_genres:
                return GenreSuggestion(
                    genre=None,
                    confidence="Low",
                    status="undetermined",
                    message=f"No genres found for '{title}'"
                )
                
            # Try to match with our valid genres
            primary_genre = movie_genres[0]  # TMDB lists genres in order of relevance
            confidence = "High" if movie.get("popularity", 0) > 10 else "Medium"
            
            # Try to match with our valid genres (case insensitive)
            for valid_genre in valid_genres:
                if valid_genre.lower() == primary_genre.lower():
                    return GenreSuggestion(
                        genre=valid_genre,  # Use our casing
                        confidence=confidence,
                        status="success",
                        message=f"Found '{movie_details.get('title')}' ({movie_details.get('release_date', '')[:4]})"
                    )
                    
            # If no match, suggest the TMDB genre
            return GenreSuggestion(
                genre=primary_genre,
                confidence=confidence,
                status="success",
                message=f"Found '{movie_details.get('title')}' ({movie_details.get('release_date', '')[:4]})"
            )
            
        except Exception as e:
            logger.error(f"TMDB API error: {e}", exc_info=True)
            return GenreSuggestion(
                genre=None,
                confidence="Low",
                status="error",
                message=str(e)
            )
