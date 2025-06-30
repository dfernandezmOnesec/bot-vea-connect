import logging
import json
from typing import Optional, Dict, Any
from src.shared_code.redis_service import redis_service
from src.config.settings import settings

logger = logging.getLogger(__name__)

class UserService:
    """
    Servicio para gestión de usuarios que interactúan con WhatsAppBot usando Redis como backend.
    """
    USER_KEY_PATTERN = "user:{}"

    def register_user(self, user_id: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Registra un nuevo usuario en Redis si no existe.
        
        Args:
            user_id (str): ID único del usuario (por ejemplo, número de WhatsApp).
            name (str): Nombre del usuario.
            metadata (dict, opcional): Metadatos adicionales (teléfono, created_at, etc).
        
        Returns:
            bool: True si el usuario fue creado, False si ya existía.
        
        Raises:
            Exception: Si hay un error de conexión con Redis.
        """
        key = self.USER_KEY_PATTERN.format(user_id)
        try:
            if redis_service.exists(key):
                logger.info(f"Usuario ya registrado: {user_id}")
                return False
            user_data = {"user_id": user_id, "name": name}
            if metadata:
                user_data.update(metadata)
            redis_service.set(key, json.dumps(user_data))
            logger.info(f"Usuario registrado exitosamente: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error registrando usuario {user_id}: {e}")
            raise

    def is_registered(self, user_id: str) -> bool:
        """
        Verifica si un usuario ya está registrado en Redis.
        
        Args:
            user_id (str): ID único del usuario.
        
        Returns:
            bool: True si el usuario existe, False en caso contrario.
        
        Raises:
            Exception: Si hay un error de conexión con Redis.
        """
        key = self.USER_KEY_PATTERN.format(user_id)
        try:
            exists = redis_service.exists(key)
            logger.info(f"Verificación de usuario {user_id}: {'existe' if exists else 'no existe'}")
            return bool(exists)
        except Exception as e:
            logger.error(f"Error verificando usuario {user_id}: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un usuario desde Redis.
        
        Args:
            user_id (str): ID único del usuario.
        
        Returns:
            dict | None: Diccionario con los datos del usuario, o None si no existe.
        
        Raises:
            Exception: Si hay un error de conexión con Redis.
        """
        key = self.USER_KEY_PATTERN.format(user_id)
        try:
            user_json = redis_service.get(key)
            if user_json is None:
                logger.info(f"Usuario no encontrado: {user_id}")
                return None
            user_data = json.loads(user_json)
            logger.info(f"Datos de usuario recuperados: {user_id}")
            return user_data
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            raise

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualiza los campos de un usuario existente en Redis.
        
        Args:
            user_id (str): ID único del usuario.
            updates (dict): Campos a actualizar.
        
        Returns:
            bool: True si la actualización fue exitosa, False si el usuario no existe.
        
        Raises:
            Exception: Si hay un error de conexión con Redis.
        """
        key = self.USER_KEY_PATTERN.format(user_id)
        try:
            user_json = redis_service.get(key)
            if user_json is None:
                logger.info(f"No se puede actualizar, usuario no encontrado: {user_id}")
                return False
            user_data = json.loads(user_json)
            user_data.update(updates)
            redis_service.set(key, json.dumps(user_data))
            logger.info(f"Usuario actualizado exitosamente: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error actualizando usuario {user_id}: {e}")
            raise

user_service = UserService() 