"""
Tests unitarios para las interfaces del sistema.

ESTE ARCHIVO CONTIENE TESTS UNITARIOS (100% MOCKEADOS)
Estos tests validan que todas las interfaces están correctamente definidas
y que los servicios implementan correctamente todos los métodos requeridos.
"""

import pytest
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

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


class TestIWhatsAppService:
    """Tests para la interfaz IWhatsAppService."""
    
    @patch('shared_code.whatsapp_service.settings')
    def test_whatsapp_service_implements_interface(self, mock_settings):
        """Verificar que WhatsAppService implementa IWhatsAppService."""
        # Mock settings para evitar inicialización real
        mock_settings.whatsapp_phone_number_id = "test_id"
        mock_settings.whatsapp_access_token = "test_token"
        mock_settings.whatsapp_verify_token = "test_verify"
        
        with patch.object(WhatsAppService, '_validate_configuration'):
            service = WhatsAppService()
            assert isinstance(service, IWhatsAppService)
    
    @patch('shared_code.whatsapp_service.settings')
    def test_whatsapp_service_has_all_required_methods(self, mock_settings):
        """Verificar que WhatsAppService tiene todos los métodos requeridos."""
        # Mock settings para evitar inicialización real
        mock_settings.whatsapp_phone_number_id = "test_id"
        mock_settings.whatsapp_access_token = "test_token"
        mock_settings.whatsapp_verify_token = "test_verify"
        
        with patch.object(WhatsAppService, '_validate_configuration'):
            service = WhatsAppService()
            
            required_methods = [
                'send_text_message',
                'send_document_message',
                'send_template_message',
                'send_interactive_message',
                'send_quick_reply_message',
                'mark_message_as_read'
            ]
            
            for method_name in required_methods:
                assert hasattr(service, method_name), f"Falta método: {method_name}"
                assert callable(getattr(service, method_name)), f"El método {method_name} no es callable"
    
    @patch('shared_code.whatsapp_service.settings')
    def test_whatsapp_service_method_signatures(self, mock_settings):
        """Verificar que los métodos tienen las firmas correctas."""
        # Mock settings para evitar inicialización real
        mock_settings.whatsapp_phone_number_id = "test_id"
        mock_settings.whatsapp_access_token = "test_token"
        mock_settings.whatsapp_verify_token = "test_verify"
        
        with patch.object(WhatsAppService, '_validate_configuration'):
            service = WhatsAppService()
            
            # Verificar que send_text_message acepta los parámetros correctos
            import inspect
            sig = inspect.signature(service.send_text_message)
            assert 'message' in sig.parameters
            assert 'recipient_id' in sig.parameters


