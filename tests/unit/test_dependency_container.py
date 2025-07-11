"""
Tests unitarios para el contenedor de dependencias.

ESTE ARCHIVO CONTIENE TESTS UNITARIOS (100% MOCKEADOS)
Estos tests validan que el contenedor de dependencias funciona correctamente
y que la inyección de dependencias se realiza de manera apropiada.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Optional

from shared_code.dependency_container import DependencyContainer
from shared_code.interfaces import (
    IWhatsAppService, IUserService, IOpenAIService, IVisionService,
    IBlobStorageService, IRedisService, IErrorHandler, IMessageProcessor
)
from shared_code.whatsapp_service import WhatsAppService
from shared_code.user_service import UserService
from shared_code.openai_service import OpenAIService
from shared_code.vision_service import VisionService
from shared_code.azure_blob_storage import AzureBlobStorageService
from shared_code.redis_service import RedisService
from shared_code.error_handler import ErrorHandler
from shared_code.message_processor import MessageProcessor


class TestDependencyContainer:
    """Tests básicos para el contenedor de dependencias."""
    
    @pytest.fixture
    def container(self) -> DependencyContainer:
        """Crear instancia del contenedor."""
        return DependencyContainer()
    
    def test_container_initialization(self, container: DependencyContainer):
        """Test inicialización del contenedor."""
        assert container is not None
        assert isinstance(container, DependencyContainer)
    
    def test_register_service(self, container: DependencyContainer):
        """Test registro de servicio."""
        # Arrange
        mock_service = Mock(spec=IWhatsAppService)
        
        # Act
        container.register_service('whatsapp_service', mock_service)
        
        # Assert
        assert container.has_service('whatsapp_service')
        retrieved_service = container.get_service('whatsapp_service')
        assert retrieved_service == mock_service
    
    def test_register_service_overwrite(self, container: DependencyContainer):
        """Test sobrescritura de servicio."""
        # Arrange
        mock_service1 = Mock(spec=IWhatsAppService)
        mock_service2 = Mock(spec=IWhatsAppService)
        
        # Act
        container.register_service('whatsapp_service', mock_service1)
        container.register_service('whatsapp_service', mock_service2)
        
        # Assert
        retrieved_service = container.get_service('whatsapp_service')
        assert retrieved_service == mock_service2
        assert retrieved_service != mock_service1
    
    def test_get_service_success(self, container: DependencyContainer):
        """Test obtención exitosa de servicio."""
        # Arrange
        mock_service = Mock(spec=IWhatsAppService)
        container.register_service('whatsapp_service', mock_service)
        
        # Act
        retrieved_service = container.get_service('whatsapp_service')
        
        # Assert
        assert retrieved_service == mock_service
    
    def test_get_service_not_found(self, container: DependencyContainer):
        """Test obtener servicio no registrado."""
        with pytest.raises(KeyError, match="Servicio no registrado: nonexistent_service"):
            container.get_service('nonexistent_service')
    
    def test_get_service_with_default(self, container: DependencyContainer):
        """Test obtener servicio con valor por defecto."""
        # Nota: El método get_service no tiene parámetro default, 
        # pero podemos probar el comportamiento cuando no existe
        with pytest.raises(KeyError):
            container.get_service('nonexistent_service')
    
    def test_has_service(self, container: DependencyContainer):
        """Test verificar si existe un servicio."""
        # Registrar un servicio
        test_service = Mock()
        container.register_service('test_service', test_service)
        
        # Verificar que existe
        assert container.has_service('test_service') is True
        assert container.has_service('nonexistent_service') is False
    
    def test_register_service_twice(self, container: DependencyContainer):
        """Test registrar el mismo servicio dos veces."""
        test_service = Mock()
        
        # Primera vez
        container.register_service('test_service', test_service)
        assert container.has_service('test_service') is True
        
        # Segunda vez (debería sobrescribir)
        new_service = Mock()
        container.register_service('test_service', new_service)
        assert container.has_service('test_service') is True
        
        # Verificar que se sobrescribió
        retrieved_service = container.get_service('test_service')
        assert retrieved_service is new_service
    
    def test_register_multiple_services(self, container: DependencyContainer):
        """Test registrar múltiples servicios."""
        # Registrar varios servicios
        service1 = Mock()
        service2 = Mock()
        service3 = Mock()
        
        container.register_service('service1', service1)
        container.register_service('service2', service2)
        container.register_service('service3', service3)
        
        # Verificar que están todos registrados
        assert container.has_service('service1') is True
        assert container.has_service('service2') is True
        assert container.has_service('service3') is True
        assert container.get_service('service1') is service1
        assert container.get_service('service2') is service2
        assert container.get_service('service3') is service3


class TestDependencyContainerWithRealServices:
    """Tests para el contenedor con servicios reales (mockeados)."""
    
    @pytest.fixture
    def container_with_services(self) -> DependencyContainer:
        """Crear contenedor con servicios reales mockeados."""
        container = DependencyContainer()
        
        # Mock settings para evitar inicialización real
        with patch('shared_code.whatsapp_service.settings') as mock_whatsapp_settings, \
             patch('shared_code.openai_service.settings') as mock_openai_settings, \
             patch('shared_code.vision_service.settings') as mock_vision_settings, \
             patch('shared_code.azure_blob_storage.settings') as mock_blob_settings, \
             patch('shared_code.redis_service.settings') as mock_redis_settings:
            
            # Configurar mocks de settings
            mock_whatsapp_settings.whatsapp_phone_number_id = "test_id"
            mock_whatsapp_settings.whatsapp_access_token = "test_token"
            mock_whatsapp_settings.whatsapp_verify_token = "test_verify"
            
            mock_openai_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
            mock_openai_settings.azure_openai_api_key = "test_key"
            mock_openai_settings.azure_openai_chat_api_version = "2024-01-01"
            mock_openai_settings.azure_openai_chat_deployment = "test_deployment"
            mock_openai_settings.openai_embeddings_engine_doc = "test_embeddings"
            
            mock_vision_settings.azure_computer_vision_endpoint = "https://test.vision.azure.com/"
            mock_vision_settings.azure_computer_vision_api_key = "test_key"
            
            mock_blob_settings.azure_storage_connection_string = "test_connection_string"
            mock_blob_settings.blob_container_name = "test-container"
            
            mock_redis_settings.redis_connection_string = "redis://test:test@localhost:6379/0"
            
            # Mock validaciones para evitar conexiones reales
            with patch.object(WhatsAppService, '_validate_configuration'), \
                 patch.object(OpenAIService, '_validate_connections'), \
                 patch('shared_code.vision_service.ComputerVisionClient') as mock_vision_client, \
                 patch('shared_code.azure_blob_storage.BlobServiceClient') as mock_blob_client, \
                 patch.object(RedisService, '_validate_connection'):
                
                # Mock VisionService
                mock_vision_client_instance = Mock()
                mock_vision_client.return_value = mock_vision_client_instance
                mock_vision_client_instance.analyze_image.return_value = Mock()
                
                # Mock BlobStorageService
                mock_blob_client_instance = Mock()
                mock_blob_client.from_connection_string.return_value = mock_blob_client_instance
                mock_container_client = Mock()
                mock_blob_client_instance.get_container_client.return_value = mock_container_client
                mock_container_client.get_container_properties.return_value = Mock()
                
                # Registrar servicios reales
                container.register_service('whatsapp_service', WhatsAppService())
                # Crear RedisService primero para pasarlo a UserService
                redis_service = RedisService()
                container.register_service('redis_service', redis_service)
                container.register_service('user_service', UserService(redis_service))
                container.register_service('openai_service', OpenAIService())
                container.register_service('vision_service', VisionService())
                container.register_service('blob_storage_service', AzureBlobStorageService())
                container.register_service('redis_service', RedisService())
                container.register_service('error_handler', ErrorHandler())
                
                return container
    
    def test_get_real_services(self, container_with_services: DependencyContainer):
        """Test obtención de servicios reales."""
        # Act
        whatsapp = container_with_services.get_service('whatsapp_service')
        user = container_with_services.get_service('user_service')
        openai = container_with_services.get_service('openai_service')
        
        # Assert
        assert isinstance(whatsapp, WhatsAppService)
        assert isinstance(user, UserService)
        assert isinstance(openai, OpenAIService)
    
    def test_services_implement_interfaces(self, container_with_services: DependencyContainer):
        """Test que los servicios reales implementan las interfaces correctas."""
        # Act
        whatsapp = container_with_services.get_service('whatsapp_service')
        user = container_with_services.get_service('user_service')
        openai = container_with_services.get_service('openai_service')
        vision = container_with_services.get_service('vision_service')
        blob = container_with_services.get_service('blob_storage_service')
        redis = container_with_services.get_service('redis_service')
        error_handler = container_with_services.get_service('error_handler')
        
        # Assert
        assert isinstance(whatsapp, IWhatsAppService)
        assert isinstance(user, IUserService)
        assert isinstance(openai, IOpenAIService)
        assert isinstance(vision, IVisionService)
        assert isinstance(blob, IBlobStorageService)
        assert isinstance(redis, IRedisService)
        assert isinstance(error_handler, IErrorHandler)


class TestDependencyContainerMessageProcessor:
    """Tests específicos para MessageProcessor con inyección de dependencias."""
    
    @pytest.fixture
    def container_with_mocks(self) -> DependencyContainer:
        """Crear contenedor con mocks para testing."""
        container = DependencyContainer()
        
        # Registrar mocks
        container.register_service('whatsapp_service', Mock(spec=IWhatsAppService))
        container.register_service('user_service', Mock(spec=IUserService))
        container.register_service('openai_service', Mock(spec=IOpenAIService))
        container.register_service('vision_service', Mock(spec=IVisionService))
        container.register_service('blob_storage_service', Mock(spec=IBlobStorageService))
        container.register_service('redis_service', Mock(spec=IRedisService))
        container.register_service('error_handler', Mock(spec=IErrorHandler))
        
        return container
    
    def test_create_message_processor_with_container(self, container_with_mocks: DependencyContainer):
        """Test creación de MessageProcessor usando el contenedor."""
        # Act
        processor = MessageProcessor(
            whatsapp_service=container_with_mocks.get_service('whatsapp_service'),
            user_service=container_with_mocks.get_service('user_service'),
            openai_service=container_with_mocks.get_service('openai_service'),
            vision_service=container_with_mocks.get_service('vision_service'),
            blob_storage_service=container_with_mocks.get_service('blob_storage_service'),
            error_handler=container_with_mocks.get_service('error_handler')
        )
        
        # Assert
        assert isinstance(processor, MessageProcessor)
        assert isinstance(processor, IMessageProcessor)
    
    def test_message_processor_dependencies(self, container_with_mocks: DependencyContainer):
        """Test que MessageProcessor tiene todas las dependencias inyectadas."""
        # Act
        processor = MessageProcessor(
            whatsapp_service=container_with_mocks.get_service('whatsapp_service'),
            user_service=container_with_mocks.get_service('user_service'),
            openai_service=container_with_mocks.get_service('openai_service'),
            vision_service=container_with_mocks.get_service('vision_service'),
            blob_storage_service=container_with_mocks.get_service('blob_storage_service'),
            error_handler=container_with_mocks.get_service('error_handler')
        )
        
        # Assert
        assert processor.whatsapp_service is not None
        assert processor.user_service is not None
        assert processor.openai_service is not None
        assert processor.vision_service is not None
        assert processor.blob_storage_service is not None
        assert processor.error_handler is not None





class TestDependencyContainerErrorHandling:
    """Tests para el manejo de errores en el contenedor."""
    
    @pytest.fixture
    def container(self) -> DependencyContainer:
        """Crear contenedor para tests de errores."""
        return DependencyContainer()
    
    def test_register_none_service(self, container: DependencyContainer):
        """Test registrar servicio None."""
        # Nota: La implementación actual no valida servicios None
        # Este test verifica el comportamiento actual
        container.register_service('test_service', None)
        assert container.has_service('test_service') is True
        assert container.get_service('test_service') is None
    
    def test_register_empty_service_name(self, container: DependencyContainer):
        """Test registrar servicio con nombre vacío."""
        # Nota: La implementación actual no valida nombres vacíos
        # Este test verifica el comportamiento actual
        test_service = Mock()
        container.register_service('', test_service)
        assert container.has_service('') is True
        assert container.get_service('') is test_service
    
    def test_register_none_service_name(self, container: DependencyContainer):
        """Test registrar servicio con nombre None."""
        # Nota: La implementación actual no valida nombres None
        # Este test verifica el comportamiento actual
        test_service = Mock()
        # Usar type ignore para evitar errores de tipo
        container.register_service(None, test_service)  # type: ignore
        assert container.has_service(None) is True  # type: ignore
        assert container.get_service(None) is test_service  # type: ignore


class TestDependencyContainerThreadSafety:
    """Tests para la seguridad de hilos del contenedor."""
    
    @pytest.fixture
    def container(self) -> DependencyContainer:
        """Crear instancia del contenedor."""
        return DependencyContainer()
    
    def test_concurrent_service_registration(self, container: DependencyContainer):
        """Test registro concurrente de servicios."""
        import threading
        import time
        
        def register_service(service_id: int):
            mock_service = Mock(spec=IWhatsAppService)
            container.register_service(f'service_{service_id}', mock_service)
            time.sleep(0.01)  # Simular trabajo
        
        # Crear múltiples hilos
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_service, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar a que todos terminen
        for thread in threads:
            thread.join()
        
        # Verificar que todos los servicios fueron registrados
        for i in range(10):
            assert container.has_service(f'service_{i}')
    
    def test_concurrent_service_access(self, container: DependencyContainer):
        """Test acceso concurrente a servicios."""
        import threading
        import time
        
        # Registrar un servicio
        mock_service = Mock(spec=IWhatsAppService)
        container.register_service('test_service', mock_service)
        
        def access_service():
            for _ in range(100):
                service = container.get_service('test_service')
                assert service == mock_service
                time.sleep(0.001)
        
        # Crear múltiples hilos
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_service)
            threads.append(thread)
            thread.start()
        
        # Esperar a que todos terminen
        for thread in threads:
            thread.join()


class TestDependencyContainerPerformance:
    """Tests de performance del contenedor."""
    
    @pytest.fixture
    def container(self) -> DependencyContainer:
        """Crear instancia del contenedor."""
        return DependencyContainer()
    
    def test_service_registration_performance(self, container: DependencyContainer):
        """Test performance del registro de servicios."""
        import time
        
        # Medir tiempo de registro de múltiples servicios
        start_time = time.time()
        
        for i in range(1000):
            mock_service = Mock(spec=IWhatsAppService)
            container.register_service(f'service_{i}', mock_service)
        
        end_time = time.time()
        registration_time = end_time - start_time
        
        # Verificar que el tiempo es razonable (< 1 segundo para 1000 servicios)
        assert registration_time < 1.0
        
        # Verificar que todos los servicios fueron registrados
        for i in range(1000):
            assert container.has_service(f'service_{i}')
    
    def test_service_retrieval_performance(self, container: DependencyContainer):
        """Test performance de la obtención de servicios."""
        import time
        
        # Registrar servicios
        for i in range(100):
            mock_service = Mock(spec=IWhatsAppService)
            container.register_service(f'service_{i}', mock_service)
        
        # Medir tiempo de obtención
        start_time = time.time()
        
        for i in range(1000):
            service = container.get_service(f'service_{i % 100}')
            assert service is not None
        
        end_time = time.time()
        retrieval_time = end_time - start_time
        
        # Verificar que el tiempo es razonable (< 0.1 segundo para 1000 accesos)
        assert retrieval_time < 0.1


class TestDependencyContainerIntegration:
    """Tests de integración del contenedor con el sistema completo."""
    
    @pytest.fixture
    def full_container(self) -> DependencyContainer:
        """Crear contenedor con todos los servicios del sistema (mockeados)."""
        container = DependencyContainer()
        
        # Mock settings para evitar inicialización real
        with patch('shared_code.whatsapp_service.settings') as mock_whatsapp_settings, \
             patch('shared_code.openai_service.settings') as mock_openai_settings, \
             patch('shared_code.vision_service.settings') as mock_vision_settings, \
             patch('shared_code.azure_blob_storage.settings') as mock_blob_settings, \
             patch('shared_code.redis_service.settings') as mock_redis_settings:
            
            # Configurar mocks de settings
            mock_whatsapp_settings.whatsapp_phone_number_id = "test_id"
            mock_whatsapp_settings.whatsapp_access_token = "test_token"
            mock_whatsapp_settings.whatsapp_verify_token = "test_verify"
            
            mock_openai_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
            mock_openai_settings.azure_openai_api_key = "test_key"
            mock_openai_settings.azure_openai_chat_api_version = "2024-01-01"
            mock_openai_settings.azure_openai_chat_deployment = "test_deployment"
            mock_openai_settings.openai_embeddings_engine_doc = "test_embeddings"
            
            mock_vision_settings.azure_computer_vision_endpoint = "https://test.vision.azure.com/"
            mock_vision_settings.azure_computer_vision_api_key = "test_key"
            
            mock_blob_settings.azure_storage_connection_string = "test_connection_string"
            mock_blob_settings.blob_container_name = "test-container"
            
            mock_redis_settings.redis_connection_string = "redis://test:test@localhost:6379/0"
            
            # Mock validaciones para evitar conexiones reales
            with patch.object(WhatsAppService, '_validate_configuration'), \
                 patch.object(OpenAIService, '_validate_connections'), \
                 patch('shared_code.vision_service.ComputerVisionClient') as mock_vision_client, \
                 patch('shared_code.azure_blob_storage.BlobServiceClient') as mock_blob_client, \
                 patch.object(RedisService, '_validate_connection'):
                
                # Mock VisionService
                mock_vision_client_instance = Mock()
                mock_vision_client.return_value = mock_vision_client_instance
                mock_vision_client_instance.analyze_image.return_value = Mock()
                
                # Mock BlobStorageService
                mock_blob_client_instance = Mock()
                mock_blob_client.from_connection_string.return_value = mock_blob_client_instance
                mock_container_client = Mock()
                mock_blob_client_instance.get_container_client.return_value = mock_container_client
                mock_container_client.get_container_properties.return_value = Mock()
                
                # Registrar todos los servicios del sistema
                container.register_service('whatsapp_service', WhatsAppService())
                # Crear RedisService primero para pasarlo a UserService
                redis_service = RedisService()
                container.register_service('redis_service', redis_service)
                container.register_service('user_service', UserService(redis_service))
                container.register_service('openai_service', OpenAIService())
                container.register_service('vision_service', VisionService())
                container.register_service('blob_storage_service', AzureBlobStorageService())
                container.register_service('redis_service', RedisService())
                container.register_service('error_handler', ErrorHandler())
                
                return container
    
    def test_full_system_integration(self, full_container: DependencyContainer):
        """Test integración completa del sistema usando el contenedor."""
        # Crear MessageProcessor con todas las dependencias
        processor = MessageProcessor(
            whatsapp_service=full_container.get_service('whatsapp_service'),
            user_service=full_container.get_service('user_service'),
            openai_service=full_container.get_service('openai_service'),
            vision_service=full_container.get_service('vision_service'),
            blob_storage_service=full_container.get_service('blob_storage_service'),
            error_handler=full_container.get_service('error_handler')
        )
        
        # Verificar que todas las dependencias están inyectadas correctamente
        assert processor.whatsapp_service is not None
        assert processor.user_service is not None
        assert processor.openai_service is not None
        assert processor.vision_service is not None
        assert processor.blob_storage_service is not None
        assert processor.error_handler is not None
        
        # Verificar que implementan las interfaces correctas
        assert isinstance(processor.whatsapp_service, IWhatsAppService)
        assert isinstance(processor.user_service, IUserService)
        assert isinstance(processor.openai_service, IOpenAIService)
        assert isinstance(processor.vision_service, IVisionService)
        assert isinstance(processor.blob_storage_service, IBlobStorageService)
        assert isinstance(processor.error_handler, IErrorHandler) 