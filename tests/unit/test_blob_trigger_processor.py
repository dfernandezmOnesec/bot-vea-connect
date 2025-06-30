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
        """Test successful blob processing."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
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
        main(mock_blob_stream)
        
        # Assert
        mock_blob_service.get_blob_metadata.assert_called_once_with("test_document.pdf")
        mock_calculate_hash.assert_called_once()
        mock_generate_id.assert_called_once_with("test_document.pdf", "abc123hash")
        mock_extract_text.assert_called_once()
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

    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_blob_service_failure(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_blob_stream
    ):
        """Test handling of blob service failure."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.get_blob_metadata.side_effect = Exception("Blob service error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to process blob test_document.pdf"):
            main(mock_blob_stream)

    @patch('src.processing.blob_trigger_processor.openai_service')
    @patch('src.processing.blob_trigger_processor.extract_text_from_file')
    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_no_text_extracted(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_extract_text,
        mock_openai_service,
        mock_blob_stream,
        mock_file_metadata
    ):
        """Test when no text is extracted from file."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        mock_extract_text.return_value = ""
        
        # Act
        main(mock_blob_stream)
        
        # Assert
        mock_extract_text.assert_called_once()
        mock_openai_service.generate_embeddings.assert_not_called()

    @patch('src.processing.blob_trigger_processor.openai_service')
    @patch('src.processing.blob_trigger_processor.extract_text_from_file')
    @patch('src.processing.blob_trigger_processor.blob_storage_service')
    @patch('tempfile.NamedTemporaryFile')
    def test_blob_trigger_processor_embedding_generation_failure(
        self,
        mock_temp_file,
        mock_blob_service,
        mock_extract_text,
        mock_openai_service,
        mock_blob_stream,
        mock_file_metadata
    ):
        """Test when embedding generation fails."""
        # Arrange
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.pdf"
        mock_blob_service.get_blob_metadata.return_value = mock_file_metadata
        mock_extract_text.return_value = "Test content"
        mock_openai_service.generate_embeddings.side_effect = Exception("OpenAI error")
        
        # Act
        main(mock_blob_stream)
        
        # Assert
        mock_openai_service.generate_embeddings.assert_called_once()

    @patch('src.processing.blob_trigger_processor.redis_service')
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

    @patch('src.processing.blob_trigger_processor.redis_service')
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
        with pytest.raises(Exception, match="Failed to store document embeddings"):
            store_document_embeddings("test_doc", "test.pdf", mock_embeddings, mock_file_metadata)

    def test_update_blob_metadata_success(self):
        """Test successful blob metadata update."""
        # Act
        update_blob_metadata("test.pdf", "test_doc_123", 5)
        
        # Assert - should not raise exception and should log the metadata
        # (actual implementation would update blob metadata)

    def test_update_blob_metadata_failure(self):
        """Test handling of metadata update failure."""
        # This test would be implemented when actual metadata update is implemented
        # For now, the function just logs the metadata
        pass


class TestTextExtraction:
    """Test cases for text extraction functions."""

    @patch('src.processing.blob_trigger_processor.vision_service')
    def test_extract_text_from_file_image(
        self,
        mock_vision_service
    ):
        """Test text extraction from image file."""
        # Arrange
        mock_vision_service.extract_text_from_image_file.return_value = "Extracted text from image"
        
        # Act
        result = extract_text_from_file("/tmp/test.jpg", "test.jpg")
        
        # Assert
        assert result == "Extracted text from image"
        mock_vision_service.extract_text_from_image_file.assert_called_once_with("/tmp/test.jpg")

    @patch('src.processing.blob_trigger_processor.PyPDF2')
    def test_extract_text_from_pdf_success(self, mock_pypdf2):
        """Test successful PDF text extraction."""
        # Arrange
        mock_reader = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Act
        with patch('builtins.open', mock_open(read_data=b"pdf content")):
            result = extract_text_from_pdf("/tmp/test.pdf")
        
        # Assert
        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch('src.processing.blob_trigger_processor.PyPDF2')
    def test_extract_text_from_pdf_failure(self, mock_pypdf2):
        """Test PDF text extraction failure."""
        # Arrange
        mock_pypdf2.PdfReader.side_effect = Exception("PDF error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to extract text from PDF"):
            with patch('builtins.open', mock_open(read_data=b"pdf content")):
                extract_text_from_pdf("/tmp/test.pdf")

    @patch('src.processing.blob_trigger_processor.Document')
    def test_extract_text_from_word_success(self, mock_document):
        """Test successful Word document text extraction."""
        # Arrange
        mock_doc = Mock()
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "Paragraph 1"
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Paragraph 2"
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        mock_document.return_value = mock_doc
        
        # Act
        result = extract_text_from_word("/tmp/test.docx")
        
        # Assert
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result

    @patch('src.processing.blob_trigger_processor.Document')
    def test_extract_text_from_word_failure(self, mock_document):
        """Test Word document text extraction failure."""
        # Arrange
        mock_document.side_effect = Exception("Word error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to extract text from Word document"):
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
        result = extract_text_from_file("/tmp/test.xyz", "test.xyz")
        
        # Assert
        assert result == ""

    @patch('src.processing.blob_trigger_processor.vision_service')
    def test_extract_text_from_file_vision_service_failure(
        self,
        mock_vision_service
    ):
        """Test handling of vision service failure."""
        # Arrange
        mock_vision_service.extract_text_from_image_file.side_effect = Exception("Vision error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to extract text from test.jpg"):
            extract_text_from_file("/tmp/test.jpg", "test.jpg") 