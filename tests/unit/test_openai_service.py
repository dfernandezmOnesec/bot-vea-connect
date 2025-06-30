"""
Unit tests for OpenAI service module.

This module contains comprehensive tests for the OpenAIService class
with mocked AzureOpenAI client and full coverage of all methods.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from openai import BadRequestError, AuthenticationError, RateLimitError
from src.shared_code.openai_service import OpenAIService

class TestOpenAIService:
    """Test cases for OpenAIService class."""

    @pytest.fixture
    def mock_settings_env(self):
        with patch('src.shared_code.openai_service.settings') as mock_settings:
            mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
            mock_settings.azure_openai_api_key = "test-key"
            mock_settings.azure_openai_chat_api_version = "2024-02-15-preview"
            mock_settings.azure_openai_embeddings_endpoint = "https://test.openai.azure.com/"
            mock_settings.azure_openai_embeddings_api_key = "test-key"
            mock_settings.azure_openai_embeddings_api_version = "2024-02-15-preview"
            mock_settings.azure_openai_chat_deployment = "gpt-4"
            mock_settings.openai_embeddings_engine_doc = "embedding-model"
            yield mock_settings

    @pytest.fixture
    def mock_azure_openai(self):
        with patch('src.shared_code.openai_service.AzureOpenAI') as mock_client:
            yield mock_client

    @pytest.fixture
    def openai_service(self, mock_settings_env, mock_azure_openai):
        with patch('src.shared_code.openai_service.OpenAIService._validate_connections'):
            service = OpenAIService()
            service.chat_client = Mock()
            service.embeddings_client = Mock()
            return service

    def test_generate_chat_completion_success(self, openai_service):
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hola, ¿cómo puedo ayudarte?"))]
        mock_response.usage = Mock(total_tokens=10, prompt_tokens=5, completion_tokens=5)
        openai_service.chat_client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "Hola"}]
        result = openai_service.generate_chat_completion(messages)
        assert "Hola" in result

    def test_generate_chat_completion_bad_request(self, openai_service):
        openai_service.chat_client.chat.completions.create.side_effect = BadRequestError("Bad request")
        with pytest.raises(BadRequestError):
            openai_service.generate_chat_completion([{"role": "user", "content": "Hola"}])

    def test_generate_chat_completion_auth_error(self, openai_service):
        openai_service.chat_client.chat.completions.create.side_effect = AuthenticationError("Auth error")
        with pytest.raises(AuthenticationError):
            openai_service.generate_chat_completion([{"role": "user", "content": "Hola"}])

    def test_generate_chat_completion_rate_limit(self, openai_service):
        openai_service.chat_client.chat.completions.create.side_effect = RateLimitError("Rate limit")
        with pytest.raises(RateLimitError):
            openai_service.generate_chat_completion([{"role": "user", "content": "Hola"}])

    def test_generate_embeddings_success(self, openai_service):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        openai_service.embeddings_client.embeddings.create.return_value = mock_response
        result = openai_service.generate_embeddings("test text")
        assert isinstance(result, list)
        assert result == [0.1, 0.2, 0.3]

    def test_generate_embeddings_empty_text(self, openai_service):
        with pytest.raises(ValueError):
            openai_service.generate_embeddings("")

    def test_generate_embeddings_too_long(self, openai_service):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        openai_service.embeddings_client.embeddings.create.return_value = mock_response
        long_text = "a" * 9000
        result = openai_service.generate_embeddings(long_text)
        assert isinstance(result, list)

    def test_generate_batch_embeddings_success(self, openai_service):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2]), Mock(embedding=[0.3, 0.4])]
        openai_service.embeddings_client.embeddings.create.return_value = mock_response
        result = openai_service.generate_batch_embeddings(["text1", "text2"])
        assert isinstance(result, list)
        assert result[0] == [0.1, 0.2]

    def test_generate_batch_embeddings_empty_list(self, openai_service):
        with pytest.raises(ValueError):
            openai_service.generate_batch_embeddings([])

    def test_generate_batch_embeddings_invalid_texts(self, openai_service):
        with pytest.raises(ValueError):
            openai_service.generate_batch_embeddings([""])

    def test_generate_whatsapp_response_success(self, openai_service):
        with patch.object(openai_service, 'generate_chat_completion', return_value="Respuesta pastoral") as mock_chat:
            result = openai_service.generate_whatsapp_response("¿Cuándo es el culto?", context="El culto es el domingo.", user_name="Juan")
            assert "Respuesta pastoral" in result
            mock_chat.assert_called_once()

    def test_analyze_document_content_summary(self, openai_service):
        with patch.object(openai_service, 'generate_chat_completion', return_value="Resumen generado") as mock_chat:
            result = openai_service.analyze_document_content("Contenido de prueba", analysis_type="summary")
            assert "Resumen generado" in result
            mock_chat.assert_called_once()

    def test_analyze_document_content_invalid_type(self, openai_service):
        with pytest.raises(ValueError):
            openai_service.analyze_document_content("Contenido", analysis_type="invalid_type")

    def test_validate_text_length(self, openai_service):
        assert openai_service.validate_text_length("a" * 1000, max_tokens=8000)
        assert not openai_service.validate_text_length("a" * 40000, max_tokens=1000)

    def test_get_chat_history_summary(self, openai_service):
        with patch.object(openai_service, 'generate_chat_completion', return_value="Resumen de chat") as mock_chat:
            messages = [{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "Bienvenido"}]
            result = openai_service.get_chat_history_summary(messages)
            assert "Resumen de chat" in result
            mock_chat.assert_called_once()

    def test_get_chat_history_summary_empty(self, openai_service):
        result = openai_service.get_chat_history_summary([])
        assert result == "" 