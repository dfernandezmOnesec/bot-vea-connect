"""
Tests unitarios para batch_start_processing.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from typing import Dict, Any, List

from src.processing.batch_start_processing import main


class TestBatchStartProcessing:
    """Tests para la función batch_start_processing"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock de todos los servicios"""
        with patch('src.processing.batch_start_processing.AzureBlobStorage') as mock_blob, \
             patch('src.processing.batch_start_processing.OpenAIService') as mock_openai, \
             patch('src.processing.batch_start_processing.RedisService') as mock_redis, \
             patch('src.processing.batch_start_processing.get_settings') as mock_settings:
            
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
    
    def test_main_success(self, mock_services):
        """Test ejecución exitosa de la función"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = [
            "document1.pdf",
            "document2.docx",
            "image1.jpg"
        ]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 3
        assert response_data["data"]["stored_documents"] == 3
        
        # Verificar que se llamaron los servicios correctos
        mock_services['blob'].list_blobs.assert_called_once_with("test-container")
        assert mock_services['blob'].download_blob.call_count == 3
        assert mock_services['openai'].generate_embedding.call_count == 3
        assert mock_services['redis'].store_document.call_count == 3
    
    def test_main_no_files(self, mock_services):
        """Test cuando no hay archivos para procesar"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = []
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 0
        assert response_data["data"]["stored_documents"] == 0
        
        # Verificar que no se procesaron archivos
        mock_services['blob'].download_blob.assert_not_called()
        mock_services['openai'].generate_embedding.assert_not_called()
        mock_services['redis'].store_document.assert_not_called()
    
    def test_main_with_batch_size_limit(self, mock_services):
        """Test procesamiento con límite de batch size"""
        # Configurar mocks con muchos archivos
        mock_services['blob'].list_blobs.return_value = [
            f"document{i}.pdf" for i in range(20)
        ]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock con batch_size pequeño
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 5
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 5  # Solo 5 archivos procesados
        assert response_data["data"]["stored_documents"] == 5
        
        # Verificar que solo se procesaron 5 archivos
        assert mock_services['blob'].download_blob.call_count == 5
        assert mock_services['openai'].generate_embedding.call_count == 5
        assert mock_services['redis'].store_document.call_count == 5
    
    def test_main_download_error(self, mock_services):
        """Test error al descargar archivo"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = ["document1.pdf", "document2.pdf"]
        mock_services['blob'].download_blob.side_effect = [
            b"test content",  # Primer archivo exitoso
            Exception("Download error")  # Segundo archivo falla
        ]
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 2
        assert response_data["data"]["stored_documents"] == 1  # Solo 1 documento almacenado
        assert response_data["data"]["errors"] == 1
        
        # Verificar que se procesó el primer archivo pero no el segundo
        assert mock_services['blob'].download_blob.call_count == 2
        assert mock_services['openai'].generate_embedding.call_count == 1
        assert mock_services['redis'].store_document.call_count == 1
    
    def test_main_embedding_error(self, mock_services):
        """Test error al generar embedding"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = ["document1.pdf"]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.side_effect = Exception("Embedding error")
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 1
        assert response_data["data"]["stored_documents"] == 0
        assert response_data["data"]["errors"] == 1
        
        # Verificar que se descargó pero no se generó embedding
        mock_services['blob'].download_blob.assert_called_once()
        mock_services['openai'].generate_embedding.assert_called_once()
        mock_services['redis'].store_document.assert_not_called()
    
    def test_main_store_error(self, mock_services):
        """Test error al almacenar documento"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = ["document1.pdf"]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.side_effect = Exception("Store error")
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 1
        assert response_data["data"]["stored_documents"] == 0
        assert response_data["data"]["errors"] == 1
        
        # Verificar que se procesó pero no se almacenó
        mock_services['blob'].download_blob.assert_called_once()
        mock_services['openai'].generate_embedding.assert_called_once()
        mock_services['redis'].store_document.assert_called_once()
    
    def test_main_invalid_request(self, mock_services):
        """Test request inválido"""
        # Crear request mock sin parámetros requeridos
        req = Mock()
        req.get_json.return_value = {}
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["success"] is False
        assert "container_name" in response_data["message"]
    
    def test_main_missing_container_name(self, mock_services):
        """Test request sin container_name"""
        # Crear request mock sin container_name
        req = Mock()
        req.get_json.return_value = {
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["success"] is False
        assert "container_name" in response_data["message"]
    
    def test_main_blob_list_error(self, mock_services):
        """Test error al listar blobs"""
        # Configurar mocks
        mock_services['blob'].list_blobs.side_effect = Exception("List error")
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 500
        response_data = json.loads(response.get_body())
        assert response_data["success"] is False
        assert "Error" in response_data["message"]
    
    def test_main_unsupported_file_type(self, mock_services):
        """Test archivo con tipo no soportado"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = ["document1.exe"]  # Tipo no soportado
        mock_services['blob'].download_blob.return_value = b"test content"
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 1
        assert response_data["data"]["stored_documents"] == 0
        assert response_data["data"]["skipped_files"] == 1
        
        # Verificar que no se procesó el archivo no soportado
        mock_services['blob'].download_blob.assert_not_called()
        mock_services['openai'].generate_embedding.assert_not_called()
        mock_services['redis'].store_document.assert_not_called()
    
    def test_main_mixed_file_types(self, mock_services):
        """Test mezcla de tipos de archivo"""
        # Configurar mocks
        mock_services['blob'].list_blobs.return_value = [
            "document1.pdf",  # Soportado
            "image1.exe",     # No soportado
            "document2.docx", # Soportado
            "script1.bat"     # No soportado
        ]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 4
        assert response_data["data"]["stored_documents"] == 2  # Solo los soportados
        assert response_data["data"]["skipped_files"] == 2    # Los no soportados
        
        # Verificar que solo se procesaron los archivos soportados
        assert mock_services['blob'].download_blob.call_count == 2
        assert mock_services['openai'].generate_embedding.call_count == 2
        assert mock_services['redis'].store_document.call_count == 2
    
    def test_main_large_content(self, mock_services):
        """Test procesamiento de contenido grande"""
        # Configurar mocks con contenido grande
        large_content = b"x" * 1000000  # 1MB de contenido
        mock_services['blob'].list_blobs.return_value = ["large_document.pdf"]
        mock_services['blob'].download_blob.return_value = large_content
        mock_services['openai'].generate_embedding.return_value = [0.1] * 1536  # Embedding grande
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 1
        assert response_data["data"]["stored_documents"] == 1
        
        # Verificar que se procesó el contenido grande
        mock_services['blob'].download_blob.assert_called_once()
        mock_services['openai'].generate_embedding.assert_called_once()
        mock_services['redis'].store_document.assert_called_once()
    
    def test_main_empty_content(self, mock_services):
        """Test procesamiento de contenido vacío"""
        # Configurar mocks con contenido vacío
        mock_services['blob'].list_blobs.return_value = ["empty_document.pdf"]
        mock_services['blob'].download_blob.return_value = b""
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 1
        assert response_data["data"]["stored_documents"] == 0
        assert response_data["data"]["skipped_files"] == 1
        
        # Verificar que no se procesó el contenido vacío
        mock_services['openai'].generate_embedding.assert_not_called()
        mock_services['redis'].store_document.assert_not_called()
    
    def test_main_unicode_content(self, mock_services):
        """Test procesamiento de contenido con caracteres Unicode"""
        # Configurar mocks con contenido Unicode
        unicode_content = "Contenido con acentos: áéíóú ñü".encode('utf-8')
        mock_services['blob'].list_blobs.return_value = ["unicode_document.pdf"]
        mock_services['blob'].download_blob.return_value = unicode_content
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 1
        assert response_data["data"]["stored_documents"] == 1
        
        # Verificar que se procesó el contenido Unicode
        mock_services['openai'].generate_embedding.assert_called_once()
        mock_services['redis'].store_document.assert_called_once()
    
    def test_main_concurrent_processing(self, mock_services):
        """Test procesamiento concurrente (simulado)"""
        # Configurar mocks para procesamiento rápido
        mock_services['blob'].list_blobs.return_value = [
            f"document{i}.pdf" for i in range(5)
        ]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 5
        assert response_data["data"]["stored_documents"] == 5
        
        # Verificar que todos los archivos se procesaron
        assert mock_services['blob'].download_blob.call_count == 5
        assert mock_services['openai'].generate_embedding.call_count == 5
        assert mock_services['redis'].store_document.call_count == 5
    
    def test_main_memory_efficiency(self, mock_services):
        """Test eficiencia de memoria con muchos archivos"""
        # Configurar mocks para muchos archivos
        mock_services['blob'].list_blobs.return_value = [
            f"document{i}.pdf" for i in range(100)
        ]
        mock_services['blob'].download_blob.return_value = b"test content"
        mock_services['openai'].generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_services['redis'].store_document.return_value = True
        
        # Crear request mock con batch_size pequeño
        req = Mock()
        req.get_json.return_value = {
            "container_name": "test-container",
            "batch_size": 10
        }
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["success"] is True
        assert response_data["data"]["processed_files"] == 10  # Solo 10 procesados
        assert response_data["data"]["stored_documents"] == 10
        
        # Verificar que solo se procesaron 10 archivos (límite de batch)
        assert mock_services['blob'].download_blob.call_count == 10
        assert mock_services['openai'].generate_embedding.call_count == 10
        assert mock_services['redis'].store_document.call_count == 10 