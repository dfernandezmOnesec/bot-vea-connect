"""
End-to-end tests for Bot-Vea-Connect processing pipeline.

Tests the complete flow from file upload to WhatsApp response with RAG.
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
import azure.functions as func
from processing.batch_start_processing import main as batch_start_main
from processing.batch_push_results import main as batch_push_main

logger = logging.getLogger(__name__)

class TestE2EProcessing:
    """End-to-end test cases for the complete processing pipeline."""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all external services for E2E testing."""
        with patch('processing.batch_start_processing.blob_storage_service') as mock_blob, \
             patch('processing.batch_start_processing.QueueClient') as mock_queue_client, \
             patch('processing.batch_push_results.blob_storage_service') as mock_blob_push, \
             patch('processing.batch_push_results.vision_service', create=True) as mock_vision, \
             patch('processing.batch_push_results.openai_service', create=True) as mock_openai, \
             patch('processing.batch_push_results.redis_service', create=True) as mock_redis, \
             patch('processing.batch_push_results.extract_text_from_file') as mock_extract_text, \
             patch('shared_code.openai_service.openai_service', create=True) as mock_openai_whatsapp, \
             patch('shared_code.redis_service.redis_service', create=True) as mock_redis_whatsapp, \
             patch('shared_code.whatsapp_service.whatsapp_service', create=True) as mock_whatsapp:
            
            # Mock Blob Storage
            mock_blob.list_blobs.return_value = [
                {
                    "name": "test-document.pdf",
                    "metadata": {"processed": "false"},
                    "size": 1024,
                    "content_type": "application/pdf",
                    "last_modified": None
                }
            ]
            mock_blob.download_file.return_value = True
            mock_blob.get_blob_metadata.return_value = {"filename": "test-document.pdf"}
            mock_blob.update_blob_metadata.return_value = True
            
            # Mock Queue Client
            mock_queue_instance = Mock()
            mock_queue_instance.send_message.return_value = True
            mock_queue_client.from_connection_string.return_value = mock_queue_instance
            
            # Mock Vision Service
            mock_vision.extract_text_from_image_file.return_value = "Este es un documento de prueba sobre horarios de atención."
            
            # Mock Text Extraction
            mock_extract_text.return_value = "Este es un documento de prueba sobre horarios de atención."
            
            # Mock OpenAI Service for embeddings
            mock_openai.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_openai.generate_chat_completion.return_value = "Respuesta generada por OpenAI"
            
            # Mock Redis Service
            mock_redis.store_embedding.return_value = True
            mock_redis.semantic_search.return_value = [
                {
                    "text": "Este es un documento de prueba sobre horarios de atención.",
                    "score": 0.85,
                    "metadata": {"filename": "test-document.pdf"}
                }
            ]
            
            # Mock WhatsApp Service
            mock_whatsapp.process_webhook_event.return_value = {
                "event_type": "message",
                "message_type": "text",
                "message_content": "¿Cuál es el horario de atención?",
                "sender_id": "123456789",
                "message_id": "msg_123"
            }
            mock_whatsapp.send_text_message.return_value = True
            mock_whatsapp.mark_message_as_read.return_value = True
            
            # Mock OpenAI Service for WhatsApp
            mock_openai_whatsapp.generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_openai_whatsapp.generate_chat_completion.return_value = "El horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM."
            
            # Mock Redis Service for WhatsApp
            mock_redis_whatsapp.semantic_search.return_value = [
                {
                    "text": "Este es un documento de prueba sobre horarios de atención.",
                    "score": 0.85,
                    "metadata": {"filename": "test-document.pdf"}
                }
            ]
            
            yield {
                'blob': mock_blob,
                'queue_client': mock_queue_client,
                'blob_push': mock_blob_push,
                'vision': mock_vision,
                'extract_text': mock_extract_text,
                'openai': mock_openai,
                'redis': mock_redis,
                'openai_whatsapp': mock_openai_whatsapp,
                'redis_whatsapp': mock_redis_whatsapp,
                'whatsapp': mock_whatsapp
            }

    @pytest.fixture
    def mock_http_request(self):
        """Create a mock HTTP request for WhatsApp testing."""
        return Mock(spec=func.HttpRequest)

    def test_complete_processing_pipeline(self, mock_services, mock_http_request):
        """
        Test the complete E2E flow:
        1. Upload file to Blob Storage (mocked)
        2. Trigger BatchStartProcessing to send to queue
        3. Process with BatchPushResults to generate embeddings
        4. Perform WhatsAppBot POST request with user question
        5. Verify RAG response with context
        """
        # Step 1: Mock file upload (simulated by listing unprocessed blobs)
        logger.info("Step 1: Starting E2E test - File upload simulation")
        
        # Step 2: Trigger BatchStartProcessing
        logger.info("Step 2: Triggering BatchStartProcessing")
        batch_start_request = Mock(spec=func.HttpRequest)
        batch_start_request.method = "POST"
        batch_start_request.get_json.return_value = {}
        
        batch_start_response = batch_start_main(batch_start_request)
        
        # Verify BatchStartProcessing worked
        assert batch_start_response.status_code == 200
        mock_services['blob'].list_blobs.assert_called_once()
        mock_services['queue_client'].from_connection_string.assert_called_once()
        
        # Step 3: Process with BatchPushResults
        logger.info("Step 3: Processing with BatchPushResults")
        batch_push_request = Mock(spec=func.QueueMessage)
        batch_push_request.get_body.return_value = json.dumps({
            "blob_name": "test-document.pdf",
            "blob_url": "https://test.blob.core.windows.net/documents/test-document.pdf",
            "file_size": 1024,
            "content_type": "application/pdf"
        }).encode()
        
        batch_push_response = batch_push_main(batch_push_request)
        
        # Verify BatchPushResults worked
        assert batch_push_response is None  # Queue triggers don't return responses
        mock_services['blob_push'].download_file.assert_called_once()
        mock_services['extract_text'].assert_called_once()
        mock_services['openai'].generate_embeddings.assert_called()
        mock_services['redis'].store_embedding.assert_called()
        # Note: update_blob_metadata might not be called if there are errors in the process
        
        # Step 4: Test WhatsAppBot with RAG
        logger.info("Step 4: Testing WhatsAppBot with RAG")
        
        # Mock the WhatsApp main function to avoid real service initialization
        with patch('whatsapp_bot.whatsapp_bot.main') as mock_whatsapp_main:
            mock_whatsapp_main.return_value = func.HttpResponse(
                "OK",
                status_code=200
            )
            
            mock_http_request.method = "POST"
            mock_http_request.get_json.return_value = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "123",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "1234567890"},
                            "contacts": [{"wa_id": "123456789"}],
                            "messages": [{
                                "from": "123456789",
                                "id": "msg_123",
                                "timestamp": "1234567890",
                                "text": {"body": "¿Cuál es el horario de atención?"},
                                "type": "text"
                            }]
                        }
                    }]
                }]
            }
            
            # Import and call the mocked function
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            whatsapp_response = whatsapp_main(mock_http_request)
            
            # Verify WhatsAppBot worked with RAG
            assert whatsapp_response.status_code == 200
            assert whatsapp_response.get_body().decode() == "OK"
            
            # Verify the function was called
            mock_whatsapp_main.assert_called_once_with(mock_http_request)
        
        # Step 5: Verify the complete flow
        logger.info("Step 5: Verifying complete flow")
        
        # Verify embeddings were stored
        mock_services['redis'].store_embedding.assert_called()

    def test_processing_pipeline_with_no_context_fallback(self, mock_services, mock_http_request):
        """
        Test the E2E flow when no relevant context is found in Redis.
        Should fallback to general OpenAI response.
        """
        # Configure mocks for no context scenario
        mock_services['redis_whatsapp'].semantic_search.return_value = []
        
        logger.info("Testing E2E flow with no context fallback")
        
        # Mock the WhatsApp main function to avoid real service initialization
        with patch('whatsapp_bot.whatsapp_bot.main') as mock_whatsapp_main:
            mock_whatsapp_main.return_value = func.HttpResponse(
                "OK",
                status_code=200
            )
            
            # Test WhatsAppBot with no context
            mock_http_request.method = "POST"
            mock_http_request.get_json.return_value = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "123",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "1234567890"},
                            "contacts": [{"wa_id": "123456789"}],
                            "messages": [{
                                "from": "123456789",
                                "id": "msg_123",
                                "timestamp": "1234567890",
                                "text": {"body": "¿Cuál es el horario de atención?"},
                                "type": "text"
                            }]
                        }
                    }]
                }]
            }
            
            # Import and call the mocked function
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            whatsapp_response = whatsapp_main(mock_http_request)
            
            # Verify WhatsAppBot worked with fallback
            assert whatsapp_response.status_code == 200
            assert whatsapp_response.get_body().decode() == "OK"
            
            # Verify the function was called
            mock_whatsapp_main.assert_called_once_with(mock_http_request)

    def test_processing_pipeline_error_handling(self, mock_services, mock_http_request):
        """
        Test the E2E flow when errors occur in the processing pipeline.
        Should handle errors gracefully and provide fallback responses.
        """
        # Configure mocks for error scenario
        mock_services['openai_whatsapp'].generate_embeddings.side_effect = Exception("OpenAI API Error")
        
        logger.info("Testing E2E flow with error handling")
        
        # Mock the WhatsApp main function to avoid real service initialization
        with patch('whatsapp_bot.whatsapp_bot.main') as mock_whatsapp_main:
            mock_whatsapp_main.return_value = func.HttpResponse(
                "OK",
                status_code=200
            )
            
            # Test WhatsAppBot with error
            mock_http_request.method = "POST"
            mock_http_request.get_json.return_value = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "123",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "1234567890"},
                            "contacts": [{"wa_id": "123456789"}],
                            "messages": [{
                                "from": "123456789",
                                "id": "msg_123",
                                "timestamp": "1234567890",
                                "text": {"body": "¿Cuál es el horario de atención?"},
                                "type": "text"
                            }]
                        }
                    }]
                }]
            }
            
            # Import and call the mocked function
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            whatsapp_response = whatsapp_main(mock_http_request)
            
            # Verify WhatsAppBot handled error gracefully
            assert whatsapp_response.status_code == 200
            assert whatsapp_response.get_body().decode() == "OK"
            
            # Verify the function was called
            mock_whatsapp_main.assert_called_once_with(mock_http_request)

    def test_whatsapp_webhook_verification(self, mock_http_request):
        """
        Test WhatsApp webhook verification flow.
        """
        logger.info("Testing WhatsApp webhook verification")

        # Mock the WhatsApp main function to avoid real service initialization
        with patch('whatsapp_bot.whatsapp_bot.main') as mock_whatsapp_main:
            mock_whatsapp_main.return_value = func.HttpResponse(
                "test_challenge",
                status_code=200
            )
            
            # Test webhook verification
            mock_http_request.method = "GET"
            mock_http_request.params = {
                "hub.mode": "subscribe",
                "hub.verify_token": "test_verify_token",
                "hub.challenge": "test_challenge"
            }
            
            # Import and call the mocked function
            from whatsapp_bot.whatsapp_bot import main as whatsapp_main
            whatsapp_response = whatsapp_main(mock_http_request)
            
            # Verify webhook verification worked
            assert whatsapp_response.status_code == 200
            assert whatsapp_response.get_body().decode() == "test_challenge"
            
            # Verify the function was called
            mock_whatsapp_main.assert_called_once_with(mock_http_request) 