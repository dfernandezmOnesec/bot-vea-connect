"""
Azure Blob Storage operations module.

This module provides functions for uploading, downloading, and managing
documents in Azure Blob Storage.
"""

import logging
from typing import Optional, List, Dict, Any
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import AzureError, ResourceNotFoundError
from src.config.settings import settings

logger = logging.getLogger(__name__)

class AzureBlobStorageService:
    """Service class for Azure Blob Storage operations."""
    
    def __init__(self):
        """Initialize the Azure Blob Storage service."""
        try:
            self.connection_string = settings.azure_storage_connection_string
            self.container_name = settings.blob_container_name
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            logger.info(f"Azure Blob Storage service initialized for container: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage service: {e}")
            raise

    def upload_file(self, file_path: str, blob_name: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_path: Local path to the file to upload
            blob_name: Name to assign to the blob in storage
            metadata: Optional metadata to attach to the blob
            
        Returns:
            str: URL of the uploaded blob
            
        Raises:
            AzureError: If upload fails
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, metadata=metadata, overwrite=True)
            
            blob_url = blob_client.url
            logger.info(f"File uploaded successfully: {blob_name} -> {blob_url}")
            return blob_url
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise
        except AzureError as e:
            logger.error(f"Azure Blob Storage upload failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading {blob_name}: {e}")
            raise

    def download_file(self, blob_name: str, destination_path: str) -> bool:
        """
        Download a file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to download
            destination_path: Local path where to save the file
            
        Returns:
            bool: True if download successful, False otherwise
            
        Raises:
            ResourceNotFoundError: If blob doesn't exist
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            with open(destination_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"File downloaded successfully: {blob_name} -> {destination_path}")
            return True
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}")
            raise

    def list_blobs(self, name_starts_with: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List blobs in the container.
        
        Args:
            name_starts_with: Optional prefix to filter blob names
            
        Returns:
            List[Dict[str, Any]]: List of blob information dictionaries
        """
        try:
            blobs = []
            blob_list = self.container_client.list_blobs(name_starts_with=name_starts_with)
            
            for blob in blob_list:
                blob_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type,
                    "metadata": blob.metadata
                }
                blobs.append(blob_info)
            
            logger.info(f"Listed {len(blobs)} blobs from container")
            return blobs
            
        except Exception as e:
            logger.error(f"Failed to list blobs: {e}")
            raise

    def delete_blob(self, blob_name: str) -> bool:
        """
        Delete a blob from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ResourceNotFoundError: If blob doesn't exist
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"Blob deleted successfully: {blob_name}")
            return True
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found for deletion: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            raise

    def get_blob_metadata(self, blob_name: str) -> Dict[str, str]:
        """
        Get metadata for a specific blob.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Dict[str, str]: Blob metadata dictionary
            
        Raises:
            ResourceNotFoundError: If blob doesn't exist
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            
            metadata = properties.metadata or {}
            logger.info(f"Retrieved metadata for blob: {blob_name}")
            return metadata
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for blob {blob_name}: {e}")
            raise

# Global instance for easy access
blob_storage_service = AzureBlobStorageService() 