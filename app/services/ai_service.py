# app/services/ai_service.py
# Error 429 will show up upon using AI Book Recommendation Service, since I have not paid for tokens to usae OpenAI services using my API key.

# Standard library imports
import os  # Operating system interface
import json  # JSON parsing
from typing import Dict, List  # Type hints

# Third party imports
from openai import OpenAI, OpenAIError  # OpenAI API client

class AIRecommendationService:
    """Service for getting AI-powered book recommendations"""
    
    def __init__(self):
        # Get API key from environment
        self.api_key = os.environ['OPENAI_API_KEY']
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

    def get_recommendations(self, preferences: Dict) -> List[Dict]:
        """Get book recommendations based on user preferences"""
        try:
            # Input validation
            if not preferences.get('genres') and not preferences.get('authors'):
                raise ValueError("At least one genre or author must be provided")

            # Build prompt for AI
            prompt = self._build_prompt(preferences)
            
            # Get AI response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use GPT-3.5 model
                messages=[{
                    "role": "system",  # System message for context
                    "content": "You are a knowledgeable book recommendation assistant. "
                             "Provide recommendations in valid JSON format."
                },
                {
                    "role": "user",  # User prompt with preferences
                    "content": prompt
                }],
                max_tokens=500,  # Limit response length
                temperature=0.7  # Control randomness
            )
            
            # Parse and validate response
            recommendations = self._parse_recommendations(response.choices[0].message.content)
            
            # Ensure valid format
            if not isinstance(recommendations, list):
                raise ValueError("Invalid recommendations format")
                
            return recommendations

        # Error handling
        except OpenAIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")  # API-specific errors
        except json.JSONDecodeError:
            raise Exception("Failed to parse AI response as JSON")  # JSON parsing errors
        except Exception as e:
            raise Exception(f"Error getting recommendations: {str(e)}")  # Generic errors

    def _build_prompt(self, preferences: Dict) -> str:
        """Build AI prompt from user preferences"""
        # Extract preferences
        genres = preferences.get('genres', [])
        authors = preferences.get('authors', [])
        
        # Return formatted prompt
        return f"""Please recommend 5 books based on these preferences:
        Genres: {', '.join(genres)}
        Favorite Authors: {', '.join(authors)}
        
        Return response as a JSON array where each book has:
        - title: string
        - author: string
        - description: string (max 100 words)
        - genre: string
        
        Example format:
        [
            {{"title": "Book Title", "author": "Author Name", "description": "Brief description", "genre": "Genre"}}
        ]"""

    def _parse_recommendations(self, raw_recommendations: str) -> List[Dict]:
        """Parse and validate AI response"""
        try:
            # Parse JSON response
            recommendations = json.loads(raw_recommendations)
            
            # Validate list format
            if not isinstance(recommendations, list):
                raise ValueError("Recommendations must be a list")
                
            # Check required fields
            required_fields = {'title', 'author', 'description', 'genre'}
            for book in recommendations:
                if not all(field in book for field in required_fields):
                    raise ValueError("Each book must have title, author, description and genre")
                    
            return recommendations
            
        except json.JSONDecodeError:
            raise Exception("Failed to parse recommendations as JSON")
        except Exception as e:
            raise Exception(f"Error parsing recommendations: {str(e)}")