"""
Unit tests for Azure Blob Storage service module.

This module contains comprehensive tests for the AzureBlobStorageService class
with mocked external dependencies and full coverage of all methods.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from azure.core.exceptions import AzureError, ResourceNotFoundError, ClientAuthenticationError
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient

# Mock settings ANTES de importar el servicio
with patch('shared_code.azure_blob_storage.settings') as mock_settings:
    mock_settings.azure_storage_connection_string = "test_connection_string"
    mock_settings.blob_container_name = "test-container"
    mock_settings.blob_account_name = "testaccount"
    from shared_code.azure_blob_storage import AzureBlobStorageService
    from shared_code.azure_blob_storage import blob_storage_service


class TestAzureBlobStorageService:
    """Test cases for AzureBlobStorageService class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('shared_code.azure_blob_storage.settings') as mock_settings:
            mock_settings.azure_storage_connection_string = "test_connection_string"
            mock_settings.blob_container_name = "test-container"
            mock_settings.blob_account_name = "testaccount"
            yield mock_settings

    @pytest.fixture
    def mock_blob_service_client(self):
        """Mock BlobServiceClient."""
        with patch('shared_code.azure_blob_storage.BlobServiceClient') as mock_client:
            yield mock_client

    @pytest.fixture
    def mock_container_client(self):
        """Mock ContainerClient."""
        mock_client = Mock(spec=ContainerClient)
        mock_client.get_container_properties.return_value = Mock()
        return mock_client

    @pytest.fixture
    def blob_storage_service(self, mock_settings, mock_blob_service_client, mock_container_client):
        """Create AzureBlobStorageService instance with mocked dependencies."""
        mock_blob_service_client.from_connection_string.return_value.get_container_client.return_value = mock_container_client
        
        with patch('shared_code.azure_blob_storage.AzureBlobStorageService._validate_connection'):
            service = AzureBlobStorageService()
            service.container_client = mock_container_client
            return service

    def test_init_success(self, mock_settings, mock_blob_service_client, mock_container_client):
        """Test successful initialization of AzureBlobStorageService."""
        with patch('shared_code.azure_blob_storage.AzureBlobStorageService._validate_connection'):
            service = AzureBlobStorageService()
            # Verificar que los atributos se inicializaron correctamente
            assert hasattr(service, 'connection_string')
            assert hasattr(service, 'container_name')
            assert hasattr(service, 'account_name')
            assert hasattr(service, 'container_client')

    def test_init_authentication_error(self, mock_settings, mock_blob_service_client):
        """Test initialization with authentication error."""
        with patch('shared_code.azure_blob_storage.BlobServiceClient.from_connection_string', 
                  side_effect=ClientAuthenticationError("Auth failed")):
            with pytest.raises(ClientAuthenticationError):
                AzureBlobStorageService()

    def test_init_general_error(self, mock_settings, mock_blob_service_client):
        """Test initialization with general error."""
        mock_blob_service_client.from_connection_string.side_effect = Exception("General error")
        with patch('shared_code.azure_blob_storage.settings', mock_settings):
            with pytest.raises(Exception):
                AzureBlobStorageService()

    def test_validate_connection_success(self, blob_storage_service):
        """Test successful connection validation."""
        blob_storage_service._validate_connection()
        blob_storage_service.container_client.get_container_properties.assert_called_once()

    def test_validate_connection_failure(self, blob_storage_service):
        """Test connection validation failure."""
        blob_storage_service.container_client.get_container_properties.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            blob_storage_service._validate_connection()

    def test_upload_file_success(self, blob_storage_service):
        """Test successful file upload."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.url = "https://test.blob.core.windows.net/test-container/test.txt"
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with patch('builtins.open', mock_open(read_data=b"test content")), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=12):
            
            result = blob_storage_service._upload_file_internal("test.txt", "test-blob.txt")
            
            assert result == "https://test.blob.core.windows.net/test-container/test.txt"
            mock_blob_client.upload_blob.assert_called_once()

    def test_upload_file_file_not_found(self, blob_storage_service):
        """Test file upload with non-existent file."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                blob_storage_service._upload_file_internal("nonexistent.txt", "test-blob.txt")

    def test_upload_file_azure_error(self, blob_storage_service):
        """Test file upload with Azure error."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.upload_blob.side_effect = AzureError("Upload failed")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with patch('builtins.open', mock_open(read_data=b"test content")), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=12):
            
            with pytest.raises(AzureError):
                blob_storage_service._upload_file_internal("test.txt", "test-blob.txt")

    def test_upload_stream_success(self, blob_storage_service):
        """Test successful stream upload."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.url = "https://test.blob.core.windows.net/test-container/test-stream.txt"
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        mock_stream = Mock()
        mock_stream.read.return_value = b"test content"
        
        result = blob_storage_service.upload_stream(mock_stream, "test-stream.txt")
        
        assert result == "https://test.blob.core.windows.net/test-container/test-stream.txt"
        mock_blob_client.upload_blob.assert_called_once()

    def test_upload_stream_azure_error(self, blob_storage_service):
        """Test stream upload with Azure error."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.upload_blob.side_effect = AzureError("Upload failed")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        mock_stream = Mock()
        
        with pytest.raises(AzureError):
            blob_storage_service.upload_stream(mock_stream, "test-stream.txt")

    def test_download_file_success(self, blob_storage_service):
        """Test successful file download."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_download_stream = Mock()
        mock_download_stream.readall.return_value = b"test content"
        mock_blob_client.download_blob.return_value = mock_download_stream
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with patch('builtins.open', mock_open()), \
             patch('os.makedirs'), \
             patch('os.path.getsize', return_value=12):
            
            result = blob_storage_service._download_file_internal("test-blob.txt", "local-test.txt")
            
            assert result is True
            mock_blob_client.download_blob.assert_called_once()

    def test_download_file_resource_not_found(self, blob_storage_service):
        """Test file download with non-existent blob."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with patch('os.makedirs'), \
             patch('builtins.open', mock_open()), \
             pytest.raises(ResourceNotFoundError):
            blob_storage_service._download_file_internal("nonexistent.txt", "/tmp/local.txt")

    def test_download_stream_success(self, blob_storage_service):
        """Test successful stream download."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_download_stream = Mock()
        mock_blob_client.download_blob.return_value = mock_download_stream
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        result = blob_storage_service.download_stream("test-blob.txt")
        
        assert result == mock_download_stream
        mock_blob_client.download_blob.assert_called_once()

    def test_download_stream_resource_not_found(self, blob_storage_service):
        """Test stream download with non-existent blob."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with pytest.raises(ResourceNotFoundError):
            blob_storage_service.download_stream("nonexistent.txt")

    def test_list_blobs_success(self, blob_storage_service):
        """Test successful blob listing."""
        mock_blob1 = Mock()
        mock_blob1.name = "test1.txt"
        mock_blob1.size = 100
        mock_blob1.last_modified = datetime.now()
        mock_blob1.content_settings.content_type = "text/plain"
        mock_blob1.etag = "etag1"
        mock_blob1.metadata = {"key1": "value1"}
        
        mock_blob2 = Mock()
        mock_blob2.name = "test2.txt"
        mock_blob2.size = 200
        mock_blob2.last_modified = datetime.now()
        mock_blob2.content_settings.content_type = "text/plain"
        mock_blob2.etag = "etag2"
        mock_blob2.metadata = None
        
        blob_storage_service.container_client.list_blobs.return_value = [mock_blob1, mock_blob2]
        
        result = blob_storage_service.list_blobs(include_metadata=True)
        
        assert len(result) == 2
        assert result[0]["name"] == "test1.txt"
        assert result[0]["metadata"] == {"key1": "value1"}
        assert result[1]["name"] == "test2.txt"
        assert "metadata" not in result[1]

    def test_list_blobs_azure_error(self, blob_storage_service):
        """Test blob listing with Azure error."""
        blob_storage_service.container_client.list_blobs.side_effect = AzureError("List failed")
        
        with pytest.raises(AzureError):
            blob_storage_service.list_blobs()

    def test_delete_blob_success(self, blob_storage_service):
        """Test successful blob deletion."""
        mock_blob_client = Mock(spec=BlobClient)
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        result = blob_storage_service.delete_blob("test-blob.txt")
        
        assert result is True
        mock_blob_client.delete_blob.assert_called_once()

    def test_delete_blob_resource_not_found(self, blob_storage_service):
        """Test blob deletion with non-existent blob."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.delete_blob.side_effect = ResourceNotFoundError("Blob not found")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with pytest.raises(ResourceNotFoundError):
            blob_storage_service.delete_blob("nonexistent.txt")

    def test_get_blob_metadata_success(self, blob_storage_service):
        """Test successful metadata retrieval."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_properties = Mock()
        mock_properties.metadata = {"key1": "value1", "key2": "value2"}
        mock_blob_client.get_blob_properties.return_value = mock_properties
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        result = blob_storage_service.get_blob_metadata("test-blob.txt")
        
        assert result == {"key1": "value1", "key2": "value2"}
        mock_blob_client.get_blob_properties.assert_called_once()

    def test_get_blob_metadata_resource_not_found(self, blob_storage_service):
        """Test metadata retrieval with non-existent blob."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.get_blob_properties.side_effect = ResourceNotFoundError("Blob not found")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with pytest.raises(ResourceNotFoundError):
            blob_storage_service.get_blob_metadata("nonexistent.txt")

    def test_blob_exists_true(self, blob_storage_service):
        """Test blob existence check when blob exists."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.exists.return_value = True
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        result = blob_storage_service.blob_exists("test-blob.txt")
        
        assert result is True
        mock_blob_client.exists.assert_called_once()

    def test_blob_exists_false(self, blob_storage_service):
        """Test blob existence check when blob doesn't exist."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.exists.return_value = False
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        result = blob_storage_service.blob_exists("test-blob.txt")
        
        assert result is False
        mock_blob_client.exists.assert_called_once()

    def test_blob_exists_azure_error(self, blob_storage_service):
        """Test blob existence check with Azure error."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.exists.side_effect = AzureError("Check failed")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with pytest.raises(AzureError):
            blob_storage_service.blob_exists("test-blob.txt")

    def test_get_blob_properties_success(self, blob_storage_service):
        """Test successful blob properties retrieval."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_properties = Mock()
        mock_properties.size = 1000
        mock_properties.last_modified = datetime.now()
        mock_properties.content_settings.content_type = "text/plain"
        mock_properties.etag = "etag123"
        mock_properties.metadata = {"key1": "value1"}
        mock_properties.blob_type = "BlockBlob"
        mock_properties.lease = None
        mock_blob_client.get_blob_properties.return_value = mock_properties
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        result = blob_storage_service.get_blob_properties("test-blob.txt")
        
        assert result["name"] == "test-blob.txt"
        assert result["size"] == 1000
        assert result["content_type"] == "text/plain"
        assert result["etag"] == "etag123"
        assert result["metadata"] == {"key1": "value1"}
        assert result["blob_type"] == "BlockBlob"
        assert result["lease_status"] is None

    def test_get_blob_properties_resource_not_found(self, blob_storage_service):
        """Test blob properties retrieval with non-existent blob."""
        mock_blob_client = Mock(spec=BlobClient)
        mock_blob_client.get_blob_properties.side_effect = ResourceNotFoundError("Blob not found")
        blob_storage_service.container_client.get_blob_client.return_value = mock_blob_client
        
        with pytest.raises(ResourceNotFoundError):
            blob_storage_service.get_blob_properties("nonexistent.txt")


class TestAzureBlobStorageServiceGlobal:
    """Test cases for global AzureBlobStorageService instance."""

    def test_global_instance_creation(self):
        """Test that global instance is created correctly."""
        from shared_code.azure_blob_storage import blob_storage_service
        
        assert blob_storage_service is not None
        assert hasattr(blob_storage_service, 'container_client') 