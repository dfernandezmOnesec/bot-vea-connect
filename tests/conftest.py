import pytest
import os
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests."""
    env_vars = {
        # Azure
        'AzureWebJobsStorage': 'UseDevelopmentStorage=true',
        'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net',
        'BLOB_ACCOUNT_NAME': 'testaccount',
        'BLOB_ACCOUNT_KEY': 'testkey',
        'BLOB_CONTAINER_NAME': 'documents',
        'QUEUE_NAME': 'doc-processing',
        
        # OpenAI
        'AZURE_OPENAI_ENDPOINT': 'https://openai-veaconnect.openai.azure.com/',
        'AZURE_OPENAI_API_KEY': 'test-openai-key',
        'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-35-turbo',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
        'AZURE_OPENAI_CHAT_API_VERSION': '2025-01-01-preview',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://openai-veaconnect.openai.azure.com/',
        'AZURE_OPENAI_EMBEDDINGS_API_KEY': 'test-embeddings-key',
        'AZURE_OPENAI_EMBEDDINGS_API_VERSION': '2025-01-01-preview',
        'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://openai-veaconnect.openai.azure.com/',
        'OPENAI_EMBEDDINGS_ENGINE_DOC': 'text-embedding-ada-002',
        
        # Redis
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'REDIS_USERNAME': 'test',
        'REDIS_PASSWORD': 'test',
        'REDIS_SSL': 'false',
        'REDIS_CONNECTION_STRING': 'redis://test:test@localhost:6379/0',
        
        # WhatsApp
        'WHATSAPP_TOKEN': 'test-whatsapp-token',
        'WHATSAPP_VERIFY_TOKEN': 'verify-token',
        'WHATSAPP_PHONE_NUMBER_ID': 'test-phone-id',
        'WHATSAPP_VERSION': 'v18.0',
        
        # Computer Vision
        'AZURE_COMPUTER_VISION_ENDPOINT': 'https://test-vision.cognitiveservices.azure.com/',
        'AZURE_COMPUTER_VISION_API_KEY': 'test-vision-key',
        
        # ACS
        'ACS_ENDPOINT': 'https://test-acs.communication.azure.com/',
        'ACS_CHANNEL_ID': 'test-channel-id',
        'ACS_ACCESS_KEY': 'test-acs-key',
        'ACS_CONNECTION_STRING': 'endpoint=https://test-acs.communication.azure.com/;accesskey=test',
        
        # Event Grid
        'EVENT_GRID_TOPIC_ENDPOINT': 'https://test-topic.westus2-1.eventgrid.azure.net/api/events',
        'EVENT_GRID_TOPIC_KEY': 'test-event-grid-key',
        'EVENT_GRID_WEBHOOK_SECRET': 'test-webhook-secret',
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        yield

@pytest.fixture(autouse=True)
def mock_redis():
    with patch("redis.Redis", MagicMock()):
        yield

@pytest.fixture(autouse=True)
def mock_whatsapp_service():
    """Mock WhatsAppService to avoid URL issues in tests"""
    with patch('shared_code.whatsapp_service.WhatsAppService.send_text_message') as mock_send, \
         patch('shared_code.whatsapp_service.WhatsAppService.send_document_message') as mock_doc, \
         patch('shared_code.whatsapp_service.WhatsAppService.send_template_message') as mock_template, \
         patch('shared_code.whatsapp_service.WhatsAppService.send_interactive_message') as mock_interactive, \
         patch('shared_code.whatsapp_service.WhatsAppService.send_quick_reply_message') as mock_quick, \
         patch('shared_code.whatsapp_service.WhatsAppService.mark_message_as_read') as mock_read, \
         patch('httpx.post') as mock_httpx_post:
        
        mock_send.return_value = True
        mock_doc.return_value = True
        mock_template.return_value = True
        mock_interactive.return_value = True
        mock_quick.return_value = True
        mock_read.return_value = True
        
        # Mock HTTP responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test-message-id"}
        mock_httpx_post.return_value = mock_response
        
        yield {
            'send_text_message': mock_send,
            'send_document_message': mock_doc,
            'send_template_message': mock_template,
            'send_interactive_message': mock_interactive,
            'send_quick_reply_message': mock_quick,
            'mark_message_as_read': mock_read,
            'httpx_post': mock_httpx_post
        }

@pytest.fixture(autouse=True)
def mock_openai_service():
    """Mock OpenAIService to avoid connection issues in tests"""
    with patch('shared_code.openai_service.OpenAIService._validate_connections'):
        yield

@pytest.fixture(autouse=False)
def mock_user_service():
    """Mock UserService methods for E2E tests"""
    with patch('shared_code.user_service.UserService.get_user') as mock_get_user, \
         patch('shared_code.user_service.UserService.update_session') as mock_update_session, \
         patch('shared_code.user_service.UserService.create_user') as mock_create_user, \
         patch('shared_code.user_service.UserService.get_user_sessions') as mock_get_sessions, \
         patch('shared_code.user_service.UserService.create_session') as mock_create_session:
        
        # Mock user data
        mock_user = {
            "user_id": "+1234567890",
            "name": "Usuario de WhatsApp",
            "phone_number": "+1234567890"
        }
        mock_get_user.return_value = mock_user
        
        # Mock session data
        mock_session = MagicMock()
        mock_session.session_id = "test-session-123"
        mock_session.user_phone = "+1234567890"
        mock_session.is_active = True
        mock_session.context = {}
        mock_create_session.return_value = mock_session
        mock_get_sessions.return_value = []
        
        # Mock other methods
        mock_create_user.return_value = True
        mock_update_session.return_value = True
        
        yield {
            'get_user': mock_get_user,
            'update_session': mock_update_session,
            'create_user': mock_create_user,
            'get_user_sessions': mock_get_sessions,
            'create_session': mock_create_session
        }

@pytest.fixture(autouse=True)
def mock_redis_global():
    with patch('redis.Redis') as mock_redis:
        mock_instance = MagicMock()
        mock_redis.return_value = mock_instance
        # Configuración por defecto
        mock_instance.exists.return_value = False
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.delete.return_value = 1
        mock_instance.keys.return_value = []
        mock_instance.scan.return_value = (0, [])
        yield mock_instance

@pytest.fixture(autouse=True)
def reload_config():
    """Recarga la configuración después de aplicar los mocks de entorno"""
    # Limpiar cualquier instancia previa de settings
    modules_to_clear = [
        'config.settings',
        'config',
        'shared_code.whatsapp_service',
        'shared_code',
        'whatsapp_bot.whatsapp_bot',
        'whatsapp_bot'
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    # Recargar la configuración
    from config import settings
    yield settings 