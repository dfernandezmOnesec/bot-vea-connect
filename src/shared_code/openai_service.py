"""
OpenAI service module for chat completions and embeddings.

This module provides functions for interacting with Azure OpenAI services
for both chat completions and text embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
import openai
from openai import AzureOpenAI
from src.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service class for OpenAI operations."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        try:
            # Initialize Azure OpenAI client for chat
            self.chat_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_chat_api_version
            )
            
            # Initialize Azure OpenAI client for embeddings
            self.embeddings_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_embeddings_endpoint,
                api_key=settings.azure_openai_embeddings_api_key,
                api_version=settings.azure_openai_embeddings_api_version
            )
            
            self.chat_deployment = settings.azure_openai_chat_deployment
            self.embeddings_deployment = settings.openai_embeddings_engine_doc
            
            logger.info("OpenAI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise

    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a chat completion response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            str: Generated response text
            
        Raises:
            Exception: If chat completion fails
        """
        try:
            response = self.chat_client.chat.completions.create(
                model=self.chat_deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"Chat completion generated successfully. Tokens used: {response.usage.total_tokens}")
            return response_text
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for a given text.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            response = self.embeddings_client.embeddings.create(
                model=self.embeddings_deployment,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Embeddings generated successfully for text of length: {len(text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            Exception: If batch embedding generation fails
        """
        try:
            response = self.embeddings_client.embeddings.create(
                model=self.embeddings_deployment,
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Batch embeddings generated successfully for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    def analyze_document_content(self, content: str, analysis_type: str = "summary") -> str:
        """
        Analyze document content using chat completion.
        
        Args:
            content: Document content to analyze
            analysis_type: Type of analysis ("summary", "extract_key_points", "classify")
            
        Returns:
            str: Analysis result
            
        Raises:
            Exception: If analysis fails
        """
        try:
            system_prompt = self._get_analysis_prompt(analysis_type)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze the following content:\n\n{content}"}
            ]
            
            result = self.generate_chat_completion(messages, max_tokens=500, temperature=0.3)
            logger.info(f"Document analysis completed successfully. Type: {analysis_type}")
            return result
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise

    def _get_analysis_prompt(self, analysis_type: str) -> str:
        """
        Get the appropriate system prompt for analysis type.
        
        Args:
            analysis_type: Type of analysis requested
            
        Returns:
            str: System prompt for the analysis
        """
        prompts = {
            "summary": "You are a helpful assistant that creates concise summaries of documents. Focus on the main points and key information.",
            "extract_key_points": "You are a helpful assistant that extracts key points and important information from documents. Present them in a clear, bullet-point format.",
            "classify": "You are a helpful assistant that classifies documents by type, topic, and relevance. Provide a clear classification with reasoning."
        }
        
        return prompts.get(analysis_type, prompts["summary"])

    def validate_text_length(self, text: str, max_tokens: int = 8000) -> bool:
        """
        Validate if text length is within token limits.
        
        Args:
            text: Text to validate
            max_tokens: Maximum allowed tokens
            
        Returns:
            bool: True if text is within limits
        """
        try:
            # Rough estimation: 1 token ≈ 4 characters for English text
            estimated_tokens = len(text) // 4
            is_valid = estimated_tokens <= max_tokens
            
            if not is_valid:
                logger.warning(f"Text length exceeds token limit. Estimated: {estimated_tokens}, Max: {max_tokens}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating text length: {e}")
            return False

# Global instance for easy access
openai_service = OpenAIService() 