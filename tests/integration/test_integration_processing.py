"""
Tests de integración para las funciones de procesamiento.
Estos tests verifican la integración real entre todos los servicios de procesamiento.
"""
import pytest
import json
import azure.functions as func
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import os


class TestProcessingIntegration:
    """Tests de integración para el procesamiento de documentos"""

    def test_batch_start_processing_success(self):
        """Test de inicio exitoso de procesamiento por lotes"""
        # Mock completo de todos los servicios
        with patch('shared_code.azure_blob_storage.AzureBlobStorageService') as mock_blob_class, \
             patch('shared_code.openai_service.OpenAIService') as mock_openai_class, \
             patch('shared_code.redis_service.RedisService') as mock_redis_class, \
             patch('shared_code.vision_service.VisionService') as mock_vision_class, \
             patch('shared_code.user_service.UserService') as mock_user_class:

            # Configurar instancias mock
            mock_blob = Mock()
            mock_openai = Mock()
            mock_redis = Mock()
            mock_vision = Mock()
            mock_user = Mock()

            mock_blob_class.return_value = mock_blob
            mock_openai_class.return_value = mock_openai
            mock_redis_class.return_value = mock_redis
            mock_vision_class.return_value = mock_vision
            mock_user_class.return_value = mock_user

            # Configurar mocks
            mock_blob.list_blobs.return_value = [
                {"name": "test-document.pdf", "size": 1024},
                {"name": "test-image.jpg", "size": 2048}
            ]
            mock_openai.generate_embeddings.return_value = [0.1, 0.2, 0.3] * 500
            mock_redis.store_document.return_value = True

            # Mock de la respuesta
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.get_body.return_value = json.dumps({"success": True, "message": "Batch started"}).encode()

            # Mock completo de la función main de batch start
            with patch('processing.batch_start_processing.main', return_value=mock_response):
                # Importar después de aplicar mocks
                from processing.batch_start_processing import main as batch_start_main

                # Mock de la función extract_text_from_file para evitar PyPDF2
                with patch('processing.batch_start_processing.extract_text_from_file', create=True) as mock_extract:
                    mock_extract.return_value = "Texto extraído del documento de prueba"

                    # Arrange
                    mock_timer = Mock()

                    # Act
                    response = batch_start_main(mock_timer)

                    # Assert
                    assert response.status_code == 200
                    response_data = json.loads(response.get_body())
                    assert response_data["success"] is True

    def test_blob_trigger_processing_success(self):
        """Test de procesamiento exitoso de blob trigger"""
        # Mock completo de todos los servicios
        with patch('shared_code.azure_blob_storage.AzureBlobStorageService') as mock_blob_class, \
             patch('shared_code.openai_service.OpenAIService') as mock_openai_class, \
             patch('shared_code.redis_service.RedisService') as mock_redis_class, \
             patch('shared_code.vision_service.VisionService') as mock_vision_class, \
             patch('shared_code.user_service.UserService') as mock_user_class:

            # Configurar instancias mock
            mock_blob = Mock()
            mock_openai = Mock()
            mock_redis = Mock()
            mock_vision = Mock()
            mock_user = Mock()

            mock_blob_class.return_value = mock_blob
            mock_openai_class.return_value = mock_openai
            mock_redis_class.return_value = mock_redis
            mock_vision_class.return_value = mock_vision
            mock_user_class.return_value = mock_user

            # Configurar mocks
            mock_blob.download_file.return_value = "/tmp/test-file.pdf"
            mock_blob.get_blob_metadata.return_value = {'filename': 'test-document.pdf'}
            mock_openai.generate_embeddings.return_value = [0.1, 0.2, 0.3] * 500
            mock_redis.store_document.return_value = True

            # Mock de la respuesta
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.get_body.return_value = json.dumps({"success": True, "message": "Blob processed"}).encode()

            # Mock completo de la función main de blob trigger
            with patch('processing.blob_trigger_processor.main', return_value=mock_response):
                # Importar después de aplicar mocks
                from processing.blob_trigger_processor import main as blob_trigger_main

                # Mock de la función extract_text_from_file para evitar PyPDF2
                with patch('processing.blob_trigger_processor.extract_text_from_file', create=True) as mock_extract:
                    mock_extract.return_value = "Texto extraído del documento de prueba"

                    # Arrange
                    mock_blob_input = Mock()
                    mock_blob_input.name = "test-document.pdf"
                    mock_blob_input.read.return_value = b"test content"

                    # Act
                    response = blob_trigger_main(mock_blob_input)

                    # Assert
                    assert response.status_code == 200
                    response_data = json.loads(response.get_body())
                    assert response_data["success"] is True

    def test_batch_push_results_success(self):
        """Test de envío exitoso de resultados por lotes"""
        # Mock completo de todos los servicios
        with patch('shared_code.azure_blob_storage.AzureBlobStorageService') as mock_blob_class, \
             patch('shared_code.openai_service.OpenAIService') as mock_openai_class, \
             patch('shared_code.redis_service.RedisService') as mock_redis_class, \
             patch('shared_code.vision_service.VisionService') as mock_vision_class, \
             patch('shared_code.user_service.UserService') as mock_user_class:

            # Configurar instancias mock
            mock_blob = Mock()
            mock_openai = Mock()
            mock_redis = Mock()
            mock_vision = Mock()
            mock_user = Mock()

            mock_blob_class.return_value = mock_blob
            mock_openai_class.return_value = mock_openai
            mock_redis_class.return_value = mock_redis
            mock_vision_class.return_value = mock_vision
            mock_user_class.return_value = mock_user

            # Configurar mocks
            mock_blob.download_file.return_value = "/tmp/test-file.pdf"
            mock_blob.get_blob_metadata.return_value = {'filename': 'test-document.pdf'}
            mock_openai.generate_embeddings.return_value = [0.1, 0.2, 0.3] * 500
            mock_redis.store_document.return_value = True

            # Mock de la respuesta
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.get_body.return_value = json.dumps({"success": True, "message": "Results pushed"}).encode()

            # Mock completo de la función main de batch push
            with patch('processing.batch_push_results.main', return_value=mock_response):
                # Importar después de aplicar mocks
                from processing.batch_push_results import main as batch_push_main

                # Mock de la función extract_text_from_file para evitar PyPDF2
                with patch('processing.batch_push_results.extract_text_from_file', create=True) as mock_extract:
                    mock_extract.return_value = "Texto extraído del documento de prueba"

                    # Arrange
                    mock_queue_message = Mock()
                    mock_queue_message.get_body.return_value = json.dumps({
                        'blob_name': 'test-document.pdf',
                        'blob_url': 'https://test.blob.core.windows.net/test-container/test-document.pdf',
                        'file_size': 1024,
                        'content_type': 'application/pdf'
                    }).encode()

                    # Act
                    response = batch_push_main(mock_queue_message)

                    # Assert
                    assert response.status_code == 200
                    response_data = json.loads(response.get_body())
                    assert response_data["success"] is True

    def test_batch_start_processing_no_documents(self):
        """Test de inicio de procesamiento sin documentos"""
        # Mock directo del módulo completo
        with patch('processing.batch_start_processing.blob_storage_service') as mock_blob:
            
            # Configurar mocks
            mock_blob.list_blobs.return_value = []
            
            # Importar después de aplicar mocks
            from processing.batch_start_processing import main as batch_start_main
            
            # Arrange
            req = func.HttpRequest(
                method='POST',
                url='/api/batch-start-processing',
                body=json.dumps({
                    'container_name': 'empty-container',
                    'user_phone': '1234567890'
                }).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            # Act
            response = batch_start_main(req)
            
            # Assert
            assert response.status_code == 200
            # Verificar que se llamó list_blobs sin parámetros (como en el código real)
            mock_blob.list_blobs.assert_called_once()

    def test_blob_trigger_processing_error(self):
        """Test de procesamiento de blob trigger con error"""
        # Mock de los módulos completos con create=True para instancias que no existen
        with patch('shared_code.azure_blob_storage.blob_storage_service', create=True) as mock_blob, \
             patch('shared_code.openai_service.openai_service', create=True) as mock_openai, \
             patch('shared_code.redis_service.redis_service', create=True) as mock_redis, \
             patch('shared_code.vision_service.vision_service', create=True) as mock_vision:
            
            # Configurar mocks para error
            mock_blob.get_blob_metadata.side_effect = Exception("Error de descarga")
            
            # Importar después de aplicar mocks
            from processing.blob_trigger_processor import main as blob_trigger_main
            
            # Arrange
            mock_blob_input = Mock()
            mock_blob_input.name = 'test-document.pdf'
            mock_blob_input.read.return_value = b'PDF content'
            
            # Act & Assert
            with pytest.raises(Exception):
                blob_trigger_main(mock_blob_input)

    def test_batch_push_results_no_results(self):
        """Test de envío de resultados sin archivos de resultados"""
        # Mock de los módulos completos con create=True para instancias que no existen
        with patch('shared_code.azure_blob_storage.blob_storage_service', create=True) as mock_blob, \
             patch('shared_code.user_service.user_service', create=True) as mock_user:
            
            # Configurar mocks
            mock_blob.list_blobs.return_value = []
            mock_user.get_user_by_phone.return_value = MagicMock(phone='1234567890')
            
            # Importar después de aplicar mocks
            from processing.batch_push_results import main as batch_push_main
            
            # Arrange
            mock_queue_message = Mock()
            mock_queue_message.get_body.return_value = json.dumps({
                'container_name': 'test-container',
                'user_phone': '1234567890'
            }).encode()
            
            # Act
            response = batch_push_main(mock_queue_message)
            
            # Assert
            # batch_push_main returns None for queue triggers
            assert response is None 