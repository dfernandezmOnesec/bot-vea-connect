"""
Batch Push Results Azure Function.

This function is triggered by Queue Storage messages to process files,
generate embeddings, and store them in Redis for semantic search.
"""

import azure.functions as func
import logging
import json
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path
from shared_code.azure_blob_storage import blob_storage_service
from shared_code.openai_service import openai_service
from shared_code.redis_service import redis_service
from shared_code.vision_service import vision_service
from shared_code.utils import generate_document_id, calculate_file_hash, clean_text, chunk_text
from config.settings import settings

logger = logging.getLogger(__name__)

def main(msg: func.QueueMessage) -> None:
    """
    Processes queue messages to generate embeddings for documents.
    
    This function:
    1. Receives a filename from the queue
    2. Downloads file content from Blob Storage
    3. Extracts text based on file type (PDF, Image, Text)
    4. Generates embeddings using OpenAI
    5. Stores embeddings and metadata in Redis
    6. Updates blob metadata to mark as processed
    
    Args:
        msg (func.QueueMessage): The queue message containing file information.
        
    Raises:
        Exception: If document processing fails.
    """
    try:
        # Parse queue message
        message_body = msg.get_body().decode('utf-8')
        queue_data = json.loads(message_body)
        
        blob_name = queue_data.get("blob_name")
        blob_url = queue_data.get("blob_url")
        file_size = queue_data.get("file_size", 0)
        content_type = queue_data.get("content_type", "")
        
        logger.info(f"Processing queue message for blob: {blob_name}")
        
        if not blob_name:
            logger.error("Queue message missing blob_name")
            return
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(blob_name).suffix) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Download file from blob storage
            download_success = blob_storage_service.download_file(blob_name, temp_file_path)
            if not download_success:
                logger.error(f"Failed to download blob: {blob_name}")
                return
            
            logger.info(f"Successfully downloaded blob: {blob_name}")
            
            # Get file metadata
            file_metadata = blob_storage_service.get_blob_metadata(blob_name)
            
            # Calculate file hash for document ID
            file_hash = calculate_file_hash(temp_file_path)
            document_id = generate_document_id(blob_name, file_hash)
            
            # Extract text based on file type
            extracted_text = extract_text_from_file(temp_file_path, blob_name, content_type)
            if not extracted_text:
                logger.warning(f"No text extracted from file: {blob_name}")
                return
            
            # Clean and chunk text
            cleaned_text = clean_text(extracted_text)
            text_chunks = chunk_text(cleaned_text, chunk_size=1000, overlap=100)
            
            logger.info(f"Text extracted and chunked. Original length: {len(extracted_text)}, Chunks: {len(text_chunks)}")
            
            # Generate embeddings for each chunk
            embeddings = []
            for i, chunk in enumerate(text_chunks):
                try:
                    embedding = openai_service.generate_embeddings(chunk)
                    embeddings.append({
                        "chunk_index": i,
                        "text": chunk,
                        "embedding": embedding
                    })
                    logger.info(f"Generated embedding for chunk {i+1}/{len(text_chunks)}")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                    continue
            
            if not embeddings:
                logger.error("No embeddings generated for any chunks")
                return
            
            # Store embeddings and metadata in Redis
            store_document_embeddings(document_id, blob_name, embeddings, file_metadata)
            
            # Update blob metadata to mark as processed
            update_blob_metadata(blob_name, document_id, len(embeddings))
            
            logger.info(f"Successfully processed document: {document_id}")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"Temporary file cleaned up: {temp_file_path}")
                
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse queue message JSON: {e}")
        raise
    except Exception as e:
        error_message = f"Failed to process queue message: {str(e)}"
        logger.error(error_message)
        raise

