"""
OpenAI API facade for enhanced abstraction.
Provides a clean interface for LLM operations with configuration from environment variables.
"""

import os
import logging
from typing import TypeVar, Type, Optional
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    """
    Facade for OpenAI API interactions.
    Reads configuration from environment variables for flexibility.
    """
    
    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._model: Optional[str] = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable must be set")
            self._client = OpenAI(api_key=api_key)
        return self._client
    
    @property
    def model(self) -> str:
        """Get the model from environment variable or use default."""
        if self._model is None:
            self._model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
        return self._model
    
    def parse_structured(
        self, 
        system_prompt: str, 
        user_content: str, 
        response_format: Type[T]
    ) -> T:
        """
        Parse structured data from text using OpenAI's structured outputs.
        
        Args:
            system_prompt: The system prompt defining extraction rules
            user_content: The user input to parse
            response_format: Pydantic model class defining the output structure
            
        Returns:
            Parsed Pydantic model instance
            
        Raises:
            ValueError: If parsing fails or model refuses
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=response_format,
            )
            
            parsed = response.choices[0].message.parsed
            
            if parsed is None:
                raise ValueError("Model returned empty response")
                
            return parsed
            
        except Exception as e:
            error_msg = str(e)
            if "Refusal" in error_msg:
                raise ValueError("The model refused to parse this input")
            logger.error(f"OpenAI parse error: {error_msg}")
            raise
    
    def generate_text(
        self,
        system_prompt: str,
        user_content: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text response from OpenAI.
        
        Args:
            system_prompt: System instructions
            user_content: User input
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature,
        }
        
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
            
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""


# Singleton instance for application-wide use
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get or create the singleton OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client


def parse_structured(
    system_prompt: str,
    user_content: str,
    response_format: Type[T]
) -> T:
    """Convenience function for structured parsing using singleton client."""
    return get_openai_client().parse_structured(system_prompt, user_content, response_format)


def generate_text(
    system_prompt: str,
    user_content: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """Convenience function for text generation using singleton client."""
    return get_openai_client().generate_text(system_prompt, user_content, temperature, max_tokens)
