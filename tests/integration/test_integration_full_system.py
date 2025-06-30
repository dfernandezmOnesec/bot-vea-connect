"""
Tests de integración para el flujo completo del sistema.
Estos tests verifican la integración real entre todos los componentes del sistema.
"""
import pytest
import json
import azure.functions as func
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from src.whatsapp_bot.whatsapp_bot import main as whatsapp_main, WhatsAppBot
from src.processing.batch_start_processing import main as batch_main
from src.processing.blob_trigger_processor import main as blob_main
from src.processing.batch_push_results import main as push_main
from src.shared_code.whatsapp_service import WhatsAppService
from src.shared_code.openai_service import OpenAIService
from src.shared_code.redis_service import RedisService
from src.shared_code.user_service import UserService
from src.shared_code.vision_service import VisionService
from src.shared_code.azure_blob_storage import AzureBlobStorageService


class TestFullSystemIntegration:
    """Tests de integración para el flujo completo del sistema"""
    
    @pytest.fixture
    def mock_full_environment(self):
        """Mock del entorno completo para todo el sistema"""
        with patch.dict('os.environ', {
            'WHATSAPP_TOKEN': 'test-whatsapp-token-12345',
            'WHATSAPP_PHONE_NUMBER_ID': '123456789012345',
            'AZURE_OPENAI_ENDPOINT': 'https://test-openai.openai.azure.com/',
            'AZURE_OPENAI_API_KEY': 'test-openai-key-abcdef123456',
            'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-4-deployment',
            'REDIS_CONNECTION_STRING': 'redis://localhost:6379/0',
            'AZURE_COMPUTER_VISION_ENDPOINT': 'https://test-vision.cognitiveservices.azure.com/',
            'AZURE_COMPUTER_VISION_API_KEY': 'test-vision-key-abcdef123456',
            'WHATSAPP_VERIFY_TOKEN': 'test-verify-token-67890',
            'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=teststorage;AccountKey=testkey;EndpointSuffix=core.windows.net',
            'AZURE_STORAGE_CONTAINER_NAME': 'test-container'
        }):
            yield
    
    @pytest.fixture
    def real_full_system_services(self, mock_full_environment):
        """Instancias reales de todos los servicios del sistema"""
        with patch('src.whatsapp_bot.whatsapp_bot.requests') as mock_whatsapp_requests, \
             patch('src.whatsapp_bot.whatsapp_bot.openai') as mock_openai, \
             patch('src.whatsapp_bot.whatsapp_bot.redis') as mock_redis, \
             patch('src.whatsapp_bot.whatsapp_bot.requests') as mock_vision_requests, \
             patch('src.processing.batch_start_processing.AzureBlobStorageService') as mock_blob, \
             patch('src.processing.batch_start_processing.OpenAIService') as mock_processing_openai, \
             patch('src.processing.batch_start_processing.RedisService') as mock_processing_redis, \
             patch('src.processing.blob_trigger_processor.AzureBlobStorageService') as mock_blob_trigger, \
             patch('src.processing.blob_trigger_processor.OpenAIService') as mock_blob_openai, \
             patch('src.processing.blob_trigger_processor.RedisService') as mock_blob_redis, \
             patch('src.processing.batch_push_results.AzureBlobStorageService') as mock_push_blob:
            
            # Configurar mocks de WhatsApp
            mock_whatsapp_requests.post.return_value = Mock(
                status_code=200,
                json=lambda: {"messages": [{"id": "test-message-id"}]}
            )
            mock_whatsapp_requests.get.return_value = Mock(
                status_code=200,
                content=b"test_media_content"
            )
            
            # Configurar mocks de OpenAI
            mock_openai.AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Respuesta generada por OpenAI"))]
            )
            mock_openai.AzureOpenAI.return_value.embeddings.create.return_value = Mock(
                data=[Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 300)]  # 1500 dimensiones
            )
            
            # Configurar mocks de Redis
            mock_redis_client = Mock()
            mock_redis_client.get.return_value = None
            mock_redis_client.set.return_value = True
            mock_redis_client.expire.return_value = True
            mock_redis_client.delete.return_value = 1
            mock_redis_client.keys.return_value = []
            mock_redis.from_url.return_value = mock_redis_client
            
            # Configurar mocks de Vision
            mock_vision_requests.post.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "description": {"captions": [{"text": "Personas orando en una iglesia"}]},
                    "tags": [{"name": "oración"}, {"name": "iglesia"}, {"name": "fe"}]
                }
            )
            
            # Configurar mocks de procesamiento
            mock_blob.return_value = Mock()
            mock_processing_openai.return_value = Mock()
            mock_processing_redis.return_value = Mock()
            mock_blob_trigger.return_value = Mock()
            mock_blob_openai.return_value = Mock()
            mock_blob_redis.return_value = Mock()
            mock_push_blob.return_value = Mock()
            
            yield {
                'whatsapp_requests': mock_whatsapp_requests,
                'openai': mock_openai,
                'redis': mock_redis,
                'redis_client': mock_redis_client,
                'vision_requests': mock_vision_requests,
                'blob': mock_blob.return_value,
                'processing_openai': mock_processing_openai.return_value,
                'processing_redis': mock_processing_redis.return_value,
                'blob_trigger': mock_blob_trigger.return_value,
                'blob_openai': mock_blob_openai.return_value,
                'blob_redis': mock_blob_redis.return_value,
                'push_blob': mock_push_blob.return_value
            }
    
    def test_complete_user_journey_integration(self, real_full_system_services):
        """
        Test de integración: Viaje completo del usuario
        Verifica línea por línea el flujo completo desde el primer mensaje hasta la respuesta
        """
        # Configurar usuario nuevo
        real_full_system_services['redis_client'].get.return_value = None
        real_full_system_services['redis_client'].keys.return_value = []
        
        # Configurar OpenAI para respuesta de bienvenida
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="¡Bienvenido a VEA Connect! 🙏"))]
        )
        
        # Preparar mensaje de bienvenida
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
        
        # Ejecutar función de WhatsApp
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se creó el usuario
        user_creation_call = real_full_system_services['redis_client'].set.call_args_list[0]
        assert "user:+1234567890" in str(user_creation_call)
        
        # Verificar que se envió mensaje de bienvenida
        real_full_system_services['whatsapp_requests'].post.assert_called_once()
        
        # Ahora simular pregunta sobre servicios
        real_full_system_services['redis_client'].get.side_effect = [
            json.dumps({
                "phone_number": "+1234567890",
                "name": "Usuario Test",
                "preferences": {"language": "es"},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }).encode(),
            json.dumps({
                "session_id": "test-session-123",
                "user_phone": "+1234567890",
                "context": {"conversation_history": ["Hola", "¡Bienvenido a VEA Connect! 🙏"]},
                "created_at": "2024-01-01T00:00:00",
                "is_active": True
            }).encode()
        ]
        real_full_system_services['redis_client'].keys.return_value = [b"session:test-session-123"]
        
        # Configurar búsqueda semántica
        relevant_docs = [{"content": "Los servicios son los domingos a las 9:00 AM y 11:00 AM"}]
        real_full_system_services['redis_client'].search_similar_documents = Mock(return_value=relevant_docs)
        
        # Configurar OpenAI para respuesta sobre servicios
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Los servicios son los domingos a las 9:00 AM y 11:00 AM"))]
        )
        
        # Preparar pregunta sobre servicios
        service_message_data = {
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
        
        req.get_json.return_value = service_message_data
        
        # Ejecutar función de WhatsApp nuevamente
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se actualizó la sesión
        assert real_full_system_services['redis_client'].set.call_count >= 2
    
    def test_document_processing_and_query_integration(self, real_full_system_services):
        """
        Test de integración: Procesamiento de documento y consulta posterior
        Verifica línea por línea el flujo completo de procesamiento y consulta
        """
        # Configurar procesamiento de documento
        real_full_system_services['blob_trigger'].download_blob.return_value = b"Contenido del documento sobre ministerios"
        real_full_system_services['blob_openai'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        real_full_system_services['blob_redis'].store_document.return_value = True
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "ministerio_plan.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar procesamiento de documento
        blob_main(blob_trigger)
        
        # Verificar que se procesó el documento
        real_full_system_services['blob_trigger'].download_blob.assert_called_once()
        real_full_system_services['blob_openai'].generate_embedding.assert_called_once()
        real_full_system_services['blob_redis'].store_document.assert_called_once()
        
        # Ahora simular consulta sobre el documento procesado
        real_full_system_services['redis_client'].get.return_value = json.dumps({
            "phone_number": "+1234567890",
            "name": "Usuario Test",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }).encode()
        real_full_system_services['redis_client'].keys.return_value = []
        
        # Configurar búsqueda semántica que encuentra el documento procesado
        relevant_docs = [{"content": "Contenido del documento sobre ministerios"}]
        real_full_system_services['redis_client'].search_similar_documents = Mock(return_value=relevant_docs)
        
        # Configurar OpenAI para respuesta basada en el documento
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Según el documento de ministerios, aquí tienes la información..."))]
        )
        
        # Preparar consulta sobre ministerios
        query_message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "¿Qué dice el documento sobre ministerios?"},
                            "from": "+1234567890",
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
        
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = query_message_data
        
        # Ejecutar función de WhatsApp
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se encontró el documento procesado
        real_full_system_services['redis_client'].search_similar_documents.assert_called_once()
    
    def test_batch_processing_and_results_integration(self, real_full_system_services):
        """
        Test de integración: Procesamiento por lotes y push de resultados
        Verifica línea por línea el flujo completo de procesamiento por lotes
        """
        # Configurar procesamiento por lotes
        file_list = ["document1.pdf", "document2.docx", "document3.txt"]
        real_full_system_services['blob'].list_blobs.return_value = file_list
        
        real_full_system_services['blob'].download_blob.side_effect = [
            b"PDF content for document1",
            b"DOCX content for document2",
            b"TXT content for document3"
        ]
        
        real_full_system_services['processing_openai'].generate_embedding.side_effect = [
            [0.1, 0.2, 0.3] * 500,
            [0.2, 0.3, 0.4] * 500,
            [0.3, 0.4, 0.5] * 500
        ]
        
        real_full_system_services['processing_redis'].store_document.return_value = True
        
        # Crear request de procesamiento por lotes
        batch_req = Mock()
        batch_req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar procesamiento por lotes
        response = batch_main(batch_req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 3
        assert response_data["data"]["stored_documents"] == 3
        
        # Ahora simular push de resultados
        results_data = {
            "processed_files": 3,
            "stored_documents": 3,
            "errors": 0,
            "skipped_files": 0,
            "processing_time": 45.2,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        real_full_system_services['push_blob'].upload_blob.return_value = True
        
        # Crear request de push de resultados
        push_req = Mock()
        push_req.get_json.return_value = {
            "results": results_data,
            "container_name": "test-container",
            "filename": "batch_results.json"
        }
        
        # Ejecutar push de resultados
        response = push_main(push_req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["uploaded"] is True
        
        # Verificar que se subió el archivo de resultados
        real_full_system_services['push_blob'].upload_blob.assert_called_once()
    
    def test_image_processing_and_analysis_integration(self, real_full_system_services):
        """
        Test de integración: Procesamiento de imagen y análisis
        Verifica línea por línea el flujo completo de procesamiento de imagen
        """
        # Configurar usuario existente
        real_full_system_services['redis_client'].get.return_value = json.dumps({
            "phone_number": "+1234567890",
            "name": "Usuario Test",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }).encode()
        real_full_system_services['redis_client'].keys.return_value = []
        
        # Configurar descarga de imagen
        real_full_system_services['whatsapp_requests'].get.return_value = Mock(
            status_code=200,
            content=b"fake_image_data"
        )
        
        # Configurar análisis de imagen
        vision_response = {
            "description": {"captions": [{"text": "Personas orando en una iglesia"}]},
            "tags": [{"name": "oración"}, {"name": "iglesia"}, {"name": "fe"}]
        }
        real_full_system_services['vision_requests'].post.return_value = Mock(
            status_code=200,
            json=lambda: vision_response
        )
        
        # Configurar respuesta de OpenAI para imagen
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Gracias por compartir esta hermosa imagen de fe. Que Dios bendiga tu caminar."))]
        )
        
        # Preparar mensaje de imagen
        image_message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "image",
                            "image": {
                                "id": "image_id_12345",
                                "mime_type": "image/jpeg",
                                "sha256": "abc123def456",
                                "filename": "prayer_group.jpg"
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
        req.get_json.return_value = image_message_data
        
        # Ejecutar función de WhatsApp
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["image_analyzed"] is True
        
        # Verificar llamadas a servicios
        real_full_system_services['whatsapp_requests'].get.assert_called_once()  # Descarga de imagen
        real_full_system_services['vision_requests'].post.assert_called_once()   # Análisis de imagen
        real_full_system_services['openai'].AzureOpenAI.assert_called_once()     # Generación de respuesta
        real_full_system_services['whatsapp_requests'].post.assert_called_once() # Envío de respuesta
    
    def test_error_recovery_integration(self, real_full_system_services):
        """
        Test de integración: Recuperación de errores
        Verifica línea por línea el manejo y recuperación de errores en el sistema
        """
        # Configurar usuario existente
        real_full_system_services['redis_client'].get.return_value = json.dumps({
            "phone_number": "+1234567890",
            "name": "Usuario Test",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }).encode()
        real_full_system_services['redis_client'].keys.return_value = []
        
        # Configurar fallo de OpenAI
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.side_effect = Exception("OpenAI error")
        
        # Preparar mensaje
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
        
        # Ejecutar función de WhatsApp
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa (con fallback)
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se envió respuesta de respaldo
        real_full_system_services['whatsapp_requests'].post.assert_called_once()
        call_args = real_full_system_services['whatsapp_requests'].post.call_args
        request_body = call_args[1]['json']
        assert "servicios son los domingos" in request_body['text']['body']
        
        # Ahora simular recuperación del servicio
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.side_effect = None
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="El próximo evento es este sábado a las 6:00 PM"))]
        )
        
        # Preparar nuevo mensaje
        message_data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "¿Cuándo es el próximo evento?"
        
        # Ejecutar función de WhatsApp nuevamente
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa con servicio recuperado
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se usó OpenAI esta vez
        assert real_full_system_services['openai'].AzureOpenAI.call_count >= 1
    
    def test_concurrent_user_handling_integration(self, real_full_system_services):
        """
        Test de integración: Manejo de usuarios concurrentes
        Verifica línea por línea el manejo de múltiples usuarios simultáneos
        """
        # Configurar múltiples usuarios
        users = [
            {"phone": "+1234567890", "name": "Usuario 1"},
            {"phone": "+0987654321", "name": "Usuario 2"},
            {"phone": "+1122334455", "name": "Usuario 3"}
        ]
        
        # Simular mensajes concurrentes
        for i, user in enumerate(users):
            # Configurar datos de usuario
            user_data = {
                "phone_number": user["phone"],
                "name": user["name"],
                "preferences": {"language": "es"},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
            
            # Configurar Redis para este usuario
            real_full_system_services['redis_client'].get.return_value = json.dumps(user_data).encode()
            real_full_system_services['redis_client'].keys.return_value = []
            
            # Configurar OpenAI para respuesta específica
            real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content=f"Respuesta para {user['name']}"))]
            )
            
            # Preparar mensaje
            message_data = {
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "type": "text",
                                "text": {"body": f"Hola, soy {user['name']}"},
                                "from": user["phone"],
                                "timestamp": f"123456789{i}"
                            }]
                        }
                    }]
                }]
            }
            
            req = Mock()
            req.method = "POST"
            req.get_json.return_value = message_data
            
            # Ejecutar función de WhatsApp
            response = whatsapp_main(req)
            
            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True
        
        # Verificar que se procesaron todos los usuarios
        assert real_full_system_services['whatsapp_requests'].post.call_count == 3
        assert real_full_system_services['openai'].AzureOpenAI.call_count == 3
    
    def test_data_persistence_integration(self, real_full_system_services):
        """
        Test de integración: Persistencia de datos
        Verifica línea por línea la persistencia de datos entre sesiones
        """
        # Configurar usuario con datos existentes
        user_data = {
            "phone_number": "+1234567890",
            "name": "Usuario Persistente",
            "email": "usuario@example.com",
            "preferences": {"language": "es", "notifications": True},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        session_data = {
            "session_id": "persistent-session-123",
            "user_phone": "+1234567890",
            "context": {
                "conversation_history": [
                    "Hola", "¡Hola! ¿En qué puedo ayudarte?",
                    "¿Cuándo son los servicios?", "Los servicios son los domingos..."
                ]
            },
            "created_at": "2024-01-01T00:00:00",
            "is_active": True
        }
        
        # Configurar Redis para retornar datos existentes
        real_full_system_services['redis_client'].get.side_effect = [
            json.dumps(user_data).encode(),
            json.dumps(session_data).encode()
        ]
        real_full_system_services['redis_client'].keys.return_value = [b"session:persistent-session-123"]
        
        # Configurar búsqueda semántica
        relevant_docs = [{"content": "Información sobre grupos pequeños"}]
        real_full_system_services['redis_client'].search_similar_documents = Mock(return_value=relevant_docs)
        
        # Configurar OpenAI para respuesta contextual
        real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Basándome en nuestra conversación anterior, aquí tienes más información..."))]
        )
        
        # Preparar mensaje de seguimiento
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "¿Y los grupos pequeños?"},
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
        
        # Ejecutar función de WhatsApp
        response = whatsapp_main(req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se mantuvieron los datos del usuario
        user_calls = [call for call in real_full_system_services['redis_client'].get.call_args_list 
                     if 'user:+1234567890' in str(call)]
        assert len(user_calls) >= 1
        
        # Verificar que se actualizó la sesión
        session_calls = [call for call in real_full_system_services['redis_client'].set.call_args_list 
                        if 'session:' in str(call)]
        assert len(session_calls) >= 1
        
        # Verificar que OpenAI recibió el contexto histórico
        openai_call = real_full_system_services['openai'].AzureOpenAI.return_value.chat.completions.create.call_args
        messages = openai_call[1]['messages']
        assert len(messages) == 2  # System + User
        assert "¿Y los grupos pequeños?" in messages[1]['content']
    
    def test_system_health_monitoring_integration(self, real_full_system_services):
        """
        Test de integración: Monitoreo de salud del sistema
        Verifica línea por línea el monitoreo y reportes de salud del sistema
        """
        # Simular métricas del sistema
        system_metrics = {
            "active_users": 150,
            "messages_processed": 1250,
            "documents_processed": 45,
            "errors_count": 3,
            "response_time_avg": 2.5,
            "uptime": 99.8
        }
        
        # Configurar servicios para reportar métricas
        real_full_system_services['redis_client'].get.return_value = json.dumps(system_metrics).encode()
        real_full_system_services['push_blob'].upload_blob.return_value = True
        
        # Crear request de reporte de salud
        health_req = Mock()
        health_req.get_json.return_value = {
            "metrics": system_metrics,
            "container_name": "test-container",
            "filename": "system_health_report.json"
        }
        
        # Ejecutar push de métricas de salud
        response = push_main(health_req)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["uploaded"] is True
        
        # Verificar que se subió el reporte de salud
        real_full_system_services['push_blob'].upload_blob.assert_called_once()
        upload_call = real_full_system_services['push_blob'].upload_blob.call_args
        uploaded_content = json.loads(upload_call[0][2])
        assert uploaded_content["active_users"] == 150
        assert uploaded_content["messages_processed"] == 1250
        assert uploaded_content["uptime"] == 99.8 

    @pytest.fixture
    def mock_whatsapp_services(self):
        """Mock de servicios de WhatsApp bot"""
        with patch('src.whatsapp_bot.whatsapp_bot.WhatsAppService') as mock_whatsapp, \
             patch('src.whatsapp_bot.whatsapp_bot.OpenAIService') as mock_openai, \
             patch('src.whatsapp_bot.whatsapp_bot.RedisService') as mock_redis, \
             patch('src.whatsapp_bot.whatsapp_bot.UserService') as mock_user, \
             patch('src.whatsapp_bot.whatsapp_bot.VisionService') as mock_vision, \
             patch('src.whatsapp_bot.whatsapp_bot.AzureBlobStorageService') as mock_blob:
            
            yield {
                'whatsapp': mock_whatsapp.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'user': mock_user.return_value,
                'vision': mock_vision.return_value,
                'blob': mock_blob.return_value
            }

    @pytest.fixture
    def mock_batch_start_services(self):
        """Mock de servicios de batch start processing"""
        with patch('src.processing.batch_start_processing.AzureBlobStorageService') as mock_blob, \
             patch('src.processing.batch_start_processing.OpenAIService') as mock_openai, \
             patch('src.processing.batch_start_processing.RedisService') as mock_redis, \
             patch('src.processing.batch_start_processing.UserService') as mock_user, \
             patch('src.processing.batch_start_processing.VisionService') as mock_vision:
            
            yield {
                'blob': mock_blob.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'user': mock_user.return_value,
                'vision': mock_vision.return_value
            }

    @pytest.fixture
    def mock_blob_trigger_services(self):
        """Mock de servicios de blob trigger processor"""
        with patch('src.processing.blob_trigger_processor.AzureBlobStorageService') as mock_blob, \
             patch('src.processing.blob_trigger_processor.OpenAIService') as mock_openai, \
             patch('src.processing.blob_trigger_processor.RedisService') as mock_redis, \
             patch('src.processing.blob_trigger_processor.UserService') as mock_user, \
             patch('src.processing.blob_trigger_processor.VisionService') as mock_vision:
            
            yield {
                'blob': mock_blob.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'user': mock_user.return_value,
                'vision': mock_vision.return_value
            }

    @pytest.fixture
    def mock_batch_push_services(self):
        """Mock de servicios de batch push results"""
        with patch('src.processing.batch_push_results.AzureBlobStorageService') as mock_blob, \
             patch('src.processing.batch_push_results.OpenAIService') as mock_openai, \
             patch('src.processing.batch_push_results.RedisService') as mock_redis, \
             patch('src.processing.batch_push_results.UserService') as mock_user, \
             patch('src.processing.batch_push_results.VisionService') as mock_vision:
            
            yield {
                'blob': mock_blob.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'user': mock_user.return_value,
                'vision': mock_vision.return_value
            }

    @pytest.fixture
    def mock_all_services(self, mock_whatsapp_services, mock_batch_start_services, 
                         mock_blob_trigger_services, mock_batch_push_services):
        """Mock de todos los servicios del sistema"""
        return {
            'whatsapp_bot': mock_whatsapp_services,
            'batch_start': mock_batch_start_services,
            'blob_trigger': mock_blob_trigger_services,
            'batch_push': mock_batch_push_services
        }

    def test_complete_document_processing_flow(self, mock_all_services):
        """Test del flujo completo de procesamiento de documentos"""
        # 1. Usuario envía mensaje para procesar documentos
        whatsapp_req = func.HttpRequest(
            method='POST',
            url='/api/whatsapp-bot',
            body=json.dumps({
                'object': 'whatsapp_business_account',
                'entry': [{
                    'changes': [{
                        'value': {
                            'messages': [{
                                'from': '1234567890',
                                'text': {'body': 'Procesa mis documentos'},
                                'timestamp': '1234567890'
                            }]
                        }
                    }]
                }]
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks para WhatsApp
        mock_all_services['whatsapp_bot']['whatsapp'].verify_webhook_signature.return_value = True
        mock_all_services['whatsapp_bot']['user'].get_or_create_user.return_value = MagicMock(phone='1234567890')
        mock_all_services['whatsapp_bot']['openai'].process_message.return_value = "Iniciando procesamiento de documentos"
        mock_all_services['whatsapp_bot']['whatsapp'].send_message.return_value = True
        
        # Act - Procesar mensaje de WhatsApp
        whatsapp_response = whatsapp_main(whatsapp_req)
        
        # Assert
        assert whatsapp_response.status_code == 200
        
        # 2. Iniciar procesamiento por lotes
        batch_req = func.HttpRequest(
            method='POST',
            url='/api/batch-start-processing',
            body=json.dumps({
                'container_name': 'user-1234567890',
                'user_phone': '1234567890'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks para batch start
        mock_all_services['batch_start']['blob'].list_blobs.return_value = ['doc1.pdf', 'doc2.pdf']
        mock_all_services['batch_start']['redis'].set_processing_status.return_value = True
        
        # Act - Iniciar procesamiento
        batch_response = batch_main(batch_req)
        
        # Assert
        assert batch_response.status_code == 200
        
        # 3. Procesar cada documento (simular blob trigger)
        blob_input = func.BlobInput(
            name='doc1.pdf',
            path='user-1234567890/doc1.pdf',
            connection='AzureWebJobsStorage'
        )
        
        # Configurar mocks para blob trigger
        mock_all_services['blob_trigger']['blob'].download_blob.return_value = b'PDF content'
        mock_all_services['blob_trigger']['vision'].extract_text_from_pdf.return_value = "Texto extraído del PDF"
        mock_all_services['blob_trigger']['openai'].process_document.return_value = "Análisis del documento"
        mock_all_services['blob_trigger']['blob'].upload_blob.return_value = True
        
        # Act - Procesar documento
        blob_main(blob_input)
        
        # Assert
        mock_all_services['blob_trigger']['blob'].download_blob.assert_called_once()
        mock_all_services['blob_trigger']['vision'].extract_text_from_pdf.assert_called_once()
        mock_all_services['blob_trigger']['openai'].process_document.assert_called_once()
        mock_all_services['blob_trigger']['blob'].upload_blob.assert_called_once()
        
        # 4. Enviar resultados al usuario
        push_req = func.HttpRequest(
            method='POST',
            url='/api/batch-push-results',
            body=json.dumps({
                'container_name': 'user-1234567890',
                'user_phone': '1234567890'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks para batch push
        mock_all_services['batch_push']['blob'].list_blobs.return_value = ['result1.json']
        mock_all_services['batch_push']['blob'].download_blob.return_value = json.dumps({
            'analysis': 'Análisis del documento completado'
        }).encode()
        mock_all_services['batch_push']['user'].get_user_by_phone.return_value = MagicMock(phone='1234567890')
        
        # Act - Enviar resultados
        push_response = push_main(push_req)
        
        # Assert
        assert push_response.status_code == 200

    def test_error_handling_integration(self, mock_all_services):
        """Test de manejo de errores en el sistema completo"""
        # Simular error en el procesamiento de documentos
        blob_input = func.BlobInput(
            name='error-doc.pdf',
            path='user-1234567890/error-doc.pdf',
            connection='AzureWebJobsStorage'
        )
        
        # Configurar mocks para simular error
        mock_all_services['blob_trigger']['blob'].download_blob.side_effect = Exception("Error de descarga")
        
        # Act & Assert
        with pytest.raises(Exception):
            blob_main(blob_input)

    def test_concurrent_processing_integration(self, mock_all_services):
        """Test de procesamiento concurrente"""
        # Simular múltiples documentos siendo procesados simultáneamente
        documents = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
        
        # Configurar mocks para batch start
        mock_all_services['batch_start']['blob'].list_blobs.return_value = documents
        mock_all_services['batch_start']['redis'].set_processing_status.return_value = True
        
        # Act - Iniciar procesamiento de múltiples documentos
        batch_req = func.HttpRequest(
            method='POST',
            url='/api/batch-start-processing',
            body=json.dumps({
                'container_name': 'user-1234567890',
                'user_phone': '1234567890'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        batch_response = batch_main(batch_req)
        
        # Assert
        assert batch_response.status_code == 200
        mock_all_services['batch_start']['blob'].list_blobs.assert_called_once_with('user-1234567890')

    def test_user_session_management_integration(self, mock_all_services):
        """Test de gestión de sesiones de usuario"""
        # Simular múltiples interacciones del mismo usuario
        user_phone = '1234567890'
        
        # Primera interacción
        whatsapp_req1 = func.HttpRequest(
            method='POST',
            url='/api/whatsapp-bot',
            body=json.dumps({
                'object': 'whatsapp_business_account',
                'entry': [{
                    'changes': [{
                        'value': {
                            'messages': [{
                                'from': user_phone,
                                'text': {'body': 'Hola'},
                                'timestamp': '1234567890'
                            }]
                        }
                    }]
                }]
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks
        mock_all_services['whatsapp_bot']['whatsapp'].verify_webhook_signature.return_value = True
        mock_all_services['whatsapp_bot']['user'].get_or_create_user.return_value = MagicMock(phone=user_phone)
        mock_all_services['whatsapp_bot']['openai'].process_message.return_value = "Hola, ¿en qué puedo ayudarte?"
        mock_all_services['whatsapp_bot']['whatsapp'].send_message.return_value = True
        
        # Act
        response1 = whatsapp_main(whatsapp_req1)
        
        # Assert
        assert response1.status_code == 200
        mock_all_services['whatsapp_bot']['user'].get_or_create_user.assert_called_once_with(user_phone) 
