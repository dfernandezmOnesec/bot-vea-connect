"""
Unit tests for BatchPushResults Azure Function.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import azure.functions as func
from src.processing.batch_push_results import (
    main, 
    extract_text_from_file, 
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_text_file,
    store_document_embeddings,
    update_blob_metadata
)


@pytest.fixture
def mock_queue_message():
    """Create a mock queue message."""
    message = Mock(spec=func.QueueMessage)
    queue_data = {
        "blob_name": "test_document.pdf",
        "blob_url": "https://testaccount.blob.core.windows.net/documents/test_document.pdf",
        "file_size": 1024,
        "content_type": "application/pdf"
    }
    message.get_body.return_value = json.dumps(queue_data).encode('utf-8')
    return message


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


class TestBatchPushResults:
    """Test cases for BatchPushResults function."""

    @patch('src.processing.batch_push_results.update_blob_metadata')
    @patch('src.processing.batch_push_results.store_document_embeddings')
    @patch('src.processing.batch_push_results.openai_service')
    @patch('src.processing.batch_push_results.clean_text')
    @patch('src.processing.batch_push_results.chunk_text')
    @patch('src.processing.batch_push_results.extract_text_from_file')
    @patch('src.processing.batch_push_results.generate_document_id')
    @patch('src.processing.batch_push_results.calculate_file_hash')
    @patch('src.processing.batch_push_results.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_batch_push_results_success(
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
        mock_queue_message,
        mock_file_metadata,
        mock_embeddings
    ):
        """Test successful processing of a text file."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.download_file.return_value = True
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        mock_calculate_hash.return_value = "abc123hash"
        mock_generate_id.return_value = "test_document_abc123_20240101"
        mock_extract_text.return_value = "This is test content from the document."
        mock_clean_text.return_value = "This is test content from the document."
        mock_chunk_text.return_value = ["This is test content", "from the document."]
        
        # Mock OpenAI service
        mock_openai_service.generate_embeddings.side_effect = [
            mock_embeddings[0]["embedding"],
            mock_embeddings[1]["embedding"]
        ]
        
        # Act
        main(mock_queue_message)
        
        # Assert
        mock_blob_service.download_file.assert_called_once_with("test_document.pdf", "/tmp/test_file.pdf")
        mock_blob_service.get_blob_metadata.assert_called_once_with("test_document.pdf")
        mock_calculate_hash.assert_called_once()
        mock_generate_id.assert_called_once_with("test_document.pdf", "abc123hash")
        mock_extract_text.assert_called_once_with("/tmp/test_file.pdf", "test_document.pdf", "application/pdf")
        mock_clean_text.assert_called_once()
        mock_chunk_text.assert_called_once()
        
        # Verify OpenAI was called for each chunk
        assert mock_openai_service.generate_embeddings.call_count == 2
        
        # Verify embeddings were stored
        mock_store_embeddings.assert_called_once()
        call_args = mock_store_embeddings.call_args
        assert call_args[0][0] == "test_document_abc123_20240101"  # document_id
        assert call_args[0][1] == "test_document.pdf"  # blob_name
        
        # Verify metadata was updated
        mock_update_metadata.assert_called_once_with("test_document.pdf", "test_document_abc123_20240101", 2)

    @patch('src.processing.batch_push_results.vision_service')
    @patch('src.processing.batch_push_results.openai_service')
    @patch('src.processing.batch_push_results.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_batch_push_results_image_ocr_success(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_openai_service,
        mock_vision_service,
        mock_embeddings
    ):
        """Test successful processing of an image/PDF file with OCR."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_image.jpg"
        mock_blob_service.download_file.return_value = True
        mock_blob_service.get_blob_metadata.return_value = {"content_type": "image/jpeg"}
        
        # Mock vision service for OCR
        mock_vision_service.extract_text_from_image_file.return_value = "Text extracted from image via OCR"
        
        # Mock other services
        with patch('src.processing.batch_push_results.calculate_file_hash') as mock_hash:
            with patch('src.processing.batch_push_results.generate_document_id') as mock_id:
                with patch('src.processing.batch_push_results.clean_text') as mock_clean:
                    with patch('src.processing.batch_push_results.chunk_text') as mock_chunk:
                        mock_hash.return_value = "image123hash"
                        mock_id.return_value = "test_image_image123_20240101"
                        mock_clean.return_value = "Text extracted from image via OCR"
                        mock_chunk.return_value = ["Text extracted from image via OCR"]
                        
                        # Mock OpenAI service
                        mock_openai_service.generate_embeddings.return_value = mock_embeddings[0]["embedding"]
                        
                        # Create queue message for image
                        message = Mock(spec=func.QueueMessage)
                        queue_data = {
                            "blob_name": "test_image.jpg",
                            "content_type": "image/jpeg"
                        }
                        message.get_body.return_value = json.dumps(queue_data).encode('utf-8')
                        
                        # Act
                        main(message)
                        
                        # Assert
                        mock_vision_service.extract_text_from_image_file.assert_called_once_with("/tmp/test_image.jpg")
                        mock_openai_service.generate_embeddings.assert_called_once()

    @patch('src.processing.batch_push_results.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_batch_push_results_download_failure(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_queue_message
    ):
        """Test handling of blob download failure."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.download_file.return_value = False
        
        # Act
        main(mock_queue_message)
        
        # Assert
        mock_blob_service.download_file.assert_called_once()
        # Should not proceed with processing if download fails

    @patch('src.processing.batch_push_results.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_batch_push_results_no_text_extracted(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_queue_message,
        mock_file_metadata
    ):
        """Test when no text is extracted from file."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.download_file.return_value = True
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        
        with patch('src.processing.batch_push_results.extract_text_from_file') as mock_extract:
            mock_extract.return_value = ""
            
            # Act
            main(mock_queue_message)
            
            # Assert
            mock_extract.assert_called_once()
            # Should not proceed with embedding generation

    @patch('src.processing.batch_push_results.openai_service')
    @patch('src.processing.batch_push_results.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_batch_push_results_embedding_generation_failure(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_openai_service,
        mock_queue_message,
        mock_file_metadata
    ):
        """Test handling of embedding generation failure."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.download_file.return_value = True
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        
        with patch('src.processing.batch_push_results.extract_text_from_file') as mock_extract:
            with patch('src.processing.batch_push_results.clean_text') as mock_clean:
                with patch('src.processing.batch_push_results.chunk_text') as mock_chunk:
                    mock_extract.return_value = "Test content"
                    mock_clean.return_value = "Test content"
                    mock_chunk.return_value = ["Test content"]
                    
                    # Mock OpenAI service to fail
                    mock_openai_service.generate_embeddings.side_effect = Exception("OpenAI error")
                    
                    # Act
                    main(mock_queue_message)
                    
                    # Assert
                    mock_openai_service.generate_embeddings.assert_called_once()
                    # Should not proceed with storage if no embeddings generated

    @patch('src.processing.batch_push_results.redis_service')
    def test_store_document_embeddings_success(
        self,
        mock_redis_service,
        mock_embeddings,
        mock_file_metadata
    ):
        """Test successful storage of document embeddings."""
        # Arrange
        document_id = "test_doc_123"
        blob_name = "test.pdf"
        
        # Act
        store_document_embeddings(document_id, blob_name, mock_embeddings, mock_file_metadata)
        
        # Assert
        mock_redis_service.store_embedding.assert_called_once()
        call_args = mock_redis_service.store_embedding.call_args
        assert call_args[0][0] == document_id
        assert len(call_args[0][1]) == 1500  # Average embedding length
        
        # Verify metadata includes embeddings_generated flag
        metadata = call_args[0][2]
        assert metadata["embeddings_generated"] == "true"

    @patch('src.processing.batch_push_results.redis_service')
    def test_store_document_embeddings_failure(
        self,
        mock_redis_service,
        mock_embeddings,
        mock_file_metadata
    ):
        """Test handling of Redis storage failure."""
        # Arrange
        mock_redis_service.store_embedding.side_effect = Exception("Redis error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Redis error"):
            store_document_embeddings("test_doc", "test.pdf", mock_embeddings, mock_file_metadata)

    def test_update_blob_metadata_success(self):
        """Test successful blob metadata update."""
        # Act
        update_blob_metadata("test.pdf", "test_doc_123", 5)
        
        # Assert - should not raise exception and should log the metadata
        # (actual implementation would update blob metadata)

    def test_queue_message_missing_blob_name(self):
        """Test handling of queue message missing blob_name."""
        # Arrange
        message = Mock(spec=func.QueueMessage)
        queue_data = {
            "blob_url": "https://test.blob.core.windows.net/test.pdf",
            "content_type": "application/pdf"
        }
        message.get_body.return_value = json.dumps(queue_data).encode('utf-8')
        
        # Act
        main(message)
        
        # Assert - should log error and return early

    def test_queue_message_invalid_json(self):
        """Test handling of invalid JSON in queue message."""
        # Arrange
        message = Mock(spec=func.QueueMessage)
        message.get_body.return_value = b"invalid json"
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to parse queue message JSON"):
            main(message)