def extract_text_from_file(file_path: str, blob_name: str, content_type: str) -> str:
    """
    Extract text from file based on its type and content type.
    
    Args:
        file_path: Path to the temporary file
        blob_name: Original blob name for reference
        content_type: MIME content type of the file
        
    Returns:
        str: Extracted text content
        
    Raises:
        Exception: If text extraction fails
    """
    try:
        file_extension = Path(blob_name).suffix.lower()
        
        # Check if it's an image file (based on extension or content type)
        if (file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'] or 
            'image/' in content_type.lower()):
            # Process image files using Computer Vision
            logger.info(f"Processing image file with OCR: {blob_name}")
            return vision_service.extract_text_from_image_file(file_path)
            
        elif file_extension == '.pdf' or content_type == 'application/pdf':
            # Process PDF files
            logger.info(f"Processing PDF file: {blob_name}")
            return extract_text_from_pdf(file_path)
            
        elif file_extension in ['.docx', '.doc'] or 'word' in content_type.lower():
            # Process Word documents
            logger.info(f"Processing Word document: {blob_name}")
            return extract_text_from_word(file_path)
            
        elif (file_extension in ['.txt', '.md', '.csv'] or 
              'text/' in content_type.lower() or 
              'plain' in content_type.lower()):
            # Process text files
            logger.info(f"Processing text file: {blob_name}")
            return extract_text_from_text_file(file_path)
            
        else:
            logger.warning(f"Unsupported file type: {file_extension} (content_type: {content_type})")
            return ""
            
    except Exception as e:
        logger.error(f"Failed to extract text from {blob_name}: {e}")
        raise

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise

def extract_text_from_word(file_path: str) -> str:
    """
    Extract text from Word document.
    
    Args:
        file_path: Path to the Word document
        
    Returns:
        str: Extracted text content
    """
    try:
        from docx import Document
        
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Failed to extract text from Word document: {e}")
        raise

def extract_text_from_text_file(file_path: str) -> str:
    """
    Extract text from plain text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        str: File content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
            
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Failed to read text file with alternative encoding: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to read text file: {e}")
        raise

def store_document_embeddings(
    document_id: str, 
    blob_name: str, 
    embeddings: list, 
    file_metadata: Dict[str, Any]
) -> None:
    """
    Store document embeddings and metadata in Redis.
    
    Args:
        document_id: Unique document identifier
        blob_name: Original blob name
        embeddings: List of embeddings with text chunks
        file_metadata: File metadata from blob storage
        
    Raises:
        Exception: If storage fails
    """
    try:
        # Create document metadata
        document_metadata = {
            "document_id": document_id,
            "filename": blob_name,
            "text": " ".join([emb["text"] for emb in embeddings]),
            "content_type": file_metadata.get("content_type", ""),
            "upload_date": file_metadata.get("upload_date", ""),
            "file_size": file_metadata.get("file_size", 0),
            "chunks_count": len(embeddings),
            "processing_timestamp": file_metadata.get("processing_timestamp", ""),
            "embeddings_generated": "true"
        }
        
        # Store main document embedding (average of all chunks)
        if embeddings:
            # Calculate average embedding
            avg_embedding = []
            embedding_length = len(embeddings[0]["embedding"])
            
            for i in range(embedding_length):
                avg_value = sum(emb["embedding"][i] for emb in embeddings) / len(embeddings)
                avg_embedding.append(avg_value)
            
            # Store in Redis
            redis_service.store_embedding(document_id, avg_embedding, document_metadata)
            logger.info(f"Stored document embeddings in Redis: {document_id}")
            
    except Exception as e:
        logger.error(f"Failed to store document embeddings: {e}")
        raise

def update_blob_metadata(blob_name: str, document_id: str, chunks_count: int) -> None:
    """
    Update blob metadata to mark embeddings as added.
    
    Args:
        blob_name: Name of the blob
        document_id: Generated document ID
        chunks_count: Number of text chunks processed
        
    Raises:
        Exception: If metadata update fails
    """
    try:
        import datetime
        
        metadata = {
            "processed": "true",
            "document_id": document_id,
            "chunks_count": str(chunks_count),
            "embeddings_generated": "true",
            "processed_timestamp": datetime.datetime.now().isoformat()
        }
        
        # Note: This would require implementing update_metadata method in blob_storage_service
        # For now, we'll log the metadata that should be updated
        logger.info(f"Blob metadata to be updated for {blob_name}: {metadata}")
        
    except Exception as e:
        logger.error(f"Failed to update blob metadata: {e}")
        raise 