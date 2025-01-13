from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class GenreSuggestion:
    """Data class to hold genre suggestion results"""
    genre: Optional[str]
    confidence: str  # 'High', 'Medium', 'Low'
    status: str  # 'success', 'undetermined', 'error'
    message: Optional[str] = None

class GenreSuggesterInterface(ABC):
    """Abstract base class for genre suggestion implementations"""
    
    @abstractmethod
    def suggest_genre(self, title: str, valid_genres: List[str]) -> GenreSuggestion:
        """
        Suggest a genre for the given movie title.
        
        Args:
            title: The movie title to get a genre for
            valid_genres: List of valid genres to choose from
            
        Returns:
            GenreSuggestion object containing the suggested genre and metadata
            
        Raises:
            ValueError: If there's an error getting the genre
            TimeoutError: If the request times out
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize any necessary resources or connections"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any resources or connections"""
        pass
