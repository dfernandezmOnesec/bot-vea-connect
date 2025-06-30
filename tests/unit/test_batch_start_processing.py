"""
Unit tests for BatchStartProcessing Azure Function.
"""

import pytest
import json
import azure.functions as func
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from src.processing.batch_start_processing import main


@pytest.fixture
def mock_request():
    """Create a mock HTTP request."""
    req = Mock(spec=func.HttpRequest)
    req.method = "GET"
    req.url = "https://localhost/api/batch-start-processing"
    return req


@pytest.fixture
def mock_blobs():
    """Create mock blob data."""
    return [
        {
            "name": "document1.pdf",
            "size": 1024,
            "last_modified": datetime.now(timezone.utc),
            "content_type": "application/pdf",
            "metadata": {}
        },
        {
            "name": "document2.docx",
            "size": 2048,
            "last_modified": datetime.now(timezone.utc),
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "metadata": {"processed": "true"}
        },
        {
            "name": "document3.txt",
            "size": 512,
            "last_modified": datetime.now(timezone.utc),
            "content_type": "text/plain",
            "metadata": {}
        }
    ]


@pytest.fixture
def mock_queue_client():
    """Create a mock queue client."""
    client = Mock()
    client.send_message = Mock()
    return client


class TestBatchStartProcessing:
    """Test cases for BatchStartProcessing function."""

    @patch('src.processing.batch_start_processing.QueueClient')
    @patch('src.processing.batch_start_processing.blob_storage_service')
    @patch('src.processing.batch_start_processing.settings')
    def test_batch_start_processing_success(
        self, 
        mock_settings, 
        mock_blob_service, 
        mock_queue_client_class,
        mock_request,
        mock_blobs,
        mock_queue_client
    ):
        """Test successful batch processing initialization."""
        # Arrange
        mock_settings.azure_storage_connection_string = "test_connection_string"
        mock_settings.queue_name = "test_queue"
        mock_settings.blob_account_name = "testaccount"
        mock_settings.blob_container_name = "testcontainer"
        
        mock_blob_service.list_blobs.return_value = mock_blobs
        mock_queue_client_class.from_connection_string.return_value = mock_queue_client
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        
        response_data = json.loads(response.get_body().decode())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 3
        assert response_data["unprocessed_files"] == 2  # document1.pdf and document3.txt
        assert response_data["queued_files"] == 2
        
        # Verify blob service was called
        mock_blob_service.list_blobs.assert_called_once()
        
        # Verify queue client was initialized
        mock_queue_client_class.from_connection_string.assert_called_once_with(
            conn_str="test_connection_string",
            queue_name="test_queue"
        )
        
        # Verify messages were sent to queue
        assert mock_queue_client.send_message.call_count == 2
        
        # Verify correct message content for first file
        first_call_args = mock_queue_client.send_message.call_args_list[0][0][0]
        first_message = json.loads(first_call_args)
        assert first_message["blob_name"] == "document1.pdf"
        assert first_message["content_type"] == "application/pdf"

    @patch('src.processing.batch_start_processing.QueueClient')
    @patch('src.processing.batch_start_processing.blob_storage_service')
    @patch('src.processing.batch_start_processing.settings')
    def test_batch_start_processing_blob_service_failure(
        self, 
        mock_settings, 
        mock_blob_service, 
        mock_queue_client_class,
        mock_request
    ):
        """Test handling of blob service failure."""
        # Arrange
        mock_settings.azure_storage_connection_string = "test_connection_string"
        mock_settings.queue_name = "test_queue"
        
        mock_blob_service.list_blobs.side_effect = Exception("Blob service error")
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 500
        
        response_data = json.loads(response.get_body().decode())
        assert response_data["status"] == "error"
        assert "Failed to start batch processing" in response_data["message"]
        assert "Blob service error" in response_data["message"]

    @patch('src.processing.batch_start_processing.QueueClient')
    @patch('src.processing.batch_start_processing.blob_storage_service')
    @patch('src.processing.batch_start_processing.settings')
    def test_batch_start_processing_queue_failure(
        self, 
        mock_settings, 
        mock_blob_service, 
        mock_queue_client_class,
        mock_request,
        mock_blobs
    ):
        """Test handling of queue operation failure."""
        # Arrange
        mock_settings.azure_storage_connection_string = "test_connection_string"
        mock_settings.queue_name = "test_queue"
        mock_settings.blob_account_name = "testaccount"
        mock_settings.blob_container_name = "testcontainer"
        
        mock_blob_service.list_blobs.return_value = mock_blobs
        
        # Mock queue client that fails on send_message
        mock_queue_client = Mock()
        mock_queue_client.send_message.side_effect = Exception("Queue error")
        mock_queue_client_class.from_connection_string.return_value = mock_queue_client
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200  # Should still return success
        
        response_data = json.loads(response.get_body().decode())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 3
        assert response_data["unprocessed_files"] == 2
        assert response_data["queued_files"] == 0  # No files were successfully queued

    @patch('src.processing.batch_start_processing.QueueClient')
    @patch('src.processing.batch_start_processing.blob_storage_service')
    @patch('src.processing.batch_start_processing.settings')
    def test_batch_start_processing_no_unprocessed_files(
        self, 
        mock_settings, 
        mock_blob_service, 
        mock_queue_client_class,
        mock_request
    ):
        """Test when all files are already processed."""
        # Arrange
        mock_settings.azure_storage_connection_string = "test_connection_string"
        mock_settings.queue_name = "test_queue"
        
        # All files are processed
        processed_blobs = [
            {
                "name": "document1.pdf",
                "size": 1024,
                "last_modified": datetime.now(timezone.utc),
                "content_type": "application/pdf",
                "metadata": {"processed": "true"}
            },
            {
                "name": "document2.docx",
                "size": 2048,
                "last_modified": datetime.now(timezone.utc),
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "metadata": {"processed": "true"}
            }
        ]
        
        mock_blob_service.list_blobs.return_value = processed_blobs
        mock_queue_client = Mock()
        mock_queue_client_class.from_connection_string.return_value = mock_queue_client
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        
        response_data = json.loads(response.get_body().decode())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 2
        assert response_data["unprocessed_files"] == 0
        assert response_data["queued_files"] == 0
        
        # Verify no messages were sent to queue
        mock_queue_client.send_message.assert_not_called()

    @patch('src.processing.batch_start_processing.QueueClient')
    @patch('src.processing.batch_start_processing.blob_storage_service')
    @patch('src.processing.batch_start_processing.settings')
    def test_batch_start_processing_empty_container(
        self, 
        mock_settings, 
        mock_blob_service, 
        mock_queue_client_class,
        mock_request
    ):
        """Test when container is empty."""
        # Arrange
        mock_settings.azure_storage_connection_string = "test_connection_string"
        mock_settings.queue_name = "test_queue"
        
        mock_blob_service.list_blobs.return_value = []
        mock_queue_client = Mock()
        mock_queue_client_class.from_connection_string.return_value = mock_queue_client
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        
        response_data = json.loads(response.get_body().decode())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 0
        assert response_data["unprocessed_files"] == 0
        assert response_data["queued_files"] == 0
        
        # Verify no messages were sent to queue
        mock_queue_client.send_message.assert_not_called()

    @patch('src.processing.batch_start_processing.QueueClient')
    @patch('src.processing.batch_start_processing.blob_storage_service')
    @patch('src.processing.batch_start_processing.settings')
    def test_batch_start_processing_partial_queue_failure(
        self, 
        mock_settings, 
        mock_blob_service, 
        mock_queue_client_class,
        mock_request,
        mock_blobs
    ):
        """Test when some files fail to queue but others succeed."""
        # Arrange
        mock_settings.azure_storage_connection_string = "test_connection_string"
        mock_settings.queue_name = "test_queue"
        mock_settings.blob_account_name = "testaccount"
        mock_settings.blob_container_name = "testcontainer"
        
        mock_blob_service.list_blobs.return_value = mock_blobs
        
        # Mock queue client that fails on second message
        mock_queue_client = Mock()
        mock_queue_client.send_message.side_effect = [
            None,  # First call succeeds
            Exception("Queue error"),  # Second call fails
            None  # Third call succeeds
        ]
        mock_queue_client_class.from_connection_string.return_value = mock_queue_client
        
        # Act
        response = main(mock_request)
        
        # Assert
        assert response.status_code == 200
        
        response_data = json.loads(response.get_body().decode())
        assert response_data["status"] == "success"
        assert response_data["total_files"] == 3
        assert response_data["unprocessed_files"] == 2
        assert response_data["queued_files"] == 2  # Should still count successful ones
        
        # Verify messages were attempted for all unprocessed files
        assert mock_queue_client.send_message.call_count == 2 