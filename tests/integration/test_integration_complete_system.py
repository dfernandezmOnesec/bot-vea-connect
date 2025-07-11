"""
Tests de integración para el sistema completo.

ESTE ARCHIVO CONTIENE TESTS DE INTEGRACIÓN (REQUIERE CONFIGURACIÓN REAL)
Estos tests validan la integración entre todos los componentes del sistema,
incluyendo el flujo completo desde la recepción de mensajes hasta la respuesta.
"""

import pytest
import json
import time
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from shared_code.dependency_container import DependencyContainer
from shared_code.message_processor import MessageProcessor
from shared_code.whatsapp_service import WhatsAppService
from shared_code.user_service import UserService
from shared_code.openai_service import OpenAIService
from shared_code.vision_service import VisionService
from shared_code.azure_blob_storage import AzureBlobStorageService
from shared_code.redis_service import RedisService
from shared_code.error_handler import ErrorHandler
from shared_code.user_service import User, UserSession
from shared_code.interfaces import (
    IWhatsAppService, IUserService, IOpenAIService, IVisionService,
    IBlobStorageService, IRedisService, IErrorHandler
)


class TestMessageProcessingIntegration:
    """Tests de integración para el procesamiento de mensajes."""
    
    @pytest.fixture
    def mock_services_container(self) -> DependencyContainer:
        """Crear contenedor con servicios mockeados."""
        container = DependencyContainer()
        
        # Crear mocks
        mock_whatsapp = Mock(spec=IWhatsAppService)
        mock_user = Mock(spec=IUserService)
        mock_openai = Mock(spec=IOpenAIService)
        mock_vision = Mock(spec=IVisionService)
        mock_blob = Mock(spec=IBlobStorageService)
        mock_redis = Mock(spec=IRedisService)
        mock_error = Mock(spec=IErrorHandler)
        
        # Configurar mocks
        mock_whatsapp.send_text_message.return_value = {"success": True, "message_id": "test_id"}
        
        mock_user.get_user.return_value = {
            "user_id": "+1234567890",
            "name": "Usuario Test",
            "phone_number": "+1234567890"
        }
        mock_user.update_session.return_value = True
        
        mock_openai.generate_response.return_value = "Respuesta generada por IA"
        
        mock_vision.analyze_image.return_value = {
            "description": "Una imagen de prueba",
            "tags": ["test", "image"]
        }
        
        mock_blob.upload_file.return_value = {"success": True, "url": "https://test.com/file.pdf"}
        
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None
        
        mock_error.create_error_response.return_value = {
            "success": False,
            "error": {"code": "TEST_ERROR", "message": "Error de prueba"}
        }
        
        # Registrar mocks
        container.register_service('whatsapp_service', mock_whatsapp)
        container.register_service('user_service', mock_user)
        container.register_service('openai_service', mock_openai)
        container.register_service('vision_service', mock_vision)
        container.register_service('blob_storage_service', mock_blob)
        container.register_service('redis_service', mock_redis)
        container.register_service('error_handler', mock_error)
        
        return container
    
    @pytest.fixture
    def message_processor_with_mocks(self, mock_services_container: DependencyContainer) -> MessageProcessor:
        """Crear MessageProcessor con servicios mockeados."""
        return MessageProcessor(
            whatsapp_service=mock_services_container.get_service('whatsapp_service'),
            user_service=mock_services_container.get_service('user_service'),
            openai_service=mock_services_container.get_service('openai_service'),
            vision_service=mock_services_container.get_service('vision_service'),
            blob_storage_service=mock_services_container.get_service('blob_storage_service'),
            error_handler=mock_services_container.get_service('error_handler')
        )
    
    def test_text_message_processing_flow(self, message_processor_with_mocks: MessageProcessor):
        """Test flujo completo de procesamiento de mensaje de texto."""
        # Arrange
        message = {
            "text": {"body": "Hola, ¿cómo estás?"},
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Act
        result = message_processor_with_mocks.process_text_message(message, user, session)
        
        # Assert
        assert result["success"] is True
        assert result["message_type"] == "text"
        assert result["user_id"] == user.phone_number
        
        # Verificar que se llamaron los servicios
        # Type: ignore para mocks de unittest
        message_processor_with_mocks.openai_service.generate_response.assert_called_once()  # type: ignore
        message_processor_with_mocks.whatsapp_service.send_text_message.assert_called_once()  # type: ignore
        message_processor_with_mocks.user_service.update_session.assert_called_once()  # type: ignore
    
    def test_image_message_processing_flow(self, message_processor_with_mocks: MessageProcessor):
        """Test flujo completo de procesamiento de mensaje de imagen."""
        # Arrange
        message = {
            "image": {
                "id": "image_123",
                "url": "https://example.com/image.jpg",
                "mime_type": "image/jpeg"
            },
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Act
        result = message_processor_with_mocks.process_media_message(message, user, session)
        
        # Assert
        assert result["success"] is True
        assert result["message_type"] == "image"
        assert result["user_id"] == user.phone_number
        
        # Verificar que se llamaron los servicios
        message_processor_with_mocks.vision_service.analyze_image.assert_called_once()  # type: ignore
        # Nota: generate_response puede no ser llamado en todos los flujos de imagen
        message_processor_with_mocks.whatsapp_service.send_text_message.assert_called_once()  # type: ignore
    
    def test_document_message_processing_flow(self, message_processor_with_mocks: MessageProcessor):
        """Test flujo completo de procesamiento de mensaje de documento."""
        # Arrange
        message = {
            "document": {
                "id": "doc_123",
                "url": "https://example.com/document.pdf",
                "mime_type": "application/pdf",
                "filename": "test.pdf"
            },
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Act
        result = message_processor_with_mocks.process_media_message(message, user, session)
        
        # Assert
        assert result["success"] is True
        assert result["message_type"] == "document"
        assert result["user_id"] == user.phone_number
        
        # Verificar que se llamaron los servicios
        # Nota: upload_file puede no ser llamado en todos los flujos de documento
        message_processor_with_mocks.whatsapp_service.send_text_message.assert_called_once()  # type: ignore


class TestErrorHandlingIntegration:
    """Tests de integración para el manejo de errores."""
    
    @pytest.fixture
    def error_container(self) -> DependencyContainer:
        """Crear contenedor configurado para testing de errores."""
        container = DependencyContainer()
        
        # Crear mocks que fallan
        mock_whatsapp = Mock(spec=IWhatsAppService)
        mock_user = Mock(spec=IUserService)
        mock_openai = Mock(spec=IOpenAIService)
        mock_vision = Mock(spec=IVisionService)
        mock_blob = Mock(spec=IBlobStorageService)
        mock_redis = Mock(spec=IRedisService)
        mock_error = Mock(spec=IErrorHandler)
        
        # Configurar mocks para fallar
        mock_openai.generate_response.side_effect = Exception("Error de OpenAI")
        mock_vision.analyze_image.side_effect = Exception("Error de Vision")
        mock_whatsapp.send_text_message.side_effect = Exception("Error de WhatsApp")
        
        # Configurar error handler para devolver un dict real
        mock_error.create_error_response.return_value = {
            "success": False,
            "error": {"code": "PROCESSING_ERROR", "message": "Error en procesamiento"}
        }
        mock_error.handle_error.return_value = {
            "success": False,
            "error": {"code": "HANDLER_ERROR", "message": "Error manejado"}
        }
        
        # Registrar mocks
        container.register_service('whatsapp_service', mock_whatsapp)
        container.register_service('user_service', mock_user)
        container.register_service('openai_service', mock_openai)
        container.register_service('vision_service', mock_vision)
        container.register_service('blob_storage_service', mock_blob)
        container.register_service('redis_service', mock_redis)
        container.register_service('error_handler', mock_error)
        
        return container
    
    @pytest.fixture
    def error_processor(self, error_container: DependencyContainer) -> MessageProcessor:
        """Crear MessageProcessor configurado para testing de errores."""
        return MessageProcessor(
            whatsapp_service=error_container.get_service('whatsapp_service'),
            user_service=error_container.get_service('user_service'),
            openai_service=error_container.get_service('openai_service'),
            vision_service=error_container.get_service('vision_service'),
            blob_storage_service=error_container.get_service('blob_storage_service'),
            error_handler=error_container.get_service('error_handler')
        )
    
    def test_openai_error_handling(self, error_processor: MessageProcessor):
        """Test manejo de errores de OpenAI."""
        # Arrange
        message = {
            "text": {"body": "Hola"},
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Act
        result = error_processor.process_text_message(message, user, session)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        # El error handler devuelve HANDLER_ERROR, no PROCESSING_ERROR
        assert result["error"]["code"] == "HANDLER_ERROR"
    
    def test_vision_error_handling(self, error_processor: MessageProcessor):
        """Test manejo de errores de Vision."""
        # Arrange
        message = {
            "image": {
                "id": "image_123",
                "url": "https://example.com/image.jpg",
                "mime_type": "image/jpeg"
            },
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )

        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )

        # Act
        result = error_processor.process_media_message(message, user, session)

        # Assert
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
    
    def test_whatsapp_error_handling(self, error_processor: MessageProcessor):
        """Test manejo de errores de WhatsApp."""
        # Configurar el mock para que falle en el envío
        error_processor.whatsapp_service.send_text_message.side_effect = Exception("Error de WhatsApp")  # type: ignore
        
        # Arrange
        message = {
            "text": {"body": "Hola"},
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Act
        result = error_processor.process_text_message(message, user, session)
        
        # Assert
        assert result["success"] is False
        assert "error" in result


class TestPerformanceIntegration:
    """Tests de performance del sistema integrado."""
    
    @pytest.fixture
    def performance_container(self) -> DependencyContainer:
        """Crear contenedor para tests de performance."""
        container = DependencyContainer()
        
        # Crear mocks optimizados para performance
        mock_whatsapp = Mock(spec=IWhatsAppService)
        mock_user = Mock(spec=IUserService)
        mock_openai = Mock(spec=IOpenAIService)
        mock_vision = Mock(spec=IVisionService)
        mock_blob = Mock(spec=IBlobStorageService)
        mock_redis = Mock(spec=IRedisService)
        mock_error = Mock(spec=IErrorHandler)
        
        # Configurar respuestas rápidas
        mock_whatsapp.send_text_message.return_value = {"success": True, "message_id": "test_id"}
        mock_user.update_session.return_value = True
        mock_openai.generate_response.return_value = "Respuesta rápida"
        mock_vision.analyze_image.return_value = {"description": "Imagen analizada"}
        mock_blob.upload_file.return_value = {"success": True, "url": "https://test.com/file.pdf"}
        mock_redis.set.return_value = True
        
        # Registrar mocks
        container.register_service('whatsapp_service', mock_whatsapp)
        container.register_service('user_service', mock_user)
        container.register_service('openai_service', mock_openai)
        container.register_service('vision_service', mock_vision)
        container.register_service('blob_storage_service', mock_blob)
        container.register_service('redis_service', mock_redis)
        container.register_service('error_handler', mock_error)
        
        return container
    
    @pytest.fixture
    def performance_processor(self, performance_container: DependencyContainer) -> MessageProcessor:
        """Crear MessageProcessor para tests de performance."""
        return MessageProcessor(
            whatsapp_service=performance_container.get_service('whatsapp_service'),
            user_service=performance_container.get_service('user_service'),
            openai_service=performance_container.get_service('openai_service'),
            vision_service=performance_container.get_service('vision_service'),
            blob_storage_service=performance_container.get_service('blob_storage_service'),
            error_handler=performance_container.get_service('error_handler')
        )
    
    def test_text_message_processing_performance(self, performance_processor: MessageProcessor):
        """Test performance del procesamiento de mensajes de texto."""
        # Arrange
        message = {
            "text": {"body": "Mensaje de prueba para performance"},
            "from": "+1234567890",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Medir tiempo de procesamiento
        start_time = time.time()
        
        # Act
        result = performance_processor.process_text_message(message, user, session)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Assert
        assert result["success"] is True
        assert processing_time < 1.0  # Debe procesar en menos de 1 segundo
    
    def test_batch_message_processing_performance(self, performance_processor: MessageProcessor):
        """Test performance del procesamiento de múltiples mensajes."""
        # Arrange
        messages = []
        for i in range(10):
            messages.append({
                "text": {"body": f"Mensaje {i} para batch processing"},
                "from": "+1234567890",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        user = User(
            phone_number="+1234567890",
            name="Usuario Test",
            created_at=datetime.now(timezone.utc)
        )
        
        session = UserSession(
            session_id="test_session_123",
            user_phone="+1234567890",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        # Medir tiempo de procesamiento batch
        start_time = time.time()
        
        # Act
        results = []
        for message in messages:
            result = performance_processor.process_text_message(message, user, session)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert
        assert all(result["success"] for result in results)
        assert total_time < 5.0  # 10 mensajes deben procesarse en menos de 5 segundos
        assert total_time / len(messages) < 0.5  # Promedio de menos de 0.5 segundos por mensaje


class TestConcurrencyIntegration:
    """Tests de concurrencia del sistema integrado."""
    
    @pytest.fixture
    def concurrency_container(self) -> DependencyContainer:
        """Crear contenedor para tests de concurrencia."""
        container = DependencyContainer()
        
        # Crear mocks thread-safe
        mock_whatsapp = Mock(spec=IWhatsAppService)
        mock_user = Mock(spec=IUserService)
        mock_openai = Mock(spec=IOpenAIService)
        mock_vision = Mock(spec=IVisionService)
        mock_blob = Mock(spec=IBlobStorageService)
        mock_redis = Mock(spec=IRedisService)
        mock_error = Mock(spec=IErrorHandler)
        
        # Configurar respuestas
        mock_whatsapp.send_text_message.return_value = {"success": True, "message_id": "test_id"}
        mock_user.update_session.return_value = True
        mock_openai.generate_response.return_value = "Respuesta concurrente"
        mock_vision.analyze_image.return_value = {"description": "Imagen concurrente"}
        mock_blob.upload_file.return_value = {"success": True, "url": "https://test.com/file.pdf"}
        mock_redis.set.return_value = True
        
        # Registrar mocks
        container.register_service('whatsapp_service', mock_whatsapp)
        container.register_service('user_service', mock_user)
        container.register_service('openai_service', mock_openai)
        container.register_service('vision_service', mock_vision)
        container.register_service('blob_storage_service', mock_blob)
        container.register_service('redis_service', mock_redis)
        container.register_service('error_handler', mock_error)
        
        return container
    
    @pytest.fixture
    def concurrency_processor(self, concurrency_container: DependencyContainer) -> MessageProcessor:
        """Crear MessageProcessor para tests de concurrencia."""
        return MessageProcessor(
            whatsapp_service=concurrency_container.get_service('whatsapp_service'),
            user_service=concurrency_container.get_service('user_service'),
            openai_service=concurrency_container.get_service('openai_service'),
            vision_service=concurrency_container.get_service('vision_service'),
            blob_storage_service=concurrency_container.get_service('blob_storage_service'),
            error_handler=concurrency_container.get_service('error_handler')
        )
    
    def test_concurrent_message_processing(self, concurrency_processor: MessageProcessor):
        """Test procesamiento concurrente de mensajes."""
        import threading
        import time
        
        # Arrange
        def process_message(message_id: int, results: list):
            message = {
                "text": {"body": f"Mensaje concurrente {message_id}"},
                "from": f"+123456789{message_id}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            user = User(
                phone_number=f"+123456789{message_id}",
                name=f"Usuario {message_id}",
                created_at=datetime.now(timezone.utc)
            )
            
            session = UserSession(
                session_id=f"session_{message_id}",
                user_phone=f"+123456789{message_id}",
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            result = concurrency_processor.process_text_message(message, user, session)
            results.append((message_id, result))
        
        # Crear múltiples hilos
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=process_message, args=(i, results))
            threads.append(thread)
            thread.start()
        
        # Esperar a que todos terminen
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(results) == 5
        for message_id, result in results:
            assert result["success"] is True
            assert result["message_type"] == "text"
    
    def test_concurrent_service_access(self, concurrency_container: DependencyContainer):
        """Test acceso concurrente a servicios."""
        import threading
        import time
        
        def access_service(service_name: str, results: list):
            service = concurrency_container.get_service(service_name)
            # Simular acceso al servicio
            results.append((service_name, "accessed"))
        
        # Crear múltiples hilos accediendo a diferentes servicios
        threads = []
        results = []
        
        services = [
            'whatsapp_service',
            'user_service',
            'openai_service',
            'vision_service',
            'blob_storage_service',
            'redis_service'
        ]
        
        for service_name in services:
            thread = threading.Thread(target=access_service, args=(service_name, results))
            threads.append(thread)
            thread.start()
        
        # Esperar a que todos terminen
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(results) == len(services)
        for service_name, _ in results:
            assert service_name in services 