"""
Computer Vision service module for text extraction from images.

This module provides functions for extracting text from images using
Azure Computer Vision OCR capabilities.
"""

import logging
import base64
from typing import Optional, List, Dict, Any
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from src.config.settings import settings

logger = logging.getLogger(__name__)

class VisionService:
    """Service class for Computer Vision operations."""
    
    def __init__(self):
        """Initialize the Computer Vision service."""
        try:
            self.endpoint = settings.computer_vision_endpoint
            self.key = settings.computer_vision_key
            self.client = ComputerVisionClient(
                self.endpoint,
                CognitiveServicesCredentials(self.key)
            )
            logger.info("Computer Vision service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Computer Vision service: {e}")
            raise

    def extract_text_from_image_url(self, image_url: str) -> str:
        """
        Extract text from an image using its URL.
        
        Args:
            image_url: URL of the image to process
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            # Call OCR API
            result = self.client.recognize_printed_text(url=image_url)
            
            # Extract text from results
            extracted_text = ""
            for region in result.regions:
                for line in region.lines:
                    for word in line.words:
                        extracted_text += word.text + " "
                    extracted_text += "\n"
                extracted_text += "\n"
            
            logger.info(f"Text extracted successfully from image URL. Length: {len(extracted_text)}")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from image URL: {e}")
            raise

    def extract_text_from_image_file(self, image_path: str) -> str:
        """
        Extract text from an image file.
        
        Args:
            image_path: Local path to the image file
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            with open(image_path, "rb") as image_file:
                result = self.client.recognize_printed_text_in_stream(image_file)
            
            # Extract text from results
            extracted_text = ""
            for region in result.regions:
                for line in region.lines:
                    for word in line.words:
                        extracted_text += word.text + " "
                    extracted_text += "\n"
                extracted_text += "\n"
            
            logger.info(f"Text extracted successfully from image file. Length: {len(extracted_text)}")
            return extracted_text.strip()
            
        except FileNotFoundError as e:
            logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from image file: {e}")
            raise

    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            from io import BytesIO
            image_stream = BytesIO(image_bytes)
            
            result = self.client.recognize_printed_text_in_stream(image_stream)
            
            # Extract text from results
            extracted_text = ""
            for region in result.regions:
                for line in region.lines:
                    for word in line.words:
                        extracted_text += word.text + " "
                    extracted_text += "\n"
                extracted_text += "\n"
            
            logger.info(f"Text extracted successfully from image bytes. Length: {len(extracted_text)}")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from image bytes: {e}")
            raise

    def extract_text_async(self, image_url: str) -> str:
        """
        Extract text from image using async OCR (better for complex documents).
        
        Args:
            image_url: URL of the image to process
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            # Start async OCR operation
            operation = self.client.read(url=image_url, raw=True)
            
            # Get operation location
            operation_location = operation.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]
            
            # Wait for operation to complete
            import time
            while True:
                result = self.client.get_read_result(operation_id)
                if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                    break
                time.sleep(1)
            
            # Extract text from results
            extracted_text = ""
            if result.status == OperationStatusCodes.succeeded:
                for text_result in result.analyze_result.read_results:
                    for line in text_result.lines:
                        extracted_text += line.text + "\n"
            
            logger.info(f"Async text extraction completed. Length: {len(extracted_text)}")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text async from image: {e}")
            raise

    def analyze_image_content(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze image content for tags, descriptions, and categories.
        
        Args:
            image_url: URL of the image to analyze
            
        Returns:
            Dict[str, Any]: Analysis results including tags, descriptions, categories
            
        Raises:
            Exception: If analysis fails
        """
        try:
            # Get image analysis
            analysis = self.client.analyze_image(
                url=image_url,
                features=["tags", "description", "categories"],
                language="en"
            )
            
            result = {
                "tags": [tag.name for tag in analysis.tags],
                "description": analysis.description.captions[0].text if analysis.description.captions else "",
                "categories": [cat.name for cat in analysis.categories],
                "confidence": analysis.description.captions[0].confidence if analysis.description.captions else 0.0
            }
            
            logger.info(f"Image analysis completed. Tags: {len(result['tags'])}, Categories: {len(result['categories'])}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze image content: {e}")
            raise

    def detect_language(self, text: str) -> str:
        """
        Detect the language of extracted text.
        
        Args:
            text: Text to analyze for language detection
            
        Returns:
            str: Detected language code (e.g., 'en', 'es', 'fr')
            
        Raises:
            Exception: If language detection fails
        """
        try:
            # Use a simple heuristic for language detection
            # In production, you might want to use a dedicated language detection service
            import re
            
            # Simple patterns for common languages
            patterns = {
                'en': r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b',
                'es': r'\b(el|la|los|las|y|o|pero|en|con|por|para|de|del)\b',
                'fr': r'\b(le|la|les|et|ou|mais|dans|avec|pour|de|du|des)\b'
            }
            
            text_lower = text.lower()
            scores = {}
            
            for lang, pattern in patterns.items():
                matches = len(re.findall(pattern, text_lower))
                scores[lang] = matches
            
            # Return language with highest score, default to English
            detected_lang = max(scores, key=scores.get) if any(scores.values()) else 'en'
            
            logger.info(f"Language detected: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            return 'en'  # Default to English

    def validate_image_format(self, image_path: str) -> bool:
        """
        Validate if the image format is supported.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if format is supported
            
        Raises:
            Exception: If validation fails
        """
        try:
            from PIL import Image
            
            supported_formats = ['JPEG', 'PNG', 'BMP', 'GIF', 'TIFF']
            
            with Image.open(image_path) as img:
                format_name = img.format
                
            is_supported = format_name in supported_formats
            
            if not is_supported:
                logger.warning(f"Unsupported image format: {format_name}")
            
            return is_supported
            
        except Exception as e:
            logger.error(f"Failed to validate image format: {e}")
            return False

    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Get basic metadata about an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict[str, Any]: Image metadata (size, format, dimensions)
            
        Raises:
            Exception: If metadata extraction fails
        """
        try:
            from PIL import Image
            import os
            
            with Image.open(image_path) as img:
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "file_size": os.path.getsize(image_path)
                }
            
            logger.info(f"Image metadata extracted: {metadata['format']}, {metadata['size']}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get image metadata: {e}")
            raise

# Global instance for easy access
vision_service = VisionService() 