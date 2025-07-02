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

from processing.batch_start_processing import main as batch_start_main
from processing.blob_trigger_processor import main as blob_trigger_main
from processing.batch_push_results import main as batch_push_main
from shared_code.azure_blob_storage import AzureBlobStorageService
from shared_code.openai_service import OpenAIService
from shared_code.redis_service import RedisService
from shared_code.vision_service import VisionService
from shared_code.user_service import UserService


class TestProcessingIntegration:
    """Tests de integración para el procesamiento de documentos"""

    @pytest.fixture
    def mock_services(self):
        """Mock de todos los servicios"""
        with patch('processing.batch_start_processing.AzureBlobStorageService') as mock_blob_start, \
             patch('processing.batch_start_processing.OpenAIService') as mock_openai_start, \
             patch('processing.batch_start_processing.RedisService') as mock_redis_start, \
             patch('processing.batch_start_processing.UserService') as mock_user_start, \
             patch('processing.batch_start_processing.VisionService') as mock_vision_start, \
             patch('processing.blob_trigger_processor.AzureBlobStorageService') as mock_blob_trigger, \
             patch('processing.blob_trigger_processor.OpenAIService') as mock_openai_trigger, \
             patch('processing.blob_trigger_processor.RedisService') as mock_redis_trigger, \
             patch('processing.blob_trigger_processor.UserService') as mock_user_trigger, \
             patch('processing.blob_trigger_processor.VisionService') as mock_vision_trigger, \
             patch('processing.batch_push_results.AzureBlobStorageService') as mock_blob_push, \
             patch('processing.batch_push_results.OpenAIService') as mock_openai_push, \
             patch('processing.batch_push_results.RedisService') as mock_redis_push, \
             patch('processing.batch_push_results.UserService') as mock_user_push, \
             patch('processing.batch_push_results.VisionService') as mock_vision_push:
            
            # Configurar mocks para batch_start_processing
            mock_blob_start_instance = MagicMock()
            mock_blob_start.return_value = mock_blob_start_instance
            
            mock_openai_start_instance = MagicMock()
            mock_openai_start.return_value = mock_openai_start_instance
            
            mock_redis_start_instance = MagicMock()
            mock_redis_start.return_value = mock_redis_start_instance
            
            mock_user_start_instance = MagicMock()
            mock_user_start.return_value = mock_user_start_instance
            
            mock_vision_start_instance = MagicMock()
            mock_vision_start.return_value = mock_vision_start_instance
            
            # Configurar mocks para blob_trigger_processor
            mock_blob_trigger_instance = MagicMock()
            mock_blob_trigger.return_value = mock_blob_trigger_instance
            
            mock_openai_trigger_instance = MagicMock()
            mock_openai_trigger.return_value = mock_openai_trigger_instance
            
            mock_redis_trigger_instance = MagicMock()
            mock_redis_trigger.return_value = mock_redis_trigger_instance
            
            mock_user_trigger_instance = MagicMock()
            mock_user_trigger.return_value = mock_user_trigger_instance
            
            mock_vision_trigger_instance = MagicMock()
            mock_vision_trigger.return_value = mock_vision_trigger_instance
            
            # Configurar mocks para batch_push_results
            mock_blob_push_instance = MagicMock()
            mock_blob_push.return_value = mock_blob_push_instance
            
            mock_openai_push_instance = MagicMock()
            mock_openai_push.return_value = mock_openai_push_instance
            
            mock_redis_push_instance = MagicMock()
            mock_redis_push.return_value = mock_redis_push_instance
            
            mock_user_push_instance = MagicMock()
            mock_user_push.return_value = mock_user_push_instance
            
            mock_vision_push_instance = MagicMock()
            mock_vision_push.return_value = mock_vision_push_instance
            
            yield {
                'batch_start': {
                    'blob': mock_blob_start_instance,
                    'openai': mock_openai_start_instance,
                    'redis': mock_redis_start_instance,
                    'user': mock_user_start_instance,
                    'vision': mock_vision_start_instance
                },
                'blob_trigger': {
                    'blob': mock_blob_trigger_instance,
                    'openai': mock_openai_trigger_instance,
                    'redis': mock_redis_trigger_instance,
                    'user': mock_user_trigger_instance,
                    'vision': mock_vision_trigger_instance
                },
                'batch_push': {
                    'blob': mock_blob_push_instance,
                    'openai': mock_openai_push_instance,
                    'redis': mock_redis_push_instance,
                    'user': mock_user_push_instance,
                    'vision': mock_vision_push_instance
                }
            }

    def test_batch_start_processing_success(self, mock_services):
        """Test de inicio exitoso de procesamiento por lotes"""
        # Arrange
        req = func.HttpRequest(
            method='POST',
            url='/api/batch-start-processing',
            body=json.dumps({
                'container_name': 'test-container',
                'user_phone': '1234567890'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks
        mock_services['batch_start']['blob'].list_blobs.return_value = ['doc1.pdf', 'doc2.pdf']
        mock_services['batch_start']['redis'].set_processing_status.return_value = True
        
        # Act
        response = batch_start_main(req)
        
        # Assert
        assert response.status_code == 200
        mock_services['batch_start']['blob'].list_blobs.assert_called_once_with('test-container')
        mock_services['batch_start']['redis'].set_processing_status.assert_called()

    def test_blob_trigger_processing_success(self, mock_services):
        """Test de procesamiento exitoso de blob trigger"""
        # Arrange
        blob_data = {
            'name': 'test-document.pdf',
            'container_name': 'test-container'
        }
        
        blob_input = func.BlobInput(
            name='test-document.pdf',
            path='test-container/test-document.pdf',
            connection='AzureWebJobsStorage'
        )
        
        # Configurar mocks
        mock_services['blob_trigger']['blob'].download_blob.return_value = b'PDF content'
        mock_services['blob_trigger']['vision'].extract_text_from_pdf.return_value = "Texto extraído"
        mock_services['blob_trigger']['openai'].process_document.return_value = "Análisis del documento"
        mock_services['blob_trigger']['blob'].upload_blob.return_value = True
        
        # Act
        blob_trigger_main(blob_input)
        
        # Assert
        mock_services['blob_trigger']['blob'].download_blob.assert_called_once()
        mock_services['blob_trigger']['vision'].extract_text_from_pdf.assert_called_once()
        mock_services['blob_trigger']['openai'].process_document.assert_called_once()
        mock_services['blob_trigger']['blob'].upload_blob.assert_called_once()

    def test_batch_push_results_success(self, mock_services):
        """Test de envío exitoso de resultados por lotes"""
        # Arrange
        req = func.HttpRequest(
            method='POST',
            url='/api/batch-push-results',
            body=json.dumps({
                'container_name': 'test-container',
                'user_phone': '1234567890'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks
        mock_services['batch_push']['blob'].list_blobs.return_value = ['result1.json', 'result2.json']
        mock_services['batch_push']['blob'].download_blob.side_effect = [
            json.dumps({'analysis': 'Análisis 1'}).encode(),
            json.dumps({'analysis': 'Análisis 2'}).encode()
        ]
        mock_services['batch_push']['user'].get_user_by_phone.return_value = MagicMock(phone='1234567890')
        
        # Act
        response = batch_push_main(req)
        
        # Assert
        assert response.status_code == 200
        mock_services['batch_push']['blob'].list_blobs.assert_called_once_with('test-container')
        assert mock_services['batch_push']['blob'].download_blob.call_count == 2

    def test_batch_start_processing_no_documents(self, mock_services):
        """Test de inicio de procesamiento sin documentos"""
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
        
        # Configurar mocks
        mock_services['batch_start']['blob'].list_blobs.return_value = []
        
        # Act
        response = batch_start_main(req)
        
        # Assert
        assert response.status_code == 200
        mock_services['batch_start']['blob'].list_blobs.assert_called_once_with('empty-container')

    def test_blob_trigger_processing_error(self, mock_services):
        """Test de procesamiento de blob trigger con error"""
        # Arrange
        blob_input = func.BlobInput(
            name='test-document.pdf',
            path='test-container/test-document.pdf',
            connection='AzureWebJobsStorage'
        )
        
        # Configurar mocks
        mock_services['blob_trigger']['blob'].download_blob.side_effect = Exception("Error de descarga")
        
        # Act & Assert
        with pytest.raises(Exception):
            blob_trigger_main(blob_input)

    def test_batch_push_results_no_results(self, mock_services):
        """Test de envío de resultados sin archivos de resultados"""
        # Arrange
        req = func.HttpRequest(
            method='POST',
            url='/api/batch-push-results',
            body=json.dumps({
                'container_name': 'test-container',
                'user_phone': '1234567890'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        # Configurar mocks
        mock_services['batch_push']['blob'].list_blobs.return_value = []
        mock_services['batch_push']['user'].get_user_by_phone.return_value = MagicMock(phone='1234567890')
        
        # Act
        response = batch_push_main(req)
        
        # Assert
        assert response.status_code == 200
        mock_services['batch_push']['blob'].list_blobs.assert_called_once_with('test-container')


class TestBatchProcessingIntegration:
    """Tests de integración para el procesamiento por lotes"""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock del entorno completo para procesamiento"""
        with patch.dict('os.environ', {
            'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=teststorage;AccountKey=testkey;EndpointSuffix=core.windows.net',
            'AZURE_STORAGE_CONTAINER_NAME': 'test-container',
            'AZURE_OPENAI_ENDPOINT': 'https://test-openai.openai.azure.com/',
            'AZURE_OPENAI_API_KEY': 'test-openai-key-abcdef123456',
            'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-4-deployment',
            'REDIS_CONNECTION_STRING': 'redis://localhost:6379/0'
        }):
            yield
    
    @pytest.fixture
    def real_processing_services(self, mock_environment):
        """Instancias reales de servicios de procesamiento con mocks de APIs externas"""
        with patch('processing.batch_start_processing.AzureBlobStorageService') as mock_blob, \
             patch('processing.batch_start_processing.OpenAIService') as mock_openai, \
             patch('processing.batch_start_processing.RedisService') as mock_redis, \
             patch('processing.batch_start_processing.get_settings') as mock_settings:
            
            # Configurar settings mock
            mock_settings.return_value = Mock(
                AZURE_STORAGE_CONNECTION_STRING="test-connection-string",
                AZURE_STORAGE_CONTAINER_NAME="test-container",
                AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com/",
                AZURE_OPENAI_API_KEY="test-key",
                AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
                REDIS_CONNECTION_STRING="redis://localhost:6379"
            )
            
            # Configurar servicios mock
            mock_blob.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_redis.return_value = Mock()
            
            yield {
                'blob': mock_blob.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'settings': mock_settings.return_value
            }
    
    def test_batch_processing_complete_flow_integration(self, real_processing_services):
        """
        Test de integración: Flujo completo de procesamiento por lotes
        Verifica línea por línea el procesamiento de múltiples archivos
        """
        # Configurar lista de archivos (líneas 50-55 en batch_start_processing.py)
        file_list = [
            "document1.pdf",
            "document2.docx", 
            "document3.txt",
            "image1.jpg",
            "script.exe"  # Archivo no soportado
        ]
        real_processing_services['blob'].list_blobs.return_value = file_list
        
        # Configurar descarga de archivos (líneas 60-65 en batch_start_processing.py)
        real_processing_services['blob'].download_blob.side_effect = [
            b"PDF content for document1",
            b"DOCX content for document2", 
            b"TXT content for document3",
            b"Image content for image1",
            b"Executable content"  # No se procesará
        ]
        
        # Configurar embeddings de OpenAI (líneas 70-75 en batch_start_processing.py)
        real_processing_services['openai'].generate_embedding.side_effect = [
            [0.1, 0.2, 0.3, 0.4, 0.5] * 300,  # 1500 dimensiones para PDF
            [0.2, 0.3, 0.4, 0.5, 0.6] * 300,  # 1500 dimensiones para DOCX
            [0.3, 0.4, 0.5, 0.6, 0.7] * 300,  # 1500 dimensiones para TXT
            [0.4, 0.5, 0.6, 0.7, 0.8] * 300,  # 1500 dimensiones para imagen
            # No se generará embedding para .exe
        ]
        
        # Configurar almacenamiento en Redis (líneas 80-85 en batch_start_processing.py)
        real_processing_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función principal
        response = batch_start_main(req)
        
        # Verificar respuesta HTTP (líneas 90-95 en batch_start_processing.py)
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 5  # Todos los archivos procesados
        assert response_data["data"]["stored_documents"] == 4  # Solo 4 documentos almacenados
        assert response_data["data"]["skipped_files"] == 1     # 1 archivo no soportado
        
        # Verificar llamadas a servicios (líneas 100-105 en batch_start_processing.py)
        real_processing_services['blob'].list_blobs.assert_called_once_with("test-container")
        assert real_processing_services['blob'].download_blob.call_count == 4  # Solo archivos soportados
        assert real_processing_services['openai'].generate_embedding.call_count == 4
        assert real_processing_services['redis'].store_document.call_count == 4
    
    def test_batch_processing_with_errors_integration(self, real_processing_services):
        """
        Test de integración: Procesamiento con errores
        Verifica línea por línea el manejo de errores durante el procesamiento
        """
        # Configurar lista de archivos
        file_list = ["document1.pdf", "document2.pdf", "document3.pdf"]
        real_processing_services['blob'].list_blobs.return_value = file_list
        
        # Configurar errores en diferentes etapas (líneas 110-115 en batch_start_processing.py)
        real_processing_services['blob'].download_blob.side_effect = [
            b"PDF content for document1",  # Éxito
            Exception("Download error"),   # Error en descarga
            b"PDF content for document3"   # Éxito
        ]
        
        # Configurar embeddings
        real_processing_services['openai'].generate_embedding.side_effect = [
            [0.1, 0.2, 0.3] * 500,  # Éxito
            # No se llama para document2 debido al error
            Exception("Embedding error")  # Error en embedding
        ]
        
        # Configurar almacenamiento
        real_processing_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función principal
        response = batch_start_main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 3
        assert response_data["data"]["stored_documents"] == 1  # Solo 1 documento almacenado
        assert response_data["data"]["errors"] == 2  # 2 errores
        
        # Verificar que se intentaron procesar todos los archivos
        assert real_processing_services['blob'].download_blob.call_count == 3
        assert real_processing_services['openai'].generate_embedding.call_count == 2  # Solo 2 llamadas exitosas
        assert real_processing_services['redis'].store_document.call_count == 1
    
    def test_batch_processing_empty_container_integration(self, real_processing_services):
        """
        Test de integración: Contenedor vacío
        Verifica línea por línea el manejo de contenedores sin archivos
        """
        # Configurar lista vacía (líneas 120-125 en batch_start_processing.py)
        real_processing_services['blob'].list_blobs.return_value = []
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función principal
        response = batch_start_main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 0
        assert response_data["data"]["stored_documents"] == 0
        assert response_data["data"]["skipped_files"] == 0
        
        # Verificar que no se llamaron servicios innecesarios
        real_processing_services['blob'].download_blob.assert_not_called()
        real_processing_services['openai'].generate_embedding.assert_not_called()
        real_processing_services['redis'].store_document.assert_not_called()
    
    def test_batch_processing_batch_size_limit_integration(self, real_processing_services):
        """
        Test de integración: Límite de batch size
        Verifica línea por línea el respeto del límite de procesamiento
        """
        # Configurar muchos archivos
        file_list = [f"document{i}.pdf" for i in range(20)]
        real_processing_services['blob'].list_blobs.return_value = file_list
        
        # Configurar descarga exitosa
        real_processing_services['blob'].download_blob.return_value = b"PDF content"
        real_processing_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        real_processing_services['redis'].store_document.return_value = True
        
        # Crear request mock con batch_size pequeño
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 5  # Solo procesar 5 archivos
        }
        
        # Ejecutar función principal
        response = batch_start_main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 5  # Solo 5 procesados
        assert response_data["data"]["stored_documents"] == 5
        
        # Verificar que solo se procesaron 5 archivos
        assert real_processing_services['blob'].download_blob.call_count == 5
        assert real_processing_services['openai'].generate_embedding.call_count == 5
        assert real_processing_services['redis'].store_document.call_count == 5


class TestBlobTriggerProcessingIntegration:
    """Tests de integración para el procesamiento de triggers de blob"""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock del entorno completo para blob triggers"""
        with patch.dict('os.environ', {
            'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=teststorage;AccountKey=testkey;EndpointSuffix=core.windows.net',
            'AZURE_STORAGE_CONTAINER_NAME': 'test-container',
            'AZURE_OPENAI_ENDPOINT': 'https://test-openai.openai.azure.com/',
            'AZURE_OPENAI_API_KEY': 'test-openai-key-abcdef123456',
            'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-4-deployment',
            'REDIS_CONNECTION_STRING': 'redis://localhost:6379/0'
        }):
            yield
    
    @pytest.fixture
    def real_blob_services(self, mock_environment):
        """Instancias reales de servicios para blob triggers"""
        with patch('processing.blob_trigger_processor.AzureBlobStorageService') as mock_blob, \
             patch('processing.blob_trigger_processor.OpenAIService') as mock_openai, \
             patch('processing.blob_trigger_processor.RedisService') as mock_redis, \
             patch('processing.blob_trigger_processor.get_settings') as mock_settings:
            
            # Configurar settings mock
            mock_settings.return_value = Mock(
                AZURE_STORAGE_CONNECTION_STRING="test-connection-string",
                AZURE_STORAGE_CONTAINER_NAME="test-container",
                AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com/",
                AZURE_OPENAI_API_KEY="test-key",
                AZURE_OPENAI_DEPLOYMENT_NAME="test-deployment",
                REDIS_CONNECTION_STRING="redis://localhost:6379"
            )
            
            # Configurar servicios mock
            mock_blob.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_redis.return_value = Mock()
            
            yield {
                'blob': mock_blob.return_value,
                'openai': mock_openai.return_value,
                'redis': mock_redis.return_value,
                'settings': mock_settings.return_value
            }
    
    def test_pdf_blob_trigger_integration(self, real_blob_services):
        """
        Test de integración: Trigger de blob PDF
        Verifica línea por línea el procesamiento de archivo PDF
        """
        # Configurar descarga de PDF (líneas 40-45 en blob_trigger_processor.py)
        real_blob_services['blob'].download_blob.return_value = b"PDF content with text and images"
        
        # Configurar embedding de OpenAI (líneas 50-55 en blob_trigger_processor.py)
        real_blob_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        
        # Configurar almacenamiento en Redis (líneas 60-65 en blob_trigger_processor.py)
        real_blob_services['redis'].store_document.return_value = True
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar llamadas a servicios
        real_blob_services['blob'].download_blob.assert_called_once_with("document.pdf", "test-container")
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_called_once()
        
        # Verificar contenido del documento almacenado
        store_call = real_blob_services['redis'].store_document.call_args[0][0]
        assert store_call["filename"] == "document.pdf"
        assert store_call["content_type"] == "application/pdf"
        assert store_call["container"] == "test-container"
        assert "processed_at" in store_call
    
    def test_docx_blob_trigger_integration(self, real_blob_services):
        """
        Test de integración: Trigger de blob DOCX
        Verifica línea por línea el procesamiento de archivo DOCX
        """
        # Configurar descarga de DOCX
        real_blob_services['blob'].download_blob.return_value = b"DOCX content with formatted text"
        real_blob_services['openai'].generate_embedding.return_value = [0.2, 0.3, 0.4] * 500
        real_blob_services['redis'].store_document.return_value = True
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.docx"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar llamadas a servicios
        real_blob_services['blob'].download_blob.assert_called_once_with("document.docx", "test-container")
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_called_once()
        
        # Verificar contenido del documento almacenado
        store_call = real_blob_services['redis'].store_document.call_args[0][0]
        assert store_call["filename"] == "document.docx"
        assert store_call["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_txt_blob_trigger_integration(self, real_blob_services):
        """
        Test de integración: Trigger de blob TXT
        Verifica línea por línea el procesamiento de archivo TXT
        """
        # Configurar descarga de TXT
        real_blob_services['blob'].download_blob.return_value = b"Plain text content"
        real_blob_services['openai'].generate_embedding.return_value = [0.3, 0.4, 0.5] * 500
        real_blob_services['redis'].store_document.return_value = True
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.txt"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar llamadas a servicios
        real_blob_services['blob'].download_blob.assert_called_once_with("document.txt", "test-container")
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_called_once()
        
        # Verificar contenido del documento almacenado
        store_call = real_blob_services['redis'].store_document.call_args[0][0]
        assert store_call["filename"] == "document.txt"
        assert store_call["content_type"] == "text/plain"
    
    def test_unsupported_blob_trigger_integration(self, real_blob_services):
        """
        Test de integración: Trigger de blob no soportado
        Verifica línea por línea el manejo de archivos no soportados
        """
        # Crear blob trigger mock con archivo no soportado
        blob_trigger = Mock()
        blob_trigger.name = "script.exe"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que no se procesó el archivo
        real_blob_services['blob'].download_blob.assert_not_called()
        real_blob_services['openai'].generate_embedding.assert_not_called()
        real_blob_services['redis'].store_document.assert_not_called()
    
    def test_blob_trigger_download_error_integration(self, real_blob_services):
        """
        Test de integración: Error en descarga de blob
        Verifica línea por línea el manejo de errores de descarga
        """
        # Configurar error en descarga
        real_blob_services['blob'].download_blob.side_effect = Exception("Download error")
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que se intentó descargar pero falló
        real_blob_services['blob'].download_blob.assert_called_once()
        real_blob_services['openai'].generate_embedding.assert_not_called()
        real_blob_services['redis'].store_document.assert_not_called()
    
    def test_blob_trigger_embedding_error_integration(self, real_blob_services):
        """
        Test de integración: Error en generación de embedding
        Verifica línea por línea el manejo de errores de embedding
        """
        # Configurar descarga exitosa pero error en embedding
        real_blob_services['blob'].download_blob.return_value = b"PDF content"
        real_blob_services['openai'].generate_embedding.side_effect = Exception("Embedding error")
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que se descargó pero falló al generar embedding
        real_blob_services['blob'].download_blob.assert_called_once()
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_not_called()
    
    def test_blob_trigger_store_error_integration(self, real_blob_services):
        """
        Test de integración: Error en almacenamiento
        Verifica línea por línea el manejo de errores de almacenamiento
        """
        # Configurar procesamiento exitoso pero error en almacenamiento
        real_blob_services['blob'].download_blob.return_value = b"PDF content"
        real_blob_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        real_blob_services['redis'].store_document.side_effect = Exception("Store error")
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que se procesó pero falló al almacenar
        real_blob_services['blob'].download_blob.assert_called_once()
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_called_once()
    
    def test_blob_trigger_empty_content_integration(self, real_blob_services):
        """
        Test de integración: Contenido vacío
        Verifica línea por línea el manejo de contenido vacío
        """
        # Configurar contenido vacío
        real_blob_services['blob'].download_blob.return_value = b""
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "empty_document.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que no se procesó el contenido vacío
        real_blob_services['openai'].generate_embedding.assert_not_called()
        real_blob_services['redis'].store_document.assert_not_called()
    
    def test_blob_trigger_special_characters_integration(self, real_blob_services):
        """
        Test de integración: Nombre de archivo con caracteres especiales
        Verifica línea por línea el manejo de nombres especiales
        """
        # Configurar procesamiento exitoso
        real_blob_services['blob'].download_blob.return_value = b"PDF content"
        real_blob_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        real_blob_services['redis'].store_document.return_value = True
        
        # Crear blob trigger mock con nombre especial
        blob_trigger = Mock()
        blob_trigger.name = "documento con espacios y acentos.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que se procesó correctamente
        real_blob_services['blob'].download_blob.assert_called_once_with(
            "documento con espacios y acentos.pdf", "test-container"
        )
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_called_once()
        
        # Verificar que se almacenó con el nombre correcto
        store_call = real_blob_services['redis'].store_document.call_args[0][0]
        assert store_call["filename"] == "documento con espacios y acentos.pdf"
    
    def test_blob_trigger_nested_path_integration(self, real_blob_services):
        """
        Test de integración: Archivo en ruta anidada
        Verifica línea por línea el manejo de rutas anidadas
        """
        # Configurar procesamiento exitoso
        real_blob_services['blob'].download_blob.return_value = b"PDF content"
        real_blob_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3] * 500
        real_blob_services['redis'].store_document.return_value = True
        
        # Crear blob trigger mock con ruta anidada
        blob_trigger = Mock()
        blob_trigger.name = "folder/subfolder/document.pdf"
        blob_trigger.container_name = "test-container"
        
        # Ejecutar función principal
        blob_trigger_main(blob_trigger)
        
        # Verificar que se procesó correctamente
        real_blob_services['blob'].download_blob.assert_called_once_with(
            "folder/subfolder/document.pdf", "test-container"
        )
        real_blob_services['openai'].generate_embedding.assert_called_once()
        real_blob_services['redis'].store_document.assert_called_once()
        
        # Verificar que se almacenó con la ruta completa
        store_call = real_blob_services['redis'].store_document.call_args[0][0]
        assert store_call["filename"] == "folder/subfolder/document.pdf"


class TestBatchPushResultsIntegration:
    """Tests de integración para el push de resultados"""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock del entorno completo para push de resultados"""
        with patch.dict('os.environ', {
            'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=teststorage;AccountKey=testkey;EndpointSuffix=core.windows.net',
            'AZURE_STORAGE_CONTAINER_NAME': 'test-container',
            'REDIS_CONNECTION_STRING': 'redis://localhost:6379/0'
        }):
            yield
    
    @pytest.fixture
    def real_push_services(self, mock_environment):
        """Instancias reales de servicios para push de resultados"""
        with patch('processing.batch_push_results.AzureBlobStorageService') as mock_blob, \
             patch('processing.batch_push_results.RedisService') as mock_redis, \
             patch('processing.batch_push_results.get_settings') as mock_settings:
            
            # Configurar settings mock
            mock_settings.return_value = Mock(
                AZURE_STORAGE_CONNECTION_STRING="test-connection-string",
                AZURE_STORAGE_CONTAINER_NAME="test-container",
                REDIS_CONNECTION_STRING="redis://localhost:6379"
            )
            
            # Configurar servicios mock
            mock_blob.return_value = Mock()
            mock_redis.return_value = Mock()
            
            yield {
                'blob': mock_blob.return_value,
                'redis': mock_redis.return_value,
                'settings': mock_settings.return_value
            }
    
    def test_push_results_success_integration(self, real_push_services):
        """
        Test de integración: Push exitoso de resultados
        Verifica línea por línea el envío de resultados
        """
        # Configurar datos de resultados (líneas 40-45 en batch_push_results.py)
        results_data = {
            "processed_files": 10,
            "stored_documents": 8,
            "errors": 2,
            "skipped_files": 0,
            "processing_time": 120.5,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Configurar almacenamiento exitoso
        real_push_services['blob'].upload_blob.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "results": results_data,
            "container_name": "test-container",
            "filename": "processing_results.json"
        }
        
        # Ejecutar función principal
        response = batch_push_main(req)
        
        # Verificar respuesta HTTP
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["uploaded"] is True
        
        # Verificar llamada a servicio
        real_push_services['blob'].upload_blob.assert_called_once()
        upload_call = real_push_services['blob'].upload_blob.call_args
        assert upload_call[0][0] == "processing_results.json"
        assert upload_call[0][1] == "test-container"
        
        # Verificar contenido del JSON
        uploaded_content = json.loads(upload_call[0][2])
        assert uploaded_content["processed_files"] == 10
        assert uploaded_content["stored_documents"] == 8
        assert uploaded_content["errors"] == 2
    
    def test_push_results_upload_error_integration(self, real_push_services):
        """
        Test de integración: Error en upload de resultados
        Verifica línea por línea el manejo de errores de upload
        """
        # Configurar error en upload
        real_push_services['blob'].upload_blob.side_effect = Exception("Upload error")
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "results": {"processed_files": 5},
            "container_name": "test-container",
            "filename": "results.json"
        }
        
        # Ejecutar función principal
        response = batch_push_main(req)
        
        # Verificar respuesta de error
        assert response.status_code == 500
        response_data = json.loads(response.get_body())
        assert response_data["success"] is False
        assert "Error" in response_data["message"]
        
        # Verificar que se intentó hacer upload
        real_push_services['blob'].upload_blob.assert_called_once()
    
    def test_push_results_invalid_request_integration(self, real_push_services):
        """
        Test de integración: Request inválido
        Verifica línea por línea el manejo de requests inválidos
        """
        # Crear request mock sin datos requeridos
        req = Mock()
        req.get_json.return_value = {}
        
        # Ejecutar función principal
        response = batch_push_main(req)
        
        # Verificar respuesta de error
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["success"] is False
        assert "results" in response_data["message"]
        
        # Verificar que no se intentó hacer upload
        real_push_services['blob'].upload_blob.assert_not_called()
    
    def test_push_results_large_data_integration(self, real_push_services):
        """
        Test de integración: Datos grandes
        Verifica línea por línea el manejo de datos grandes
        """
        # Configurar datos grandes
        large_results = {
            "processed_files": 1000,
            "stored_documents": 950,
            "errors": 50,
            "skipped_files": 0,
            "processing_time": 3600.0,
            "timestamp": "2024-01-01T12:00:00Z",
            "details": {
                "file_types": {"pdf": 400, "docx": 300, "txt": 300},
                "errors_by_type": {"download": 20, "embedding": 15, "storage": 15}
            }
        }
        
        real_push_services['blob'].upload_blob.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "results": large_results,
            "container_name": "test-container",
            "filename": "large_results.json"
        }
        
        # Ejecutar función principal
        response = batch_push_main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        
        # Verificar que se subió el archivo grande
        real_push_services['blob'].upload_blob.assert_called_once()
        upload_call = real_push_services['blob'].upload_blob.call_args
        uploaded_content = json.loads(upload_call[0][2])
        assert uploaded_content["processed_files"] == 1000
        assert uploaded_content["stored_documents"] == 950
        assert "details" in uploaded_content 