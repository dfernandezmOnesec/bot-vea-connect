"""
Utility functions module for Bot-Vea-Connect.

This module provides common utility functions used across the application
for file processing, text manipulation, validation, and other helper operations.
"""

import logging
import os
import hashlib
import uuid
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

def generate_document_id(filename: str, content_hash: Optional[str] = None) -> str:
    """
    Generate a unique document ID based on filename and optional content hash.
    
    Args:
        filename: Original filename
        content_hash: Optional hash of document content
        
    Returns:
        str: Unique document identifier
    """
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        
        if content_hash:
            doc_id = f"{base_name}_{content_hash[:8]}_{timestamp}"
        else:
            doc_id = f"{base_name}_{uuid.uuid4().hex[:8]}_{timestamp}"
        
        logger.info(f"Generated document ID: {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"Failed to generate document ID: {e}")
        raise

def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file using specified algorithm.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (md5, sha1, sha256)
        
    Returns:
        str: Hexadecimal hash string
        
    Raises:
        Exception: If hash calculation fails
    """
    try:
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        file_hash = hash_func.hexdigest()
        logger.info(f"File hash calculated: {algorithm} = {file_hash[:16]}...")
        return file_hash
        
    except FileNotFoundError as e:
        logger.error(f"File not found for hash calculation: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to calculate file hash: {e}")
        raise

def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dict[str, Any]: File metadata including size, type, timestamps
        
    Raises:
        Exception: If metadata extraction fails
    """
    try:
        file_stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        metadata = {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": file_stat.st_size,
            "mime_type": mime_type or "application/octet-stream",
            "extension": Path(file_path).suffix.lower(),
            "created_time": datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc).isoformat(),
            "modified_time": datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat(),
            "accessed_time": datetime.fromtimestamp(file_stat.st_atime, tz=timezone.utc).isoformat()
        }
        
        logger.info(f"File metadata extracted: {metadata['filename']}, {metadata['file_size']} bytes")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to get file metadata: {e}")
        raise

def validate_file_type(file_path: str, allowed_extensions: List[str]) -> bool:
    """
    Validate if file has an allowed extension.
    
    Args:
        file_path: Path to the file
        allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.docx'])
        
    Returns:
        bool: True if file type is allowed
        
    Raises:
        Exception: If validation fails
    """
    try:
        file_extension = Path(file_path).suffix.lower()
        is_allowed = file_extension in allowed_extensions
        
        if not is_allowed:
            logger.warning(f"File type not allowed: {file_extension}. Allowed: {allowed_extensions}")
        
        return is_allowed
        
    except Exception as e:
        logger.error(f"Failed to validate file type: {e}")
        return False

def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        str: Cleaned and normalized text
    """
    try:
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might cause issues
        cleaned = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', '', cleaned)
        
        # Normalize line breaks
        cleaned = re.sub(r'\n+', '\n', cleaned)
        
        logger.info(f"Text cleaned. Original length: {len(text)}, Cleaned length: {len(cleaned)}")
        return cleaned
        
    except Exception as e:
        logger.error(f"Failed to clean text: {e}")
        return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks for processing.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    try:
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        logger.info(f"Text chunked into {len(chunks)} pieces")
        return chunks
        
    except Exception as e:
        logger.error(f"Failed to chunk text: {e}")
        return [text]

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    try:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
        
    except Exception as e:
        logger.error(f"Failed to format file size: {e}")
        return f"{size_bytes} B"

def create_safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing or replacing unsafe characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Safe filename
    """
    try:
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        safe_filename = safe_filename.strip('. ')
        
        # Ensure filename is not empty
        if not safe_filename:
            safe_filename = "unnamed_file"
        
        logger.info(f"Safe filename created: {filename} -> {safe_filename}")
        return safe_filename
        
    except Exception as e:
        logger.error(f"Failed to create safe filename: {e}")
        return "unnamed_file"

def parse_json_safely(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string with error handling.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON object or None if parsing fails
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return None

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email format is valid
    """
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = re.match(pattern, email) is not None
        
        if not is_valid:
            logger.warning(f"Invalid email format: {email}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Failed to validate email: {e}")
        return False

def retry_operation(operation, max_retries: int = 3, delay: float = 1.0):
    """
    Retry an operation with exponential backoff.
    
    Args:
        operation: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        
    Returns:
        Any: Result of the operation
        
    Raises:
        Exception: If all retries fail
    """
    try:
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s: {e}")
                    
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error(f"Operation failed after {max_retries + 1} attempts")
                    raise last_exception
                    
    except Exception as e:
        logger.error(f"Retry operation failed: {e}")
        raise

def format_timestamp(timestamp: Union[datetime, str, float], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to string.
    
    Args:
        timestamp: Timestamp to format (datetime, string, or float)
        format_str: Format string for datetime
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        if isinstance(timestamp, str):
            # Try to parse string timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                dt = datetime.fromtimestamp(float(timestamp))
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")
        
        return dt.strftime(format_str)
        
    except Exception as e:
        logger.error(f"Failed to format timestamp: {e}")
        return str(timestamp)

def sanitize_log_message(message: str) -> str:
    """
    Sanitize log message to remove sensitive information.
    
    Args:
        message: Original log message
        
    Returns:
        str: Sanitized log message
    """
    try:
        # Remove potential sensitive data patterns
        patterns = [
            r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
            r'api_key["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
            r'token["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
            r'secret["\']?\s*[:=]\s*["\']?[^"\s]+["\']?'
        ]
        
        sanitized = message
        for pattern in patterns:
            sanitized = re.sub(pattern, r'\1=***', sanitized, flags=re.IGNORECASE)
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Failed to sanitize log message: {e}")
        return message 