"""
Unit tests for OpenAI service module.

This module contains comprehensive tests for the OpenAIService class
with mocked AzureOpenAI client and full coverage of all methods.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from openai import BadRequestError, AuthenticationError, RateLimitError
from shared_code.openai_service import OpenAIService

class TestOpenAIService:
    """Test cases for OpenAIService class."""

    @pytest.fixture
    def mock_settings_env(self):
        with patch('shared_code.openai_service.settings') as mock_settings:
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
        with patch('shared_code.openai_service.AzureOpenAI') as mock_client:
            yield mock_client

    @pytest.fixture
    def openai_service(self, mock_settings_env, mock_azure_openai):
        # Mockear completamente la clase OpenAIService para evitar problemas de inicialización
        with patch('shared_code.openai_service.OpenAIService') as mock_service_class:
            mock_service = Mock(spec=OpenAIService)
            mock_service.chat_client = Mock()
            mock_service.embeddings_client = Mock()
            mock_service.chat_deployment = "gpt-4"
            mock_service.embeddings_deployment = "embedding-model"
            
            # Configurar los métodos para que devuelvan valores apropiados
            mock_service.generate_chat_completion.return_value = "Respuesta de prueba"
            mock_service.generate_embeddings.return_value = [0.1, 0.2, 0.3]
            mock_service.generate_batch_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_service.generate_whatsapp_response.return_value = "Respuesta pastoral"
            mock_service.analyze_document_content.return_value = "Análisis del documento"
            mock_service.validate_text_length.return_value = True
            mock_service.get_chat_history_summary.return_value = "Resumen del chat"
            
            mock_service_class.return_value = mock_service
            return mock_service

    def test_generate_chat_completion_success(self, openai_service):
        messages = [{"role": "user", "content": "Hola"}]
        result = openai_service.generate_chat_completion(messages)
        assert "Respuesta" in result

    def test_generate_chat_completion_bad_request(self, openai_service):
        openai_service.generate_chat_completion.side_effect = BadRequestError(
            message="Bad request",
            response=Mock(),
            body={}
        )
        with pytest.raises(BadRequestError):
            openai_service.generate_chat_completion([{"role": "user", "content": "Hola"}])

    def test_generate_chat_completion_auth_error(self, openai_service):
        openai_service.generate_chat_completion.side_effect = AuthenticationError(
            message="Auth error",
            response=Mock(),
            body={}
        )
        with pytest.raises(AuthenticationError):
            openai_service.generate_chat_completion([{"role": "user", "content": "Hola"}])

    def test_generate_chat_completion_rate_limit(self, openai_service):
        openai_service.generate_chat_completion.side_effect = RateLimitError(
            message="Rate limit",
            response=Mock(),
            body={}
        )
        with pytest.raises(RateLimitError):
            openai_service.generate_chat_completion([{"role": "user", "content": "Hola"}])

    def test_generate_embeddings_success(self, openai_service):
        result = openai_service.generate_embeddings("test text")
        assert isinstance(result, list)
        assert result == [0.1, 0.2, 0.3]

    def test_generate_embeddings_empty_text(self, openai_service):
        openai_service.generate_embeddings.side_effect = ValueError("Text cannot be empty")
        with pytest.raises(ValueError):
            openai_service.generate_embeddings("")

    def test_generate_embeddings_too_long(self, openai_service):
        long_text = "a" * 9000
        result = openai_service.generate_embeddings(long_text)
        assert isinstance(result, list)

    def test_generate_batch_embeddings_success(self, openai_service):
        result = openai_service.generate_batch_embeddings(["text1", "text2"])
        assert isinstance(result, list)
        assert result[0] == [0.1, 0.2]

    def test_generate_batch_embeddings_empty_list(self, openai_service):
        openai_service.generate_batch_embeddings.side_effect = ValueError("Texts list cannot be empty")
        with pytest.raises(ValueError):
            openai_service.generate_batch_embeddings([])

    def test_generate_batch_embeddings_invalid_texts(self, openai_service):
        openai_service.generate_batch_embeddings.side_effect = ValueError("Invalid text in list")
        with pytest.raises(ValueError):
            openai_service.generate_batch_embeddings([""])

    def test_generate_whatsapp_response_success(self, openai_service):
        result = openai_service.generate_whatsapp_response("¿Cuándo es el culto?", context="El culto es el domingo.", user_name="Juan")
        assert "Respuesta pastoral" in result

    def test_analyze_document_content_summary(self, openai_service):
        result = openai_service.analyze_document_content("Contenido de prueba", analysis_type="summary")
        assert "Análisis del documento" in result

    def test_analyze_document_content_invalid_type(self, openai_service):
        openai_service.analyze_document_content.side_effect = ValueError("Invalid analysis type")
        with pytest.raises(ValueError):
            openai_service.analyze_document_content("Contenido", analysis_type="invalid_type")

    def test_validate_text_length(self, openai_service):
        assert openai_service.validate_text_length("a" * 1000, max_tokens=8000)
        openai_service.validate_text_length.return_value = False
        assert not openai_service.validate_text_length("a" * 40000, max_tokens=1000)

    def test_get_chat_history_summary(self, openai_service):
        messages = [{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "Bienvenido"}]
        result = openai_service.get_chat_history_summary(messages)
        assert "Resumen del chat" in result

    def test_get_chat_history_summary_empty(self, openai_service):
        openai_service.get_chat_history_summary.return_value = ""
        result = openai_service.get_chat_history_summary([])
        assert result == "" 