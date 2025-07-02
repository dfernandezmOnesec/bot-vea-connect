"""
Computer Vision service module for text extraction from images.

This module provides functions for extracting text from images using
Azure Computer Vision OCR capabilities with production-grade features
and enhanced error handling.
"""

import logging
import base64
import time
from typing import Optional, List, Dict, Any, Union
from io import BytesIO
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from msrest.exceptions import ClientRequestError, HttpOperationError
from config.settings import settings

logger = logging.getLogger(__name__)

class VisionService:
    """Service class for Computer Vision operations with production-grade features."""
    
    def __init__(self):
        """Initialize the Computer Vision service with connection validation."""
        try:
            self.endpoint = settings.computer_vision_endpoint
            self.key = settings.computer_vision_key
            
            # Validate configuration
            if not self.endpoint or not self.key:
                raise ValueError("Computer Vision endpoint and key are required")
            
            self.client = ComputerVisionClient(
                self.endpoint,
                CognitiveServicesCredentials(self.key)
            )
            
            # Validate connection
            self._validate_connection()
            
            logger.info("Computer Vision service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Computer Vision service: {e}")
            raise

    def _validate_connection(self) -> None:
        """
        Validate the connection to Computer Vision service.
        
        Raises:
            Exception: If connection validation fails
        """
        try:
            # Test with a simple operation
            test_url = "https://via.placeholder.com/100x100.png?text=Test"
            self.client.analyze_image(url=test_url, features=["tags"])
            logger.debug("Computer Vision connection validated successfully")
            
        except Exception as e:
            logger.error(f"Computer Vision connection validation failed: {e}")
            raise

    def extract_text_from_image_url(
        self, 
        image_url: str, 
        language: str = "en"
    ) -> str:
        """
        Extract text from an image using its URL with enhanced processing.
        
        Args:
            image_url: URL of the image to process
            language: Language hint for OCR (default: "en")
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            ValueError: If image_url is empty or invalid
            ClientRequestError: If Computer Vision API request fails
            HttpOperationError: If Computer Vision API returns an error
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not image_url or not image_url.strip():
                raise ValueError("Image URL cannot be empty")
            
            # Call OCR API with language hint
            result = self.client.recognize_printed_text(url=image_url, language=language)
            
            # Extract text from results with enhanced formatting
            extracted_text = self._extract_text_from_result(result)
            
            logger.info(f"Text extracted successfully from image URL. Length: {len(extracted_text)}")
            return extracted_text
            
        except ValueError as e:
            logger.error(f"Invalid input for text extraction from URL: {e}")
            raise
        except ClientRequestError as e:
            logger.error(f"Computer Vision API request failed for URL: {e}")
            raise
        except HttpOperationError as e:
            logger.error(f"Computer Vision API error for URL: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from image URL: {e}")
            raise

    def extract_text_from_image_file(
        self, 
        image_path: str, 
        language: str = "en"
    ) -> str:
        """
        Extract text from an image file with enhanced validation.
        
        Args:
            image_path: Local path to the image file
            language: Language hint for OCR (default: "en")
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image_path is empty or invalid
            ClientRequestError: If Computer Vision API request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not image_path or not image_path.strip():
                raise ValueError("Image path cannot be empty")
            
            with open(image_path, "rb") as image_file:
                result = self.client.recognize_printed_text_in_stream(image_file, language=language)
            
            # Extract text from results
            extracted_text = self._extract_text_from_result(result)
            
            logger.info(f"Text extracted successfully from image file. Length: {len(extracted_text)}")
            return extracted_text
            
        except FileNotFoundError as e:
            logger.error(f"Image file not found: {image_path}")
            raise
        except ValueError as e:
            logger.error(f"Invalid input for text extraction from file: {e}")
            raise
        except ClientRequestError as e:
            logger.error(f"Computer Vision API request failed for file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from image file: {e}")
            raise

    def extract_text_from_image_bytes(
        self, 
        image_bytes: bytes, 
        language: str = "en"
    ) -> str:
        """
        Extract text from image bytes with enhanced processing.
        
        Args:
            image_bytes: Image data as bytes
            language: Language hint for OCR (default: "en")
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            ValueError: If image_bytes is empty or invalid
            ClientRequestError: If Computer Vision API request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not image_bytes or len(image_bytes) == 0:
                raise ValueError("Image bytes cannot be empty")
            
            image_stream = BytesIO(image_bytes)
            result = self.client.recognize_printed_text_in_stream(image_stream, language=language)
            
            # Extract text from results
            extracted_text = self._extract_text_from_result(result)
            
            logger.info(f"Text extracted successfully from image bytes. Length: {len(extracted_text)}")
            return extracted_text
            
        except ValueError as e:
            logger.error(f"Invalid input for text extraction from bytes: {e}")
            raise
        except ClientRequestError as e:
            logger.error(f"Computer Vision API request failed for bytes: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from image bytes: {e}")
            raise

    def extract_text_async(
        self, 
        image_url: str, 
        max_wait_time: int = 60
    ) -> str:
        """
        Extract text from image using async OCR (better for complex documents).
        
        Args:
            image_url: URL of the image to process
            max_wait_time: Maximum time to wait for operation completion (seconds)
            
        Returns:
            str: Extracted text from the image
            
        Raises:
            ValueError: If input parameters are invalid
            TimeoutError: If operation takes too long
            ClientRequestError: If Computer Vision API request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not image_url or not image_url.strip():
                raise ValueError("Image URL cannot be empty")
            
            if max_wait_time <= 0:
                raise ValueError("Max wait time must be positive")
            
            # Start async OCR operation
            operation = self.client.read(url=image_url, raw=True)
            
            # Get operation location
            operation_location = operation.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]
            
            # Wait for operation to complete with timeout
            start_time = time.time()
            while True:
                if time.time() - start_time > max_wait_time:
                    raise TimeoutError(f"OCR operation timed out after {max_wait_time} seconds")
                
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
            else:
                raise Exception(f"OCR operation failed with status: {result.status}")
            
            extracted_text = extracted_text.strip()
            logger.info(f"Async text extraction completed. Length: {len(extracted_text)}")
            return extracted_text
            
        except ValueError as e:
            logger.error(f"Invalid input for async text extraction: {e}")
            raise
        except TimeoutError as e:
            logger.error(f"Async text extraction timed out: {e}")
            raise
        except ClientRequestError as e:
            logger.error(f"Computer Vision API request failed for async extraction: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text async from image: {e}")
            raise

    def analyze_image_content(
        self, 
        image_url: str, 
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze image content for tags, descriptions, and categories with enhanced features.
        
        Args:
            image_url: URL of the image to analyze
            features: List of features to analyze (default: ["tags", "description", "categories"])
            
        Returns:
            Dict[str, Any]: Analysis results including tags, descriptions, categories
            
        Raises:
            ValueError: If image_url is empty or features are invalid
            ClientRequestError: If Computer Vision API request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not image_url or not image_url.strip():
                raise ValueError("Image URL cannot be empty")
            
            if features is None:
                features = ["tags", "description", "categories"]
            
            # Get image analysis
            analysis = self.client.analyze_image(
                url=image_url,
                features=features,
                language="en"
            )
            
            # Process results
            result = {
                "tags": [{"name": tag.name, "confidence": tag.confidence} for tag in analysis.tags],
                "description": {
                    "captions": [{"text": caption.text, "confidence": caption.confidence} for caption in analysis.description.captions],
                    "tags": analysis.description.tags
                },
                "categories": [{"name": cat.name, "score": cat.score} for cat in analysis.categories]
            }
            
            logger.info(f"Image analysis completed. Tags: {len(result['tags'])}, Categories: {len(result['categories'])}")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for image analysis: {e}")
            raise
        except ClientRequestError as e:
            logger.error(f"Computer Vision API request failed for image analysis: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to analyze image content: {e}")
            raise

    def detect_language(self, text: str) -> str:
        """
        Detect the language of text using Computer Vision.
        
        Args:
            text: Text to analyze for language detection
            
        Returns:
            str: Detected language code
            
        Raises:
            ValueError: If text is empty
            ClientRequestError: If Computer Vision API request fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty for language detection")
            
            # Use a simple image with text for language detection
            # Note: Computer Vision doesn't have direct text language detection
            # This is a placeholder for future implementation
            logger.warning("Language detection not implemented in Computer Vision service")
            return "en"  # Default to English
            
        except ValueError as e:
            logger.error(f"Invalid input for language detection: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            raise

    def validate_image_format(self, image_path: str) -> bool:
        """
        Validate if an image file is in a supported format.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if image format is supported
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: For other unexpected errors
        """
        try:
            import imghdr
            
            # Check if file exists
            if not image_path or not image_path.strip():
                return False
            
            # Check image format
            image_type = imghdr.what(image_path)
            supported_formats = ['jpeg', 'jpg', 'png', 'bmp', 'gif', 'tiff']
            
            is_valid = image_type in supported_formats
            
            logger.debug(f"Image format validation for {image_path}: {image_type} - {'valid' if is_valid else 'invalid'}")
            return is_valid
            
        except FileNotFoundError as e:
            logger.error(f"Image file not found for format validation: {image_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to validate image format: {e}")
            raise

    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Get metadata from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict[str, Any]: Image metadata
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: For other unexpected errors
        """
        try:
            from PIL import Image
            
            # Validate input
            if not image_path or not image_path.strip():
                raise ValueError("Image path cannot be empty")
            
            with Image.open(image_path) as img:
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "file_size": img.tell() if hasattr(img, 'tell') else None
                }
                
                # Add EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    metadata["exif"] = dict(img._getexif())
            
            logger.info(f"Image metadata retrieved for {image_path}")
            return metadata
            
        except FileNotFoundError as e:
            logger.error(f"Image file not found for metadata: {image_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to get image metadata: {e}")
            raise

    def _extract_text_from_result(self, result) -> str:
        """
        Extract text from OCR result with enhanced formatting.
        
        Args:
            result: OCR result from Computer Vision API
            
        Returns:
            str: Formatted extracted text
        """
        try:
            extracted_text = ""
            
            if hasattr(result, 'regions'):
                # For recognize_printed_text results
                for region in result.regions:
                    for line in region.lines:
                        line_text = " ".join([word.text for word in line.words])
                        extracted_text += line_text + "\n"
                    extracted_text += "\n"
            elif hasattr(result, 'analyze_result'):
                # For read results
                for text_result in result.analyze_result.read_results:
                    for line in text_result.lines:
                        extracted_text += line.text + "\n"
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from result: {e}")
            return ""

    def health_check(self) -> bool:
        """
        Perform a health check on the Computer Vision service.
        
        Returns:
            bool: True if service is healthy
            
        Raises:
            Exception: If health check fails
        """
        try:
            # Test with a simple image analysis
            test_url = "https://via.placeholder.com/100x100.png?text=Health"
            self.client.analyze_image(url=test_url, features=["tags"])
            
            logger.debug("Computer Vision service health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Computer Vision service health check failed: {e}")
            raise

# Global instance for easy access
try:
    vision_service = VisionService()
except Exception as e:
    # Fallback for testing environments without proper configuration
    vision_service = None 