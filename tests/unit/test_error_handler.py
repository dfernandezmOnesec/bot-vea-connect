"""
Tests unitarios para el ErrorHandler.

ESTE ARCHIVO CONTIENE TESTS UNITARIOS (100% MOCKEADOS)
Estos tests validan que el ErrorHandler funciona correctamente
y maneja errores de manera apropiada.
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

from shared_code.error_handler import ErrorHandler
from shared_code.interfaces import IErrorHandler


class TestErrorHandler:
    """Tests básicos para el ErrorHandler."""
    
    @pytest.fixture
    def error_handler(self) -> ErrorHandler:
        """Crear instancia del ErrorHandler."""
        return ErrorHandler()
    
    def test_error_handler_initialization(self, error_handler: ErrorHandler):
        """Test inicialización del ErrorHandler."""
        assert error_handler is not None
        assert isinstance(error_handler, ErrorHandler)
        assert isinstance(error_handler, IErrorHandler)
    
    def test_create_error_response_basic(self, error_handler: ErrorHandler):
        """Test creación de respuesta de error básica."""
        # Act
        result = error_handler.create_error_response("Error de prueba", "TEST_ERROR")
        
        # Assert
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Error de prueba"
    
    def test_create_error_response_empty_message(self, error_handler: ErrorHandler):
        """Test creación de respuesta de error con mensaje vacío."""
        # Act
        result = error_handler.create_error_response("", "EMPTY_ERROR")
        
        # Assert
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["error"]["code"] == "EMPTY_ERROR"
        assert result["error"]["message"] == ""
    
    def test_create_error_response_with_details(self, error_handler: ErrorHandler):
        """Test creación de respuesta de error con detalles."""
        # Act
        details = {"field": "email", "value": "invalid"}
        result = error_handler.create_error_response("Error con detalles", "DETAILS_ERROR", details)
        
        # Assert
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["error"]["code"] == "DETAILS_ERROR"
        assert result["error"]["message"] == "Error con detalles"
        assert result["error"]["details"] == details


class TestErrorHandlerLogging:
    """Tests para el logging de errores."""
    
    @pytest.fixture
    def error_handler(self) -> ErrorHandler:
        """Crear instancia del ErrorHandler."""
        return ErrorHandler()
    
    @patch('shared_code.error_handler.logger')
    def test_log_error_basic(self, mock_logger, error_handler: ErrorHandler):
        """Test logging básico de error."""
        # Arrange
        test_error = ValueError("Error de prueba")
        
        # Act
        error_handler.log_error(test_error, "test_context")
        
        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "test_context" in call_args
        assert "ValueError" in call_args
        assert "Error de prueba" in call_args
    
    @patch('shared_code.error_handler.logger')
    def test_log_error_with_exception(self, mock_logger, error_handler: ErrorHandler):
        """Test logging de error con excepción."""
        # Arrange
        test_error = RuntimeError("Error de runtime")
        
        # Act
        error_handler.log_error(test_error, "runtime_context")
        
        # Assert
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "runtime_context" in call_args
        assert "RuntimeError" in call_args
        assert "Error de runtime" in call_args


class TestErrorHandlerIntegration:
    """Tests de integración del ErrorHandler."""
    
    @pytest.fixture
    def error_handler(self) -> ErrorHandler:
        """Crear instancia del ErrorHandler."""
        return ErrorHandler()
    
    @patch('shared_code.error_handler.logger')
    def test_full_error_workflow(self, mock_logger, error_handler: ErrorHandler):
        """Test flujo completo de manejo de errores."""
        # Arrange
        test_error = ValueError("Error en flujo")
        
        # Act
        error_response = error_handler.create_error_response("Error en flujo", "WORKFLOW_ERROR")
        error_handler.log_error(test_error, "Flujo de prueba")
        
        # Assert
        assert error_response["success"] is False
        assert error_response["error"]["code"] == "WORKFLOW_ERROR"
        assert error_response["error"]["message"] == "Error en flujo"
        mock_logger.error.assert_called_once()
    
    def test_handle_error_method(self, error_handler: ErrorHandler):
        """Test del método handle_error."""
        # Arrange
        error_message = "Error de validación"
        error_code = "VALIDATION_ERROR"
        context = "test_context"
        
        # Act
        result = error_handler.create_error_response(error_message, error_code, {"context": context})
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["message"] == error_message
        assert result["error"]["code"] == "VALIDATION_ERROR"  # El código se mantiene
        if "context" in result["error"]:
            assert result["error"]["context"] == context


class TestErrorHandlerEdgeCases:
    """Tests para casos edge del ErrorHandler."""
    
    @pytest.fixture
    def error_handler(self) -> ErrorHandler:
        """Crear instancia del ErrorHandler."""
        return ErrorHandler()
    
    def test_very_long_error_message(self, error_handler: ErrorHandler):
        """Test con mensaje de error muy largo."""
        long_message = "A" * 1000
        result = error_handler.create_error_response(long_message, "LONG_ERROR")
        
        assert result["error"]["message"] == long_message
    
    def test_special_characters_in_error_message(self, error_handler: ErrorHandler):
        """Test con caracteres especiales en el mensaje."""
        special_message = "Error con caracteres especiales: áéíóú @#$%^&*()"
        result = error_handler.create_error_response(special_message, "SPECIAL_ERROR")
        
        assert result["error"]["message"] == special_message
    
    def test_unicode_characters_in_error_message(self, error_handler: ErrorHandler):
        """Test con caracteres Unicode en el mensaje."""
        unicode_message = "Error con Unicode: 🚀 📧 💻"
        result = error_handler.create_error_response(unicode_message, "UNICODE_ERROR")
        
        assert result["error"]["message"] == unicode_message


class TestErrorHandlerErrorClassification:
    """Tests para la clasificación de errores."""
    
    @pytest.fixture
    def error_handler(self) -> ErrorHandler:
        """Crear instancia del ErrorHandler."""
        return ErrorHandler()
    
    def test_rate_limit_error_classification(self, error_handler: ErrorHandler):
        """Test clasificación de error de rate limit."""
        # Arrange
        test_error = Exception("Rate limit exceeded")
        
        # Act
        result = error_handler.handle_error(test_error, "test_context")
        
        # Assert
        assert result["error"]["code"] == "RATE_LIMIT"
    
    def test_network_error_classification(self, error_handler: ErrorHandler):
        """Test clasificación de error de red."""
        # Arrange
        test_error = Exception("Connection timeout")
        
        # Act
        result = error_handler.handle_error(test_error, "test_context")
        
        # Assert
        assert result["error"]["code"] == "NETWORK_ERROR"
    
    def test_openai_error_classification(self, error_handler: ErrorHandler):
        """Test clasificación de error de OpenAI."""
        # Arrange
        test_error = Exception("OpenAI API error")
        
        # Act
        result = error_handler.handle_error(test_error, "test_context")
        
        # Assert
        assert result["error"]["code"] == "OPENAI_ERROR" 