"""
Unit tests for WhatsAppBot Azure Function.

Tests webhook verification, message processing, and RAG functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import azure.functions as func
from src.whatsapp_bot.whatsapp_bot import (
    main,
    handle_webhook_verification,
    handle_message_processing,
    generate_rag_response,
    build_context_prompt,
    generate_contextual_response,
    generate_general_response
)

class TestWhatsAppBot:
    """Test cases for WhatsAppBot function."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock HTTP request."""
        return Mock(spec=func.HttpRequest)
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with verify token."""
        with patch('src.whatsapp_bot.whatsapp_bot.settings') as mock:
            mock.verify_token = "test_verify_token_123"
            yield mock
    
    @pytest.fixture
    def mock_services(self):
        """Mock all external services."""
        with patch('src.whatsapp_bot.whatsapp_bot.openai_service') as mock_openai, \
             patch('src.whatsapp_bot.whatsapp_bot.redis_service') as mock_redis, \
             patch('src.whatsapp_bot.whatsapp_bot.whatsapp_service') as mock_whatsapp:
            
            # Mock OpenAI service methods directly
            mock_openai.generate_embeddings.return_value = [0.1, 0.2, 0.3]
            mock_openai.generate_chat_completion.return_value = "Respuesta generada"
            
            # Mock Redis service methods directly
            mock_redis.semantic_search.return_value = []
            
            # Mock WhatsApp service methods directly
            mock_whatsapp.process_webhook_event.return_value = {
                "event_type": "message",
                "message_type": "text",
                "message_content": "Hola",
                "sender_id": "123456789",
                "message_id": "msg_123"
            }
            mock_whatsapp.send_text_message.return_value = True
            mock_whatsapp.mark_message_as_read.return_value = True
            
            yield {
                'openai': mock_openai,
                'redis': mock_redis,
                'whatsapp': mock_whatsapp
            }

    def test_main_get_request_webhook_verification(self, mock_request, mock_settings):
        """Test successful webhook verification with GET request."""
        # Arrange
        mock_request.method = "GET"
        mock_request.params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token_123",
            "hub.challenge": "challenge_123"
        }
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "challenge_123"

    def test_main_get_request_invalid_token(self, mock_request, mock_settings):
        """Test webhook verification with invalid token."""
        # Arrange
        mock_request.method = "GET"
        mock_request.params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "challenge_123"
        }
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 403
        assert "Verification token mismatch" in response.get_body().decode()

    def test_main_get_request_missing_parameters(self, mock_request, mock_settings):
        """Test webhook verification with missing parameters."""
        # Arrange
        mock_request.method = "GET"
        mock_request.params = {
            "hub.mode": "subscribe"
            # Missing verify_token and challenge
        }
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 400
        assert "Missing parameters" in response.get_body().decode()

    def test_main_post_request_successful_rag(self, mock_request, mock_services):
        """Test successful POST request with RAG processing."""
        # Arrange
        mock_request.method = "POST"
        mock_request.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "1234567890"},
                        "contacts": [{"wa_id": "123456789"}],
                        "messages": [{
                            "from": "123456789",
                            "id": "msg_123",
                            "timestamp": "1234567890",
                            "text": {"body": "¿Cuál es el horario de atención?"},
                            "type": "text"
                        }]
                    }
                }]
            }]
        }
        
        # Mock Redis to return relevant context
        mock_services['redis'].semantic_search.return_value = [
            {
                "text": "El horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM",
                "score": 0.85,
                "metadata": {"filename": "horarios.pdf"}
            }
        ]
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "OK"
        
        # Verify services were called
        mock_services['openai'].generate_embeddings.assert_called_once()
        mock_services['redis'].semantic_search.assert_called_once()
        mock_services['whatsapp'].send_text_message.assert_called_once()

    def test_main_post_request_no_context_fallback(self, mock_request, mock_services):
        """Test POST request when no relevant context is found."""
        # Arrange
        mock_request.method = "POST"
        mock_request.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "1234567890"},
                        "contacts": [{"wa_id": "123456789"}],
                        "messages": [{
                            "from": "123456789",
                            "id": "msg_123",
                            "timestamp": "1234567890",
                            "text": {"body": "Hola, ¿cómo estás?"},
                            "type": "text"
                        }]
                    }
                }]
            }]
        }
        
        # Mock Redis to return no relevant context
        mock_services['redis'].semantic_search.return_value = [
            {
                "text": "Información no relevante",
                "score": 0.3,
                "metadata": {"filename": "otro.pdf"}
            }
        ]
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "OK"
        
        # Verify general response was generated
        mock_services['openai'].generate_chat_completion.assert_called()

    def test_main_post_request_invalid_json(self, mock_request):
        """Test POST request with invalid JSON payload."""
        # Arrange
        mock_request.method = "POST"
        mock_request.get_json.side_effect = Exception("Invalid JSON")
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 400
        assert "Invalid JSON" in response.get_body().decode()

    def test_main_unsupported_method(self, mock_request):
        """Test request with unsupported HTTP method."""
        # Arrange
        mock_request.method = "PUT"
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 405
        assert "Method not allowed" in response.get_body().decode()

    def test_handle_webhook_verification_success(self, mock_request, mock_settings):
        """Test successful webhook verification."""
        # Arrange
        mock_request.params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token_123",
            "hub.challenge": "challenge_123"
        }
        
        # Act
        response = handle_webhook_verification(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "challenge_123"

    def test_handle_webhook_verification_failure(self, mock_request, mock_settings):
        """Test webhook verification failure."""
        # Arrange
        mock_request.params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "challenge_123"
        }
        
        # Act
        response = handle_webhook_verification(mock_request)
        
        # Assert
        assert response.status_code == 403

    def test_handle_message_processing_non_message_event(self, mock_request, mock_services):
        """Test processing of non-message events."""
        # Arrange
        mock_request.get_json.return_value = {"test": "data"}
        mock_services['whatsapp'].process_webhook_event.return_value = {
            "event_type": "status_update",
            "message_type": None,
            "message_content": None,
            "sender_id": None,
            "message_id": None
        }
        
        # Act
        response = handle_message_processing(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "OK"

    def test_handle_message_processing_non_text_message(self, mock_request, mock_services):
        """Test processing of non-text messages."""
        # Arrange
        mock_request.get_json.return_value = {"test": "data"}
        mock_services['whatsapp'].process_webhook_event.return_value = {
            "event_type": "message",
            "message_type": "image",
            "message_content": None,
            "sender_id": "123456789",
            "message_id": "msg_123"
        }
        
        # Act
        response = handle_message_processing(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "OK"

    def test_handle_message_processing_empty_content(self, mock_request, mock_services):
        """Test processing of message with empty content."""
        # Arrange
        mock_request.get_json.return_value = {"test": "data"}
        mock_services['whatsapp'].process_webhook_event.return_value = {
            "event_type": "message",
            "message_type": "text",
            "message_content": "",
            "sender_id": "123456789",
            "message_id": "msg_123"
        }
        
        # Act
        response = handle_message_processing(mock_request)
        
        # Assert
        assert response.status_code == 200
        assert response.get_body().decode() == "OK"

    def test_generate_rag_response_with_context(self, mock_services):
        """Test RAG response generation with relevant context."""
        # Arrange
        user_question = "¿Cuál es el horario de atención?"
        mock_services['redis'].semantic_search.return_value = [
            {
                "text": "El horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM",
                "score": 0.85,
                "metadata": {"filename": "horarios.pdf"}
            }
        ]
        
        # Act
        response = generate_rag_response(user_question)
        
        # Assert
        # Verify that the methods were called correctly
        mock_services['openai'].generate_embeddings.assert_called_once_with(user_question)
        mock_services['redis'].semantic_search.assert_called_once()
        mock_services['openai'].generate_chat_completion.assert_called_once()
        # Verify response is not None
        assert response is not None

    def test_generate_rag_response_no_context(self, mock_services):
        """Test RAG response generation without relevant context."""
        # Arrange
        user_question = "Hola, ¿cómo estás?"
        mock_services['redis'].semantic_search.return_value = [
            {
                "text": "Información no relevante",
                "score": 0.3,
                "metadata": {"filename": "otro.pdf"}
            }
        ]
        
        # Act
        response = generate_rag_response(user_question)
        
        # Assert
        # Should call general response generation
        mock_services['openai'].generate_chat_completion.assert_called()
        # Verify response is not None
        assert response is not None

    def test_generate_rag_response_exception(self, mock_services):
        """Test RAG response generation with exception."""
        # Arrange
        user_question = "Test question"
        mock_services['openai'].generate_embeddings.side_effect = Exception("OpenAI error")
        
        # Act
        response = generate_rag_response(user_question)
        
        # Assert
        assert "Lo siento, estoy teniendo problemas" in response

    def test_build_context_prompt_with_relevant_results(self):
        """Test building context prompt with relevant search results."""
        # Arrange
        search_results = [
            {
                "text": "Información importante sobre horarios de atención",
                "score": 0.85,
                "metadata": {"filename": "horarios.pdf"}
            },
            {
                "text": "Información adicional sobre servicios",
                "score": 0.75,
                "metadata": {"filename": "servicios.pdf"}
            }
        ]
        user_question = "¿Cuál es el horario de atención?"
        
        # Act
        prompt = build_context_prompt(search_results, user_question)
        
        # Assert
        assert "VEA Connect AI Assistant" in prompt
        assert "Contexto:" in prompt
        assert "Pregunta del Usuario:" in prompt
        assert "Información importante sobre horarios" in prompt

    def test_build_context_prompt_no_relevant_results(self):
        """Test building context prompt with no relevant results."""
        # Arrange
        search_results = [
            {
                "text": "Información no relevante",
                "score": 0.3,
                "metadata": {"filename": "otro.pdf"}
            }
        ]
        user_question = "Test question"
        
        # Act
        prompt = build_context_prompt(search_results, user_question)
        
        # Assert
        assert prompt == ""

    def test_generate_contextual_response_success(self, mock_services):
        """Test successful contextual response generation."""
        # Arrange
        context_prompt = "Contexto relevante"
        user_question = "¿Cuál es el horario?"
        
        # Act
        response = generate_contextual_response(context_prompt, user_question)
        
        # Assert
        mock_services['openai'].generate_chat_completion.assert_called_once()
        # Verify response is not None
        assert response is not None

    def test_generate_contextual_response_exception(self, mock_services):
        """Test contextual response generation with exception."""
        # Arrange
        context_prompt = "Contexto relevante"
        user_question = "¿Cuál es el horario?"
        mock_services['openai'].generate_chat_completion.side_effect = Exception("OpenAI error")
        
        # Act
        response = generate_contextual_response(context_prompt, user_question)
        
        # Assert
        assert "Lo siento, no pude generar una respuesta basada en el contexto" in response

    def test_generate_general_response_success(self, mock_services):
        """Test successful general response generation."""
        # Arrange
        user_question = "Hola, ¿cómo estás?"
        
        # Act
        response = generate_general_response(user_question)
        
        # Assert
        mock_services['openai'].generate_chat_completion.assert_called_once()
        # Verify response is not None
        assert response is not None

    def test_generate_general_response_exception(self, mock_services):
        """Test general response generation with exception."""
        # Arrange
        user_question = "Hola, ¿cómo estás?"
        mock_services['openai'].generate_chat_completion.side_effect = Exception("OpenAI error")
        
        # Act
        response = generate_general_response(user_question)
        
        # Assert
        assert "Hola! Soy el asistente de VEA Connect" in response 