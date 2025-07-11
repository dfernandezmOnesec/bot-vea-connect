"""
Interfaces para los servicios del bot de WhatsApp VEA Connect.

Este módulo define las interfaces abstractas que deben implementar
todos los servicios para garantizar consistencia y facilitar testing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import azure.functions as func


class IWhatsAppService(ABC):
    """Interfaz para el servicio de WhatsApp."""
    
    @abstractmethod
    def send_text_message(
        self, 
        message: str, 
        recipient_id: Optional[str] = None,
        preview_url: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Enviar mensaje de texto."""
        pass
    
    @abstractmethod
    def send_document_message(
        self, 
        document_url: str, 
        filename: str,
        caption: Optional[str] = None,
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enviar documento."""
        pass
    
    @abstractmethod
    def send_template_message(
        self, 
        template_name: str,
        template_variables: Optional[Dict[str, Any]] = None,
        recipient_id: Optional[str] = None,
        language_code: str = "es"
    ) -> Dict[str, Any]:
        """Enviar mensaje de plantilla."""
        pass
    
    @abstractmethod
    def send_interactive_message(
        self,
        body_text: str,
        buttons: List[Dict[str, str]],
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enviar mensaje interactivo."""
        pass
    
    @abstractmethod
    def send_quick_reply_message(
        self,
        body_text: str,
        quick_replies: List[Dict[str, str]],
        recipient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enviar mensaje de respuesta rápida."""
        pass
    
    @abstractmethod
    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Marcar mensaje como leído."""
        pass
    
    @abstractmethod
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Obtener estado del mensaje."""
        pass
    
    @abstractmethod
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verificar webhook de WhatsApp."""
        pass
    
    @abstractmethod
    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar evento del webhook."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verificar salud del servicio."""
        pass


class IUserService(ABC):
    """Interfaz para el servicio de usuarios."""
    
    @abstractmethod
    def register_user(
        self, 
        user_id: str, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None,
        expiration_days: int = 365
    ) -> bool:
        """Registrar nuevo usuario."""
        pass
    
    @abstractmethod
    def is_registered(self, user_id: str) -> bool:
        """Verificar si usuario está registrado."""
        pass
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener datos del usuario."""
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Actualizar datos del usuario."""
        pass
    
    @abstractmethod
    def update_last_activity(self, user_id: str) -> bool:
        """Actualizar última actividad del usuario."""
        pass
    
    @abstractmethod
    def create_user(self, user: 'User') -> bool:
        """Crear usuario desde modelo User."""
        pass
    
    @abstractmethod
    def get_user_sessions(self, phone_number: str) -> List['UserSession']:
        """Obtener sesiones del usuario."""
        pass
    
    @abstractmethod
    def create_session(self, phone_number: str) -> 'UserSession':
        """Crear nueva sesión para usuario."""
        pass
    
    @abstractmethod
    def update_session(self, session: 'UserSession') -> bool:
        """Actualizar sesión del usuario."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verificar salud del servicio."""
        pass


class IOpenAIService(ABC):
    """Interfaz para el servicio de OpenAI."""
    
    @abstractmethod
    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generar respuesta de chat usando OpenAI."""
        pass
    
    @abstractmethod
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generar respuesta usando OpenAI (alias para compatibilidad)."""
        pass
    
    @abstractmethod
    def generate_embeddings(self, text: str) -> List[float]:
        """Generar embeddings para texto."""
        pass
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generar embedding para texto (alias para compatibilidad)."""
        pass
    
    @abstractmethod
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generar embeddings para múltiples textos."""
        pass
    
    @abstractmethod
    def generate_whatsapp_response(
        self, 
        user_message: str, 
        context: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> str:
        """Generar respuesta específica para WhatsApp."""
        pass
    
    @abstractmethod
    def analyze_document_content(self, content: str, analysis_type: str = "summary") -> str:
        """Analizar contenido de documento."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verificar salud del servicio."""
        pass


class IVisionService(ABC):
    """Interfaz para el servicio de visión."""
    
    @abstractmethod
    def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """Analizar imagen."""
        pass
    
    @abstractmethod
    def extract_text_from_image(self, image_url: str) -> str:
        """Extraer texto de imagen."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verificar salud del servicio."""
        pass


class IBlobStorageService(ABC):
    """Interfaz para el servicio de almacenamiento de blobs."""
    
    @abstractmethod
    def upload_file(self, file_path: str, container_name: str, blob_name: str) -> str:
        """Subir archivo al blob storage."""
        pass
    
    @abstractmethod
    def download_file(self, container_name: str, blob_name: str, destination_path: str) -> bool:
        """Descargar archivo del blob storage."""
        pass
    
    @abstractmethod
    def delete_file(self, container_name: str, blob_name: str) -> bool:
        """Eliminar archivo del blob storage."""
        pass
    
    @abstractmethod
    def get_file_url(self, container_name: str, blob_name: str) -> str:
        """Obtener URL del archivo."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verificar salud del servicio."""
        pass


class IRedisService(ABC):
    """Interfaz para el servicio de Redis."""
    
    @abstractmethod
    def store_embedding(
        self, 
        document_id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any],
        index_name: str = "document_embeddings",
        expiration_days: int = 30
    ) -> bool:
        """Almacenar embedding de documento con metadatos."""
        pass
    
    @abstractmethod
    def create_search_index(self, index_name: str = "document_embeddings") -> bool:
        """Crear índice de búsqueda en Redis."""
        pass
    
    @abstractmethod
    def semantic_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        index_name: str = "document_embeddings",
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica de documentos."""
        pass
    
    @abstractmethod
    def search_similar_documents(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        index_name: str = "document_embeddings",
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Buscar documentos similares."""
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtener documento por ID."""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Eliminar documento."""
        pass
    
    @abstractmethod
    def list_documents(self, pattern: str = "doc:*", limit: int = 100) -> List[str]:
        """Listar documentos."""
        pass
    
    @abstractmethod
    def get_index_info(self, index_name: str = "document_embeddings") -> Dict[str, Any]:
        """Obtener información del índice."""
        pass
    
    @abstractmethod
    def get_document_count(self, index_name: str = "document_embeddings") -> int:
        """Obtener cantidad de documentos."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, expiration: Optional[int] = None) -> bool:
        """Establecer valor en Redis."""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Obtener valor de Redis."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Eliminar clave de Redis."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Verificar si clave existe."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Verificar salud del servicio."""
        pass


class IMessageProcessor(ABC):
    """Interfaz para el procesador de mensajes."""
    
    @abstractmethod
    def process_text_message(
        self, 
        message: Dict[str, Any], 
        user: 'User', 
        session: 'UserSession'
    ) -> Dict[str, Any]:
        """Procesar mensaje de texto."""
        pass
    
    @abstractmethod
    def process_media_message(
        self, 
        message: Dict[str, Any], 
        user: 'User', 
        session: 'UserSession'
    ) -> Dict[str, Any]:
        """Procesar mensaje multimedia."""
        pass
    
    @abstractmethod
    def process_unsupported_message(
        self, 
        message: Dict[str, Any], 
        user: 'User', 
        session: 'UserSession'
    ) -> Dict[str, Any]:
        """Procesar mensaje no soportado."""
        pass


class IResponseGenerator(ABC):
    """Interfaz para el generador de respuestas."""
    
    @abstractmethod
    def generate_response(
        self, 
        user_message: str, 
        user: 'User', 
        session: 'UserSession', 
        relevant_info: List[Dict[str, Any]]
    ) -> str:
        """Generar respuesta para el usuario."""
        pass
    
    @abstractmethod
    def generate_image_response(
        self, 
        image_analysis: Dict[str, Any], 
        user: 'User'
    ) -> str:
        """Generar respuesta para imagen."""
        pass
    
    @abstractmethod
    def get_fallback_response(self, user_message: str) -> str:
        """Obtener respuesta de fallback."""
        pass


class IErrorHandler(ABC):
    """Interfaz para el manejador de errores."""
    
    @abstractmethod
    def handle_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Manejar error y retornar respuesta apropiada."""
        pass
    
    @abstractmethod
    def create_error_response(
        self, 
        message: str, 
        error_code: str = "UNKNOWN_ERROR"
    ) -> Dict[str, Any]:
        """Crear respuesta de error estructurada."""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: str) -> None:
        """Registrar error en logs."""
        pass


# Importar modelos para evitar referencias circulares
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shared_code.user_service import User, UserSession 