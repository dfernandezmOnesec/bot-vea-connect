import pytest
import os
from unittest.mock import patch, MagicMock
from shared_code.acs_whatsapp_client import send_whatsapp_message_via_acs

def test_send_whatsapp_message_via_acs_success(monkeypatch):
    os.environ["ACS_ENDPOINT"] = "https://fake.endpoint"
    os.environ["ACS_CHANNEL_ID"] = "fake-channel-id"
    os.environ["ACS_ACCESS_KEY"] = "fake-access-key"

    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "msg-123", "status": "sent"}
    mock_response.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = send_whatsapp_message_via_acs("+1234567890", "Hello!")
        assert result == {"id": "msg-123", "status": "sent"}
        mock_post.assert_called_once()
        # Verifica que la URL y el payload sean correctos
        args, kwargs = mock_post.call_args
        assert args[0] == "https://fake.endpoint/messages?api-version=2023-04-15-preview"
        assert kwargs["json"] == {
            "channelRegistrationId": "fake-channel-id",
            "to": "+1234567890",
            "message": {
                "type": "text",
                "text": {"body": "Hello!"}
            }
        }


def test_send_whatsapp_message_via_acs_error(monkeypatch):
    os.environ["ACS_ENDPOINT"] = "https://fake.endpoint"
    os.environ["ACS_CHANNEL_ID"] = "fake-channel-id"
    os.environ["ACS_ACCESS_KEY"] = "fake-access-key"

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("Request failed")

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(Exception) as excinfo:
            send_whatsapp_message_via_acs("+1234567890", "Hello!")
        assert "Request failed" in str(excinfo.value) 