"""
Helpers de tipos para resolver problemas de compatibilidad.

Este módulo proporciona funciones y tipos para manejar la compatibilidad
entre interfaces y implementaciones de servicios.
"""

from typing import TypeVar, Union, Any, Dict, List, Optional
from shared_code.interfaces import (
    IWhatsAppService, IUserService, IOpenAIService, IVisionService,
    IBlobStorageService, IRedisService, IMessageProcessor,
    IResponseGenerator, IErrorHandler
)

# Type variables para servicios
WhatsAppServiceType = TypeVar('WhatsAppServiceType', bound=IWhatsAppService)
UserServiceType = TypeVar('UserServiceType', bound=IUserService)
OpenAIServiceType = TypeVar('OpenAIServiceType', bound=IOpenAIService)
VisionServiceType = TypeVar('VisionServiceType', bound=IVisionService)
BlobStorageServiceType = TypeVar('BlobStorageServiceType', bound=IBlobStorageService)
RedisServiceType = TypeVar('RedisServiceType', bound=IRedisService)
MessageProcessorType = TypeVar('MessageProcessorType', bound=IMessageProcessor)
ResponseGeneratorType = TypeVar('ResponseGeneratorType', bound=IResponseGenerator)
ErrorHandlerType = TypeVar('ErrorHandlerType', bound=IErrorHandler)

# Union types para servicios opcionales
OptionalVisionService = Optional[IVisionService]
OptionalBlobStorageService = Optional[IBlobStorageService]
OptionalRedisService = Optional[IRedisService]

# Type aliases para compatibilidad
ServiceType = Union[
    IWhatsAppService, IUserService, IOpenAIService, IVisionService,
    IBlobStorageService, IRedisService, IMessageProcessor,
    IResponseGenerator, IErrorHandler
]

def validate_service_interface(service: Any, interface_type: type) -> bool:
    """
    Validar que un servicio implementa correctamente una interfaz.
    
    Args:
        service: Servicio a validar
        interface_type: Tipo de interfaz esperado
        
    Returns:
        bool: True si el servicio implementa la interfaz correctamente
    """
    try:
        # Verificar que el servicio es una instancia del tipo esperado
        if not isinstance(service, interface_type):
            return False
        
        # Verificar que tiene los métodos requeridos
        required_methods = getattr(interface_type, '__abstractmethods__', set())
        for method in required_methods:
            if not hasattr(service, method):
                return False
        
        return True
    except Exception:
        return False

def cast_service_safe(service: Any, interface_type: type) -> Optional[Any]:
    """
    Hacer cast seguro de un servicio a una interfaz.
    
    Args:
        service: Servicio a hacer cast
        interface_type: Tipo de interfaz objetivo
        
    Returns:
        Optional[Any]: Servicio cast a la interfaz o None si falla
    """
    try:
        if validate_service_interface(service, interface_type):
            return service
        return None
    except Exception:
        return None

# Type guards para verificar tipos de servicios
def is_whatsapp_service(service: Any) -> bool:
    """Verificar si un servicio es un IWhatsAppService."""
    return validate_service_interface(service, IWhatsAppService)

def is_user_service(service: Any) -> bool:
    """Verificar si un servicio es un IUserService."""
    return validate_service_interface(service, IUserService)

def is_openai_service(service: Any) -> bool:
    """Verificar si un servicio es un IOpenAIService."""
    return validate_service_interface(service, IOpenAIService)

def is_vision_service(service: Any) -> bool:
    """Verificar si un servicio es un IVisionService."""
    return validate_service_interface(service, IVisionService)

def is_blob_storage_service(service: Any) -> bool:
    """Verificar si un servicio es un IBlobStorageService."""
    return validate_service_interface(service, IBlobStorageService)

def is_redis_service(service: Any) -> bool:
    """Verificar si un servicio es un IRedisService."""
    return validate_service_interface(service, IRedisService)

def is_message_processor(service: Any) -> bool:
    """Verificar si un servicio es un IMessageProcessor."""
    return validate_service_interface(service, IMessageProcessor)

def is_error_handler(service: Any) -> bool:
    """Verificar si un servicio es un IErrorHandler."""
    return validate_service_interface(service, IErrorHandler) 