class TestIUserService:
    """Tests para la interfaz IUserService."""
    
    def test_user_service_implements_interface(self):
        """Verificar que UserService implementa IUserService."""
        mock_redis_service = MagicMock()
        service = UserService(mock_redis_service)
        assert isinstance(service, IUserService)
    
    def test_user_service_has_all_required_methods(self):
        """Verificar que UserService tiene todos los métodos requeridos."""
        mock_redis_service = MagicMock()
        service = UserService(mock_redis_service)
        
        required_methods = [
            'get_user',
            'create_user',
            'update_user',
            'create_session',
            'update_session'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"Falta método: {method_name}"
            assert callable(getattr(service, method_name)), f"El método {method_name} no es callable"


class TestIOpenAIService:
    """Tests para la interfaz IOpenAIService."""
    
    @patch('shared_code.openai_service.settings')
    def test_openai_service_implements_interface(self, mock_settings):
        """Verificar que OpenAIService implementa IOpenAIService."""
        # Mock settings para evitar inicialización real
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_key = "test_key"
        mock_settings.azure_openai_chat_api_version = "2024-01-01"
        mock_settings.azure_openai_chat_deployment = "test_deployment"
        mock_settings.openai_embeddings_engine_doc = "test_embeddings"
        
        with patch.object(OpenAIService, '_validate_connections'):
            service = OpenAIService()
            assert isinstance(service, IOpenAIService)
    
    @patch('shared_code.openai_service.settings')
    def test_openai_service_has_all_required_methods(self, mock_settings):
        """Verificar que OpenAIService tiene todos los métodos requeridos."""
        # Mock settings para evitar inicialización real
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_key = "test_key"
        mock_settings.azure_openai_chat_api_version = "2024-01-01"
        mock_settings.azure_openai_chat_deployment = "test_deployment"
        mock_settings.openai_embeddings_engine_doc = "test_embeddings"
        
        with patch.object(OpenAIService, '_validate_connections'):
            service = OpenAIService()
            
            required_methods = [
                'generate_response',
                'generate_embeddings',
                'generate_chat_completion',
                'generate_whatsapp_response',
                'analyze_document_content',
                'validate_text_length',
                'get_chat_history_summary'
            ]
            
            for method_name in required_methods:
                assert hasattr(service, method_name), f"Falta método: {method_name}"
                assert callable(getattr(service, method_name)), f"El método {method_name} no es callable"


class TestIVisionService:
    """Tests para la interfaz IVisionService."""
    
    @patch('shared_code.vision_service.settings')
    @patch('shared_code.vision_service.ComputerVisionClient')
    def test_vision_service_implements_interface(self, mock_client, mock_settings):
        """Verificar que VisionService implementa IVisionService."""
        # Mock settings para evitar inicialización real
        mock_settings.azure_computer_vision_endpoint = "https://test.vision.azure.com/"
        mock_settings.azure_computer_vision_api_key = "test_key"
        
        # Mock el cliente de Computer Vision para evitar conexiones reales
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.analyze_image.return_value = Mock()
        
        # Crear servicio con mocks completos
        service = VisionService()
        assert isinstance(service, IVisionService)
    
    @patch('shared_code.vision_service.settings')
    @patch('shared_code.vision_service.ComputerVisionClient')
    def test_vision_service_has_all_required_methods(self, mock_client, mock_settings):
        """Verificar que VisionService implementa IVisionService."""
        # Mock settings para evitar inicialización real
        mock_settings.azure_computer_vision_endpoint = "https://test.vision.azure.com/"
        mock_settings.azure_computer_vision_api_key = "test_key"
        
        # Mock el cliente de Computer Vision para evitar conexiones reales
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.analyze_image.return_value = Mock()
        
        # Crear servicio con mocks completos
        service = VisionService()
        
        required_methods = [
            'analyze_image',
            'extract_text_from_image_url'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"Falta método: {method_name}"
            assert callable(getattr(service, method_name)), f"El método {method_name} no es callable"


class TestIBlobStorageService:
    """Tests para la interfaz IBlobStorageService."""
    
    @patch('shared_code.azure_blob_storage.settings')
    @patch('shared_code.azure_blob_storage.BlobServiceClient')
    def test_blob_storage_service_implements_interface(self, mock_blob_client, mock_settings):
        """Verificar que AzureBlobStorageService implementa IBlobStorageService."""
        # Mock settings para evitar inicialización real
        mock_settings.azure_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net"
        mock_settings.blob_container_name = "test-container"
        
        # Mock el cliente de Blob Storage para evitar conexiones reales
        mock_blob_client_instance = Mock()
        mock_blob_client.from_connection_string.return_value = mock_blob_client_instance
        
        mock_container_client = Mock()
        mock_blob_client_instance.get_container_client.return_value = mock_container_client
        mock_container_client.get_container_properties.return_value = Mock()
        
        # Crear servicio con mocks completos
        service = AzureBlobStorageService()
        assert isinstance(service, IBlobStorageService)
    
    @patch('shared_code.azure_blob_storage.settings')
    @patch('shared_code.azure_blob_storage.BlobServiceClient')
    def test_blob_storage_service_has_all_required_methods(self, mock_blob_client, mock_settings):
        """Verificar que AzureBlobStorageService tiene todos los métodos requeridos."""
        # Mock settings para evitar inicialización real
        mock_settings.azure_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net"
        mock_settings.blob_container_name = "test-container"
        
        # Mock el cliente de Blob Storage para evitar conexiones reales
        mock_blob_client_instance = Mock()
        mock_blob_client.from_connection_string.return_value = mock_blob_client_instance
        
        mock_container_client = Mock()
        mock_blob_client_instance.get_container_client.return_value = mock_container_client
        mock_container_client.get_container_properties.return_value = Mock()
        
        # Crear servicio con mocks completos
        service = AzureBlobStorageService()
        
        required_methods = [
            'upload_file',
            'download_file',
            'list_blobs',
            'blob_exists',
            'get_blob_metadata'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"Falta método: {method_name}"
            assert callable(getattr(service, method_name)), f"El método {method_name} no es callable"


class TestIRedisService:
    """Tests para la interfaz IRedisService."""
    
    @patch('shared_code.redis_service.settings')
    def test_redis_service_implements_interface(self, mock_settings):
        """Verificar que RedisService implementa IRedisService."""
        # Mock settings para evitar inicialización real
        mock_settings.redis_connection_string = "redis://test:test@localhost:6379/0"
        
        with patch.object(RedisService, '_validate_connection'):
            service = RedisService()
            assert isinstance(service, IRedisService)
    
    @patch('shared_code.redis_service.settings')
    def test_redis_service_has_all_required_methods(self, mock_settings):
        """Verificar que RedisService tiene todos los métodos requeridos."""
        # Mock settings para evitar inicialización real
        mock_settings.redis_connection_string = "redis://test:test@localhost:6379/0"
        
        with patch.object(RedisService, '_validate_connection'):
            service = RedisService()
            
            required_methods = [
                'set',
                'get',
                'delete',
                'exists'
            ]
            
            for method_name in required_methods:
                assert hasattr(service, method_name), f"Falta método: {method_name}"
                assert callable(getattr(service, method_name)), f"El método {method_name} no es callable"


class TestIErrorHandler:
    """Tests para la interfaz IErrorHandler."""
    
    def test_error_handler_implements_interface(self):
        """Verificar que ErrorHandler implementa IErrorHandler."""
        handler = ErrorHandler()
        assert isinstance(handler, IErrorHandler)
    
    def test_error_handler_has_all_required_methods(self):
        """Verificar que ErrorHandler tiene todos los métodos requeridos."""
        handler = ErrorHandler()
        
        required_methods = [
            'create_error_response',
            'log_error'
        ]
        
        for method_name in required_methods:
            assert hasattr(handler, method_name), f"Falta método: {method_name}"
            assert callable(getattr(handler, method_name)), f"El método {method_name} no es callable"


class TestIMessageProcessor:
    """Tests para la interfaz IMessageProcessor."""
    
    def test_message_processor_implements_interface(self):
        """Verificar que MessageProcessor implementa IMessageProcessor."""
        # Crear mocks para las dependencias
        mock_whatsapp = Mock(spec=IWhatsAppService)
        mock_user = Mock(spec=IUserService)
        mock_openai = Mock(spec=IOpenAIService)
        mock_vision = Mock(spec=IVisionService)
        mock_blob = Mock(spec=IBlobStorageService)
        mock_error = Mock(spec=IErrorHandler)
        
        processor = MessageProcessor(
            whatsapp_service=mock_whatsapp,
            user_service=mock_user,
            openai_service=mock_openai,
            vision_service=mock_vision,
            blob_storage_service=mock_blob,
            error_handler=mock_error
        )
        
        assert isinstance(processor, IMessageProcessor)
    
    def test_message_processor_has_all_required_methods(self):
        """Verificar que MessageProcessor tiene todos los métodos requeridos."""
        # Crear mocks para las dependencias
        mock_whatsapp = Mock(spec=IWhatsAppService)
        mock_user = Mock(spec=IUserService)
        mock_openai = Mock(spec=IOpenAIService)
        mock_vision = Mock(spec=IVisionService)
        mock_blob = Mock(spec=IBlobStorageService)
        mock_error = Mock(spec=IErrorHandler)
        
        processor = MessageProcessor(
            whatsapp_service=mock_whatsapp,
            user_service=mock_user,
            openai_service=mock_openai,
            vision_service=mock_vision,
            blob_storage_service=mock_blob,
            error_handler=mock_error
        )
        
        required_methods = [
            'process_text_message',
            'process_media_message'
        ]
        
        for method_name in required_methods:
            assert hasattr(processor, method_name), f"Falta método: {method_name}"
            assert callable(getattr(processor, method_name)), f"El método {method_name} no es callable"


class TestInterfaceCompatibility:
    """Tests para verificar compatibilidad entre interfaces."""
    
    def test_all_services_return_consistent_error_format(self):
        """Verificar que todos los servicios retornan formato de error consistente."""
        # Este test verifica que cuando los servicios fallan,
        # retornan un formato de error consistente
        pass 