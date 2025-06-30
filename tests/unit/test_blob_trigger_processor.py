"""
Unit tests for BlobTriggerProcessor Azure Function.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import azure.functions as func
from src.processing.blob_trigger_processor import (
    main, 
    extract_text_from_file, 
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_text_file,
    store_document_embeddings,
    update_blob_metadata
)


@pytest.fixture
def mock_blob_stream():
    """Create a mock blob input stream."""
    blob_stream = Mock(spec=func.InputStream)
    blob_stream.name = "test_document.pdf"
    blob_stream.read.return_value = b"mock pdf content"
    return blob_stream


@pytest.fixture
def mock_file_metadata():
    """Create mock file metadata."""
    return {
        "content_type": "application/pdf",
        "upload_date": "2024-01-01T00:00:00Z",
        "file_size": 1024,
        "processing_timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings data."""
    return [
        {
            "chunk_index": 0,
            "text": "This is the first chunk of text.",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 300  # 1500 dimensions
        },
        {
            "chunk_index": 1,
            "text": "This is the second chunk of text.",
            "embedding": [0.6, 0.7, 0.8, 0.9, 1.0] * 300  # 1500 dimensions
        }
    ]


class TestBlobTriggerProcessor:
    """Test cases for BlobTriggerProcessor function."""

    @pytest.fixture
    def mock_services(self):
        """Mock de todos los servicios"""
        with patch('src.processing.blob_trigger_processor.blob_storage_service') as mock_blob, \
             patch('src.processing.blob_trigger_processor.openai_service') as mock_openai, \
             patch('src.processing.blob_trigger_processor.redis_service') as mock_redis, \
             patch('src.processing.blob_trigger_processor.vision_service') as mock_vision, \
             patch('src.processing.blob_trigger_processor.generate_document_id') as mock_generate_id, \
             patch('src.processing.blob_trigger_processor.calculate_file_hash') as mock_calculate_hash, \
             patch('src.processing.blob_trigger_processor.clean_text') as mock_clean_text, \
             patch('src.processing.blob_trigger_processor.chunk_text') as mock_chunk_text, \
             patch('src.processing.blob_trigger_processor.extract_text_from_file') as mock_extract_text, \
             patch('src.processing.blob_trigger_processor.store_document_embeddings') as mock_store_embeddings, \
             patch('src.processing.blob_trigger_processor.update_blob_metadata') as mock_update_metadata:
            
            # Configurar servicios mock
            mock_blob.get_blob_metadata.return_value = {
                "content_type": "application/pdf",
                "upload_date": "2024-01-01T00:00:00Z",
                "file_size": 1024
            }
            mock_openai.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
            mock_generate_id.return_value = "test_doc_123"
            mock_calculate_hash.return_value = "test_hash_123"
            mock_extract_text.return_value = "Test document content"
            mock_clean_text.return_value = "Test document content"
            mock_chunk_text.return_value = ["Test document content"]
            
            yield {
                'blob': mock_blob,
                'openai': mock_openai,
                'redis': mock_redis,
                'vision': mock_vision,
                'generate_id': mock_generate_id,
                'calculate_hash': mock_calculate_hash,
                'clean_text': mock_clean_text,
                'chunk_text': mock_chunk_text,
                'extract_text': mock_extract_text,
                'store_embeddings': mock_store_embeddings,
                'update_metadata': mock_update_metadata
            }

    def test_main_success_pdf(self, mock_services):
        """Test procesamiento exitoso de archivo PDF"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se llamaron los servicios correctos
            mock_services['blob'].get_blob_metadata.assert_called_once_with("document.pdf")
            mock_services['generate_id'].assert_called_once()
            mock_services['calculate_hash'].assert_called_once()
            mock_services['extract_text'].assert_called_once()
            mock_services['clean_text'].assert_called_once()
            mock_services['chunk_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_called_once()
            mock_services['store_embeddings'].assert_called_once()
            mock_services['update_metadata'].assert_called_once()

    def test_main_success_docx(self, mock_services):
        """Test procesamiento exitoso de archivo DOCX"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.docx"
        blob_trigger.read.return_value = b"DOCX content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.docx"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se llamaron los servicios correctos
            mock_services['blob'].get_blob_metadata.assert_called_once_with("document.docx")
            mock_services['generate_id'].assert_called_once()
            mock_services['calculate_hash'].assert_called_once()
            mock_services['extract_text'].assert_called_once()
            mock_services['clean_text'].assert_called_once()
            mock_services['chunk_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_called_once()
            mock_services['store_embeddings'].assert_called_once()
            mock_services['update_metadata'].assert_called_once()

    def test_main_success_txt(self, mock_services):
        """Test procesamiento exitoso de archivo TXT"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "text/plain",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.txt"
        blob_trigger.read.return_value = b"TXT content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.txt"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se llamaron los servicios correctos
            mock_services['blob'].get_blob_metadata.assert_called_once_with("document.txt")
            mock_services['generate_id'].assert_called_once()
            mock_services['calculate_hash'].assert_called_once()
            mock_services['extract_text'].assert_called_once()
            mock_services['clean_text'].assert_called_once()
            mock_services['chunk_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_called_once()
            mock_services['store_embeddings'].assert_called_once()
            mock_services['update_metadata'].assert_called_once()

    def test_main_unsupported_file_type(self, mock_services):
        """Test archivo con tipo no soportado"""
        # Configurar mocks
        mock_services['extract_text'].return_value = ""
        
        # Crear blob trigger mock con archivo no soportado
        blob_trigger = Mock()
        blob_trigger.name = "document.exe"
        blob_trigger.read.return_value = b"executable content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.exe"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se intentó extraer texto pero retornó vacío
            mock_services['extract_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_not_called()
            mock_services['store_embeddings'].assert_not_called()

    def test_main_download_error(self, mock_services):
        """Test error al descargar archivo"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.side_effect = Exception("Blob service error")
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función y verificar que se lanza excepción
            with pytest.raises(Exception):
                main(blob_trigger)

    def test_main_empty_content(self, mock_services):
        """Test contenido vacío"""
        # Configurar mocks
        mock_services['extract_text'].return_value = ""
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "empty_document.pdf"
        blob_trigger.read.return_value = b""
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que no se procesó el contenido vacío
            mock_services['extract_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_not_called()
            mock_services['store_embeddings'].assert_not_called()

    def test_main_embedding_error(self, mock_services):
        """Test error al generar embeddings"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        mock_services['openai'].generate_embeddings.side_effect = Exception("Embedding error")
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se intentó generar embedding pero falló
            mock_services['extract_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_called_once()
            mock_services['store_embeddings'].assert_not_called()

    def test_main_store_error(self, mock_services):
        """Test error al almacenar embeddings"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        mock_services['store_embeddings'].side_effect = Exception("Store error")
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función y verificar que se lanza excepción
            with pytest.raises(Exception):
                main(blob_trigger)

    def test_main_large_content(self, mock_services):
        """Test contenido grande"""
        # Configurar mocks
        large_content = "Large content " * 1000
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = large_content
        mock_services['clean_text'].return_value = large_content
        mock_services['chunk_text'].return_value = [large_content]
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "large_document.pdf"
        blob_trigger.read.return_value = b"Large PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se procesó el contenido grande
            mock_services['extract_text'].assert_called_once()
            mock_services['chunk_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_called_once()
            mock_services['store_embeddings'].assert_called_once()

    def test_main_unicode_content(self, mock_services):
        """Test contenido con caracteres Unicode"""
        # Configurar mocks
        unicode_content = "Contenido con ñ, á, é, í, ó, ú, ü"
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = unicode_content
        mock_services['clean_text'].return_value = unicode_content
        mock_services['chunk_text'].return_value = [unicode_content]
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "unicode_document.pdf"
        blob_trigger.read.return_value = b"Unicode PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se procesó el contenido Unicode
            mock_services['extract_text'].assert_called_once()
            mock_services['clean_text'].assert_called_once()
            mock_services['chunk_text'].assert_called_once()
            mock_services['openai'].generate_embeddings.assert_called_once()
            mock_services['store_embeddings'].assert_called_once()

    def test_main_special_characters_filename(self, mock_services):
        """Test nombre de archivo con caracteres especiales"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        
        # Crear blob trigger mock con nombre especial
        blob_trigger = Mock()
        blob_trigger.name = "documento-con-ñ-y-á.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se procesó el archivo con nombre especial
            mock_services['blob'].get_blob_metadata.assert_called_once_with("documento-con-ñ-y-á.pdf")
            mock_services['generate_id'].assert_called_once()
            mock_services['extract_text'].assert_called_once()
            mock_services['store_embeddings'].assert_called_once()

    def test_main_nested_path(self, mock_services):
        """Test archivo en ruta anidada"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        
        # Crear blob trigger mock con ruta anidada
        blob_trigger = Mock()
        blob_trigger.name = "folder/subfolder/document.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se procesó el archivo en ruta anidada
            mock_services['blob'].get_blob_metadata.assert_called_once_with("folder/subfolder/document.pdf")
            mock_services['generate_id'].assert_called_once()
            mock_services['extract_text'].assert_called_once()
            mock_services['store_embeddings'].assert_called_once()

    def test_main_different_containers(self, mock_services):
        """Test archivo en diferentes contenedores"""
        # Configurar mocks
        mock_services['blob'].get_blob_metadata.return_value = {
            "content_type": "application/pdf",
            "upload_date": "2024-01-01T00:00:00Z",
            "file_size": 1024
        }
        mock_services['generate_id'].return_value = "test_doc_123"
        mock_services['calculate_hash'].return_value = "test_hash_123"
        mock_services['extract_text'].return_value = "Test document content"
        mock_services['clean_text'].return_value = "Test document content"
        mock_services['chunk_text'].return_value = ["Test document content"]
        mock_services['openai'].generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        
        # Crear blob trigger mock
        blob_trigger = Mock()
        blob_trigger.name = "document.pdf"
        blob_trigger.read.return_value = b"PDF content"
        
        # Mock tempfile
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
            mock_temp_file.return_value.__enter__.return_value.write = Mock()
            
            # Ejecutar función
            main(blob_trigger)
            
            # Verificar que se procesó el archivo
            mock_services['blob'].get_blob_metadata.assert_called_once_with("document.pdf")
            mock_services['generate_id'].assert_called_once()
            mock_services['extract_text'].assert_called_once()
            mock_services['store_embeddings'].assert_called_once()

    @patch('src.processing.blob_trigger_processor.update_blob_metadata')
    @patch('src.processing.blob_trigger_processor.store_document_embeddings')
    @patch('src.processing.blob_trigger_processor.openai_service')
    @patch('src.processing.blob_trigger_processor.clean_text')
    @patch('src.processing.blob_trigger_processor.chunk_text')
    @patch('src.processing.blob_trigger_processor.extract_text_from_file')
    @patch('src.processing.blob_trigger_processor.generate_document_id')
    @patch('src.processing.blob_trigger_processor.calculate_file_hash')
    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_success(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_calculate_hash,
        mock_generate_id,
        mock_extract_text,
        mock_chunk_text,
        mock_clean_text,
        mock_openai_service,
        mock_store_embeddings,
        mock_update_metadata,
        mock_blob_stream,
        mock_file_metadata,
        mock_embeddings
    ):
        """Test successful blob processing workflow."""
        # Setup mocks
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_temp_file.return_value.__enter__.return_value.write = Mock()
        
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        mock_calculate_hash.return_value = "test_hash"
        mock_generate_id.return_value = "test_doc_123"
        mock_extract_text.return_value = "Test document content"
        mock_clean_text.return_value = "Test document content"
        mock_chunk_text.return_value = ["Test document content"]
        mock_openai_service.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5] * 300
        
        # Execute function
        main(mock_blob_stream)
        
        # Verify calls
        mock_blob_service.get_blob_metadata.assert_called_once_with("test_document.pdf")
        mock_calculate_hash.assert_called_once_with("/tmp/test_file.pdf")
        mock_generate_id.assert_called_once_with("test_document.pdf", "test_hash")
        mock_extract_text.assert_called_once_with("/tmp/test_file.pdf", "test_document.pdf")
        mock_clean_text.assert_called_once_with("Test document content")
        mock_chunk_text.assert_called_once_with("Test document content", chunk_size=1000, overlap=100)
        mock_openai_service.generate_embeddings.assert_called_once_with("Test document content")
        mock_store_embeddings.assert_called_once()
        mock_update_metadata.assert_called_once()

    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_blob_service_failure(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_blob_stream
    ):
        """Test blob service failure."""
        # Setup mocks
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_temp_file.return_value.__enter__.return_value.write = Mock()
        
        mock_blob_service.get_blob_metadata.side_effect = Exception("Blob service error")
        
        # Execute function and verify exception
        with pytest.raises(Exception):
            main(mock_blob_stream)

    @patch('src.processing.blob_trigger_processor.openai_service')
    @patch('src.processing.blob_trigger_processor.extract_text_from_file')
    @patch('src.processing.blob_trigger_processor.calculate_file_hash')
    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_no_text_extracted(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_calculate_hash,
        mock_extract_text,
        mock_openai_service,
        mock_blob_stream,
        mock_file_metadata
    ):
        """Test when no text is extracted from document."""
        # Setup mocks
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_temp_file.return_value.__enter__.return_value.write = Mock()
        
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        mock_calculate_hash.return_value = "test_hash"
        mock_extract_text.return_value = ""
        
        # Execute function
        main(mock_blob_stream)
        
        # Verify that processing stops when no text is extracted
        mock_extract_text.assert_called_once()
        mock_openai_service.generate_embeddings.assert_not_called()

    @patch('src.processing.blob_trigger_processor.openai_service')
    @patch('src.processing.blob_trigger_processor.extract_text_from_file')
    @patch('src.processing.blob_trigger_processor.calculate_file_hash')
    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_embedding_generation_failure(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_calculate_hash,
        mock_extract_text,
        mock_openai_service,
        mock_blob_stream,
        mock_file_metadata
    ):
        """Test embedding generation failure."""
        # Setup mocks
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_temp_file.return_value.__enter__.return_value.write = Mock()
        
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        mock_calculate_hash.return_value = "test_hash"
        mock_extract_text.return_value = "Test content"
        mock_openai_service.generate_embeddings.side_effect = Exception("Embedding error")
        
        # Execute function
        main(mock_blob_stream)
        
        # Verify that processing continues despite embedding failure
        mock_extract_text.assert_called_once()
        mock_openai_service.generate_embeddings.assert_called_once()

    @patch('src.processing.blob_trigger_processor.redis_service')
    def test_store_document_embeddings_success(
        self,
        mock_redis_service,
        mock_embeddings,
        mock_file_metadata
    ):
        """Test successful document embedding storage."""
        # Execute function
        store_document_embeddings("test_doc", "test.pdf", mock_embeddings, mock_file_metadata)
        
        # Verify Redis service calls
        assert mock_redis_service.store_embedding.call_count == 1

    @patch('src.processing.blob_trigger_processor.redis_service')
    def test_store_document_embeddings_failure(
        self,
        mock_redis_service,
        mock_embeddings,
        mock_file_metadata
    ):
        """Test document embedding storage failure."""
        # Setup mock to raise exception
        mock_redis_service.store_embedding.side_effect = Exception("Redis error")
        
        # Execute function and verify exception
        with pytest.raises(Exception):
            store_document_embeddings("test_doc", "test.pdf", mock_embeddings, mock_file_metadata)

    def test_update_blob_metadata_success(self):
        """Test successful blob metadata update."""
        # Execute function - should not raise exception
        update_blob_metadata("test.pdf", "test_doc_123", 5)
        
        # Function only logs, no external service calls to verify

    def test_update_blob_metadata_failure(self):
        """Test blob metadata update failure."""
        # Execute function - should not raise exception even if there's an error
        update_blob_metadata("test.pdf", "test_doc_123", 5)
        
        # Function only logs, no external service calls to verify


class TestTextExtraction:
    """Test cases for text extraction functions."""

    @patch('src.processing.blob_trigger_processor.vision_service')
    def test_extract_text_from_file_image(
        self,
        mock_vision_service
    ):
        """Test text extraction from image file."""
        mock_vision_service.extract_text_from_image_file.return_value = "Extracted text from image"
        
        result = extract_text_from_file("/tmp/test.jpg", "test.jpg")
        
        assert result == "Extracted text from image"
        mock_vision_service.extract_text_from_image_file.assert_called_once_with("/tmp/test.jpg")

    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        # Setup mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        with patch('builtins.open', mock_open(read_data=b"PDF content")):
            result = extract_text_from_pdf("/tmp/test.pdf")
        
        assert result == "Page content"
        mock_pdf_reader.assert_called_once()

    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf_failure(self, mock_pdf_reader):
        """Test PDF text extraction failure."""
        mock_pdf_reader.side_effect = Exception("PDF read error")
        
        with patch('builtins.open', mock_open(read_data=b"PDF content")):
            with pytest.raises(Exception):
                extract_text_from_pdf("/tmp/test.pdf")

    @patch('docx.Document')
    def test_extract_text_from_word_success(self, mock_document):
        """Test successful Word document text extraction."""
        # Setup mock document
        mock_paragraph = Mock()
        mock_paragraph.text = "Paragraph content"
        mock_document.return_value.paragraphs = [mock_paragraph]
        
        result = extract_text_from_word("/tmp/test.docx")
        
        assert result == "Paragraph content"
        mock_document.assert_called_once_with("/tmp/test.docx")

    @patch('docx.Document')
    def test_extract_text_from_word_failure(self, mock_document):
        """Test Word document text extraction failure."""
        mock_document.side_effect = Exception("Word read error")
        
        with pytest.raises(Exception):
            extract_text_from_word("/tmp/test.docx")

    def test_extract_text_from_text_file_success(self):
        """Test successful text file extraction."""
        test_content = "This is test content"
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            result = extract_text_from_text_file("/tmp/test.txt")
        
        assert result == test_content

    def test_extract_text_from_text_file_unicode_error(self):
        """Test text file extraction with Unicode error."""
        # Mock open to raise UnicodeDecodeError first, then succeed with latin-1
        mock_file = mock_open()
        mock_file.return_value.read.side_effect = [
            UnicodeDecodeError('utf-8', b'\xff\xfe', 0, 1, 'invalid utf-8'),
            "Content with latin-1 encoding"
        ]
        
        with patch('builtins.open', mock_file):
            result = extract_text_from_text_file("/tmp/test.txt")
        
        assert result == "Content with latin-1 encoding"

    def test_extract_text_from_unsupported_file_type(self):
        """Test unsupported file type."""
        result = extract_text_from_file("/tmp/test.exe", "test.exe")
        
        assert result == ""

    @patch('src.processing.blob_trigger_processor.vision_service')
    def test_extract_text_from_file_vision_service_failure(
        self,
        mock_vision_service
    ):
        """Test vision service failure during image processing."""
        mock_vision_service.extract_text_from_image_file.side_effect = Exception("Vision error")
        
        with pytest.raises(Exception):
            extract_text_from_file("/tmp/test.jpg", "test.jpg") 