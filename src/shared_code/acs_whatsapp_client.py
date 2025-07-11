import os
import logging
import requests
from typing import Dict


def send_whatsapp_message_via_acs(to_number: str, message: str) -> Dict:
    """
    Send a WhatsApp text message using Azure Communication Services (ACS) Advanced Messaging REST API.

    Args:
        to_number (str): Destination phone number in E.164 format.
        message (str): Text message to send.

    Returns:
        dict: Response JSON from ACS API.

    Raises:
        Exception: If the request fails or ACS returns an error.
    """
    logger: logging.Logger = logging.getLogger(__name__)
    acs_endpoint = os.environ.get("ACS_ENDPOINT")
    acs_channel_id = os.environ.get("ACS_CHANNEL_ID")
    acs_access_key = os.environ.get("ACS_ACCESS_KEY")

    if not all([acs_endpoint, acs_channel_id, acs_access_key]):
        logger.error("Missing ACS configuration in environment variables.")
        raise Exception("Missing ACS configuration in environment variables.")

    url = f"{acs_endpoint}/messages?api-version=2023-04-15-preview"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {acs_access_key}"
    }
    payload = {
        "channelRegistrationId": acs_channel_id,
        "to": to_number,
        "message": {
            "type": "text",
            "text": {
                "body": message
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"WhatsApp message sent to {to_number} via ACS.")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message via ACS: {e}")
        raise
