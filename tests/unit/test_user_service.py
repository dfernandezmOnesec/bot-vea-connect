"""
Tests unitarios para user_service.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
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
    
    @pytest.fixture(autouse=True)
    def patch_redis_client(self):
        """Mock global de redis_service.redis_client para todos los tests"""
        with patch("shared_code.user_service.redis_service.redis_client") as mock_redis:
            yield mock_redis
    
    def test_create_user_success(self, patch_redis_client):
        """Test creación exitosa de usuario"""
        # Configurar mocks de Redis
        patch_redis_client.exists.return_value = False  # Usuario no existe
        patch_redis_client.set.return_value = True
        
        user = User(
            phone_number="+1234567890",
            name="Ana Martínez",
            email="ana@example.com"
        )
        
        # Mockear _initialize_user_stats para que no haga nada
        with patch.object(UserService, "_initialize_user_stats", return_value=None):
            service = UserService()
            result = service.create_user(user)
        
        assert result is True
        patch_redis_client.exists.assert_called_once_with("user:+1234567890")
        patch_redis_client.set.assert_called_once()
    
    def test_create_user_redis_error(self, patch_redis_client):
        """Test error en Redis al crear usuario"""
        patch_redis_client.exists.return_value = False  # Usuario no existe
        patch_redis_client.set.side_effect = Exception("Redis error")
        
        user = User(
            phone_number="+1234567890",
            name="Pedro Sánchez"
        )
        
        with pytest.raises(Exception) as exc_info:
            with patch.object(UserService, "_initialize_user_stats", return_value=None):
                service = UserService()
                service.create_user(user)
        
        assert "Redis error" in str(exc_info.value)
    
    def test_get_user_success(self, patch_redis_client):
        """Test obtención exitosa de usuario"""
        user_data = {
            "phone_number": "+1234567890",
            "name": "Laura Torres",
            "email": "laura@example.com",
            "preferences": {"language": "es"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        patch_redis_client.get.return_value = json.dumps(user_data).encode()
        
        service = UserService()
        user = service.get_user("+1234567890")
        
        assert user is not None
        assert user["phone_number"] == "+1234567890"
        assert user["name"] == "Laura Torres"
        assert user["email"] == "laura@example.com"
        patch_redis_client.get.assert_called_once_with("user:+1234567890")
    
    def test_get_user_not_found(self, patch_redis_client):
        """Test usuario no encontrado"""
        patch_redis_client.get.return_value = None
        
        service = UserService()
        user = service.get_user("+1234567890")
        
        assert user is None
        patch_redis_client.get.assert_called_once_with("user:+1234567890")
    
    def test_get_user_invalid_data(self, patch_redis_client):
        """Test datos inválidos en Redis"""
        patch_redis_client.get.return_value = b"invalid json"
        
        with pytest.raises(Exception):
            service = UserService()
            service.get_user("+1234567890")
    
    def test_update_user_success(self, patch_redis_client):
        """Test actualización exitosa de usuario"""
        patch_redis_client.get.return_value = json.dumps({
            "user_id": "+1234567890",
            "name": "Roberto Díaz",
            "email": "roberto@example.com"
        }).encode()
        patch_redis_client.set.return_value = True
        
        service = UserService()
        updates = {"name": "Roberto Díaz Actualizado", "email": "roberto.nuevo@example.com"}
        result = service.update_user("+1234567890", updates)
        
        assert result is True
        patch_redis_client.get.assert_called_once_with("user:+1234567890")
        patch_redis_client.set.assert_called_once()
    
    def test_update_user_redis_error(self, patch_redis_client):
        """Test error en Redis al actualizar usuario"""
        patch_redis_client.get.return_value = json.dumps({
            "user_id": "+1234567890",
            "name": "Carmen Ruiz"
        }).encode()
        patch_redis_client.set.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            service = UserService()
            updates = {"name": "Carmen Ruiz Actualizada"}
            service.update_user("+1234567890", updates)
        
        assert "Redis error" in str(exc_info.value)
    
    def test_delete_user_success(self, patch_redis_client):
        """Test eliminación exitosa de usuario"""
        patch_redis_client.delete.return_value = 1
        
        service = UserService()
        result = service.delete_user("+1234567890")
        
        assert result is True
        patch_redis_client.delete.assert_any_call("user:+1234567890")
    
    def test_delete_user_redis_error(self, patch_redis_client):
        """Test error en Redis al eliminar usuario"""
        patch_redis_client.delete.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            service = UserService()
            service.delete_user("+1234567890")
        
        assert "Redis error" in str(exc_info.value)
    
    def test_create_session_success(self, patch_redis_client):
        """Test creación exitosa de sesión"""
        patch_redis_client.set.return_value = True
        
        service = UserService()
        session = service.create_session("+1234567890")
        
        assert session is not None
        assert session.user_phone == "+1234567890"
        assert session.is_active is True
        assert session.session_id is not None
        patch_redis_client.set.assert_called_once()
    
    def test_create_session_redis_error(self, patch_redis_client):
        """Test error en Redis al crear sesión"""
        patch_redis_client.set.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            service = UserService()
            service.create_session("+1234567890")
        
        assert "Redis error" in str(exc_info.value)
    
    def test_update_session_success(self, patch_redis_client):
        """Test actualización exitosa de sesión"""
        patch_redis_client.set.return_value = True
        
        session = UserSession(
            session_id="test-session-456",
            user_phone="+1234567890",
            context={"conversation_history": ["Hola", "¿Cómo estás?"]}
        )
        
        service = UserService()
        result = service.update_session(session)
        
        assert result is True
        patch_redis_client.set.assert_called_once()
    
    def test_update_session_redis_error(self, patch_redis_client):
        """Test error en Redis al actualizar sesión"""
        patch_redis_client.set.side_effect = Exception("Redis error")
        
        session = UserSession(
            session_id="test-session-789",
            user_phone="+1234567890"
        )
        
        with pytest.raises(Exception) as exc_info:
            service = UserService()
            service.update_session(session)
        
        assert "Redis error" in str(exc_info.value)
    
    def test_get_user_sessions_success(self, patch_redis_client):
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
            "is_active": True
        }
        
        # Mock scan para que devuelva las claves en una sola iteración
        patch_redis_client.scan.return_value = (0, session_keys)
        patch_redis_client.get.side_effect = [
            json.dumps(session_data_1).encode(),
            json.dumps(session_data_2).encode()
        ]
        
        service = UserService()
        sessions = service.get_user_sessions("+1234567890")
        
        assert len(sessions) == 2
        assert sessions[0].session_id == "test-1"
        assert sessions[1].session_id == "test-2"
        patch_redis_client.scan.assert_called_once()
    
    def test_get_user_sessions_redis_error(self, patch_redis_client):
        """Test error en Redis al obtener sesiones"""
        patch_redis_client.scan.side_effect = Exception("Redis error")
        
        with pytest.raises(Exception) as exc_info:
            service = UserService()
            service.get_user_sessions("+1234567890")
        
        assert "Redis error" in str(exc_info.value)
    
 