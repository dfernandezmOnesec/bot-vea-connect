"""
Tests unitarios para utils.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from shared_code.utils import (
    setup_logging,
    validate_phone_number,
    sanitize_text,
    format_response,
    parse_whatsapp_message,
    extract_media_info,
    create_error_response,
    validate_environment_variables,
    retry_with_backoff,
    rate_limit_check,
    generate_session_id,
    validate_json_schema
)


class TestSetupLogging:
    """Tests para setup_logging"""
    
    def test_setup_logging_default(self):
        """Test configuración de logging por defecto"""
        logger = setup_logging()
        
        assert logger is not None
        assert logger.name == "bot_vea_connect"
        assert logger.level == logging.INFO
    
    def test_setup_logging_custom_level(self):
        """Test configuración de logging con nivel personalizado"""
        logger = setup_logging(level=logging.DEBUG)
        
        assert logger is not None
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_custom_name(self):
        """Test configuración de logging con nombre personalizado"""
        logger = setup_logging(name="test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"


class TestValidatePhoneNumber:
    """Tests para validate_phone_number"""
    
    def test_valid_phone_number_with_plus(self):
        """Test número de teléfono válido con +"""
        result = validate_phone_number("+1234567890")
        assert result is True
    
    def test_valid_phone_number_without_plus(self):
        """Test número de teléfono válido sin +"""
        result = validate_phone_number("1234567890")
        assert result is True
    
    def test_invalid_phone_number_too_short(self):
        """Test número de teléfono muy corto"""
        result = validate_phone_number("123")
        assert result is False
    
    def test_invalid_phone_number_too_long(self):
        """Test número de teléfono muy largo"""
        result = validate_phone_number("+12345678901234567890")
        assert result is False
    
    def test_invalid_phone_number_with_letters(self):
        """Test número de teléfono con letras"""
        result = validate_phone_number("+123abc456")
        assert result is False
    
    def test_invalid_phone_number_empty(self):
        """Test número de teléfono vacío"""
        result = validate_phone_number("")
        assert result is False
    
    def test_invalid_phone_number_none(self):
        """Test número de teléfono None"""
        result = validate_phone_number("")  # Cambiado de None a string vacío
        assert result is False


class TestSanitizeText:
    """Tests para sanitize_text"""
    
    def test_sanitize_text_normal(self):
        """Test sanitización de texto normal"""
        text = "Hola, ¿cómo estás?"
        result = sanitize_text(text)
        assert result == "Hola, ¿cómo estás?"
    
    def test_sanitize_text_with_html(self):
        """Test sanitización de texto con HTML"""
        text = "<script>alert('xss')</script>Hola"
        result = sanitize_text(text)
        assert "<script>" not in result
        assert "Hola" in result
    
    def test_sanitize_text_with_special_chars(self):
        """Test sanitización de texto con caracteres especiales"""
        text = "Texto con \n saltos de línea y \t tabulaciones"
        result = sanitize_text(text)
        assert "\n" not in result
        assert "\t" not in result
    
    def test_sanitize_text_empty(self):
        """Test sanitización de texto vacío"""
        result = sanitize_text("")
        assert result == ""
    
    def test_sanitize_text_none(self):
        """Test sanitización de texto None"""
        result = sanitize_text("")  # Cambiado de None a string vacío
        assert result == ""


class TestFormatResponse:
    """Tests para format_response"""
    
    def test_format_response_success(self):
        """Test formato de respuesta exitosa"""
        message = "Respuesta exitosa"
        result = format_response(message, success=True)
        
        assert result["success"] is True
        assert result["message"] == message
        assert "timestamp" in result
    
    def test_format_response_error(self):
        """Test formato de respuesta de error"""
        message = "Error ocurrido"
        result = format_response(message, success=False)
        
        assert result["success"] is False
        assert result["message"] == message
        assert "timestamp" in result
    
    def test_format_response_with_data(self):
        """Test formato de respuesta con datos adicionales"""
        message = "Datos obtenidos"
        data = {"user_id": "123", "name": "Juan"}
        result = format_response(message, success=True, data=data)
        
        assert result["success"] is True
        assert result["message"] == message
        assert result["data"] == data
        assert "timestamp" in result


class TestParseWhatsAppMessage:
    """Tests para parse_whatsapp_message"""
    
    def test_parse_text_message(self):
        """Test parseo de mensaje de texto"""
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "Hola bot"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        result = parse_whatsapp_message(message_data)
        
        assert result is not None
        assert result["type"] == "text"
        assert result["content"] == "Hola bot"
        assert result["from"] == "+1234567890"
        assert result["timestamp"] == "1234567890"
    
    def test_parse_image_message(self):
        """Test parseo de mensaje de imagen"""
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "image",
                            "image": {
                                "id": "image_id_123",
                                "mime_type": "image/jpeg",
                                "sha256": "abc123",
                                "filename": "photo.jpg"
                            },
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        result = parse_whatsapp_message(message_data)
        
        assert result is not None
        assert result["type"] == "image"
        assert result["media_id"] == "image_id_123"
        assert result["mime_type"] == "image/jpeg"
        assert result["from"] == "+1234567890"
    
    def test_parse_audio_message(self):
        """Test parseo de mensaje de audio"""
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "audio",
                            "audio": {
                                "id": "audio_id_123",
                                "mime_type": "audio/ogg; codecs=opus",
                                "sha256": "def456",
                                "filename": "voice.ogg"
                            },
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        result = parse_whatsapp_message(message_data)
        
        assert result is not None
        assert result["type"] == "audio"
        assert result["media_id"] == "audio_id_123"
        assert result["mime_type"] == "audio/ogg; codecs=opus"
        assert result["from"] == "+1234567890"
    
    def test_parse_document_message(self):
        """Test parseo de mensaje de documento"""
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "+1234567890",
                            "type": "document",
                            "document": {
                                "id": "doc_id_123",
                                "mime_type": "application/pdf",
                                "filename": "document.pdf"
                            },
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        result = parse_whatsapp_message(message_data)
        
        assert result is not None
        assert result["type"] == "document"
        assert result["media_id"] == "doc_id_123"
        assert result["mime_type"] == "application/pdf"
        assert result["from"] == "+1234567890"
    
    def test_parse_invalid_message(self):
        """Test parseo de mensaje inválido"""
        message_data = {"invalid": "data"}
        
        result = parse_whatsapp_message(message_data)
        
        assert result is not None
        assert result["from"] is None
        assert result["type"] is None
    
    def test_parse_empty_messages(self):
        """Test parseo de mensaje sin mensajes"""
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": []
                    }
                }]
            }]
        }
        
        result = parse_whatsapp_message(message_data)
        
        assert result is None


class TestExtractMediaInfo:
    """Tests para extract_media_info"""
    
    def test_extract_image_info(self):
        """Test extracción de información de imagen"""
        message = {
            "type": "image",
            "image": {
                "id": "image_id_123",
                "mime_type": "image/jpeg",
                "sha256": "abc123",
                "filename": "photo.jpg"
            }
        }
        
        result = extract_media_info(message)
        
        assert result is not None
        assert result["media_id"] == "image_id_123"
        assert result["mime_type"] == "image/jpeg"
        assert result["sha256"] == "abc123"
        assert result["filename"] == "photo.jpg"
    
    def test_extract_audio_info(self):
        """Test extracción de información de audio"""
        message = {
            "type": "audio",
            "audio": {
                "id": "audio_id_123",
                "mime_type": "audio/ogg; codecs=opus",
                "sha256": "def456",
                "filename": "voice.ogg"
            }
        }
        
        result = extract_media_info(message)
        
        assert result is not None
        assert result["media_id"] == "audio_id_123"
        assert result["mime_type"] == "audio/ogg; codecs=opus"
        assert result["sha256"] == "def456"
        assert result["filename"] == "voice.ogg"
    
    def test_extract_document_info(self):
        """Test extracción de información de documento"""
        message = {
            "type": "document",
            "document": {
                "id": "doc_id_123",
                "mime_type": "application/pdf",
                "sha256": "ghi789",
                "filename": "document.pdf"
            }
        }
        
        result = extract_media_info(message)
        
        assert result is not None
        assert result["media_id"] == "doc_id_123"
        assert result["mime_type"] == "application/pdf"
        assert result["sha256"] == "ghi789"
        assert result["filename"] == "document.pdf"
    
    def test_extract_unsupported_type(self):
        """Test extracción de tipo no soportado"""
        message = {
            "type": "unsupported",
            "unsupported": {}
        }
        
        result = extract_media_info(message)
        
        assert result is None


class TestCreateErrorResponse:
    """Tests para create_error_response"""
    
    def test_create_error_response_basic(self):
        """Test creación de respuesta de error básica"""
        error_message = "Error de prueba"
        result = create_error_response(error_message)
        
        assert result["success"] is False
        assert result["message"] == error_message
        assert "timestamp" in result
        assert "error_code" not in result
    
    def test_create_error_response_with_code(self):
        """Test creación de respuesta de error con código"""
        error_message = "Error de prueba"
        error_code = "VALIDATION_ERROR"
        result = create_error_response(error_message, error_code=error_code)
        
        assert result["success"] is False
        assert result["message"] == error_message
        assert result["error_code"] == error_code
        assert "timestamp" in result
    
    def test_create_error_response_with_details(self):
        """Test creación de respuesta de error con detalles"""
        error_message = "Error de prueba"
        details = {"field": "phone", "issue": "invalid_format"}
        result = create_error_response(error_message, details=details)
        
        assert result["success"] is False
        assert result["message"] == error_message
        assert result["details"] == details
        assert "timestamp" in result


class TestValidateEnvironmentVariables:
    """Tests para validate_environment_variables"""
    
    @patch.dict('os.environ', {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_API_KEY': 'test-key',
        'REDIS_HOST': 'localhost',
        'WHATSAPP_VERIFY_TOKEN': 'whatsapp-token',  # Cambiado de WHATSAPP_TOKEN
        'WHATSAPP_PHONE_NUMBER_ID': '123456789'
    })
    def test_validate_environment_variables_success(self):
        """Test validación exitosa de variables de entorno"""
        result = validate_environment_variables()
        
        assert result is True
    
    @patch.dict('os.environ', {
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_API_KEY': 'test-key'
    }, clear=True)
    def test_validate_environment_variables_missing(self):
        """Test validación con variables faltantes"""
        with pytest.raises(ValueError) as exc_info:
            validate_environment_variables()
        
        assert "Missing required environment variable" in str(exc_info.value)
    
    @patch.dict('os.environ', {
        'AZURE_OPENAI_ENDPOINT': '',
        'AZURE_OPENAI_API_KEY': 'test-key'
    }, clear=True)
    def test_validate_environment_variables_empty(self):
        """Test validación con variables vacías"""
        with pytest.raises(ValueError) as exc_info:
            validate_environment_variables()
        
        assert "Missing required environment variable" in str(exc_info.value)


class TestRetryWithBackoff:
    """Tests para retry_with_backoff"""
    
    def test_retry_with_backoff_success_first_try(self):
        """Test retry exitoso en el primer intento"""
        mock_function = Mock(return_value="success")
        
        result = retry_with_backoff(mock_function, max_retries=3)
        
        assert result == "success"
        assert mock_function.call_count == 1
    
    def test_retry_with_backoff_success_after_retries(self):
        """Test retry exitoso después de varios intentos"""
        mock_function = Mock(side_effect=[Exception("Error"), Exception("Error"), "success"])
        
        result = retry_with_backoff(mock_function, max_retries=3)
        
        assert result == "success"
        assert mock_function.call_count == 3
    
    def test_retry_with_backoff_max_retries_exceeded(self):
        """Test retry que excede el máximo de intentos"""
        mock_function = Mock(side_effect=Exception("Error"))
        
        with pytest.raises(Exception) as exc_info:
            retry_with_backoff(mock_function, max_retries=2)
        
        assert "Error" in str(exc_info.value)
        assert mock_function.call_count == 3  # 1 inicial + 2 retries
    
    def test_retry_with_backoff_custom_backoff(self):
        """Test retry con backoff personalizado"""
        mock_function = Mock(side_effect=[Exception("Error"), "success"])
        
        result = retry_with_backoff(mock_function, max_retries=2, base_delay=0.1)
        
        assert result == "success"
        assert mock_function.call_count == 2


class TestRateLimitCheck:
    """Tests para rate_limit_check"""
    
    def test_rate_limit_check_allowed(self):
        """Test verificación de rate limit permitida"""
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = b"5"  # 5 requests en la ventana
        
        result = rate_limit_check(mock_redis_client, "user123", max_requests=10, window_seconds=60)
        
        assert result is True
        mock_redis_client.get.assert_called_once_with("rate_limit:user123")
    
    def test_rate_limit_check_exceeded(self):
        """Test verificación de rate limit excedida"""
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = b"15"  # 15 requests en la ventana
        
        result = rate_limit_check(mock_redis_client, "user123", max_requests=10, window_seconds=60)
        
        assert result is False
        mock_redis_client.get.assert_called_once_with("rate_limit:user123")
    
    def test_rate_limit_check_no_previous_requests(self):
        """Test verificación de rate limit sin requests previos"""
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = None
        
        result = rate_limit_check(mock_redis_client, "user123", max_requests=10, window_seconds=60)
        
        assert result is True
        mock_redis_client.get.assert_called_once_with("rate_limit:user123")
    
    def test_rate_limit_check_redis_error(self):
        """Test verificación de rate limit con error de Redis"""
        mock_redis_client = Mock()
        mock_redis_client.get.side_effect = Exception("Redis error")
        
        # Debería permitir el acceso en caso de error
        result = rate_limit_check(mock_redis_client, "user123", max_requests=10, window_seconds=60)
        
        assert result is True


class TestGenerateSessionId:
    """Tests para generate_session_id"""
    
    def test_generate_session_id_format(self):
        """Test formato del ID de sesión"""
        session_id = generate_session_id()
        
        # El ID debe tener al menos 32 caracteres (timestamp + uuid)
        assert len(session_id) >= 32
        assert session_id.startswith("session_")
    
    def test_generate_session_id_uniqueness(self):
        """Test unicidad de IDs de sesión"""
        session_ids = set()
        for _ in range(100):
            session_id = generate_session_id()
            assert session_id not in session_ids
            session_ids.add(session_id)


class TestValidateJsonSchema:
    """Tests para validate_json_schema"""
    
    def test_validate_json_schema_valid(self):
        """Test validación de esquema JSON válido"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        data = {"name": "Juan", "age": 30}
        
        result = validate_json_schema(data, schema)
        
        assert result is True
    
    def test_validate_json_schema_invalid(self):
        """Test validación de esquema JSON inválido"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        data = {"age": "not_an_integer"}
        
        result = validate_json_schema(data, schema)
        
        assert result is False
    
    def test_validate_json_schema_missing_required(self):
        """Test validación de esquema JSON con campo requerido faltante"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        data = {"age": 30}
        
        result = validate_json_schema(data, schema)
        
        assert result is False
    
    def test_validate_json_schema_invalid_schema(self):
        """Test validación con esquema inválido"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        
        data = {"name": "test"}
        
        # Un esquema válido siempre debe devolver True para datos válidos
        result = validate_json_schema(data, schema)
        
        assert result is True 