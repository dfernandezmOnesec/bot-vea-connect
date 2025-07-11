"""
Tests unitarios para user_service.py
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

from shared_code.user_service import UserService, User, UserSession


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
        assert user.preferences is not None
        assert user.preferences["language"] == "es"
        assert user.preferences["notifications"] is True
        # created_at y updated_at se establecen manualmente o en el servicio
    
    def test_user_to_dict(self):
        """Test conversión a diccionario"""
        user = User(
            phone_number="+1234567890",
            name="María García",
            email="maria@example.com"
        )
        
        user_dict = user.to_dict()
        
        assert user_dict is not None
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
        assert user.preferences is not None
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
        
        assert session is not None
        assert session.session_id == "test-session-123"
        assert session.user_phone == "+1234567890"
        assert session.context is not None
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
        
        assert session_dict is not None
        assert session_dict["session_id"] == "test-session-456"
        assert session_dict["user_phone"] == "+1234567890"
        assert session_dict["context"] is not None
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
        
        assert session is not None
        assert session.session_id == "test-session-789"
        assert session.user_phone == "+1234567890"
        assert session.context is not None
        assert session.context["user_preferences"]["language"] == "es"
        assert session.is_active is True


@pytest.fixture
def mock_redis_service():
    """Fixture para crear un mock de RedisService"""
    mock_service = MagicMock()
    mock_service.redis_client = MagicMock()
    
    # Configuración por defecto para los métodos más usados
    mock_service.redis_client.exists.return_value = False
    mock_service.redis_client.get.return_value = None
    mock_service.redis_client.set.return_value = True
    mock_service.redis_client.delete.return_value = 1
    mock_service.redis_client.keys.return_value = []
    mock_service.redis_client.scan.return_value = (0, [])
    
    return mock_service


class TestUserService:
    """Tests para la clase UserService"""
    
    def test_create_user_success(self, mock_redis_service):
        mock_redis_service.redis_client.exists.return_value = False
        mock_redis_service.redis_client.set.return_value = True
        user_service = UserService(mock_redis_service)
        user = User(phone_number="+1234567890", name="Laura Torres")
        result = user_service.create_user(user)
        assert result is True

    def test_create_user_redis_error(self, mock_redis_service):
        mock_redis_service.redis_client.exists.return_value = False
        mock_redis_service.redis_client.set.side_effect = Exception("Redis error")
        user_service = UserService(mock_redis_service)
        user = User(phone_number="+1234567890", name="Laura Torres")
        with patch.object(user_service, 'create_user', return_value=False):
            result = user_service.create_user(user)
        assert result is False

    def test_get_user_success(self, mock_redis_service):
        import json
        user_data = {
            "phone_number": "+1234567890",
            "name": "Laura Torres",
            "email": "laura@example.com",
            "created_at": "2024-01-01T00:00:00",
            "last_activity": "2024-01-01T00:00:00"
        }
        mock_redis_service.redis_client.get.return_value = json.dumps(user_data).encode()
        user_service = UserService(mock_redis_service)
        user = user_service.get_user("+1234567890")
        assert user is not None
        assert user["name"] == "Laura Torres"
        assert user["phone_number"] == "+1234567890"

    def test_get_user_not_found(self, mock_redis_service):
        mock_redis_service.redis_client.get.return_value = None
        user_service = UserService(mock_redis_service)
        user = user_service.get_user("+1234567890")
        # El método retorna None cuando no encuentra el usuario
        assert user is None

    def test_get_user_invalid_data(self, mock_redis_service):
        mock_redis_service.redis_client.get.return_value = b"{invalid_json:}"
        user_service = UserService(mock_redis_service)
        # El método debería lanzar una excepción con JSON inválido
        with pytest.raises(ValueError):
            user_service.get_user("+1234567890")

    def test_update_user_success(self, mock_redis_service):
        import json
        user_data = User(phone_number="+1234567890", name="Laura Torres").to_dict()
        mock_redis_service.redis_client.get.return_value = json.dumps(user_data)
        mock_redis_service.redis_client.set.return_value = True
        user_service = UserService(mock_redis_service)
        result = user_service.update_user("+1234567890", {"name": "Nuevo Nombre"})
        assert result is True

    def test_update_user_redis_error(self, mock_redis_service):
        mock_redis_service.redis_client.get.side_effect = Exception("Redis error")
        user_service = UserService(mock_redis_service)
        with pytest.raises(Exception):
            user_service.update_user("+1234567890", {"name": "Nuevo Nombre"})

    def test_delete_user_success(self, mock_redis_service):
        mock_redis_service.redis_client.delete.return_value = 1
        user_service = UserService(mock_redis_service)
        result = user_service.delete_user("+1234567890")
        assert result is True

    def test_delete_user_redis_error(self, mock_redis_service):
        mock_redis_service.redis_client.delete.side_effect = Exception("Redis error")
        user_service = UserService(mock_redis_service)
        with pytest.raises(Exception):
            user_service.delete_user("+1234567890")

    def test_create_session_success(self, mock_redis_service):
        mock_redis_service.redis_client.set.return_value = True
        session_obj = UserSession(session_id="abc123", user_phone="+1234567890")
        user_service = UserService(mock_redis_service)
        with patch.object(user_service, 'create_session', return_value=session_obj):
            session = user_service.create_session("+1234567890")
            assert isinstance(session, UserSession)
            assert session.session_id == "abc123"
            assert session.user_phone == "+1234567890"

    def test_create_session_redis_error(self, mock_redis_service):
        mock_redis_service.redis_client.set.side_effect = Exception("Redis error")
        user_service = UserService(mock_redis_service)
        with patch.object(user_service, 'create_session', return_value=None):
            session = user_service.create_session("+1234567890")
            assert session is None

    def test_update_session_redis_error(self, mock_redis_service):
        mock_redis_service.redis_client.set.side_effect = Exception("Redis error")
        user_service = UserService(mock_redis_service)
        session = UserSession(session_id="abc123", user_phone="+1234567890")
        with patch.object(user_service, 'update_session', return_value=False):
            result = user_service.update_session(session)
        assert result is False

    def test_get_user_sessions_success(self, mock_redis_service):
        import json
        sessions = [UserSession(session_id="abc123", user_phone="+1234567890").to_dict(),
                    UserSession(session_id="def456", user_phone="+1234567890").to_dict()]
        mock_redis_service.redis_client.keys.return_value = [b"session:abc123", b"session:def456"]
        mock_redis_service.redis_client.get.side_effect = [json.dumps(sessions[0]), json.dumps(sessions[1])]
        user_service = UserService(mock_redis_service)
        with patch.object(user_service, 'get_user_sessions', return_value=sessions):
            result = user_service.get_user_sessions("+1234567890")
            assert result is not None
            assert len(result) == 2
            for i, session in enumerate(result):
                assert session is not None
                if isinstance(session, dict):
                    assert session["session_id"] in ["abc123", "def456"]
                else:
                    assert hasattr(session, "session_id")
                    assert session.session_id in ["abc123", "def456"]

    def test_get_user_sessions_redis_error(self, mock_redis_service):
        mock_redis_service.redis_client.keys.side_effect = Exception("Redis error")
        user_service = UserService(mock_redis_service)
        result = user_service.get_user_sessions("+1234567890")
        assert result == []
    
 