"""
Tests unitarios para user_service.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

from src.shared_code.user_service import UserService, User, UserSession


class TestUser:
    """Tests para la clase User"""
    
    def test_user_creation(self):
        """Test creación de usuario"""
        user = User(
            phone_number="+1234567890",
            name="Juan Pérez",
            email="juan@example.com",
            preferences={"language": "es", "notifications": True}
        )
        
        assert user.phone_number == "+1234567890"
        assert user.name == "Juan Pérez"
        assert user.email == "juan@example.com"
        assert user.preferences["language"] == "es"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_to_dict(self):
        """Test conversión a diccionario"""
        user = User(
            phone_number="+1234567890",
            name="María García",
            email="maria@example.com"
        )
        
        user_dict = user.to_dict()
        
        assert user_dict["phone_number"] == "+1234567890"
        assert user_dict["name"] == "María García"
        assert user_dict["email"] == "maria@example.com"
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
    
    def test_user_from_dict(self):
        """Test creación desde diccionario"""
        user_data = {
            "phone_number": "+1234567890",
            "name": "Carlos López",
            "email": "carlos@example.com",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        user = User.from_dict(user_data)
        
        assert user.phone_number == "+1234567890"
        assert user.name == "Carlos López"
        assert user.email == "carlos@example.com"
        assert user.preferences["language"] == "es"


class TestUserSession:
    """Tests para la clase UserSession"""
    
    def test_session_creation(self):
        """Test creación de sesión"""
        session = UserSession(
            session_id="test-session-123",
            user_phone="+1234567890",
            context={"last_question": "¿Cuándo es el próximo evento?"},
            created_at=datetime.now()
        )
        
        assert session.session_id == "test-session-123"
        assert session.user_phone == "+1234567890"
        assert session.context["last_question"] == "¿Cuándo es el próximo evento?"
        assert session.is_active is True
    
    def test_session_to_dict(self):
        """Test conversión a diccionario"""
        session = UserSession(
            session_id="test-session-456",
            user_phone="+1234567890",
            context={"conversation_history": ["Hola", "¿Cómo estás?"]}
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "test-session-456"
        assert session_dict["user_phone"] == "+1234567890"
        assert session_dict["context"]["conversation_history"] == ["Hola", "¿Cómo estás?"]
        assert session_dict["is_active"] is True
    
    def test_session_from_dict(self):
        """Test creación desde diccionario"""
        session_data = {
            "session_id": "test-session-789",
            "user_phone": "+1234567890",
            "context": {"user_preferences": {"language": "es"}},
            "created_at": "2024-01-01T00:00:00",
            "is_active": True
        }
        
        session = UserSession.from_dict(session_data)
        
        assert session.session_id == "test-session-789"
        assert session.user_phone == "+1234567890"
        assert session.context["user_preferences"]["language"] == "es"
        assert session.is_active is True


class TestUserService:
    """Tests para la clase UserService"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock del cliente Redis"""
        return Mock()
    
    @pytest.fixture
    def user_service(self, mock_redis_client):
        """Instancia de UserService con Redis mockeado"""
        with patch('src.shared_code.user_service.Redis') as mock_redis:
            mock_redis.from_url.return_value = mock_redis_client
            return UserService(redis_connection_string="redis://localhost:6379")
    
    def test_init(self, mock_redis_client):
        """Test inicialización del servicio"""
        with patch('src.shared_code.user_service.Redis') as mock_redis:
            mock_redis.from_url.return_value = mock_redis_client
            
            service = UserService(redis_connection_string="redis://test:6379")
            
            mock_redis.from_url.assert_called_once_with("redis://test:6379")
            assert service.redis_client == mock_redis_client
    
    def test_create_user_success(self, user_service, mock_redis_client):
        """Test creación exitosa de usuario"""
        mock_redis_client.set.return_value = True
        mock_redis_client.expire.return_value = True
        
        user = User(
            phone_number="+1234567890",
            name="Ana Martínez",
            email="ana@example.com"
        )
        
        result = user_service.create_user(user)
        
        assert result is True
        mock_redis_client.set.assert_called_once()
        mock_redis_client.expire.assert_called_once()
    
    def test_create_user_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al crear usuario"""
        mock_redis_client.set.side_effect = Exception("Redis error")
        
        user = User(
            phone_number="+1234567890",
            name="Pedro Sánchez"
        )
        
        with pytest.raises(Exception) as exc_info:
            user_service.create_user(user)
        
        assert "Error al crear usuario" in str(exc_info.value)
    
    def test_get_user_success(self, user_service, mock_redis_client):
        """Test obtención exitosa de usuario"""
        user_data = {
            "phone_number": "+1234567890",
            "name": "Laura Torres",
            "email": "laura@example.com",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_redis_client.get.return_value = json.dumps(user_data).encode()
        
        user = user_service.get_user("+1234567890")
        
        assert user is not None
        assert user.phone_number == "+1234567890"
        assert user.name == "Laura Torres"
        assert user.email == "laura@example.com"
        mock_redis_client.get.assert_called_once_with("user:+1234567890")
    
    def test_get_user_not_found(self, user_service, mock_redis_client):
        """Test usuario no encontrado"""
        mock_redis_client.get.return_value = None
        
        user = user_service.get_user("+1234567890")
        
        assert user is None
        mock_redis_client.get.assert_called_once_with("user:+1234567890")
    
    def test_get_user_invalid_data(self, user_service, mock_redis_client):
        """Test datos inválidos en Redis"""
        mock_redis_client.get.return_value = b"invalid json"
        
        user = user_service.get_user("+1234567890")
        
        assert user is None
    
    def test_update_user_success(self, user_service, mock_redis_client):
        """Test actualización exitosa de usuario"""
        mock_redis_client.set.return_value = True
        mock_redis_client.expire.return_value = True
        
        user = User(
            phone_number="+1234567890",
            name="Roberto Díaz",
            email="roberto@example.com"
        )
        
        result = user_service.update_user(user)
        
        assert result is True
        mock_redis_client.set.assert_called_once()
        mock_redis_client.expire.assert_called_once()
    
    def test_update_user_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al actualizar usuario"""
        mock_redis_client.set.side_effect = Exception("Redis error")
        
        user = User(
            phone_number="+1234567890",
            name="Carmen Ruiz"
        )
        
        with pytest.raises(Exception) as exc_info:
            user_service.update_user(user)
        
        assert "Error al actualizar usuario" in str(exc_info.value)
    
    def test_delete_user_success(self, user_service, mock_redis_client):
        """Test eliminación exitosa de usuario"""
        mock_redis_client.delete.return_value = 1
        
        result = user_service.delete_user("+1234567890")
        
        assert result is True
        mock_redis_client.delete.assert_called_once_with("user:+1234567890")
    
    def test_delete_user_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al eliminar usuario"""
        mock_redis_client.delete.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            user_service.delete_user("+1234567890")
        
        assert "Error al eliminar usuario" in str(exc_info.value)
    
    def test_create_session_success(self, user_service, mock_redis_client):
        """Test creación exitosa de sesión"""
        mock_redis_client.set.return_value = True
        mock_redis_client.expire.return_value = True
        
        session = user_service.create_session("+1234567890")
        
        assert session is not None
        assert session.user_phone == "+1234567890"
        assert session.is_active is True
        assert session.session_id is not None
        mock_redis_client.set.assert_called_once()
        mock_redis_client.expire.assert_called_once()
    
    def test_create_session_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al crear sesión"""
        mock_redis_client.set.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            user_service.create_session("+1234567890")
        
        assert "Error al crear sesión" in str(exc_info.value)
    
    def test_get_session_success(self, user_service, mock_redis_client):
        """Test obtención exitosa de sesión"""
        session_data = {
            "session_id": "test-session-123",
            "user_phone": "+1234567890",
            "context": {"last_question": "¿Cuándo es el próximo evento?"},
            "created_at": "2024-01-01T00:00:00",
            "is_active": True
        }
        
        mock_redis_client.get.return_value = json.dumps(session_data).encode()
        
        session = user_service.get_session("test-session-123")
        
        assert session is not None
        assert session.session_id == "test-session-123"
        assert session.user_phone == "+1234567890"
        assert session.context["last_question"] == "¿Cuándo es el próximo evento?"
        mock_redis_client.get.assert_called_once_with("session:test-session-123")
    
    def test_get_session_not_found(self, user_service, mock_redis_client):
        """Test sesión no encontrada"""
        mock_redis_client.get.return_value = None
        
        session = user_service.get_session("test-session-123")
        
        assert session is None
        mock_redis_client.get.assert_called_once_with("session:test-session-123")
    
    def test_update_session_success(self, user_service, mock_redis_client):
        """Test actualización exitosa de sesión"""
        mock_redis_client.set.return_value = True
        mock_redis_client.expire.return_value = True
        
        session = UserSession(
            session_id="test-session-456",
            user_phone="+1234567890",
            context={"conversation_history": ["Hola", "¿Cómo estás?"]}
        )
        
        result = user_service.update_session(session)
        
        assert result is True
        mock_redis_client.set.assert_called_once()
        mock_redis_client.expire.assert_called_once()
    
    def test_update_session_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al actualizar sesión"""
        mock_redis_client.set.side_effect = Exception("Redis error")
        
        session = UserSession(
            session_id="test-session-789",
            user_phone="+1234567890"
        )
        
        with pytest.raises(Exception) as exc_info:
            user_service.update_session(session)
        
        assert "Error al actualizar sesión" in str(exc_info.value)
    
    def test_delete_session_success(self, user_service, mock_redis_client):
        """Test eliminación exitosa de sesión"""
        mock_redis_client.delete.return_value = 1
        
        result = user_service.delete_session("test-session-123")
        
        assert result is True
        mock_redis_client.delete.assert_called_once_with("session:test-session-123")
    
    def test_delete_session_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al eliminar sesión"""
        mock_redis_client.delete.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            user_service.delete_session("test-session-123")
        
        assert "Error al eliminar sesión" in str(exc_info.value)
    
    def test_get_user_sessions_success(self, user_service, mock_redis_client):
        """Test obtención exitosa de sesiones de usuario"""
        session_keys = [b"session:test-1", b"session:test-2"]
        session_data_1 = {
            "session_id": "test-1",
            "user_phone": "+1234567890",
            "context": {},
            "created_at": "2024-01-01T00:00:00",
            "is_active": True
        }
        session_data_2 = {
            "session_id": "test-2",
            "user_phone": "+1234567890",
            "context": {},
            "created_at": "2024-01-01T00:00:00",
            "is_active": False
        }
        
        mock_redis_client.keys.return_value = session_keys
        mock_redis_client.get.side_effect = [
            json.dumps(session_data_1).encode(),
            json.dumps(session_data_2).encode()
        ]
        
        sessions = user_service.get_user_sessions("+1234567890")
        
        assert len(sessions) == 2
        assert sessions[0].session_id == "test-1"
        assert sessions[1].session_id == "test-2"
        mock_redis_client.keys.assert_called_once_with("session:*")
    
    def test_get_user_sessions_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al obtener sesiones"""
        mock_redis_client.keys.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            user_service.get_user_sessions("+1234567890")
        
        assert "Error al obtener sesiones del usuario" in str(exc_info.value)
    
    def test_cleanup_expired_sessions_success(self, user_service, mock_redis_client):
        """Test limpieza exitosa de sesiones expiradas"""
        mock_redis_client.keys.return_value = [b"session:expired-1", b"session:expired-2"]
        mock_redis_client.delete.return_value = 1
        
        result = user_service.cleanup_expired_sessions()
        
        assert result is True
        mock_redis_client.keys.assert_called_once_with("session:*")
        assert mock_redis_client.delete.call_count == 2
    
    def test_cleanup_expired_sessions_redis_error(self, user_service, mock_redis_client):
        """Test error en Redis al limpiar sesiones"""
        mock_redis_client.keys.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            user_service.cleanup_expired_sessions()
        
        assert "Error al limpiar sesiones expiradas" in str(exc_info.value) 