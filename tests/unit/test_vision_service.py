"""
Unit tests for Vision service module.

This module contains comprehensive tests for the VisionService class
with mocked ComputerVisionClient and full coverage of all methods.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from msrest.exceptions import ClientRequestError, HttpOperationError
from src.shared_code.vision_service import VisionService

class TestVisionService:
    """Test cases for VisionService class."""

    @pytest.fixture
    def mock_settings_env(self):
        with patch('src.shared_code.vision_service.settings') as mock_settings:
            mock_settings.computer_vision_endpoint = "https://test.cognitiveservices.azure.com/"
            mock_settings.computer_vision_key = "test-key"
            yield mock_settings

    @pytest.fixture
    def mock_cv_client(self):
        with patch('src.shared_code.vision_service.ComputerVisionClient') as mock_client:
            yield mock_client

    @pytest.fixture
    def vision_service(self, mock_settings_env, mock_cv_client):
        with patch('src.shared_code.vision_service.VisionService._validate_connection'):
            service = VisionService()
            service.client = Mock()
            return service

    def test_extract_text_from_image_url_success(self, vision_service):
        mock_result = Mock()
        mock_result.regions = [Mock(lines=[Mock(words=[Mock(text="Hola"), Mock(text="Mundo")])])]
        vision_service.client.recognize_printed_text.return_value = mock_result
        with patch.object(vision_service, '_extract_text_from_result', return_value="Hola Mundo"):
            result = vision_service.extract_text_from_image_url("http://test.com/image.png")
            assert "Hola Mundo" in result

    def test_extract_text_from_image_url_invalid(self, vision_service):
        with pytest.raises(ValueError):
            vision_service.extract_text_from_image_url("")

    def test_extract_text_from_image_url_api_error(self, vision_service):
        vision_service.client.recognize_printed_text.side_effect = ClientRequestError("API error")
        with pytest.raises(ClientRequestError):
            vision_service.extract_text_from_image_url("http://test.com/image.png")

    def test_extract_text_from_image_file_success(self, vision_service):
        mock_result = Mock()
        vision_service.client.recognize_printed_text_in_stream.return_value = mock_result
        with patch('builtins.open', mock_open=True), \
             patch.object(vision_service, '_extract_text_from_result', return_value="Texto extraído"):
            result = vision_service.extract_text_from_image_file("test.png")
            assert "Texto extraído" in result

    def test_extract_text_from_image_file_not_found(self, vision_service):
        with patch('builtins.open', side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                vision_service.extract_text_from_image_file("noexiste.png")

    def test_extract_text_from_image_file_invalid(self, vision_service):
        with pytest.raises(ValueError):
            vision_service.extract_text_from_image_file("")

    def test_extract_text_from_image_bytes_success(self, vision_service):
        mock_result = Mock()
        vision_service.client.recognize_printed_text_in_stream.return_value = mock_result
        with patch.object(vision_service, '_extract_text_from_result', return_value="Texto bytes"):
            result = vision_service.extract_text_from_image_bytes(b"1234")
            assert "Texto bytes" in result

    def test_extract_text_from_image_bytes_invalid(self, vision_service):
        with pytest.raises(ValueError):
            vision_service.extract_text_from_image_bytes(b"")

    def test_extract_text_async_success(self, vision_service):
        mock_operation = Mock()
        mock_operation.headers = {"Operation-Location": "https://test/operation/123"}
        mock_result = Mock()
        mock_result.status = "succeeded"
        mock_result.analyze_result.read_results = [Mock(lines=[Mock(text="Async text")])]
        vision_service.client.read.return_value = mock_operation
        vision_service.client.get_read_result.side_effect = [Mock(status="running"), mock_result]
        result = vision_service.extract_text_async("http://test.com/image.png", max_wait_time=2)
        assert "Async text" in result

    def test_extract_text_async_timeout(self, vision_service):
        mock_operation = Mock()
        mock_operation.headers = {"Operation-Location": "https://test/operation/123"}
        vision_service.client.read.return_value = mock_operation
        vision_service.client.get_read_result.return_value = Mock(status="running")
        with patch('time.time', side_effect=[0, 2, 3, 4, 100]):
            with pytest.raises(TimeoutError):
                vision_service.extract_text_async("http://test.com/image.png", max_wait_time=1)

    def test_extract_text_async_invalid(self, vision_service):
        with pytest.raises(ValueError):
            vision_service.extract_text_async("")
        with pytest.raises(ValueError):
            vision_service.extract_text_async("url", max_wait_time=0)

    def test_analyze_image_content_success(self, vision_service):
        mock_analysis = Mock()
        mock_analysis.tags = [Mock(name="tag1", confidence=0.9)]
        mock_analysis.description.captions = [Mock(text="desc", confidence=0.8)]
        mock_analysis.description.tags = ["tag1"]
        mock_analysis.categories = [Mock(name="cat1", score=0.7)]
        vision_service.client.analyze_image.return_value = mock_analysis
        result = vision_service.analyze_image_content("http://test.com/image.png")
        assert "tags" in result
        assert "description" in result
        assert "categories" in result

    def test_analyze_image_content_invalid(self, vision_service):
        with pytest.raises(ValueError):
            vision_service.analyze_image_content("")

    def test_detect_language_default(self, vision_service):
        result = vision_service.detect_language("Texto de prueba")
        assert result == "en"

    def test_detect_language_invalid(self, vision_service):
        with pytest.raises(ValueError):
            vision_service.detect_language("")

    def test_validate_image_format_success(self, vision_service):
        with patch('imghdr.what', return_value='jpeg'):
            assert vision_service.validate_image_format("test.jpg")

    def test_validate_image_format_invalid(self, vision_service):
        with patch('imghdr.what', return_value=None):
            assert not vision_service.validate_image_format("test.txt")

    def test_get_image_metadata_success(self, vision_service):
        mock_img = Mock()
        mock_img.format = "JPEG"
        mock_img.mode = "RGB"
        mock_img.size = (100, 100)
        mock_img.width = 100
        mock_img.height = 100
        mock_img.tell.return_value = 1234
        with patch('PIL.Image.open', return_value=mock_img):
            result = vision_service.get_image_metadata("test.jpg")
            assert result["format"] == "JPEG"
            assert result["width"] == 100

    def test_get_image_metadata_not_found(self, vision_service):
        with patch('PIL.Image.open', side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                vision_service.get_image_metadata("noexiste.jpg")

    def test__extract_text_from_result(self, vision_service):
        mock_result = Mock()
        mock_result.regions = [Mock(lines=[Mock(words=[Mock(text="Hola"), Mock(text="Mundo")])])]
        text = vision_service._extract_text_from_result(mock_result)
        assert "Hola" in text

    def test_health_check_success(self, vision_service):
        vision_service.client.analyze_image.return_value = Mock()
        assert vision_service.health_check()

    def test_health_check_fail(self, vision_service):
        vision_service.client.analyze_image.side_effect = Exception("fail")
        with pytest.raises(Exception):
            vision_service.health_check() 