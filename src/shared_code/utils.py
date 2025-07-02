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
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import mimetypes
import time

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

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None, name: str = "bot_vea_connect") -> logging.Logger:
    """
    Configura el logging global del proyecto.
    Args:
        level: Nivel de logging (por defecto INFO)
        log_file: Ruta a un archivo de log (opcional)
        name: Nombre del logger (por defecto bot_vea_connect)
    Returns:
        logging.Logger: Logger configurado
    """
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(level=level, format=log_format, handlers=handlers, force=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

def parse_whatsapp_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae información relevante de un mensaje de WhatsApp recibido vía webhook.
    Soporta mensajes de texto, imagen, audio, documento y maneja casos edge.
    Args:
        payload: Diccionario recibido del webhook de WhatsApp
    Returns:
        Dict con los campos extraídos:
            - type: Tipo de mensaje (text, image, audio, document, etc.)
            - from: Número del remitente
            - timestamp: Timestamp del mensaje
            - content: Texto del mensaje (si aplica)
            - media_id: ID del archivo multimedia (si aplica)
            - raw: El mensaje original extraído
    """
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [{}])
        if not messages or not isinstance(messages, list):
            return None
        msg = messages[0]
        msg_type = msg.get("type")
        sender = msg.get("from")
        timestamp = msg.get("timestamp")
        result = {
            "type": msg_type,
            "from": sender,
            "timestamp": timestamp,
            "raw": msg
        }
        if msg_type == "text":
            result["content"] = msg.get("text", {}).get("body", "")
        elif msg_type == "image":
            result["media_id"] = msg.get("image", {}).get("id")
            result["mime_type"] = msg.get("image", {}).get("mime_type")
        elif msg_type == "audio":
            result["media_id"] = msg.get("audio", {}).get("id")
            result["mime_type"] = msg.get("audio", {}).get("mime_type")
        elif msg_type == "document":
            result["media_id"] = msg.get("document", {}).get("id")
            result["mime_type"] = msg.get("document", {}).get("mime_type")
        return result
    except Exception as e:
        logger.error(f"Error al parsear mensaje de WhatsApp: {e}")
        return None

def extract_media_info(media_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraer información de archivos multimedia de WhatsApp.
    
    Args:
        media_data: Datos del archivo multimedia
        
    Returns:
        Dict con información del archivo multimedia
    """
    try:
        if not media_data or not media_data.get("id"):
            return None
        media_info = {
            "media_id": media_data.get("id"),
            "id": media_data.get("id"),
            "mime_type": media_data.get("mime_type"),
            "sha256": media_data.get("sha256"),
            "filename": media_data.get("filename"),
            "url": media_data.get("url") if "url" in media_data else None
        }
        return media_info
    except Exception as e:
        logger.error(f"Error extrayendo información multimedia: {str(e)}")
        return None

def format_response(message: str, success: bool = True, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Formatear respuesta para WhatsApp.
    
    Args:
        message: Mensaje a enviar
        success: Si la operación fue exitosa
        data: Datos adicionales
        
    Returns:
        Dict con respuesta formateada
    """
    try:
        response = {
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data:
            response["data"] = data
        
        return response
        
    except Exception as e:
        logger.error(f"Error formateando respuesta: {str(e)}")
        return {
            "success": False,
            "message": "Lo siento, hubo un error procesando tu mensaje.",
            "timestamp": datetime.utcnow().isoformat()
        }

def create_error_response(message: str, error_code: str = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Crear respuesta de error estandarizada.
    
    Args:
        message: Mensaje de error
        error_code: Código de error
        details: Detalles adicionales del error
        
    Returns:
        Dict con respuesta de error
    """
    response = {
        "success": False,
        "error": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if error_code:
        response["error_code"] = error_code
    if details:
        response["details"] = details
    return response

def validate_phone_number(phone_number: str) -> bool:
    """
    Validar formato de número de teléfono.
    
    Args:
        phone_number: Número de teléfono a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    try:
        if not phone_number:
            return False
        
        # Remover caracteres no numéricos
        clean_number = re.sub(r'[^\d]', '', phone_number)
        
        # Validar longitud mínima (7 dígitos) y máxima (15 dígitos)
        if len(clean_number) < 7 or len(clean_number) > 15:
            return False
        
        # Validar que solo contenga dígitos
        if not clean_number.isdigit():
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validando número de teléfono: {str(e)}")
        return False

def sanitize_text(text: str) -> str:
    """
    Sanitizar texto para evitar inyección de código.
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto sanitizado
    """
    try:
        if not text:
            return ""
        
        # Remover caracteres peligrosos
        sanitized = re.sub(r'[<>"\']', '', text)
        # Remover saltos de línea y tabulaciones
        sanitized = re.sub(r'[\n\t\r]', '', sanitized)
        
        # Limitar longitud
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized.strip()
        
    except Exception as e:
        logger.error(f"Error sanitizando texto: {str(e)}")
        return ""

def generate_session_id(phone_number: Optional[str] = None) -> str:
    """
    Generar ID único para sesión de usuario.
    
    Args:
        phone_number: Número de teléfono del usuario (opcional)
        
    Returns:
        ID único de sesión
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())
        
        if phone_number:
            return f"{phone_number}_{timestamp}_{unique_id}"
        else:
            return f"session_{timestamp}_{unique_id}"
        
    except Exception as e:
        logger.error(f"Error generando ID de sesión: {str(e)}")
        return f"session_{int(time.time())}"

def rate_limit_check(redis_service, phone_number: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """
    Verificar límite de velocidad para un número de teléfono.
    
    Args:
        redis_service: Servicio Redis
        phone_number: Número de teléfono
        max_requests: Máximo número de requests permitidos
        window_seconds: Ventana de tiempo en segundos
        
    Returns:
        True si está dentro del límite, False si excede
    """
    try:
        if not redis_service:
            return True  # Si no hay Redis, permitir
        
        key = f"rate_limit:{phone_number}"
        current_time = int(time.time())
        
        # Obtener requests actuales
        current_requests = redis_service.get(key)
        if current_requests is None:
            current_requests = 0
        else:
            current_requests = int(current_requests)
        
        # Verificar límite
        if current_requests >= max_requests:
            return False
        
        # Incrementar contador
        redis_service.setex(key, window_seconds, current_requests + 1)
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando límite de velocidad: {str(e)}")
        return True  # En caso de error, permitir

def validate_environment_variables(required_vars: Optional[List[str]] = None) -> bool:
    """
    Validar que todas las variables de entorno requeridas estén configuradas.
    
    Args:
        required_vars: Lista de variables requeridas (opcional, usa lista por defecto si no se proporciona)
        
    Returns:
        True si todas las variables están configuradas, False en caso contrario
    """
    try:
        from config.settings import get_settings
        settings = get_settings()
        
        if required_vars is None:
            required_vars = [
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_API_KEY", 
                "REDIS_CONNECTION_STRING",
                "WHATSAPP_TOKEN",
                "WHATSAPP_PHONE_NUMBER_ID"
            ]
        
        for var in required_vars:
            # Usar getattr para acceder a las variables a través de settings
            value = getattr(settings, var.lower(), None)
            if not value or not str(value).strip():
                logger.warning(f"Variable de entorno faltante o vacía: {var}")
                raise ValueError(f"Missing required environment variable: {var}")
        return True
        
    except Exception as e:
        logger.error(f"Error validando variables de entorno: {str(e)}")
        raise

def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Ejecutar función con reintentos y backoff exponencial.
    
    Args:
        func: Función a ejecutar
        max_retries: Número máximo de reintentos
        base_delay: Delay base en segundos
        max_delay: Delay máximo en segundos
        
    Returns:
        Resultado de la función
        
    Raises:
        Exception: Si todos los reintentos fallan
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"Función falló después de {max_retries} reintentos: {str(e)}")
                raise
            
            # Calcular delay con backoff exponencial
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"Intento {attempt + 1} falló, reintentando en {delay}s: {str(e)}")
            time.sleep(delay)
    
    raise last_exception

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validar datos contra un esquema JSON.
    
    Args:
        data: Datos a validar
        schema: Esquema JSON para validación
        
    Returns:
        True si los datos son válidos, False en caso contrario
    """
    try:
        from jsonschema import validate as jsonschema_validate, SchemaError
        try:
            jsonschema_validate(instance=data, schema=schema)
            return True
        except SchemaError:
            return False
        except Exception:
            return False
    except ImportError:
        logger.warning("jsonschema no está instalado, saltando validación")
        return True 