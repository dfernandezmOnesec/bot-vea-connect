"""
User service module for managing WhatsApp users in Redis.

This module provides functions for user registration, verification,
and management with production-grade features and enhanced error handling.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from redis.exceptions import RedisError, ConnectionError
from shared_code.redis_service import redis_service
from config.settings import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class User(BaseModel):
    phone_number: str
    name: str
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir modelo a diccionario."""
        return {
            "phone_number": self.phone_number,
            "name": self.name,
            "email": self.email,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Crear modelo desde diccionario."""
        # Convertir strings de fecha a datetime
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]
        
        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                updated_at = data["updated_at"]
        
        return cls(
            phone_number=data["phone_number"],
            name=data["name"],
            email=data.get("email"),
            preferences=data.get("preferences"),
            created_at=created_at,
            updated_at=updated_at
        )

class UserSession(BaseModel):
    session_id: str
    user_phone: str
    context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir modelo a diccionario."""
        return {
            "session_id": self.session_id,
            "user_phone": self.user_phone,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Crear modelo desde diccionario."""
        # Convertir string de fecha a datetime
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]
        
        return cls(
            session_id=data["session_id"],
            user_phone=data["user_phone"],
            context=data.get("context"),
            created_at=created_at,
            is_active=data.get("is_active", True)
        )

class UserService:
    """
    Service for managing WhatsApp users using Redis as backend with production-grade features.
    """
    
    USER_KEY_PATTERN = "user:{}"
    USER_SESSION_PATTERN = "session:{}"
    USER_STATS_PATTERN = "stats:{}"
    DEFAULT_EXPIRATION_DAYS = 365  # 1 year

    def register_user(
        self, 
        user_id: str, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None,
        expiration_days: int = DEFAULT_EXPIRATION_DAYS
    ) -> bool:
        """
        Register a new user in Redis if they don't exist.
        
        Args:
            user_id: Unique user ID (e.g., WhatsApp number)
            name: User's name
            metadata: Optional additional metadata (phone, created_at, etc.)
            expiration_days: Number of days before user data expires
            
        Returns:
            bool: True if user was created, False if already existed
            
        Raises:
            ValueError: If input parameters are invalid
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input parameters
            if not user_id or not name:
                raise ValueError("User ID and name cannot be empty")
            
            key = self.USER_KEY_PATTERN.format(user_id)
            
            # Check if user already exists
            if redis_service.redis_client.exists(key):
                logger.info(f"User already registered: {user_id}")
                return False
            
            # Prepare user data
            user_data = {
                "user_id": user_id,
                "name": name,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            # Add metadata if provided
            if metadata:
                user_data.update(metadata)
            
            # Store user data
            redis_service.redis_client.set(
                key, 
                json.dumps(user_data, ensure_ascii=False),
                ex=expiration_days * 24 * 60 * 60
            )
            
            # Initialize user statistics
            self._initialize_user_stats(user_id)
            
            logger.info(f"User registered successfully: {user_id} ({name})")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid input for user registration: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error registering user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error registering user {user_id}: {e}")
            raise

    def is_registered(self, user_id: str) -> bool:
        """
        Check if a user is registered in Redis.
        
        Args:
            user_id: Unique user ID
            
        Returns:
            bool: True if user exists, False otherwise
            
        Raises:
            ValueError: If user_id is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            key = self.USER_KEY_PATTERN.format(user_id)
            exists = redis_service.redis_client.exists(key)
            
            logger.debug(f"User registration check for {user_id}: {'exists' if exists else 'not found'}")
            return bool(exists)
            
        except ValueError as e:
            logger.error(f"Invalid input for user verification: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error checking user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error verifying user {user_id}: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from Redis.
        
        Args:
            user_id: Unique user ID
            
        Returns:
            Optional[Dict[str, Any]]: User data dictionary or None if not found
            
        Raises:
            ValueError: If user_id is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            key = self.USER_KEY_PATTERN.format(user_id)
            user_json = redis_service.redis_client.get(key)
            
            if user_json is None:
                logger.info(f"User not found: {user_id}")
                return None
            
            user_data = json.loads(user_json)
            logger.info(f"User data retrieved: {user_id}")
            return user_data
            
        except ValueError as e:
            logger.error(f"Invalid input for getting user: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error getting user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update user fields in Redis.
        
        Args:
            user_id: Unique user ID
            updates: Fields to update
            
        Returns:
            bool: True if update was successful, False if user doesn't exist
            
        Raises:
            ValueError: If input parameters are invalid
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            if not updates:
                raise ValueError("Updates dictionary cannot be empty")
            
            key = self.USER_KEY_PATTERN.format(user_id)
            user_json = redis_service.redis_client.get(key)
            
            if user_json is None:
                logger.info(f"Cannot update, user not found: {user_id}")
                return False
            
            # Update user data
            user_data = json.loads(user_json)
            user_data.update(updates)
            user_data["last_updated"] = datetime.utcnow().isoformat()
            
            # Store updated data
            redis_service.redis_client.set(key, json.dumps(user_data, ensure_ascii=False))
            
            logger.info(f"User updated successfully: {user_id}")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid input for user update: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error updating user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    def update_last_activity(self, user_id: str) -> bool:
        """
        Update user's last activity timestamp.
        
        Args:
            user_id: Unique user ID
            
        Returns:
            bool: True if update was successful, False if user doesn't exist
            
        Raises:
            ValueError: If user_id is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            updates = {
                "last_activity": datetime.utcnow().isoformat()
            }
            
            success = self.update_user(user_id, updates)
            
            if success:
                # Update activity statistics
                self._increment_user_stat(user_id, "message_count")
                logger.debug(f"Last activity updated for user: {user_id}")
            
            return success
            
        except ValueError as e:
            logger.error(f"Invalid input for activity update: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error updating activity for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating activity for user {user_id}: {e}")
            raise

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from Redis.
        
        Args:
            user_id: Unique user ID
            
        Returns:
            bool: True if deletion was successful, False if user doesn't exist
            
        Raises:
            ValueError: If user_id is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            key = self.USER_KEY_PATTERN.format(user_id)
            result = redis_service.redis_client.delete(key)
            
            if result > 0:
                # Clean up related data
                self._cleanup_user_data(user_id)
                logger.info(f"User deleted successfully: {user_id}")
                return True
            else:
                logger.info(f"User not found for deletion: {user_id}")
                return False
                
        except ValueError as e:
            logger.error(f"Invalid input for user deletion: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error deleting user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise

    def list_users(self, pattern: str = "user:*", limit: int = 100) -> List[str]:
        """
        List user IDs matching a pattern.
        
        Args:
            pattern: Redis key pattern to match
            limit: Maximum number of users to return
            
        Returns:
            List[str]: List of user IDs
            
        Raises:
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            users = []
            cursor = 0
            
            while True:
                cursor, keys = redis_service.redis_client.scan(cursor, match=pattern, count=50)
                users.extend([key.decode('utf-8').replace('user:', '') for key in keys])
                
                if cursor == 0 or len(users) >= limit:
                    break
            
            # Limit results
            users = users[:limit]
            
            logger.info(f"Listed {len(users)} users matching pattern: {pattern}")
            return users
            
        except RedisError as e:
            logger.error(f"Redis error listing users: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            raise

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user statistics.
        
        Args:
            user_id: Unique user ID
            
        Returns:
            Optional[Dict[str, Any]]: User statistics or None if not found
            
        Raises:
            ValueError: If user_id is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            key = self.USER_STATS_PATTERN.format(user_id)
            stats_json = redis_service.redis_client.get(key)
            
            if stats_json is None:
                logger.info(f"User stats not found: {user_id}")
                return None
            
            stats = json.loads(stats_json)
            logger.debug(f"User stats retrieved: {user_id}")
            return stats
            
        except ValueError as e:
            logger.error(f"Invalid input for getting user stats: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error getting user stats {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user stats {user_id}: {e}")
            raise

    def _initialize_user_stats(self, user_id: str) -> None:
        """
        Initialize user statistics.
        
        Args:
            user_id: Unique user ID
        """
        try:
            key = self.USER_STATS_PATTERN.format(user_id)
            stats = {
                "message_count": 0,
                "first_message": datetime.utcnow().isoformat(),
                "last_message": datetime.utcnow().isoformat(),
                "session_count": 0
            }
            
            redis_service.redis_client.set(key, json.dumps(stats))
            logger.debug(f"User stats initialized: {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize user stats for {user_id}: {e}")

    def _increment_user_stat(self, user_id: str, stat_name: str, increment: int = 1) -> None:
        """
        Increment a user statistic.
        
        Args:
            user_id: Unique user ID
            stat_name: Name of the statistic to increment
            increment: Amount to increment (default: 1)
        """
        try:
            key = self.USER_STATS_PATTERN.format(user_id)
            stats = self.get_user_stats(user_id)
            
            if stats:
                stats[stat_name] = stats.get(stat_name, 0) + increment
                redis_service.redis_client.set(key, json.dumps(stats))
                logger.debug(f"User stat incremented: {user_id} {stat_name} = {stats[stat_name]}")
                
        except Exception as e:
            logger.warning(f"Failed to increment user stat for {user_id}: {e}")

    def _cleanup_user_data(self, user_id: str) -> None:
        """
        Clean up user-related data.
        
        Args:
            user_id: Unique user ID
        """
        try:
            # Delete user stats
            stats_key = self.USER_STATS_PATTERN.format(user_id)
            redis_service.redis_client.delete(stats_key)
            
            # Delete user session
            session_key = self.USER_SESSION_PATTERN.format(user_id)
            redis_service.redis_client.delete(session_key)
            
            logger.debug(f"User data cleaned up: {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup user data for {user_id}: {e}")

    def health_check(self) -> bool:
        """
        Perform a health check on the user service.
        
        Returns:
            bool: True if service is healthy
            
        Raises:
            RedisError: If health check fails
        """
        try:
            # Test basic Redis operations
            test_user_id = "health_check_test"
            test_data = {"test": "value"}
            
            # Test set and get
            key = self.USER_KEY_PATTERN.format(test_user_id)
            redis_service.redis_client.set(key, json.dumps(test_data), ex=10)
            result = redis_service.redis_client.get(key)
            
            if not result:
                raise RedisError("User service health check failed - basic operations not working")
            
            # Clean up
            redis_service.redis_client.delete(key)
            
            logger.debug("User service health check passed")
            return True
            
        except RedisError as e:
            logger.error(f"User service health check failed: {e}")
            raise

    def create_user(self, user: User) -> bool:
        """
        Create a new user from a User model.
        
        Args:
            user: User model instance
            
        Returns:
            bool: True if user was created successfully
            
        Raises:
            ValueError: If user data is invalid
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate user data
            if not user.phone_number or not user.name:
                raise ValueError("User phone number and name cannot be empty")
            
            # Convert user to dict and register
            user_data = user.to_dict()
            return self.register_user(
                user.phone_number,
                user.name,
                metadata=user_data,
                expiration_days=self.DEFAULT_EXPIRATION_DAYS
            )
            
        except Exception as e:
            logger.error(f"Error creating user {user.phone_number}: {e}")
            raise

    def get_user_sessions(self, phone_number: str) -> List[UserSession]:
        """
        Get all active sessions for a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            List[UserSession]: List of active user sessions
            
        Raises:
            ValueError: If phone_number is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not phone_number:
                raise ValueError("Phone number cannot be empty")
            
            sessions = []
            pattern = f"session:*{phone_number}*"
            cursor = 0
            
            while True:
                cursor, keys = redis_service.redis_client.scan(cursor, match=pattern, count=50)
                
                for key in keys:
                    session_json = redis_service.redis_client.get(key)
                    if session_json:
                        try:
                            session_data = json.loads(session_json)
                            session = UserSession.from_dict(session_data)
                            if session.is_active:
                                sessions.append(session)
                        except Exception as e:
                            logger.warning(f"Failed to parse session data for key {key}: {e}")
                
                if cursor == 0:
                    break
            
            logger.info(f"Found {len(sessions)} active sessions for user {phone_number}")
            return sessions
            
        except ValueError as e:
            logger.error(f"Invalid input for getting user sessions: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error getting user sessions for {phone_number}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user sessions for {phone_number}: {e}")
            raise

    def create_session(self, phone_number: str) -> UserSession:
        """
        Create a new session for a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            UserSession: Newly created session
            
        Raises:
            ValueError: If phone_number is empty
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate input
            if not phone_number:
                raise ValueError("Phone number cannot be empty")
            
            # Create new session
            session_id = f"session_{phone_number}_{int(datetime.utcnow().timestamp())}"
            session = UserSession(
                session_id=session_id,
                user_phone=phone_number,
                context={"conversation_history": []},
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            # Store session in Redis
            key = self.USER_SESSION_PATTERN.format(session_id)
            redis_service.redis_client.set(
                key,
                json.dumps(session.to_dict()),
                ex=24 * 60 * 60  # 24 hours expiration
            )
            
            logger.info(f"Created new session {session_id} for user {phone_number}")
            return session
            
        except ValueError as e:
            logger.error(f"Invalid input for creating session: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error creating session for {phone_number}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating session for {phone_number}: {e}")
            raise

    def update_session(self, session: UserSession) -> bool:
        """
        Update an existing session.
        
        Args:
            session: UserSession model instance to update
            
        Returns:
            bool: True if session was updated successfully
            
        Raises:
            ValueError: If session data is invalid
            RedisError: If Redis operation fails
            Exception: For other unexpected errors
        """
        try:
            # Validate session data
            if not session.session_id or not session.user_phone:
                raise ValueError("Session ID and user phone cannot be empty")
            
            # Store updated session in Redis
            key = self.USER_SESSION_PATTERN.format(session.session_id)
            redis_service.redis_client.set(
                key,
                json.dumps(session.to_dict()),
                ex=24 * 60 * 60  # 24 hours expiration
            )
            
            logger.debug(f"Updated session {session.session_id} for user {session.user_phone}")
            return True
            
        except ValueError as e:
            logger.error(f"Invalid input for updating session: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error updating session {session.session_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating session {session.session_id}: {e}")
            raise

# Global instance for easy access
user_service = UserService() 