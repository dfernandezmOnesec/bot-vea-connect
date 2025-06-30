"""
Azure Blob Storage operations module.

This module provides functions for uploading, downloading, and managing
documents in Azure Blob Storage with production-grade error handling
and comprehensive logging.
"""

import logging
import os
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import AzureError, ResourceNotFoundError, ClientAuthenticationError
from src.config.settings import settings

logger = logging.getLogger(__name__)

class AzureBlobStorageService:
    """Service class for Azure Blob Storage operations with production-grade features."""
    
    def __init__(self):
        """Initialize the Azure Blob Storage service with connection validation."""
        try:
            self.connection_string = settings.azure_storage_connection_string
            self.container_name = settings.blob_container_name
            self.account_name = settings.blob_account_name
            
            # Initialize clients
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # Validate connection and container
            self._validate_connection()
            
            logger.info(f"Azure Blob Storage service initialized successfully for container: {self.container_name}")
            
        except ClientAuthenticationError as e:
            logger.error(f"Authentication failed for Azure Blob Storage: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage service: {e}")
            raise

    def _validate_connection(self) -> None:
        """
        Validate the connection to Azure Blob Storage.
        
        Raises:
            Exception: If connection validation fails
        """
        try:
            # Test container access
            self.container_client.get_container_properties()
            logger.debug("Azure Blob Storage connection validated successfully")
        except Exception as e:
            logger.error(f"Azure Blob Storage connection validation failed: {e}")
            raise

    def upload_file(
        self, 
        file_path: str, 
        blob_name: str, 
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to Azure Blob Storage with enhanced metadata.
        
        Args:
            file_path: Local path to the file to upload
            blob_name: Name to assign to the blob in storage
            metadata: Optional metadata to attach to the blob
            content_type: Optional content type for the blob
            
        Returns:
            str: URL of the uploaded blob
            
        Raises:
            FileNotFoundError: If the source file doesn't exist
            AzureError: If upload fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            # Get file size for logging
            file_size = os.path.getsize(file_path)
            
            # Prepare metadata
            upload_metadata = {
                "upload_date": datetime.utcnow().isoformat(),
                "file_size": str(file_size),
                "source_path": file_path
            }
            if metadata:
                upload_metadata.update(metadata)
            
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Upload with content type if specified
            with open(file_path, "rb") as data:
                blob_client.upload_blob(
                    data, 
                    metadata=upload_metadata, 
                    overwrite=True,
                    content_settings=None if not content_type else 
                        blob_client.get_blob_properties().content_settings
                )
            
            blob_url = blob_client.url
            logger.info(f"File uploaded successfully: {blob_name} ({file_size} bytes) -> {blob_url}")
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

    def upload_stream(
        self, 
        data_stream: BinaryIO, 
        blob_name: str, 
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload data from a stream to Azure Blob Storage.
        
        Args:
            data_stream: Binary stream containing the data to upload
            blob_name: Name to assign to the blob in storage
            metadata: Optional metadata to attach to the blob
            content_type: Optional content type for the blob
            
        Returns:
            str: URL of the uploaded blob
            
        Raises:
            AzureError: If upload fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            # Prepare metadata
            upload_metadata = {
                "upload_date": datetime.utcnow().isoformat(),
                "upload_method": "stream"
            }
            if metadata:
                upload_metadata.update(metadata)
            
            blob_client = self.container_client.get_blob_client(blob_name)
            
            blob_client.upload_blob(
                data_stream, 
                metadata=upload_metadata, 
                overwrite=True
            )
            
            blob_url = blob_client.url
            logger.info(f"Stream uploaded successfully: {blob_name} -> {blob_url}")
            return blob_url
            
        except AzureError as e:
            logger.error(f"Azure Blob Storage stream upload failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading stream {blob_name}: {e}")
            raise

    def download_file(self, blob_name: str, destination_path: str) -> bool:
        """
        Download a file from Azure Blob Storage.
        
        Args:
            blob_name: Name of the blob to download
            destination_path: Local path where to save the file
            
        Returns:
            bool: True if download successful
            
        Raises:
            ResourceNotFoundError: If blob doesn't exist
            AzureError: If download fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            with open(destination_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            file_size = os.path.getsize(destination_path)
            logger.info(f"File downloaded successfully: {blob_name} -> {destination_path} ({file_size} bytes)")
            return True
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except AzureError as e:
            logger.error(f"Azure Blob Storage download failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}")
            raise

    def download_stream(self, blob_name: str) -> BinaryIO:
        """
        Download a blob as a stream.
        
        Args:
            blob_name: Name of the blob to download
            
        Returns:
            BinaryIO: Stream containing the blob data
            
        Raises:
            ResourceNotFoundError: If blob doesn't exist
            AzureError: If download fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            
            logger.info(f"Stream download initiated for blob: {blob_name}")
            return download_stream
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except AzureError as e:
            logger.error(f"Azure Blob Storage stream download failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to download blob stream {blob_name}: {e}")
            raise

    def list_blobs(
        self, 
        name_starts_with: Optional[str] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List blobs in the container with optional filtering.
        
        Args:
            name_starts_with: Optional prefix to filter blob names
            include_metadata: Whether to include blob metadata in results
            
        Returns:
            List[Dict[str, Any]]: List of blob information dictionaries
            
        Raises:
            AzureError: If listing fails due to Azure service issues
            Exception: For other unexpected errors
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
                    "etag": blob.etag
                }
                
                if include_metadata and blob.metadata:
                    blob_info["metadata"] = blob.metadata
                
                blobs.append(blob_info)
            
            logger.info(f"Listed {len(blobs)} blobs from container (filter: {name_starts_with or 'all'})")
            return blobs
            
        except AzureError as e:
            logger.error(f"Azure Blob Storage listing failed: {e}")
            raise
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
            AzureError: If deletion fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            
            logger.info(f"Blob deleted successfully: {blob_name}")
            return True
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found for deletion: {blob_name}")
            raise
        except AzureError as e:
            logger.error(f"Azure Blob Storage deletion failed for {blob_name}: {e}")
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
            AzureError: If metadata retrieval fails due to Azure service issues
            Exception: For other unexpected errors
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
        except AzureError as e:
            logger.error(f"Azure Blob Storage metadata retrieval failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for blob {blob_name}: {e}")
            raise

    def blob_exists(self, blob_name: str) -> bool:
        """
        Check if a blob exists in the container.
        
        Args:
            blob_name: Name of the blob to check
            
        Returns:
            bool: True if blob exists, False otherwise
            
        Raises:
            AzureError: If check fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            exists = blob_client.exists()
            
            logger.debug(f"Blob existence check for {blob_name}: {exists}")
            return exists
            
        except AzureError as e:
            logger.error(f"Azure Blob Storage existence check failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to check blob existence for {blob_name}: {e}")
            raise

    def get_blob_properties(self, blob_name: str) -> Dict[str, Any]:
        """
        Get comprehensive properties for a specific blob.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Dict[str, Any]: Blob properties dictionary
            
        Raises:
            ResourceNotFoundError: If blob doesn't exist
            AzureError: If properties retrieval fails due to Azure service issues
            Exception: For other unexpected errors
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            
            blob_properties = {
                "name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "etag": properties.etag,
                "metadata": properties.metadata or {},
                "blob_type": properties.blob_type,
                "lease_status": properties.lease.status if properties.lease else None
            }
            
            logger.info(f"Retrieved properties for blob: {blob_name}")
            return blob_properties
            
        except ResourceNotFoundError as e:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except AzureError as e:
            logger.error(f"Azure Blob Storage properties retrieval failed for {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get properties for blob {blob_name}: {e}")
            raise

# Global instance for easy access
blob_storage_service = AzureBlobStorageService() 