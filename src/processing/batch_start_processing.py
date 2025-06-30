"""
Batch Start Processing Azure Function.

This function is triggered via HTTP GET to start batch processing of documents.
It lists unprocessed files from Blob Storage and sends them to the processing queue.
"""

import azure.functions as func
import logging
import json
from typing import Dict, Any, List
from azure.storage.queue import QueueClient
from src.shared_code.azure_blob_storage import blob_storage_service
from src.config.settings import settings

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Processes incoming HTTP requests to start batch processing of files.
    
    This function:
    1. Lists all unprocessed files from Blob Storage
    2. Sends each file to the processing queue
    3. Returns a summary of the operation
    
    Args:
        req (func.HttpRequest): The incoming HTTP request.

    Returns:
        func.HttpResponse: HTTP response with processing summary.
        
    Raises:
        Exception: If blob listing or queue operations fail.
    """
    try:
        logger.info("Starting batch processing initialization")
        
        # Initialize queue client
        queue_client = QueueClient.from_connection_string(
            conn_str=settings.azure_storage_connection_string,
            queue_name=settings.queue_name
        )
        
        # List all blobs in the container
        blobs = blob_storage_service.list_blobs()
        logger.info(f"Found {len(blobs)} files in blob storage")
        
        # Filter for unprocessed files (files without 'processed' metadata)
        unprocessed_files = []
        for blob in blobs:
            metadata = blob.get("metadata", {})
            if not metadata.get("processed"):
                unprocessed_files.append(blob)
        
        logger.info(f"Found {len(unprocessed_files)} unprocessed files")
        
        # Send each unprocessed file to the queue
        queued_count = 0
        for blob in unprocessed_files:
            try:
                # Create queue message with blob information
                queue_message = {
                    "blob_name": blob["name"],
                    "blob_url": f"https://{settings.blob_account_name}.blob.core.windows.net/{settings.blob_container_name}/{blob['name']}",
                    "file_size": blob["size"],
                    "content_type": blob["content_type"],
                    "last_modified": blob["last_modified"].isoformat() if blob["last_modified"] else None
                }
                
                # Send message to queue
                queue_client.send_message(json.dumps(queue_message))
                queued_count += 1
                
                logger.info(f"Queued file for processing: {blob['name']}")
                
            except Exception as e:
                logger.error(f"Failed to queue file {blob['name']}: {e}")
                # Continue with other files even if one fails
        
        # Prepare response
        response_data = {
            "status": "success",
            "total_files": len(blobs),
            "unprocessed_files": len(unprocessed_files),
            "queued_files": queued_count,
            "message": f"Successfully queued {queued_count} files for processing"
        }
        
        logger.info(f"Batch processing initialization completed. Queued {queued_count} files")
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_message = f"Failed to start batch processing: {str(e)}"
        logger.error(error_message)
        
        error_response = {
            "status": "error",
            "message": error_message
        }
        
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype="application/json"
        ) 