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
        """Mock de todos los servicios"""
        with patch('src.whatsapp_bot.whatsapp_bot.WhatsAppService') as mock_whatsapp, \
             patch('src.whatsapp_bot.whatsapp_bot.OpenAIService') as mock_openai, \
             patch('src.whatsapp_bot.whatsapp_bot.RedisService') as mock_redis, \
             patch('src.whatsapp_bot.whatsapp_bot.VisionService') as mock_vision, \
             patch('src.whatsapp_bot.whatsapp_bot.UserService') as mock_user_service:
            
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
    
    def test_webhook_verification_e2e(self, mock_environment, mock_services):
        """Test E2E de verificación de webhook"""
        # Preparar request de verificación
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {"object": "whatsapp_business_account"}
        req.params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
            "hub.challenge": "challenge123"
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.get_body() == b"challenge123"
    
    def test_text_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E del flujo completo de mensaje de texto"""
        # Configurar mocks para el flujo completo
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="Juan Pérez"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-123",
            user_phone="+1234567890"
        )
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].search_similar_documents.return_value = [
            {"content": "Información sobre eventos de la iglesia"}
        ]
        mock_services['openai'].generate_chat_completion.return_value = (
            "Gracias por tu pregunta. Nuestros servicios son los domingos "
            "a las 9:00 AM y 11:00 AM. Que Dios te bendiga. 🙏"
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        mock_services['user_service'].update_session.return_value = True
        
        # Preparar request de mensaje de texto
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "¿Cuándo son los servicios?"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["response_sent"] is True
        
        # Verificar que se llamaron los servicios correctos
        mock_services['user_service'].get_user.assert_called_once_with("+1234567890")
        mock_services['user_service'].create_session.assert_called_once_with("+1234567890")
        mock_services['openai'].generate_embedding.assert_called_once()
        mock_services['redis'].search_similar_documents.assert_called_once()
        mock_services['openai'].generate_chat_completion.assert_called_once()
        mock_services['whatsapp'].send_text_message.assert_called_once()
        mock_services['user_service'].update_session.assert_called_once()
    
    def test_image_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E del flujo completo de mensaje de imagen"""
        # Configurar mocks para el flujo de imagen
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="María García"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-456",
            user_phone="+1234567890"
        )
        mock_services['whatsapp'].download_media.return_value = b"fake_image_data"
        mock_services['vision'].analyze_image.return_value = {
            "description": "Personas orando en una iglesia",
            "tags": ["oración", "iglesia", "fe", "comunidad"]
        }
        mock_services['openai'].generate_chat_completion.return_value = (
            "Gracias por compartir esta hermosa imagen. Veo personas unidas en oración, "
            "lo cual refleja la belleza de la comunidad cristiana. Que Dios bendiga "
            "tu fe y tu caminar con Él. 🙏"
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        
        # Preparar request de mensaje de imagen
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
                                "filename": "prayer.jpg"
                            },
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["image_analyzed"] is True
        
        # Verificar que se llamaron los servicios correctos
        mock_services['whatsapp'].download_media.assert_called_once_with("image_id_123")
        mock_services['vision'].analyze_image.assert_called_once_with(b"fake_image_data")
        mock_services['openai'].generate_chat_completion.assert_called_once()
        mock_services['whatsapp'].send_text_message.assert_called_once()
    
    def test_audio_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E del flujo completo de mensaje de audio"""
        # Configurar mocks para el flujo de audio
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="Carlos López"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-789",
            user_phone="+1234567890"
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        
        # Preparar request de mensaje de audio
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
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió el mensaje de audio no soportado
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "mensaje de voz" in call_args[1]
        assert "texto" in call_args[1]
    
    def test_document_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E del flujo completo de mensaje de documento"""
        # Configurar mocks para el flujo de documento
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="Ana Martínez"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-101",
            user_phone="+1234567890"
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        
        # Preparar request de mensaje de documento
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "document",
                            "document": {
                                "id": "doc_id_123",
                                "mime_type": "application/pdf",
                                "sha256": "ghi789",
                                "filename": "ministerio.pdf"
                            },
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió el mensaje de documento
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "ministerio.pdf" in call_args[1]
        assert "líderes de ministerio" in call_args[1]
    
    def test_welcome_message_flow_e2e(self, mock_environment, mock_services):
        """Test E2E del flujo de mensaje de bienvenida"""
        # Configurar mocks para el flujo de bienvenida
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="Nuevo Usuario"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-welcome",
            user_phone="+1234567890"
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        
        # Preparar request con mensaje vacío
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": ""},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió el mensaje de bienvenida
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "Bienvenido a VEA Connect" in call_args[1]
        assert "asistente virtual pastoral" in call_args[1]
    
    def test_rate_limit_exceeded_e2e(self, mock_environment, mock_services):
        """Test E2E de rate limit excedido"""
        # Configurar mocks para rate limit
        mock_services['redis'].redis_client.get.return_value = b"15"  # Más de 10 requests
        
        # Preparar request
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "Mensaje de prueba"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió el mensaje de rate limit
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "muy rápidamente" in call_args[1]
    
    def test_error_handling_e2e(self, mock_environment, mock_services):
        """Test E2E de manejo de errores"""
        # Configurar mocks para generar error
        mock_services['user_service'].get_user.side_effect = Exception("Redis connection error")
        
        # Preparar request
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "Hola"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió el mensaje de error
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "dificultades técnicas" in call_args[1]
    
    def test_conversation_context_persistence_e2e(self, mock_environment, mock_services):
        """Test E2E de persistencia del contexto de conversación"""
        # Configurar mocks para conversación persistente
        existing_user = User(
            phone_number="+1234567890",
            name="Usuario Existente"
        )
        existing_session = UserSession(
            session_id="existing-session",
            user_phone="+1234567890",
            context={
                "conversation_history": [
                    "Hola", "¡Hola! ¿En qué puedo ayudarte?",
                    "¿Cuándo son los servicios?", "Los servicios son los domingos..."
                ]
            }
        )
        
        mock_services['user_service'].get_user.return_value = existing_user
        mock_services['user_service'].get_user_sessions.return_value = [existing_session]
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].search_similar_documents.return_value = []
        mock_services['openai'].generate_chat_completion.return_value = (
            "Gracias por tu pregunta. Te ayudo con eso."
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        mock_services['user_service'].update_session.return_value = True
        
        # Preparar request
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "¿Y los horarios de los grupos pequeños?"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se actualizó la sesión con el nuevo contexto
        mock_services['user_service'].update_session.assert_called_once()
        updated_session = mock_services['user_service'].update_session.call_args[0][0]
        assert len(updated_session.context["conversation_history"]) > 4  # Debería tener más mensajes
    
    def test_fallback_response_e2e(self, mock_environment, mock_services):
        """Test E2E de respuesta de respaldo cuando OpenAI falla"""
        # Configurar mocks para fallo de OpenAI
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="Usuario Test"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-fallback",
            user_phone="+1234567890"
        )
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].search_similar_documents.return_value = []
        mock_services['openai'].generate_chat_completion.return_value = None  # OpenAI falla
        mock_services['whatsapp'].send_text_message.return_value = True
        
        # Preparar request con pregunta sobre eventos
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "¿Cuándo es el próximo evento?"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió la respuesta de respaldo
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "servicios son los domingos" in call_args[1]
        assert "9:00 AM" in call_args[1]
    
    def test_invalid_phone_number_e2e(self, mock_environment, mock_services):
        """Test E2E de número de teléfono inválido"""
        # Preparar request con número inválido
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "Hola"},
                            "from": "invalid-phone",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is False
        assert "Número de teléfono inválido" in response_data["message"]
    
    def test_unsupported_message_type_e2e(self, mock_environment, mock_services):
        """Test E2E de tipo de mensaje no soportado"""
        # Configurar mocks básicos
        mock_services['user_service'].get_user.return_value = User(
            phone_number="+1234567890",
            name="Usuario Test"
        )
        mock_services['user_service'].get_user_sessions.return_value = []
        mock_services['user_service'].create_session.return_value = UserSession(
            session_id="test-session-unsupported",
            user_phone="+1234567890"
        )
        mock_services['whatsapp'].send_text_message.return_value = True
        
        # Preparar request con tipo no soportado
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "video",  # Tipo no soportado
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = message_data
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió el mensaje de tipo no soportado
        mock_services['whatsapp'].send_text_message.assert_called_once()
        call_args = mock_services['whatsapp'].send_text_message.call_args[0]
        assert "texto, imágenes o documentos" in call_args[1] 