class TestTextExtraction:
    """Test cases for text extraction functions."""

    @patch('src.processing.batch_push_results.vision_service')
    def test_extract_text_from_file_image_extension(
        self,
        mock_vision_service
    ):
        """Test text extraction from image file by extension."""
        # Arrange
        mock_vision_service.extract_text_from_image_file.return_value = "Extracted text from image"
        
        # Act
        result = extract_text_from_file("/tmp/test.jpg", "test.jpg", "image/jpeg")
        
        # Assert
        assert result == "Extracted text from image"
        mock_vision_service.extract_text_from_image_file.assert_called_once_with("/tmp/test.jpg")

    @patch('src.processing.batch_push_results.vision_service')
    def test_extract_text_from_file_image_content_type(
        self,
        mock_vision_service
    ):
        """Test text extraction from image file by content type."""
        # Arrange
        mock_vision_service.extract_text_from_image_file.return_value = "Extracted text from image"
        
        # Act
        result = extract_text_from_file("/tmp/test.xyz", "test.xyz", "image/png")
        
        # Assert
        assert result == "Extracted text from image"
        mock_vision_service.extract_text_from_image_file.assert_called_once_with("/tmp/test.xyz")

    @patch('src.processing.batch_push_results.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_success(self, mock_pdf_reader):
        """Test extracción exitosa de texto de PDF."""
        # Arrange
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock()]
        mock_reader.pages[0].extract_text.return_value = "Página 1 del documento"
        mock_reader.pages[1].extract_text.return_value = "Página 2 del documento"
        mock_pdf_reader.return_value = mock_reader
        
        # Act
        result = extract_text_from_pdf("/tmp/test.pdf")
        
        # Assert
        assert result == "Página 1 del documento\nPágina 2 del documento"
        mock_pdf_reader.assert_called_once_with("/tmp/test.pdf")

    @patch('src.processing.batch_push_results.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_failure(self, mock_pdf_reader):
        """Test fallo en extracción de texto de PDF."""
        # Arrange
        mock_pdf_reader.side_effect = Exception("PDF error")
        
        # Act & Assert
        with pytest.raises(Exception, match="PDF error"):
            extract_text_from_pdf("/tmp/test.pdf")

    @patch('src.processing.batch_push_results.Document')
    def test_extract_text_from_word_success(self, mock_document):
        """Test extracción exitosa de texto de Word."""
        # Arrange
        mock_doc = Mock()
        mock_doc.paragraphs = [Mock(), Mock()]
        mock_doc.paragraphs[0].text = "Párrafo 1 del documento"
        mock_doc.paragraphs[1].text = "Párrafo 2 del documento"
        mock_document.return_value = mock_doc
        
        # Act
        result = extract_text_from_word("/tmp/test.docx")
        
        # Assert
        assert result == "Párrafo 1 del documento\nPárrafo 2 del documento"
        mock_document.assert_called_once_with("/tmp/test.docx")

    @patch('src.processing.batch_push_results.Document')
    def test_extract_text_from_word_failure(self, mock_document):
        """Test fallo en extracción de texto de Word."""
        # Arrange
        mock_document.side_effect = Exception("Word error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Word error"):
            extract_text_from_word("/tmp/test.docx")

    def test_extract_text_from_text_file_success(self):
        """Test successful text file extraction."""
        # Arrange
        test_content = "This is test content from a text file."
        
        # Act
        with patch('builtins.open', mock_open(read_data=test_content)):
            result = extract_text_from_text_file("/tmp/test.txt")
        
        # Assert
        assert result == test_content

    def test_extract_text_from_text_file_unicode_error(self):
        """Test text file extraction with Unicode decode error."""
        # Arrange
        test_content = b"This is test content with special chars: \x80\x81"
        
        # Act
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch('builtins.open', mock_open(read_data=test_content), create=True) as mock_file:
                mock_file.side_effect = [
                    UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid utf-8'),
                    test_content.decode('latin-1')
                ]
                result = extract_text_from_text_file("/tmp/test.txt")
        
        # Assert
        assert "This is test content with special chars" in result

    def test_extract_text_from_unsupported_file_type(self):
        """Test text extraction from unsupported file type."""
        # Act
        result = extract_text_from_file("/tmp/test.xyz", "test.xyz", "application/octet-stream")
        
        # Assert
        assert result == ""

    @patch('src.processing.batch_push_results.vision_service')
    def test_extract_text_from_file_vision_service_failure(
        self,
        mock_vision_service
    ):
        """Test handling of vision service failure."""
        # Arrange
        mock_vision_service.extract_text_from_image_file.side_effect = Exception("Vision error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to extract text from test.jpg"):
            extract_text_from_file("/tmp/test.jpg", "test.jpg", "image/jpeg")


def setup_module(module):
    import sys
    import types
    # Mock PyPDF2 y Document como atributos del módulo para patch
    sys.modules['src.processing.batch_push_results'].PyPDF2 = types.SimpleNamespace(PdfReader=Mock())
    sys.modules['src.processing.batch_push_results'].Document = Mock() 