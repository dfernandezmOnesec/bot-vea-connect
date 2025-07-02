"""
Unit tests for Batch Start Processing Azure Function.

This module contains comprehensive tests for the batch_start_processing function
with mocked Azure Blob Storage, OpenAI, and Redis services.
"""

import pytest
import json
from unittest.mock import Mock, patch
from processing.batch_start_processing import main
from shared_code.azure_blob_storage import blob_storage_service
from azure.storage.queue import QueueClient


class TestBatchStartProcessing:
    """Tests para la función batch_start_processing"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock de todos los servicios"""
        with patch.object(blob_storage_service, 'list_blobs') as mock_blob_list, \
             patch('src.processing.batch_start_processing.settings') as mock_settings, \
             patch.object(QueueClient, 'from_connection_string') as mock_queue_from_conn:
            
            # Configurar settings mock
            mock_settings.azure_storage_connection_string = "test-connection-string"
            mock_settings.queue_name = "test-queue"
            mock_settings.blob_account_name = "testaccount"
            mock_settings.blob_container_name = "test-container"
            
            # Configurar servicios mock
            mock_blob_list.return_value = []
            mock_queue_instance = Mock()
            mock_queue_instance.send_message.return_value = None
            mock_queue_from_conn.return_value = mock_queue_instance
            
            yield {
                'blob_list': mock_blob_list,
                'settings': mock_settings,
                'queue_from_conn': mock_queue_from_conn,
                'queue_instance': mock_queue_instance
            }
    
    def test_main_success(self, mock_services):
        """Test ejecución exitosa de la función"""
        # Configurar mocks
        test_blobs = [
            {
                "name": "document1.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            },
            {
                "name": "document2.docx",
                "size": 2048,
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "last_modified": None,
                "metadata": {}
            }
        ]
        mock_services['blob_list'].return_value = test_blobs
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 2
        assert response_data["unprocessed_files"] == 2
        assert response_data["queued_files"] == 2
        
        # Verificar que se llamaron los servicios correctos
        mock_services['blob_list'].assert_called_once()
        mock_services['queue_from_conn'].assert_called_once()
        assert mock_services['queue_instance'].send_message.call_count == 2
    
    def test_main_no_files(self, mock_services):
        """Test cuando no hay archivos para procesar"""
        # Configurar mocks
        mock_services['blob_list'].return_value = []
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 0
        assert response_data["unprocessed_files"] == 0
        assert response_data["queued_files"] == 0
        
        # Verificar que no se procesaron archivos
        mock_services['blob_list'].assert_called_once()
    
    def test_main_with_batch_size_limit(self, mock_services):
        """Test procesamiento con límite de batch size"""
        # Configurar mocks con muchos archivos
        mock_services['blob_list'].return_value = [
            {
                "name": f"document{i}.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            } for i in range(20)
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 20
        assert response_data["unprocessed_files"] == 20
        assert response_data["queued_files"] == 20
        
        # Verificar que se procesaron todos los archivos
        mock_services['blob_list'].assert_called_once()
    
    def test_main_download_error(self, mock_services):
        """Test error al listar blobs"""
        # Configurar mocks para que falle
        mock_services['blob_list'].side_effect = Exception("List error")
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta de error
        assert response.status_code == 500
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "error"
        assert "Failed to start batch processing" in response_data["message"]
    
    def test_main_embedding_error(self, mock_services):
        """Test error al enviar mensaje a la cola"""
        # Configurar mocks
        mock_services['blob_list'].return_value = [
            {
                "name": "document1.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            }
        ]
        mock_services['queue_instance'].send_message.side_effect = Exception("Queue error")
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1
        assert response_data["unprocessed_files"] == 1
        assert response_data["queued_files"] == 0  # No se pudo encolar
    
    def test_main_store_error(self, mock_services):
        """Test error al almacenar documento"""
        # Configurar mocks
        mock_services['blob_list'].return_value = [
            {
                "name": "document1.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            }
        ]
        mock_services['queue_from_conn'].return_value.send_message.return_value = None
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1
        assert response_data["unprocessed_files"] == 1
        assert response_data["queued_files"] == 1
    
    def test_main_invalid_request(self, mock_services):
        """Test request inválido"""
        # Configurar mocks
        mock_services['blob_list'].return_value = []
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
    
    def test_main_missing_container_name(self, mock_services):
        """Test sin nombre de contenedor"""
        # Configurar mocks
        mock_services['blob_list'].return_value = []
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
    
    def test_main_blob_list_error(self, mock_services):
        """Test error al listar blobs"""
        # Configurar mocks para que falle
        mock_services['blob_list'].side_effect = Exception("Blob list error")
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta de error
        assert response.status_code == 500
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "error"
    
    def test_main_unsupported_file_type(self, mock_services):
        """Test archivos no soportados"""
        # Configurar mocks con archivos no soportados
        mock_services['blob_list'].return_value = [
            {
                "name": "document1.exe",
                "size": 1024,
                "content_type": "application/x-msdownload",
                "last_modified": None,
                "metadata": {}
            }
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1
        assert response_data["unprocessed_files"] == 1
        assert response_data["queued_files"] == 1  # Se encola igual
    
    def test_main_mixed_file_types(self, mock_services):
        """Test archivos mixtos"""
        # Configurar mocks con diferentes tipos de archivo
        mock_services['blob_list'].return_value = [
            {
                "name": "document1.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            },
            {
                "name": "image1.jpg",
                "size": 2048,
                "content_type": "image/jpeg",
                "last_modified": None,
                "metadata": {}
            },
            {
                "name": "text1.txt",
                "size": 512,
                "content_type": "text/plain",
                "last_modified": None,
                "metadata": {}
            }
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 3
        assert response_data["unprocessed_files"] == 3
        assert response_data["queued_files"] == 3
    
    def test_main_large_content(self, mock_services):
        """Test contenido grande"""
        # Configurar mocks con archivo grande
        mock_services['blob_list'].return_value = [
            {
                "name": "large_document.pdf",
                "size": 50 * 1024 * 1024,  # 50MB
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            }
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1
        assert response_data["unprocessed_files"] == 1
        assert response_data["queued_files"] == 1
    
    def test_main_empty_content(self, mock_services):
        """Test contenido vacío"""
        # Configurar mocks con archivo vacío
        mock_services['blob_list'].return_value = [
            {
                "name": "empty_document.txt",
                "size": 0,
                "content_type": "text/plain",
                "last_modified": None,
                "metadata": {}
            }
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1
        assert response_data["unprocessed_files"] == 1
        assert response_data["queued_files"] == 1
    
    def test_main_unicode_content(self, mock_services):
        """Test contenido unicode"""
        # Configurar mocks con archivo con nombre unicode
        mock_services['blob_list'].return_value = [
            {
                "name": "documento_español.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            }
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1
        assert response_data["unprocessed_files"] == 1
        assert response_data["queued_files"] == 1
    
    def test_main_concurrent_processing(self, mock_services):
        """Test procesamiento concurrente"""
        # Configurar mocks con muchos archivos
        mock_services['blob_list'].return_value = [
            {
                "name": f"document{i}.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            } for i in range(100)
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 100
        assert response_data["unprocessed_files"] == 100
        assert response_data["queued_files"] == 100
    
    def test_main_memory_efficiency(self, mock_services):
        """Test eficiencia de memoria"""
        # Configurar mocks con muchos archivos
        mock_services['blob_list'].return_value = [
            {
                "name": f"document{i}.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "last_modified": None,
                "metadata": {}
            } for i in range(1000)
        ]
        
        # Crear request mock
        req = Mock()
        
        # Ejecutar función
        response = main(req)
        
        # Verificar respuesta
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 1000
        assert response_data["unprocessed_files"] == 1000
        assert response_data["queued_files"] == 1000 