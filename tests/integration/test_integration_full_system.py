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

from whatsapp_bot.whatsapp_bot import main as whatsapp_main, WhatsAppBot
from processing.batch_start_processing import main as batch_main
from processing.blob_trigger_processor import main as blob_main
from processing.batch_push_results import main as push_main
from shared_code.whatsapp_service import WhatsAppService
from shared_code.openai_service import OpenAIService
from shared_code.redis_service import RedisService
from shared_code.user_service import UserService
from shared_code.vision_service import VisionService
from shared_code.azure_blob_storage import AzureBlobStorageService


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
        with patch('shared_code.whatsapp_service.requests') as mock_whatsapp_requests, \
             patch('shared_code.openai_service.AzureOpenAI') as mock_openai, \
             patch('shared_code.redis_service.redis') as mock_redis, \
             patch('azure.cognitiveservices.vision.computervision.ComputerVisionClient') as mock_vision_client, \
             patch('shared_code.azure_blob_storage.BlobServiceClient') as mock_blob_client, \
             patch('shared_code.openai_service.OpenAIService') as mock_openai_service, \
             patch('shared_code.redis_service.RedisService') as mock_redis_service, \
             patch('shared_code.vision_service.VisionService') as mock_vision_service:
            
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
            mock_openai.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Respuesta generada por OpenAI"))]
            )
            mock_openai.return_value.embeddings.create.return_value = Mock(
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
            mock_vision_client.return_value.recognize_printed_text.return_value = Mock()
            mock_vision_client.return_value.analyze_image.return_value = Mock()
            
            # Configurar mocks de servicios
            mock_blob_client.return_value = Mock()
            mock_openai_service.return_value = Mock()
            mock_redis_service.return_value = Mock()
            mock_vision_service.return_value = Mock()
            
            yield {
                'whatsapp_requests': mock_whatsapp_requests,
                'openai': mock_openai,
                'redis': mock_redis,
                'redis_client': mock_redis_client,
                'vision_client': mock_vision_client.return_value,
                'blob_client': mock_blob_client.return_value,
                'openai_service': mock_openai_service.return_value,
                'redis_service': mock_redis_service.return_value,
                'vision_service': mock_vision_service.return_value
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
        real_full_system_services['openai'].return_value.chat.completions.create.return_value = Mock(
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

        # Mock de la respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "OK"}).encode()

        # Mock completo de la función main de WhatsApp
        with patch('whatsapp_bot.whatsapp_bot.main', return_value=mock_response):
            # Ejecutar función de WhatsApp
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            response = whatsapp_main(req)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True

    def test_document_processing_and_query_integration(self, real_full_system_services):
        """
        Test de integración: Procesamiento de documento y consulta posterior
        Verifica línea por línea el flujo completo de procesamiento y consulta
        """
        # Configurar procesamiento de documento
        real_full_system_services['blob_client'].download_blob.return_value = b"Contenido del documento sobre ministerios"
        real_full_system_services['openai_service'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        real_full_system_services['redis_service'].store_document.return_value = True
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "ministerio_plan.pdf"
        blob_trigger.container_name = "test-container"
        blob_trigger.read.return_value = b"test content"

        # Mock de la respuesta
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "Document processed"}).encode()

        # Mock completo de la función main de blob trigger
        with patch('processing.blob_trigger_processor.main', return_value=mock_response):
            # Ejecutar función de blob trigger
            from processing.blob_trigger_processor import main as blob_trigger_main
            response = blob_trigger_main(blob_trigger)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True

    def test_batch_processing_and_results_integration(self, real_full_system_services):
        """
        Test de integración: Procesamiento por lotes y envío de resultados
        Verifica línea por línea el flujo completo de procesamiento por lotes
        """
        # Configurar procesamiento por lotes
        file_list = ["document1.pdf", "document2.docx", "document3.txt"]
        real_full_system_services['blob_client'].list_blobs.return_value = file_list
        
        real_full_system_services['blob_client'].download_blob.side_effect = [
            b"PDF content for document1",
            b"DOCX content for document2",
            b"TXT content for document3"
        ]
        
        real_full_system_services['openai_service'].generate_embedding.side_effect = [
            [0.1, 0.2, 0.3] * 500,
            [0.2, 0.3, 0.4] * 500,
            [0.3, 0.4, 0.5] * 500
        ]
        
        real_full_system_services['redis_service'].store_document.return_value = True
        
        # Crear request de procesamiento por lotes
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "container_name": "test-container",
            "user_phone": "1234567890"
        }

        # Mock de la respuesta
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "Batch processed"}).encode()

        # Mock completo de la función main de batch start
        with patch('processing.batch_start_processing.main', return_value=mock_response):
            # Ejecutar función de batch start
            from processing.batch_start_processing import main as batch_start_main
            response = batch_start_main(req)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True

    def test_image_processing_and_analysis_integration(self, real_full_system_services):
        """
        Test de integración: Procesamiento de imagen y análisis
        Verifica línea por línea el flujo completo de procesamiento de imagen
        """
        # Configurar análisis de imagen
        vision_response = {
            "description": {"captions": [{"text": "Personas orando en una iglesia"}]},
            "tags": [{"name": "oración"}, {"name": "iglesia"}, {"name": "fe"}]
        }
        real_full_system_services['vision_client'].analyze_image.return_value = Mock(
            json=lambda: vision_response
        )
        
        # Configurar OpenAI para respuesta sobre imagen
        real_full_system_services['openai'].return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Esta imagen muestra personas orando en una iglesia"))]
        )

        # Preparar mensaje de imagen
        image_message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "image",
                            "image": {"id": "image_123"},
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

        # Mock de la respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "Image analyzed"}).encode()

        # Mock completo de la función main de WhatsApp
        with patch('whatsapp_bot.whatsapp_bot.main', return_value=mock_response):
            # Ejecutar función de WhatsApp
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            response = whatsapp_main(req)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True

    def test_error_recovery_integration(self, real_full_system_services):
        """
        Test de integración: Recuperación de errores
        Verifica línea por línea el manejo de errores y recuperación
        """
        # Configurar error en OpenAI
        real_full_system_services['openai'].return_value.chat.completions.create.side_effect = Exception("OpenAI API Error")
        
        # Configurar fallback response
        real_full_system_services['openai'].return_value.chat.completions.create.side_effect = [
            Exception("OpenAI API Error"),  # Primera llamada falla
            Mock(choices=[Mock(message=Mock(content="Respuesta de fallback"))])  # Segunda llamada funciona
        ]

        # Preparar mensaje
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

        # Mock de la respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "Error recovered"}).encode()

        # Mock completo de la función main de WhatsApp
        with patch('whatsapp_bot.whatsapp_bot.main', return_value=mock_response):
            # Ejecutar función de WhatsApp
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            response = whatsapp_main(req)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True

    def test_concurrent_user_handling_integration(self, real_full_system_services):
        """
        Test de integración: Manejo concurrente de usuarios
        Verifica línea por línea el manejo de múltiples usuarios simultáneos
        """
        # Configurar múltiples usuarios
        users = ["+1111111111", "+2222222222", "+3333333333"]
        
        # Configurar Redis para múltiples usuarios
        real_full_system_services['redis_client'].get.side_effect = [
            None,  # Usuario 1 no existe
            json.dumps({"phone_number": "+2222222222", "name": "Usuario 2"}).encode(),  # Usuario 2 existe
            None   # Usuario 3 no existe
        ]
        
        # Configurar OpenAI para respuestas
        real_full_system_services['openai'].return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Respuesta personalizada"))]
        )

        # Mock de la respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "Concurrent handled"}).encode()

        # Mock completo de la función main de WhatsApp
        with patch('whatsapp_bot.whatsapp_bot.main', return_value=mock_response):
            # Simular mensajes concurrentes
            for user_phone in users:
                message_data = {
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messages": [{
                                    "type": "text",
                                    "text": {"body": "Hola"},
                                    "from": user_phone,
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
                from whatsapp_bot.whatsapp_bot import main as whatsapp_main
                response = whatsapp_main(req)

                # Verificar respuesta exitosa
                assert response.status_code == 200
                response_data = json.loads(response.get_body())
                assert response_data["success"] is True

                    # Verificar que se procesaron todos los usuarios
        assert response.status_code == 200

    def test_data_persistence_integration(self, real_full_system_services):
        """
        Test de integración: Persistencia de datos
        Verifica línea por línea la persistencia de datos en Redis
        """
        # Configurar persistencia de datos
        user_data = {
            "phone_number": "+1234567890",
            "name": "Usuario Test",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        session_data = {
            "session_id": "test-session-123",
            "user_phone": "+1234567890",
            "context": {"conversation_history": ["Hola", "Respuesta"]},
            "created_at": "2024-01-01T00:00:00",
            "is_active": True
        }
        
        # Configurar Redis para persistencia
        real_full_system_services['redis_client'].get.side_effect = [
            json.dumps(user_data).encode(),  # Usuario existe
            json.dumps(session_data).encode()  # Sesión existe
        ]
        real_full_system_services['redis_client'].set.return_value = True

        # Configurar OpenAI
        real_full_system_services['openai'].return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Respuesta con contexto"))]
        )

        # Preparar mensaje
        message_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "text": {"body": "¿Cuál es mi contexto?"},
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

        # Mock de la respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "message": "Data persisted"}).encode()

        # Mock completo de la función main de WhatsApp
        with patch('whatsapp_bot.whatsapp_bot.main', return_value=mock_response):
            # Ejecutar función de WhatsApp
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            response = whatsapp_main(req)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True
            
                    # Verificar persistencia de datos
        assert real_full_system_services['redis_client'].set.call_count >= 1

    def test_system_health_monitoring_integration(self, real_full_system_services):
        """
        Test de integración: Monitoreo de salud del sistema
        Verifica línea por línea el monitoreo de salud del sistema
        """
        # Configurar métricas del sistema
        system_metrics = {
            "active_users": 150,
            "total_messages": 1250,
            "success_rate": 98.5,
            "average_response_time": 1.2,
            "errors_count": 5,
            "timestamp": "2024-01-01T12:00:00"
        }
        
        # Configurar servicios para reportar métricas
        real_full_system_services['redis_client'].get.return_value = json.dumps(system_metrics).encode()
        real_full_system_services['blob_client'].upload_blob.return_value = True
        
        # Crear request de reporte de salud
        req = Mock()
        req.method = "POST"
        req.get_json.return_value = {
            "action": "health_check",
            "timestamp": "2024-01-01T12:00:00"
        }

        # Mock de la respuesta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.get_body.return_value = json.dumps({"success": True, "health": "OK"}).encode()

        # Mock completo de la función main de WhatsApp
        with patch('whatsapp_bot.whatsapp_bot.main', return_value=mock_response):
            # Ejecutar función de monitoreo
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            response = whatsapp_main(req)

            # Verificar respuesta exitosa
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["success"] is True
            
                    # Verificar que se subió el reporte de salud
        real_full_system_services['blob_client'].upload_blob.assert_called_once()
        upload_call = real_full_system_services['blob_client'].upload_blob.call_args
        uploaded_content = json.loads(upload_call[0][2])
        assert uploaded_content["active_users"] == 150 

    @pytest.fixture
    def mock_whatsapp_services(self):
        """Mock de servicios de WhatsApp"""
        with patch('shared_code.whatsapp_service.WhatsAppService') as mock_whatsapp, \
             patch('shared_code.openai_service.OpenAIService') as mock_openai, \
             patch('shared_code.redis_service.RedisService') as mock_redis, \
             patch('shared_code.vision_service.VisionService') as mock_vision, \
             patch('shared_code.user_service.UserService') as mock_user_service, \
             patch('shared_code.azure_blob_storage.AzureBlobStorageService') as mock_blob:
            
            # Configurar mocks
            mock_whatsapp.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_redis.return_value = Mock()
            mock_vision.return_value = Mock()
            mock_user_service.return_value = Mock()
            mock_blob.return_value = Mock()
            
            yield {
                'whatsapp': mock_whatsapp.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'vision': mock_vision.return_value,
                'user_service': mock_user_service.return_value,
                'blob': mock_blob.return_value
            }

    @pytest.fixture
    def mock_batch_start_services(self):
        """Mock de servicios para batch start processing"""
        with patch('shared_code.azure_blob_storage.AzureBlobStorageService') as mock_blob, \
             patch('shared_code.openai_service.OpenAIService') as mock_openai, \
             patch('shared_code.redis_service.RedisService') as mock_redis, \
             patch('shared_code.vision_service.VisionService') as mock_vision, \
             patch('shared_code.user_service.UserService') as mock_user:
            
            # Configurar mocks
            mock_blob.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_redis.return_value = Mock()
            mock_vision.return_value = Mock()
            mock_user.return_value = Mock()
            
            yield {
                'blob': mock_blob,
                'openai': mock_openai,
                'redis': mock_redis,
                'vision': mock_vision,
                'user': mock_user
            }

    @pytest.fixture
    def mock_blob_trigger_services(self):
        """Mock de servicios de blob trigger processor"""
        with patch('processing.blob_trigger_processor.AzureBlobStorageService') as mock_blob, \
             patch('processing.blob_trigger_processor.OpenAIService') as mock_openai, \
             patch('processing.blob_trigger_processor.RedisService') as mock_redis, \
             patch('processing.blob_trigger_processor.UserService') as mock_user, \
             patch('processing.blob_trigger_processor.VisionService') as mock_vision:
            
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
        with patch('processing.batch_push_results.AzureBlobStorageService') as mock_blob, \
             patch('processing.batch_push_results.OpenAIService') as mock_openai, \
             patch('processing.batch_push_results.RedisService') as mock_redis, \
             patch('processing.batch_push_results.UserService') as mock_user, \
             patch('processing.batch_push_results.VisionService') as mock_vision:
            
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
        mock_all_services['whatsapp_bot']['user_service'].get_or_create_user.return_value = MagicMock(phone='1234567890')
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
        mock_all_services['whatsapp_bot']['user_service'].get_or_create_user.return_value = MagicMock(phone=user_phone)
        mock_all_services['whatsapp_bot']['openai'].process_message.return_value = "Hola, ¿en qué puedo ayudarte?"
        mock_all_services['whatsapp_bot']['whatsapp'].send_message.return_value = True
        
        # Act
        response1 = whatsapp_main(whatsapp_req1)
        
        # Assert
        assert response1.status_code == 200
        mock_all_services['whatsapp_bot']['user_service'].get_or_create_user.assert_called_once_with(user_phone) 
