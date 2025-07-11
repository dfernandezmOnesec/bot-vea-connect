"""
Manejador de errores mejorado para el bot de WhatsApp VEA Connect.

Este módulo proporciona manejo centralizado de errores con logging detallado,
respuestas estructuradas y recuperación automática cuando sea posible.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from shared_code.interfaces import IErrorHandler
from shared_code.utils import sanitize_log_message


logger = logging.getLogger(__name__)


class ErrorHandler(IErrorHandler):
    """
    Manejador de errores centralizado para el bot de WhatsApp.
    
    Proporciona manejo estructurado de errores con logging detallado,
    respuestas apropiadas para el usuario y recuperación automática.
    """
    
    def __init__(self):
        """Inicializar el manejador de errores."""
        self.error_counts = {}
        self.recovery_strategies = {
            "RATE_LIMIT": self._handle_rate_limit_error,
            "NETWORK_ERROR": self._handle_network_error,
            "AUTHENTICATION_ERROR": self._handle_auth_error,
            "VALIDATION_ERROR": self._handle_validation_error,
            "OPENAI_ERROR": self._handle_openai_error,
            "REDIS_ERROR": self._handle_redis_error,
            "WHATSAPP_ERROR": self._handle_whatsapp_error,
            "VISION_ERROR": self._handle_vision_error,
            "BLOB_STORAGE_ERROR": self._handle_blob_storage_error,
            "UNKNOWN_ERROR": self._handle_unknown_error
        }
    
    def handle_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """
        Manejar error y retornar respuesta apropiada.
        
        Args:
            error: Excepción que ocurrió
            context: Contexto donde ocurrió el error
            
        Returns:
            Dict[str, Any]: Respuesta estructurada para el error
        """
        try:
            # Determinar tipo de error
            error_type = self._classify_error(error)
            
            # Registrar error
            self.log_error(error, context)
            
            # Incrementar contador de errores
            self._increment_error_count(error_type)
            
            # Aplicar estrategia de recuperación
            if error_type in self.recovery_strategies:
                return self.recovery_strategies[error_type](error, context)
            else:
                return self._handle_unknown_error(error, context)
                
        except Exception as e:
            logger.error(f"Error en el manejador de errores: {e}")
            return self.create_error_response(
                "Error interno del sistema",
                error_code="HANDLER_ERROR"
            )
    
    def create_error_response(
        self, 
        message: str, 
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crear respuesta de error estructurada.
        
        Args:
            message: Mensaje de error para el usuario
            error_code: Código de error interno
            details: Detalles adicionales del error
            
        Returns:
            Dict[str, Any]: Respuesta estructurada
        """
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        if details:
            response["error"]["details"] = details
            
        return response
    
    def log_error(self, error: Exception, context: str) -> None:
        """
        Registrar error en logs con información detallada.
        
        Args:
            error: Excepción que ocurrió
            context: Contexto donde ocurrió el error
        """
        try:
            error_type = type(error).__name__
            error_message = str(error)
            
            # Sanitizar mensaje para logging
            sanitized_message = sanitize_log_message(error_message)
            
            # Obtener stack trace
            stack_trace = traceback.format_exc()
            
            # Log estructurado
            log_data = {
                "error_type": error_type,
                "error_message": sanitized_message,
                "context": context,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stack_trace": stack_trace
            }
            
            logger.error(f"Error en {context}: {error_type} - {sanitized_message}")
            logger.debug(f"Error details: {log_data}")
            
        except Exception as e:
            logger.error(f"Error logging error: {e}")
    
    def _classify_error(self, error: Exception) -> str:
        """
        Clasificar el tipo de error basado en la excepción.
        
        Args:
            error: Excepción a clasificar
            
        Returns:
            str: Tipo de error clasificado
        """
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Clasificación basada en tipo de excepción y mensaje
        if "rate limit" in error_message or "429" in error_message:
            return "RATE_LIMIT"
        elif "timeout" in error_message or "connection" in error_message:
            return "NETWORK_ERROR"
        elif "authentication" in error_message or "unauthorized" in error_message or "401" in error_message:
            return "AUTHENTICATION_ERROR"
        elif "validation" in error_message or "invalid" in error_message:
            return "VALIDATION_ERROR"
        elif "openai" in error_message or "gpt" in error_message:
            return "OPENAI_ERROR"
        elif "redis" in error_message:
            return "REDIS_ERROR"
        elif "whatsapp" in error_message:
            return "WHATSAPP_ERROR"
        elif "vision" in error_message or "image" in error_message:
            return "VISION_ERROR"
        elif "blob" in error_message or "storage" in error_message:
            return "BLOB_STORAGE_ERROR"
        else:
            return "UNKNOWN_ERROR"
    
    def _increment_error_count(self, error_type: str) -> None:
        """
        Incrementar contador de errores por tipo.
        
        Args:
            error_type: Tipo de error
        """
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def _handle_rate_limit_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de rate limit."""
        return self.create_error_response(
            "Demasiadas solicitudes. Por favor, espera un momento antes de enviar otro mensaje.",
            error_code="RATE_LIMIT",
            details={"retry_after": 60}
        )
    
    def _handle_network_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de red."""
        return self.create_error_response(
            "Error de conexión. Por favor, intenta de nuevo en unos momentos.",
            error_code="NETWORK_ERROR",
            details={"retry_after": 30}
        )
    
    def _handle_auth_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de autenticación."""
        return self.create_error_response(
            "Error de autenticación del servicio.",
            error_code="AUTHENTICATION_ERROR"
        )
    
    def _handle_validation_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de validación."""
        return self.create_error_response(
            "Datos de entrada inválidos.",
            error_code="VALIDATION_ERROR"
        )
    
    def _handle_openai_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de OpenAI."""
        return self.create_error_response(
            "Error en el servicio de inteligencia artificial. Por favor, intenta de nuevo.",
            error_code="OPENAI_ERROR"
        )
    
    def _handle_redis_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de Redis."""
        return self.create_error_response(
            "Error en el almacenamiento de datos. Por favor, intenta de nuevo.",
            error_code="REDIS_ERROR"
        )
    
    def _handle_whatsapp_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de WhatsApp."""
        return self.create_error_response(
            "Error en el servicio de WhatsApp. Por favor, intenta de nuevo.",
            error_code="WHATSAPP_ERROR"
        )
    
    def _handle_vision_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de visión."""
        return self.create_error_response(
            "Error al procesar la imagen. Por favor, intenta con otra imagen.",
            error_code="VISION_ERROR"
        )
    
    def _handle_blob_storage_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error de blob storage."""
        return self.create_error_response(
            "Error en el almacenamiento de archivos. Por favor, intenta de nuevo.",
            error_code="BLOB_STORAGE_ERROR"
        )
    
    def _handle_unknown_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error desconocido."""
        return self.create_error_response(
            "Error interno del sistema. Por favor, intenta de nuevo más tarde.",
            error_code="UNKNOWN_ERROR"
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de errores.
        
        Returns:
            Dict[str, Any]: Estadísticas de errores
        """
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def reset_error_stats(self) -> None:
        """Reiniciar estadísticas de errores."""
        self.error_counts.clear()
    
    def health_check(self) -> bool:
        """
        Verificar salud del manejador de errores.
        
        Returns:
            bool: True si el manejador está funcionando correctamente
        """
        try:
            # Verificar que las estrategias de recuperación estén disponibles
            if not self.recovery_strategies:
                return False
            
            # Verificar que se pueda crear una respuesta de error
            test_response = self.create_error_response("Test error", "TEST_ERROR")
            if not test_response or "error" not in test_response:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error en health check del ErrorHandler: {e}")
            return False 