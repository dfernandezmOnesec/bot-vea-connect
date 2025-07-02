"""
Unit tests for WhatsApp service module.

This module contains comprehensive tests for the WhatsAppService class
with mocked requests and full coverage of all methods.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from requests.exceptions import HTTPError, RequestException
from shared_code.whatsapp_service import WhatsAppService

class TestWhatsAppService:
    """Test cases for WhatsAppService class."""

    @pytest.fixture
    def mock_settings_env(self):
        with patch('src.shared_code.whatsapp_service.settings') as mock_settings:
            mock_settings.access_token = "test-token"
            mock_settings.phone_number_id = "12345"
            mock_settings.recipient_waid = "54321"
            mock_settings.version = "v16.0"
            mock_settings.verify_token = "verify-token"
            yield mock_settings

    @pytest.fixture
    def whatsapp_service(self, mock_settings_env):
        with patch('src.shared_code.whatsapp_service.WhatsAppService._validate_configuration'):
            service = WhatsAppService()
            service.base_url = "https://graph.facebook.com/v16.0/12345"
            service.headers = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}
            return service

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_text_message_success(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"messages": ["ok"]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        result = whatsapp_service.send_text_message("Hola", recipient_id="54321")
        assert "messages" in result

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_text_message_invalid(self, mock_post, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.send_text_message("")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_text_message_http_error(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(response=Mock(status_code=400, text="Bad Request"))
        mock_post.return_value = mock_response
        with pytest.raises(HTTPError):
            whatsapp_service.send_text_message("Hola")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_text_message_request_error(self, mock_post, whatsapp_service):
        mock_post.side_effect = RequestException("Network error")
        with pytest.raises(RequestException):
            whatsapp_service.send_text_message("Hola")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_document_message_success(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"messages": ["ok"]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        result = whatsapp_service.send_document_message("http://file", "file.pdf")
        assert "messages" in result

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_document_message_invalid(self, mock_post, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.send_document_message("", "file.pdf")
        with pytest.raises(ValueError):
            whatsapp_service.send_document_message("http://file", "")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_document_message_http_error(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(response=Mock(status_code=400, text="Bad Request"))
        mock_post.return_value = mock_response
        with pytest.raises(HTTPError):
            whatsapp_service.send_document_message("http://file", "file.pdf")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_template_message_success(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"messages": ["ok"]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        result = whatsapp_service.send_template_message("template_name", {"var": "value"})
        assert "messages" in result

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_template_message_invalid(self, mock_post, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.send_template_message("", {})

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_template_message_http_error(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(response=Mock(status_code=400, text="Bad Request"))
        mock_post.return_value = mock_response
        with pytest.raises(HTTPError):
            whatsapp_service.send_template_message("template_name", {})

    def test_verify_webhook_success(self, whatsapp_service):
        result = whatsapp_service.verify_webhook("subscribe", "verify-token", "challenge")
        assert result == "challenge"

    def test_verify_webhook_invalid(self, whatsapp_service):
        result = whatsapp_service.verify_webhook("subscribe", "wrong-token", "challenge")
        assert result is None
        with pytest.raises(ValueError):
            whatsapp_service.verify_webhook("", "", "")

    def test_process_webhook_event_success(self, whatsapp_service):
        event_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "id": "msgid",
                            "from": "54321",
                            "type": "text",
                            "timestamp": "123456",
                            "text": {"body": "Hola"}
                        }]
                    }
                }]
            }]
        }
        result = whatsapp_service.process_webhook_event(event_data)
        assert result["event_type"] == "message"
        assert result["message_content"] == "Hola"

    def test_process_webhook_event_invalid(self, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.process_webhook_event("")

    @patch('src.shared_code.whatsapp_service.requests.get')
    def test_get_message_status_success(self, mock_get, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"status": "delivered"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        result = whatsapp_service.get_message_status("msgid")
        assert result["status"] == "delivered"

    @patch('src.shared_code.whatsapp_service.requests.get')
    def test_get_message_status_invalid(self, mock_get, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.get_message_status("")

    @patch('src.shared_code.whatsapp_service.requests.get')
    def test_get_message_status_http_error(self, mock_get, whatsapp_service):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(response=Mock(status_code=400, text="Bad Request"))
        mock_get.return_value = mock_response
        with pytest.raises(HTTPError):
            whatsapp_service.get_message_status("msgid")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_interactive_message_success(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"messages": ["ok"]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        buttons = [{"id": "1", "title": "Yes"}, {"id": "2", "title": "No"}]
        result = whatsapp_service.send_interactive_message("Choose one", buttons)
        assert "messages" in result

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_interactive_message_invalid(self, mock_post, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.send_interactive_message("", [])

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_mark_message_as_read_success(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"status": "read"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        result = whatsapp_service.mark_message_as_read("msgid")
        assert result["status"] == "read"

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_mark_message_as_read_invalid(self, mock_post, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.mark_message_as_read("")

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_quick_reply_message_success(self, mock_post, whatsapp_service):
        mock_response = Mock()
        mock_response.json.return_value = {"messages": ["ok"]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        quick_replies = [{"id": "1", "title": "Option 1"}]
        result = whatsapp_service.send_quick_reply_message("Choose", quick_replies)
        assert "messages" in result

    @patch('src.shared_code.whatsapp_service.requests.post')
    def test_send_quick_reply_message_invalid(self, mock_post, whatsapp_service):
        with pytest.raises(ValueError):
            whatsapp_service.send_quick_reply_message("", [])

    @patch('src.shared_code.whatsapp_service.requests.get')
    def test_health_check_success(self, mock_get, whatsapp_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        assert whatsapp_service.health_check()

    @patch('src.shared_code.whatsapp_service.requests.get')
    def test_health_check_fail(self, mock_get, whatsapp_service):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        with pytest.raises(Exception):
            whatsapp_service.health_check() 