"""
Configuración de la aplicación usando Pydantic v2.

Este módulo maneja todas las configuraciones de la aplicación,
incluyendo variables de entorno, validaciones y configuraciones por defecto.
"""

import os
import logging
from typing import Optional
from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_log_message(message: str) -> str:
    """Sanitiza mensajes para logging removiendo información sensible."""
    if not message:
        return ""
    
    # Ocultar tokens y claves API
    if len(message) > 10:
        return message[:4] + "*" * (len(message) - 8) + message[-4:]
    else:
        return "*" * len(message)


class Settings(BaseSettings):
    """Configuración de la aplicación con validación estricta de variables críticas."""
    
    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else None,
        case_sensitive=False,
        extra="allow"
    )
    
    # Variables críticas - la aplicación fallará si no están definidas
    acs_connection_string: Optional[str] = None
    acs_phone_number: Optional[str] = None
    openai_api_key: Optional[str] = None
    redis_connection_string: Optional[str] = None
    
    # Variables importantes - warnings si no están definidas
    whatsapp_verify_token: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    
    # Variables opcionales
    azure_storage_connection_string: Optional[str] = None
    vision_endpoint: Optional[str] = None
    vision_key: Optional[str] = None
    log_level: str = "INFO"
    
    # Variables de Redis (para compatibilidad)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_username: str = ""
    redis_password: str = ""
    redis_ssl: bool = False
    
    # Variables de Azure (para compatibilidad)
    azure_webjobs_storage: Optional[str] = None
    blob_account_name: Optional[str] = None
    blob_account_key: Optional[str] = None
    blob_container_name: Optional[str] = None
    queue_name: Optional[str] = "doc-processing"
    
    # Variables de OpenAI (para compatibilidad)
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_chat_deployment: Optional[str] = None
    azure_openai_chat_api_version: Optional[str] = None
    azure_openai_chat_endpoint: Optional[str] = None
    azure_openai_embeddings_api_key: Optional[str] = None
    azure_openai_embeddings_api_version: Optional[str] = None
    azure_openai_embeddings_endpoint: Optional[str] = None
    openai_embeddings_engine_doc: Optional[str] = None
    
    # Variables de WhatsApp (para compatibilidad)
    whatsapp_token: Optional[str] = None
    whatsapp_version: Optional[str] = "v18.0"
    
    # Variables de Azure Communication Services (para compatibilidad)
    acs_endpoint: Optional[str] = None
    acs_channel_id: Optional[str] = None
    acs_access_key: Optional[str] = None
    
    # Variables de Event Grid (para compatibilidad)
    event_grid_topic_endpoint: Optional[str] = None
    event_grid_topic_key: Optional[str] = None
    event_grid_webhook_secret: Optional[str] = None
    
    # Variables de KeyVault & Insights (para compatibilidad)
    azure_keyvault_url: Optional[str] = None
    applicationinsights_connection_string: Optional[str] = None
    
    # Variables de Computer Vision (para compatibilidad)
    azure_computer_vision_endpoint: Optional[str] = None
    azure_computer_vision_api_key: Optional[str] = None
    
    @field_validator('acs_connection_string')
    @classmethod
    def validate_acs_connection_string(cls, v):
        """Valida que la cadena de conexión de ACS esté presente y tenga formato válido."""
        # Skip validation in testing mode
        import sys
        is_testing = any('test' in arg.lower() for arg in sys.argv) or 'pytest' in sys.modules
        if is_testing:
            return v
            
        if not v or not v.strip():
            raise ValueError("ACS_CONNECTION_STRING es requerida y no puede estar vacía")
        if not v.startswith('endpoint='):
            raise ValueError("ACS_CONNECTION_STRING debe tener formato válido de Azure Communication Services")
        return v
    
    @field_validator('acs_phone_number')
    @classmethod
    def validate_acs_phone_number(cls, v):
        """Valida que el número de teléfono de ACS esté presente y tenga formato válido."""
        # Skip validation in testing mode
        import sys
        is_testing = any('test' in arg.lower() for arg in sys.argv) or 'pytest' in sys.modules
        if is_testing:
            return v
            
        if not v or not v.strip():
            raise ValueError("ACS_PHONE_NUMBER es requerido y no puede estar vacío")
        if not v.startswith('+'):
            raise ValueError("ACS_PHONE_NUMBER debe incluir código de país (ej: +1234567890)")
        return v
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_api_key(cls, v):
        """Valida que la API key de OpenAI esté presente y tenga formato válido."""
        # Skip validation in testing mode
        import sys
        is_testing = any('test' in arg.lower() for arg in sys.argv) or 'pytest' in sys.modules
        if is_testing:
            return v
            
        if not v or not v.strip():
            raise ValueError("OPENAI_API_KEY es requerida y no puede estar vacía")
        if not v.startswith('sk-'):
            raise ValueError("OPENAI_API_KEY debe tener formato válido (comenzar con 'sk-')")
        return v
    
    @field_validator('redis_connection_string')
    @classmethod
    def validate_redis_connection_string(cls, v):
        """Valida que la cadena de conexión de Redis esté presente."""
        # Skip validation in testing mode
        import sys
        is_testing = any('test' in arg.lower() for arg in sys.argv) or 'pytest' in sys.modules
        if is_testing:
            return v
            
        if not v or not v.strip():
            raise ValueError("REDIS_CONNECTION_STRING es requerida y no puede estar vacía")
        return v
    
    @field_validator('whatsapp_verify_token')
    @classmethod
    def validate_whatsapp_verify_token(cls, v):
        """Valida el token de verificación de WhatsApp si está presente."""
        if v is not None and (not v.strip() or len(v.strip()) < 10):
            logger.warning("WHATSAPP_VERIFY_TOKEN está presente pero parece ser muy corto o inválido")
        return v
    
    @field_validator('whatsapp_access_token')
    @classmethod
    def validate_whatsapp_access_token(cls, v):
        """Valida el token de acceso de WhatsApp si está presente."""
        if v is not None and (not v.strip() or len(v.strip()) < 20):
            logger.warning("WHATSAPP_ACCESS_TOKEN está presente pero parece ser muy corto o inválido")
        return v
    
    @field_validator('whatsapp_phone_number_id')
    @classmethod
    def validate_whatsapp_phone_number_id(cls, v):
        """Valida el ID del número de teléfono de WhatsApp si está presente."""
        if v is not None and not v.strip():
            logger.warning("WHATSAPP_PHONE_NUMBER_ID está presente pero está vacío")
        return v
    
    def validate_critical_settings(self) -> None:
        """Valida todas las configuraciones críticas y lanza excepción si alguna falta."""
        missing_vars = []
        
        if not self.acs_connection_string:
            missing_vars.append("ACS_CONNECTION_STRING")
        if not self.acs_phone_number:
            missing_vars.append("ACS_PHONE_NUMBER")
        if not self.openai_api_key:
            missing_vars.append("OPENAI_API_KEY")
        if not self.redis_connection_string:
            missing_vars.append("REDIS_CONNECTION_STRING")
        
        if missing_vars:
            error_msg = f"Variables de entorno críticas faltantes: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validar configuraciones opcionales pero importantes
        optional_warnings = []
        if not self.whatsapp_verify_token:
            optional_warnings.append("WHATSAPP_VERIFY_TOKEN (opcional pero recomendado)")
        if not self.whatsapp_access_token:
            optional_warnings.append("WHATSAPP_ACCESS_TOKEN (opcional pero recomendado)")
        if not self.whatsapp_phone_number_id:
            optional_warnings.append("WHATSAPP_PHONE_NUMBER_ID (opcional pero recomendado)")
        
        if optional_warnings:
            logger.warning(f"Variables de entorno opcionales no configuradas: {', '.join(optional_warnings)}")
        
        logger.info("Validación de configuraciones completada exitosamente")
    
    def get_sanitized_settings_summary(self) -> dict:
        """Retorna un resumen de las configuraciones con datos sensibles sanitizados."""
        return {
            "acs_phone_number": sanitize_log_message(self.acs_phone_number or ""),
            "whatsapp_phone_number_id": self.whatsapp_phone_number_id,
            "log_level": self.log_level,
            "has_whatsapp_config": bool(self.whatsapp_verify_token and self.whatsapp_access_token),
            "has_vision_config": bool(self.vision_endpoint and self.vision_key),
            "has_storage_config": bool(self.azure_storage_connection_string),
        }

# Instancia global con validación estricta
try:
    settings = Settings()
    
    # Solo validar configuraciones críticas si no estamos en modo test
    import sys
    is_testing = any('test' in arg.lower() for arg in sys.argv) or 'pytest' in sys.modules
    
    if not is_testing:
        settings.validate_critical_settings()
        # Log del resumen de configuraciones (sanitizado)
        summary = settings.get_sanitized_settings_summary()
        logger.info(f"Configuraciones cargadas: {summary}")
    else:
        logger.info("Modo testing detectado - validación de configuraciones críticas omitida")
    
except ValidationError as e:
    logger.error(f"Error de validación en configuraciones: {e}")
    raise
except ValueError as e:
    logger.error(f"Error en configuraciones críticas: {e}")
    raise
except Exception as e:
    logger.error(f"Error inesperado cargando configuraciones: {e}")
    raise

def get_settings() -> Settings:
    """Retorna la instancia global de configuraciones."""
    return settings 