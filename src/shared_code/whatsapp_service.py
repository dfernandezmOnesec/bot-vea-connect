"""
WhatsApp service module for Meta WhatsApp Business API integration.

This module provides functions for sending messages and handling
WhatsApp webhook events with production-grade features and enhanced error handling.
"""

import logging
import json
import requests
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from src.config.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service class for WhatsApp operations with production-grade features."""
    
    def __init__(self):
        """Initialize the WhatsApp service with connection validation."""
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
            
            # Validate configuration
            self._validate_configuration()
            
            logger.info("WhatsApp service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp service: {e}")
            raise

    def _validate_configuration(self) -> None:
        """
        Validate WhatsApp service configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "access_token", "phone_number_id", "recipient_waid", 
            "version", "verify_token"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"WhatsApp configuration missing: {field}")

    def send_text_message(
        self, 
        message: str, 
        recipient_id: Optional[str] = None,
        preview_url: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp with enhanced features.
        
        Args:
            message: Text message to send
            recipient_id: WhatsApp ID of the recipient (defaults to configured recipient)
            preview_url: Whether to show URL preview (default: None for auto-detection)
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            ValueError: If message is empty or invalid
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")
            
            recipient = recipient_id or self.recipient_waid
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message}
            }
            
            # Add preview URL setting if specified
            if preview_url is not None:
                payload["text"]["preview_url"] = preview_url
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Text message sent successfully to {recipient} (length: {len(message)})")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for text message: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error sending text message: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed sending text message: {e}")
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
        Send a document via WhatsApp with enhanced validation.
        
        Args:
            document_url: URL of the document to send
            filename: Name of the document file
            caption: Optional caption for the document
            recipient_id: WhatsApp ID of the recipient
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            ValueError: If input parameters are invalid
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not document_url or not filename:
                raise ValueError("Document URL and filename cannot be empty")
            
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
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Document message sent successfully to {recipient} (file: {filename})")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for document message: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error sending document message: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed sending document message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending document message: {e}")
            raise

    def send_template_message(
        self, 
        template_name: str,
        template_variables: Optional[Dict[str, Any]] = None,
        recipient_id: Optional[str] = None,
        language_code: str = "es"
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp with enhanced variable handling.
        
        Args:
            template_name: Name of the template to use
            template_variables: Variables to substitute in the template
            recipient_id: WhatsApp ID of the recipient
            language_code: Language code for the template (default: "es" for Spanish)
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            ValueError: If template_name is empty
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not template_name:
                raise ValueError("Template name cannot be empty")
            
            recipient = recipient_id or self.recipient_waid
            
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code}
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
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Template message sent successfully to {recipient} (template: {template_name})")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for template message: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error sending template message: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed sending template message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending template message: {e}")
            raise

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify WhatsApp webhook for initial setup with enhanced validation.
        
        Args:
            mode: Verification mode from webhook request
            token: Verification token from webhook request
            challenge: Challenge string from webhook request
            
        Returns:
            Optional[str]: Challenge string if verification successful, None otherwise
            
        Raises:
            ValueError: If input parameters are invalid
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not mode or not token or not challenge:
                raise ValueError("Mode, token, and challenge cannot be empty")
            
            if mode == "subscribe" and token == self.verify_token:
                logger.info("Webhook verification successful")
                return challenge
            else:
                logger.warning(f"Webhook verification failed: mode={mode}, token_match={token == self.verify_token}")
                return None
                
        except ValueError as e:
            logger.error(f"Invalid input for webhook verification: {e}")
            raise
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            raise

    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook events from WhatsApp with enhanced parsing.
        
        Args:
            event_data: Raw webhook event data
            
        Returns:
            Dict[str, Any]: Processed event information
            
        Raises:
            ValueError: If event_data is invalid
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not event_data or not isinstance(event_data, dict):
                raise ValueError("Event data must be a non-empty dictionary")
            
            processed_event = {
                "event_type": "unknown",
                "message_id": None,
                "sender_id": None,
                "message_type": None,
                "message_content": None,
                "timestamp": None,
                "processed_at": datetime.utcnow().isoformat()
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
                                "mime_type": document.get("mime_type"),
                                "file_size": document.get("file_size")
                            }
                        elif message.get("type") == "image":
                            image = message.get("image", {})
                            processed_event["message_content"] = {
                                "url": image.get("url"),
                                "mime_type": image.get("mime_type"),
                                "file_size": image.get("file_size")
                            }
            
            logger.info(f"Webhook event processed: {processed_event['event_type']} from {processed_event['sender_id']}")
            return processed_event
            
        except ValueError as e:
            logger.error(f"Invalid input for webhook event processing: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to process webhook event: {e}")
            raise

    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the status of a sent message with enhanced error handling.
        
        Args:
            message_id: ID of the message to check
            
        Returns:
            Dict[str, Any]: Message status information
            
        Raises:
            ValueError: If message_id is empty
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not message_id:
                raise ValueError("Message ID cannot be empty")
            
            response = requests.get(
                f"{self.base_url}/messages/{message_id}",
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Message status retrieved for {message_id}")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for message status check: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error getting message status: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed getting message status: {e}")
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
        Send an interactive message with buttons with enhanced validation.
        
        Args:
            body_text: Main text of the message
            buttons: List of button configurations (max 3 buttons)
            recipient_id: WhatsApp ID of the recipient
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            ValueError: If input parameters are invalid
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not body_text or not buttons:
                raise ValueError("Body text and buttons cannot be empty")
            
            if len(buttons) > 3:
                logger.warning(f"Too many buttons provided ({len(buttons)}), limiting to 3")
                buttons = buttons[:3]
            
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
                            for btn in buttons
                        ]
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Interactive message sent successfully to {recipient} with {len(buttons)} buttons")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for interactive message: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error sending interactive message: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed sending interactive message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending interactive message: {e}")
            raise

    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read with enhanced validation.
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            ValueError: If message_id is empty
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not message_id:
                raise ValueError("Message ID cannot be empty")
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Message marked as read: {message_id}")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for marking message as read: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error marking message as read: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed marking message as read: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error marking message as read: {e}")
            raise

    def send_quick_reply_message(
        self,
        body_text: str,
        quick_replies: List[Dict[str, str]],
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message with quick reply options.
        
        Args:
            body_text: Main text of the message
            quick_replies: List of quick reply options (max 3)
            recipient_id: WhatsApp ID of the recipient
            
        Returns:
            Dict[str, Any]: API response from WhatsApp
            
        Raises:
            ValueError: If input parameters are invalid
            HTTPError: If WhatsApp API returns an error
            RequestException: If request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not body_text or not quick_replies:
                raise ValueError("Body text and quick replies cannot be empty")
            
            if len(quick_replies) > 3:
                logger.warning(f"Too many quick replies provided ({len(quick_replies)}), limiting to 3")
                quick_replies = quick_replies[:3]
            
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
                                "reply": {"id": reply["id"], "title": reply["title"]}
                            }
                            for reply in quick_replies
                        ]
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Quick reply message sent successfully to {recipient} with {len(quick_replies)} options")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for quick reply message: {e}")
            raise
        except HTTPError as e:
            logger.error(f"WhatsApp API error sending quick reply message: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request failed sending quick reply message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending quick reply message: {e}")
            raise

    def health_check(self) -> bool:
        """
        Perform a health check on the WhatsApp service.
        
        Returns:
            bool: True if service is healthy
            
        Raises:
            Exception: If health check fails
        """
        try:
            # Test basic API access
            response = requests.get(
                f"https://graph.facebook.com/{self.version}/{self.phone_number_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("WhatsApp service health check passed")
                return True
            else:
                raise Exception(f"WhatsApp API health check failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"WhatsApp service health check failed: {e}")
            raise

# Global instance for easy access
whatsapp_service = WhatsAppService() 