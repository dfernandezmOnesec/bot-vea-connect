"""
WhatsApp service module for Meta WhatsApp Business API integration.

This module provides functions for sending messages and handling
WhatsApp webhook events.
"""

import logging
import json
import requests
from typing import Dict, Any, Optional, List
from src.config.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service class for WhatsApp operations."""
    
    def __init__(self):
        """Initialize the WhatsApp service."""
        try:
            self.access_token = settings.access_token
            self.phone_number_id = settings.phone_number_id
            self.recipient_waid = settings.recipient_waid
            self.version = settings.version
            self.verify_token = settings.verify_token
            
            self.base_url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}"
            self.headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info("WhatsApp service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp service: {e}")
            raise

    def send_text_message(self, message: str, recipient_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            message: Text message to send
            recipient_id: WhatsApp ID of the recipient (defaults to configured recipient)
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            Exception: If message sending fails
        """
        try:
            recipient = recipient_id or self.recipient_waid
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Text message sent successfully to {recipient}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send text message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending text message: {e}")
            raise

    def send_document_message(
        self, 
        document_url: str, 
        filename: str,
        caption: Optional[str] = None,
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a document via WhatsApp.
        
        Args:
            document_url: URL of the document to send
            filename: Name of the document file
            caption: Optional caption for the document
            recipient_id: WhatsApp ID of the recipient
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            Exception: If document sending fails
        """
        try:
            recipient = recipient_id or self.recipient_waid
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "document",
                "document": {
                    "link": document_url,
                    "filename": filename
                }
            }
            
            if caption:
                payload["document"]["caption"] = caption
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Document message sent successfully to {recipient}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send document message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending document message: {e}")
            raise

    def send_template_message(
        self, 
        template_name: str,
        template_variables: Optional[Dict[str, Any]] = None,
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp.
        
        Args:
            template_name: Name of the template to use
            template_variables: Variables to substitute in the template
            recipient_id: WhatsApp ID of the recipient
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            Exception: If template message sending fails
        """
        try:
            recipient = recipient_id or self.recipient_waid
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"}
                }
            }
            
            if template_variables:
                payload["template"]["components"] = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(value)}
                            for value in template_variables.values()
                        ]
                    }
                ]
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Template message sent successfully to {recipient}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send template message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending template message: {e}")
            raise

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify WhatsApp webhook for initial setup.
        
        Args:
            mode: Verification mode from webhook request
            token: Verification token from webhook request
            challenge: Challenge string from webhook request
            
        Returns:
            Optional[str]: Challenge string if verification successful, None otherwise
            
        Raises:
            Exception: If verification fails
        """
        try:
            if mode == "subscribe" and token == self.verify_token:
                logger.info("Webhook verification successful")
                return challenge
            else:
                logger.warning("Webhook verification failed: invalid mode or token")
                return None
                
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            raise

    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook events from WhatsApp.
        
        Args:
            event_data: Raw webhook event data
            
        Returns:
            Dict[str, Any]: Processed event information
            
        Raises:
            Exception: If event processing fails
        """
        try:
            processed_event = {
                "event_type": "unknown",
                "message_id": None,
                "sender_id": None,
                "message_type": None,
                "message_content": None,
                "timestamp": None
            }
            
            # Extract entry and messaging data
            if "entry" in event_data and event_data["entry"]:
                entry = event_data["entry"][0]
                
                if "changes" in entry and entry["changes"]:
                    change = entry["changes"][0]
                    
                    if "value" in change and "messages" in change["value"]:
                        message = change["value"]["messages"][0]
                        
                        processed_event.update({
                            "event_type": "message",
                            "message_id": message.get("id"),
                            "sender_id": message.get("from"),
                            "message_type": message.get("type"),
                            "timestamp": message.get("timestamp")
                        })
                        
                        # Extract message content based on type
                        if message.get("type") == "text":
                            processed_event["message_content"] = message.get("text", {}).get("body")
                        elif message.get("type") == "document":
                            document = message.get("document", {})
                            processed_event["message_content"] = {
                                "filename": document.get("filename"),
                                "url": document.get("url"),
                                "mime_type": document.get("mime_type")
                            }
            
            logger.info(f"Webhook event processed: {processed_event['event_type']}")
            return processed_event
            
        except Exception as e:
            logger.error(f"Failed to process webhook event: {e}")
            raise

    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the status of a sent message.
        
        Args:
            message_id: ID of the message to check
            
        Returns:
            Dict[str, Any]: Message status information
            
        Raises:
            Exception: If status check fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/messages/{message_id}",
                headers=self.headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Message status retrieved for {message_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get message status: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting message status: {e}")
            raise

    def send_interactive_message(
        self,
        body_text: str,
        buttons: List[Dict[str, str]],
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an interactive message with buttons.
        
        Args:
            body_text: Main text of the message
            buttons: List of button configurations
            recipient_id: WhatsApp ID of the recipient
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            Exception: If interactive message sending fails
        """
        try:
            recipient = recipient_id or self.recipient_waid
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body_text},
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {"id": btn["id"], "title": btn["title"]}
                            }
                            for btn in buttons[:3]  # WhatsApp allows max 3 buttons
                        ]
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Interactive message sent successfully to {recipient}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send interactive message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending interactive message: {e}")
            raise

    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read.
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            Exception: If marking as read fails
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Message marked as read: {message_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to mark message as read: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error marking message as read: {e}")
            raise

# Global instance for easy access
whatsapp_service = WhatsAppService() 