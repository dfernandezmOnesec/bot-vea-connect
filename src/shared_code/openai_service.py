"""
OpenAI service module for chat completions and embeddings.

This module provides functions for interacting with Azure OpenAI services
for both chat completions and text embeddings with production-grade features
and optimized prompts for Christian community support.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import openai
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from src.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service class for OpenAI operations with production-grade features."""
    
    def __init__(self):
        """Initialize the OpenAI service with connection validation."""
        try:
            # Configurar cliente OpenAI para Azure
            openai.api_type = "azure"
            openai.api_base = settings.azure_openai_endpoint
            openai.api_key = settings.azure_openai_api_key
            openai.api_version = settings.azure_openai_chat_api_version

            self.chat_deployment = settings.azure_openai_chat_deployment
            self.embeddings_deployment = settings.openai_embeddings_engine_doc

            # No se necesita cliente especial, se usa openai.ChatCompletion y openai.Embedding
            self.chat_client = openai
            self.embeddings_client = openai

            # Validate connections
            self._validate_connections()
            
            logger.info("OpenAI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise

    def _validate_connections(self) -> None:
        """
        Validate connections to OpenAI services.
        
        Raises:
            Exception: If connection validation fails
        """
        try:
            # Test chat completion with a simple request
            test_response = self.chat_client.chat.completions.create(
                model=self.chat_deployment,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.debug("OpenAI chat service connection validated successfully")
            
        except Exception as e:
            logger.error(f"OpenAI service connection validation failed: {e}")
            raise

    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a chat completion response with enhanced error handling.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            system_prompt: Optional system prompt to prepend to messages
            
        Returns:
            str: Generated response text
            
        Raises:
            openai.BadRequestError: If request is malformed
            openai.AuthenticationError: If authentication fails
            openai.RateLimitError: If rate limit is exceeded
            Exception: For other unexpected errors
        """
        try:
            # Prepend system prompt if provided
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = self.chat_client.chat.completions.create(
                model=self.chat_deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content
            usage = response.usage
            
            logger.info(
                f"Chat completion generated successfully. "
                f"Tokens used: {usage.total_tokens} "
                f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})"
            )
            return response_text
            
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request error: {e}")
            raise
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for a given text with validation.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            ValueError: If text is empty or too long
            openai.BadRequestError: If request is malformed
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if len(text) > 8000:  # OpenAI limit
                logger.warning(f"Text truncated from {len(text)} to 8000 characters")
                text = text[:8000]
            
            response = self.embeddings_client.embeddings.create(
                model=self.embeddings_deployment,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Embeddings generated successfully for text of length: {len(text)}")
            return embedding
            
        except ValueError as e:
            logger.error(f"Invalid input for embedding generation: {e}")
            raise
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request error for embeddings: {e}")
            raise
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Alias for generate_embeddings for backward compatibility.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List[float]: Embedding vector
        """
        return self.generate_embeddings(text)

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch with validation.
        
        Args:
            texts: List of input texts
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            ValueError: If texts list is empty or contains invalid items
            openai.BadRequestError: If request is malformed
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not texts:
                raise ValueError("Texts list cannot be empty")
            
            # Filter and truncate texts
            valid_texts = []
            for text in texts:
                if text and text.strip():
                    if len(text) > 8000:
                        logger.warning(f"Text truncated from {len(text)} to 8000 characters")
                        text = text[:8000]
                    valid_texts.append(text)
            
            if not valid_texts:
                raise ValueError("No valid texts found in input list")
            
            response = self.embeddings_client.embeddings.create(
                model=self.embeddings_deployment,
                input=valid_texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Batch embeddings generated successfully for {len(valid_texts)} texts")
            return embeddings
            
        except ValueError as e:
            logger.error(f"Invalid input for batch embedding generation: {e}")
            raise
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request error for batch embeddings: {e}")
            raise
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    def generate_whatsapp_response(
        self, 
        user_message: str, 
        context: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate a WhatsApp response optimized for Christian community support.
        
        Args:
            user_message: The user's message
            context: Optional context from semantic search
            user_name: Optional user's name for personalization
            
        Returns:
            str: Generated response in Spanish
            
        Raises:
            Exception: If response generation fails
        """
        try:
            # Build system prompt for Christian community support
            system_prompt = self._get_whatsapp_system_prompt(user_name)
            
            # Build user message with context
            if context:
                full_message = f"Contexto disponible: {context}\n\nMensaje del usuario: {user_message}"
            else:
                full_message = user_message
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_message}
            ]
            
            response = self.generate_chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            logger.info(f"WhatsApp response generated successfully for user: {user_name or 'unknown'}")
            return response
            
        except Exception as e:
            logger.error(f"WhatsApp response generation failed: {e}")
            raise

    def _get_whatsapp_system_prompt(self, user_name: Optional[str] = None) -> str:
        """
        Get the system prompt for WhatsApp responses.
        
        Args:
            user_name: Optional user's name for personalization
            
        Returns:
            str: System prompt for WhatsApp responses
        """
        base_prompt = """Eres un asistente pastoral amigable y compasivo para la comunidad cristiana VEA Connect. 
Tu propósito es brindar apoyo espiritual, información sobre ministerios, eventos, donaciones y contactos del directorio.

IMPORTANTE:
- SIEMPRE responde en español natural y pastoral
- Sé cálido, empático y bíblicamente fundamentado
- Si no tienes información específica, ofrece ayuda general o redirige a un líder
- Mantén un tono pastoral y edificante
- Incluye versículos bíblicos apropiados cuando sea relevante
- Ofrece oración cuando sea apropiado

Áreas de conocimiento:
- Ministerios y grupos de la iglesia
- Eventos y actividades
- Información sobre donaciones
- Contactos del directorio
- Apoyo espiritual general
- Oración y consejería básica

Formato de respuesta:
- Saludo personalizado
- Respuesta clara y útil
- Oferta de ayuda adicional si es apropiado
- Cierre cálido y pastoral"""

        if user_name:
            base_prompt += f"\n\nEl usuario se llama {user_name}. Usa su nombre en tu respuesta cuando sea apropiado."
        
        return base_prompt

    def analyze_document_content(self, content: str, analysis_type: str = "summary") -> str:
        """
        Analyze document content using chat completion with enhanced prompts.
        
        Args:
            content: Document content to analyze
            analysis_type: Type of analysis ("summary", "extract_key_points", "classify", "pastoral_relevance")
            
        Returns:
            str: Analysis result
            
        Raises:
            ValueError: If analysis_type is not supported
            Exception: If analysis fails
        """
        try:
            system_prompt = self._get_analysis_prompt(analysis_type)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Por favor analiza el siguiente contenido:\n\n{content}"}
            ]
            
            result = self.generate_chat_completion(messages, max_tokens=500, temperature=0.3)
            logger.info(f"Document analysis completed successfully. Type: {analysis_type}")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid analysis type: {analysis_type}")
            raise
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
            
        Raises:
            ValueError: If analysis_type is not supported
        """
        prompts = {
            "summary": """Eres un asistente que crea resúmenes concisos de documentos. 
Enfócate en los puntos principales y la información clave. 
Responde en español.""",
            
            "extract_key_points": """Eres un asistente que extrae puntos clave e información importante de documentos. 
Preséntalos en un formato claro con viñetas. 
Responde en español.""",
            
            "classify": """Eres un asistente que clasifica documentos por tipo, tema y relevancia. 
Proporciona una clasificación clara con razonamiento. 
Responde en español.""",
            
            "pastoral_relevance": """Eres un asistente pastoral que analiza la relevancia de documentos 
para una comunidad cristiana. Identifica temas espirituales, ministeriales o de servicio. 
Responde en español."""
        }
        
        if analysis_type not in prompts:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
        
        return prompts[analysis_type]

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
            # Rough estimation: 1 token ≈ 4 characters for English text, 3 for Spanish
            estimated_tokens = len(text) // 3.5  # Conservative estimate for mixed content
            is_valid = estimated_tokens <= max_tokens
            
            if not is_valid:
                logger.warning(f"Text length exceeds token limit. Estimated: {estimated_tokens}, Max: {max_tokens}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Text length validation failed: {e}")
            return False

    def get_chat_history_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a summary of chat history for context.
        
        Args:
            messages: List of previous messages
            
        Returns:
            str: Summary of chat history
            
        Raises:
            Exception: If summary generation fails
        """
        try:
            if not messages or len(messages) < 2:
                return ""
            
            # Create a summary of the conversation
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in messages[-10:]  # Last 10 messages
            ])
            
            system_prompt = """Eres un asistente que crea resúmenes concisos de conversaciones. 
Enfócate en los temas principales y el contexto importante. 
Responde en español."""
            
            messages_for_summary = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume esta conversación:\n\n{conversation_text}"}
            ]
            
            summary = self.generate_chat_completion(
                messages=messages_for_summary,
                max_tokens=200,
                temperature=0.3
            )
            
            logger.info("Chat history summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Chat history summary generation failed: {e}")
            raise

# Global instance for easy access
try:
    openai_service = OpenAIService()
except Exception as e:
    # Fallback for testing environments without proper configuration
    openai_service = None 