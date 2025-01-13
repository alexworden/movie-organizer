import re
import logging
from typing import List, Optional
from huggingface_hub import InferenceClient
from .base_suggester import GenreSuggesterInterface, GenreSuggestion

logger = logging.getLogger(__name__)

class LLMGenreSuggester(GenreSuggesterInterface):
    """Genre suggester that uses Hugging Face LLM"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.client = None
        
    def initialize(self) -> None:
        """Initialize the Hugging Face client"""
        if not self.api_token:
            raise ValueError("No Hugging Face API token provided")
        self.client = InferenceClient(
            token=self.api_token,
            timeout=90  # 90 second timeout
        )
        
    def cleanup(self) -> None:
        """Clean up resources"""
        self.client = None
        
    def suggest_genre(self, title: str, valid_genres: List[str]) -> GenreSuggestion:
        """Get genre suggestion using Hugging Face LLM"""
        if not self.client:
            raise ValueError("Client not initialized. Call initialize() first")
            
        try:
            # Create the prompt
            genres_list = ', '.join(valid_genres)
            prompt = f"""For the movie "{title}", identify its primary genre from this list: {genres_list}. 
            If you are not confident about the movie's genre, or if none of the listed genres fit well, suggest a new appropriate genre.
            If you cannot determine the genre at all, respond with N/A.

Please respond using EXACTLY this format, with a SINGLE genre:
SELECTED_GENRE: [one genre from the list OR a new suggestion OR N/A]
CONFIDENCE: [High/Medium/Low]

Example responses:
For a clear action movie:
SELECTED_GENRE: Action
CONFIDENCE: High

For an unclear or unknown movie:
SELECTED_GENRE: N/A
CONFIDENCE: Low

For a movie that needs a new genre:
SELECTED_GENRE: Musical
CONFIDENCE: High
"""
            logger.info("Making API call to Hugging Face...")
            
            response = self.client.text_generation(
                prompt,
                model="mistralai/Mistral-7B-Instruct-v0.2",
                max_new_tokens=200,
                temperature=0.1,
                do_sample=False,
                return_full_text=False
            )
            
            if not response:
                return GenreSuggestion(
                    genre=None,
                    confidence="Low",
                    status="error",
                    message="Empty response from API"
                )
                
            # Extract genre and confidence
            genre_match = re.search(r'SELECTED_GENRE:\s*([^\n]+)', response)
            confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', response)
            
            if not genre_match or not confidence_match:
                return GenreSuggestion(
                    genre=None,
                    confidence="Low",
                    status="error",
                    message="Could not parse API response"
                )
                
            suggested_genre = genre_match.group(1).strip()
            confidence = confidence_match.group(1).strip()
            
            if suggested_genre.upper() in ['N/A', 'NONE', 'UNKNOWN']:
                return GenreSuggestion(
                    genre=None,
                    confidence=confidence,
                    status="undetermined",
                    message=f"Unable to determine genre for '{title}'"
                )
                
            return GenreSuggestion(
                genre=suggested_genre,
                confidence=confidence,
                status="success"
            )
            
        except Exception as e:
            logger.error("Error in LLM API call", exc_info=True)
            return GenreSuggestion(
                genre=None,
                confidence="Low",
                status="error",
                message=str(e)
            )
