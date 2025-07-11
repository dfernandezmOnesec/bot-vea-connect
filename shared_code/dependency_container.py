"""
Contenedor de dependencias para el bot de WhatsApp VEA Connect.

Este módulo proporciona inyección de dependencias progresiva,
permitiendo la configuración flexible de servicios y facilitando
el testing y la modularidad del código.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable, cast
from shared_code.interfaces import (
    IWhatsAppService, IUserService, IOpenAIService, IVisionService,
    IBlobStorageService, IRedisService, IMessageProcessor,
    IResponseGenerator, IErrorHandler
)
from shared_code.whatsapp_service import WhatsAppService
from shared_code.user_service import UserService
from shared_code.openai_service import OpenAIService
from shared_code.vision_service import VisionService
from shared_code.azure_blob_storage import AzureBlobStorageService
from shared_code.redis_service import RedisService
from shared_code.message_processor import MessageProcessor
from shared_code.error_handler import ErrorHandler
from shared_code.type_helpers import cast_service_safe
from config.settings import get_settings


logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """
    Contenedor de dependencias para inyección de dependencias.
    
    Proporciona una forma centralizada de gestionar las dependencias
    del bot, facilitando el testing y la configuración flexible.
    """
    
    def __init__(self):
        """Inicializar el contenedor de dependencias."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._settings = get_settings()
        
        # Registrar factories por defecto
        self._register_default_factories()
    
    def register_service(self, service_type: str, service_instance: Any) -> None:
        """
        Registrar una instancia de servicio.
        
        Args:
            service_type: Tipo de servicio (ej: 'whatsapp', 'user', etc.)
            service_instance: Instancia del servicio
        """
        self._services[service_type] = service_instance
        logger.info(f"Servicio registrado: {service_type}")
    
    def register_factory(self, service_type: str, factory: Callable[[], Any]) -> None:
        """
        Registrar una factory para crear servicios.
        
        Args:
            service_type: Tipo de servicio
            factory: Función factory que crea la instancia
        """
        self._factories[service_type] = factory
        logger.info(f"Factory registrada: {service_type}")
    
    def get_service(self, service_type: str) -> Any:
        """
        Obtener un servicio del contenedor.
        
        Args:
            service_type: Tipo de servicio a obtener
            
        Returns:
            Any: Instancia del servicio
            
        Raises:
            KeyError: Si el servicio no está registrado
        """
        # Verificar si ya existe una instancia singleton
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Verificar si existe una instancia registrada
        if service_type in self._services:
            return self._services[service_type]
        
        # Verificar si existe una factory
        if service_type in self._factories:
            try:
                instance = self._factories[service_type]()
                # Crear como singleton
                self._singletons[service_type] = instance
                return instance
            except Exception as e:
                logger.error(f"Error creando servicio {service_type}: {e}")
                raise
        
        raise KeyError(f"Servicio no registrado: {service_type}")
    
    def get_service_safe(self, service_type: str) -> Optional[Any]:
        """
        Obtener un servicio de forma segura (retorna None si no existe).
        
        Args:
            service_type: Tipo de servicio a obtener
            
        Returns:
            Optional[Any]: Instancia del servicio o None
        """
        try:
            return self.get_service(service_type)
        except KeyError:
            logger.warning(f"Servicio no encontrado: {service_type}")
            return None
    
    def has_service(self, service_type: str) -> bool:
        """
        Verificar si un servicio está registrado.
        
        Args:
            service_type: Tipo de servicio a verificar
            
        Returns:
            bool: True si el servicio está registrado
        """
        return (
            service_type in self._services or 
            service_type in self._factories or 
            service_type in self._singletons
        )
    
    def create_whatsapp_service(self) -> IWhatsAppService:
        """Crear instancia del servicio de WhatsApp."""
        try:
            return WhatsAppService(skip_validation=True)
        except Exception as e:
            logger.error(f"Error creando WhatsAppService: {e}")
            raise
    
    def create_user_service(self) -> IUserService:
        """Crear instancia del servicio de usuarios."""
        try:
            redis_service = self.get_service("redis")
            return UserService(redis_service)
        except Exception as e:
            logger.error(f"Error creando UserService: {e}")
            raise
    
    def create_openai_service(self) -> IOpenAIService:
        """Crear instancia del servicio de OpenAI."""
        try:
            service = OpenAIService()
            return cast(IOpenAIService, service)
        except Exception as e:
            logger.error(f"Error creando OpenAIService: {e}")
            raise
    
    def create_vision_service(self) -> Optional[IVisionService]:
        """Crear instancia del servicio de visión."""
        try:
            service = VisionService(skip_validation=True)
            return cast_service_safe(service, IVisionService)
        except Exception as e:
            logger.warning(f"Error creando VisionService (opcional): {e}")
            return None
    
    def create_blob_storage_service(self) -> Optional[IBlobStorageService]:
        """Crear instancia del servicio de blob storage."""
        try:
            service = AzureBlobStorageService()
            return cast_service_safe(service, IBlobStorageService)
        except Exception as e:
            logger.warning(f"Error creando AzureBlobStorageService (opcional): {e}")
            return None
    
    def create_redis_service(self) -> Optional[IRedisService]:
        """Crear instancia del servicio de Redis."""
        try:
            return RedisService()
        except Exception as e:
            logger.warning(f"Error creando RedisService (opcional): {e}")
            return None
    
    def create_error_handler(self) -> IErrorHandler:
        """Crear instancia del manejador de errores."""
        try:
            return ErrorHandler()
        except Exception as e:
            logger.error(f"Error creando ErrorHandler: {e}")
            raise
    
    def create_message_processor(self) -> IMessageProcessor:
        """Crear instancia del procesador de mensajes."""
        try:
            whatsapp_service = self.get_service("whatsapp")
            user_service = self.get_service("user")
            openai_service = self.get_service("openai")
            vision_service = self.get_service_safe("vision")
            blob_storage_service = self.get_service_safe("blob_storage")
            error_handler = self.get_service("error_handler")
            
            return MessageProcessor(
                whatsapp_service=whatsapp_service,
                user_service=user_service,
                openai_service=openai_service,
                vision_service=vision_service,
                blob_storage_service=blob_storage_service,
                error_handler=error_handler
            )
        except Exception as e:
            logger.error(f"Error creando MessageProcessor: {e}")
            raise
    
    def _register_default_factories(self) -> None:
        """Registrar factories por defecto."""
        self.register_factory("whatsapp", self.create_whatsapp_service)
        self.register_factory("user", self.create_user_service)
        self.register_factory("openai", self.create_openai_service)
        self.register_factory("vision", self.create_vision_service)
        self.register_factory("blob_storage", self.create_blob_storage_service)
        self.register_factory("redis", self.create_redis_service)
        self.register_factory("error_handler", self.create_error_handler)
        self.register_factory("message_processor", self.create_message_processor)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud de todos los servicios registrados.
        
        Returns:
            Dict[str, Any]: Estado de salud de los servicios
        """
        health_status = {
            "container_healthy": True,
            "services": {},
            "timestamp": None
        }
        
        try:
            from datetime import datetime, timezone
            health_status["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Verificar servicios principales
            main_services = ["whatsapp", "user", "openai", "error_handler"]
            for service_type in main_services:
                try:
                    service = self.get_service(service_type)
                    if hasattr(service, 'health_check'):
                        health_status["services"][service_type] = service.health_check()
                    else:
                        health_status["services"][service_type] = True
                except Exception as e:
                    health_status["services"][service_type] = False
                    health_status["container_healthy"] = False
                    logger.error(f"Error en health check de {service_type}: {e}")
            
            # Verificar servicios opcionales
            optional_services = ["vision", "blob_storage", "redis"]
            for service_type in optional_services:
                try:
                    service = self.get_service_safe(service_type)
                    if service and hasattr(service, 'health_check'):
                        health_status["services"][service_type] = service.health_check()
                    elif service:
                        health_status["services"][service_type] = True
                    else:
                        health_status["services"][service_type] = None  # No disponible
                except Exception as e:
                    health_status["services"][service_type] = False
                    logger.warning(f"Error en health check de {service_type}: {e}")
            
        except Exception as e:
            health_status["container_healthy"] = False
            logger.error(f"Error en health check del contenedor: {e}")
        
        return health_status
    
    def reset(self) -> None:
        """Reiniciar el contenedor (limpiar singletons)."""
        self._singletons.clear()
        logger.info("Contenedor de dependencias reiniciado")
    
    def get_registered_services(self) -> Dict[str, str]:
        """
        Obtener lista de servicios registrados.
        
        Returns:
            Dict[str, str]: Diccionario con tipos de servicio y su estado
        """
        services = {}
        
        # Servicios registrados directamente
        for service_type in self._services:
            services[service_type] = "registered"
        
        # Factories registradas
        for service_type in self._factories:
            if service_type not in services:
                services[service_type] = "factory"
        
        # Singletons creados
        for service_type in self._singletons:
            services[service_type] = "singleton"
        
        return services


# Instancia global del contenedor
dependency_container = DependencyContainer()


def get_dependency_container() -> DependencyContainer:
    """
    Obtener la instancia global del contenedor de dependencias.
    
    Returns:
        DependencyContainer: Instancia del contenedor
    """
    return dependency_container


def register_service(service_type: str, service_instance: Any) -> None:
    """
    Registrar un servicio en el contenedor global.
    
    Args:
        service_type: Tipo de servicio
        service_instance: Instancia del servicio
    """
    dependency_container.register_service(service_type, service_instance)


def get_service(service_type: str) -> Any:
    """
    Obtener un servicio del contenedor global.
    
    Args:
        service_type: Tipo de servicio
        
    Returns:
        Any: Instancia del servicio
    """
    return dependency_container.get_service(service_type)


def get_service_safe(service_type: str) -> Optional[Any]:
    """
    Obtener un servicio del contenedor global de forma segura.
    
    Args:
        service_type: Tipo de servicio
        
    Returns:
        Optional[Any]: Instancia del servicio o None
    """
    return dependency_container.get_service_safe(service_type) 