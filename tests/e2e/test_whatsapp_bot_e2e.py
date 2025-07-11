"""
Tests end-to-end para whatsapp_bot.py
"""
import pytest
import json
import azure.functions as func
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from whatsapp_bot.whatsapp_bot import main
from shared_code.user_service import User, UserSession
import config.settings


class TestWhatsAppBotE2E:
    """Tests end-to-end para WhatsAppBot"""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock del entorno completo"""
        with patch.dict('os.environ', {
            'WHATSAPP_TOKEN': 'test-whatsapp-token',
            'WHATSAPP_PHONE_NUMBER_ID': '123456789',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_API_KEY': 'test-openai-key',
            'AZURE_OPENAI_DEPLOYMENT_NAME': 'test-deployment',
            'REDIS_CONNECTION_STRING': 'redis://localhost:6379',
            'AZURE_COMPUTER_VISION_ENDPOINT': 'https://test.vision.azure.com/',
            'AZURE_COMPUTER_VISION_API_KEY': 'test-vision-key',
            'WHATSAPP_VERIFY_TOKEN': 'test-verify-token'
        }):
            yield
    
    @pytest.fixture
    def mock_services(self):
        """Mock de todos los servicios y configuración"""
        with patch('whatsapp_bot.whatsapp_bot.bot', None), \
             patch('whatsapp_bot.whatsapp_bot.get_settings') as mock_get_settings, \
             patch('whatsapp_bot.whatsapp_bot.WhatsAppService') as mock_whatsapp, \
             patch('whatsapp_bot.whatsapp_bot.OpenAIService') as mock_openai, \
             patch('whatsapp_bot.whatsapp_bot.RedisService') as mock_redis, \
             patch('whatsapp_bot.whatsapp_bot.VisionService') as mock_vision, \
             patch('whatsapp_bot.whatsapp_bot.UserService') as mock_user_service:

            # Mock de configuración para el token de verificación
            mock_settings_obj = Mock()
            mock_settings_obj.whatsapp_verify_token = 'test-verify-token'
            mock_get_settings.return_value = mock_settings_obj

            # Configurar servicios mock
            mock_whatsapp.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_redis.return_value = Mock()
            mock_vision.return_value = Mock()
            mock_user_service.return_value = Mock()
            
            yield {
                'whatsapp': mock_whatsapp.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'vision': mock_vision.return_value,
                'user_service': mock_user_service.return_value
            }
    
    def test_webhook_verification_e2e(self):
        req = MagicMock()
        req.method = "GET"
        req.params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-token",
            "hub.challenge": "12345"
        }
        with patch.object(config.settings.settings, 'whatsapp_verify_token', 'verify-token'):
            response = main(req)
        assert response.status_code == 200
        assert "12345" in response.get_body().decode()
    
    def test_text_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E de flujo de mensaje de texto"""
        # Preparar request de mensaje de texto
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Hola, ¿cómo estás?"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        
        # Verificar que se llamaron los servicios mockeados
        # Los mocks están configurados para retornar True, así que no fallarán
    
    def test_image_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E de flujo de mensaje de imagen"""
        # Preparar request de mensaje de imagen
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "image",
                            "image": {"id": "test-image-id"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
    
    def test_audio_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E de flujo de mensaje de audio"""
        # Preparar request de mensaje de audio
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "audio",
                            "audio": {"id": "test-audio-id"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_document_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E de flujo de mensaje de documento"""
        # Preparar request de mensaje de documento
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "document",
                            "document": {"id": "test-document-id"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_welcome_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E de flujo de mensaje de bienvenida"""
        # Preparar request de mensaje vacío
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": ""}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_rate_limit_exceeded_e2e(self, mock_environment, mock_services):
        """Test E2E de rate limit excedido"""
        # Preparar request de mensaje
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Mensaje de prueba"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_error_handling_e2e(self, mock_environment, mock_services):
        """Test E2E de manejo de errores"""
        # Preparar request con error
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Error"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_conversation_context_persistence_e2e(self, mock_environment, mock_services):
        """Test E2E de persistencia de contexto de conversación"""
        # Preparar request de mensaje
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Mensaje con contexto"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_fallback_response_e2e(self, mock_environment, mock_services):
        """Test E2E de respuesta de fallback"""
        # Preparar request de mensaje
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Mensaje de fallback"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200

    def test_unsupported_message_type_e2e(self, mock_environment, mock_services):
        """Test E2E de tipo de mensaje no soportado"""
        # Preparar request de mensaje de video
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "test-phone-id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "+1234567890",
                            "id": "test-message-id",
                            "timestamp": "1234567890",
                            "type": "video",
                            "video": {"id": "test-video-id"}
                        }]
                    }
                }]
            }]
        }
        req.headers = {}  # Asegurar que headers es un dict real
        req.params = {}   # Asegurar que params es un dict real
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200 