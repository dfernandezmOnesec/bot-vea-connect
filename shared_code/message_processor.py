"""
Procesador de mensajes para el bot de WhatsApp VEA Connect.

Este módulo se encarga de procesar diferentes tipos de mensajes
(texto, multimedia, documentos, etc.) y delegar el procesamiento
a los servicios apropiados.
"""

import logging
from typing import Dict, Any, Optional, List
from shared_code.interfaces import IMessageProcessor, IWhatsAppService, IUserService, IOpenAIService, IVisionService, IBlobStorageService, IErrorHandler
from shared_code.user_service import User, UserSession
from shared_code.utils import extract_media_info, sanitize_text


logger = logging.getLogger(__name__)


class MessageProcessor(IMessageProcessor):
    """
    Procesador de mensajes para el bot de WhatsApp.
    
    Se encarga de procesar diferentes tipos de mensajes y coordinar
    con los servicios apropiados para generar respuestas.
    """
    
    def __init__(
        self,
        whatsapp_service: IWhatsAppService,
        user_service: IUserService,
        openai_service: IOpenAIService,
        vision_service: Optional[IVisionService] = None,
        blob_storage_service: Optional[IBlobStorageService] = None,
        error_handler: Optional[IErrorHandler] = None
    ):
        """
        Inicializar el procesador de mensajes.
        
        Args:
            whatsapp_service: Servicio de WhatsApp
            user_service: Servicio de usuarios
            openai_service: Servicio de OpenAI
            vision_service: Servicio de visión (opcional)
            blob_storage_service: Servicio de blob storage (opcional)
            error_handler: Manejador de errores (opcional)
        """
        self.whatsapp_service = whatsapp_service
        self.user_service = user_service
        self.openai_service = openai_service
        self.vision_service = vision_service
        self.blob_storage_service = blob_storage_service
        self.error_handler = error_handler
    
    def process_text_message(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Procesar mensaje de texto.
        
        Args:
            message: Mensaje a procesar
            user: Usuario que envió el mensaje
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Extraer texto del mensaje
            text = message.get("text", {}).get("body", "").strip()
            if not text:
                return self._create_error_response("Mensaje de texto vacío", "EMPTY_MESSAGE")
            
            # Sanitizar texto
            sanitized_text = sanitize_text(text)
            
            # Buscar información relevante (si está disponible)
            relevant_info = self._search_relevant_info(sanitized_text)
            
            # Generar respuesta usando OpenAI
            response_text = self.openai_service.generate_response([
                {"role": "system", "content": self._get_system_context()},
                {"role": "user", "content": sanitized_text}
            ])
            
            # Actualizar contexto de la sesión
            self._update_session_context(session, sanitized_text, response_text)
            
            # Enviar respuesta
            send_result = self.whatsapp_service.send_text_message(
                response_text, 
                recipient_id=user.phone_number
            )
            
            # Extraer success del resultado (puede ser booleano o diccionario)
            success = send_result.get("success", True) if isinstance(send_result, dict) else bool(send_result)
            message_id = send_result.get("message_id") if isinstance(send_result, dict) else None
            
            return {
                "success": success,
                "response": response_text,
                "message_type": "text",
                "user_id": user.phone_number,
                "message_id": message_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de texto: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_text_message")
            else:
                return self._create_error_response("Error procesando mensaje", "PROCESSING_ERROR")
    
    def process_media_message(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Procesar mensaje multimedia.
        
        Args:
            message: Mensaje multimedia a procesar
            user: Usuario que envió el mensaje
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Extraer información del medio
            media_info = extract_media_info(message)
            if not media_info:
                return self._create_error_response("Información de medio no válida", "INVALID_MEDIA")
            
            media_type = media_info.get("type")
            
            # Procesar según el tipo de medio
            if media_type == "image":
                return self._process_image_message(message, media_info, user, session)
            elif media_type == "audio":
                return self._process_audio_message(message, media_info, user, session)
            elif media_type == "document":
                return self._process_document_message(message, media_info, user, session)
            else:
                return self._process_unsupported_media(message, user, session)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje multimedia: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_media_message")
            else:
                return self._create_error_response("Error procesando medio", "MEDIA_PROCESSING_ERROR")
    
    def process_unsupported_message(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Procesar mensaje no soportado.
        
        Args:
            message: Mensaje no soportado
            user: Usuario que envió el mensaje
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Enviar mensaje de tipo no soportado
            response_text = (
                "Lo siento, este tipo de mensaje no está soportado. "
                "Puedes enviarme texto, imágenes, audio o documentos."
            )
            
            send_result = self.whatsapp_service.send_text_message(
                response_text, 
                recipient_id=user.phone_number
            )
            
            # Extraer success del resultado (puede ser booleano o diccionario)
            success = send_result.get("success", True) if isinstance(send_result, dict) else bool(send_result)
            
            return {
                "success": success,
                "response": response_text,
                "message_type": "unsupported",
                "user_id": user.phone_number
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje no soportado: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_unsupported_message")
            else:
                return self._create_error_response("Error procesando mensaje", "PROCESSING_ERROR")
    
    def _process_image_message(
        self, 
        message: Dict[str, Any], 
        media_info: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """Procesar mensaje de imagen."""
        try:
            image_url = media_info.get("url")
            if not image_url:
                return self._create_error_response("URL de imagen no válida", "INVALID_IMAGE_URL")
            
            # Analizar imagen si el servicio de visión está disponible
            if self.vision_service:
                image_analysis = self.vision_service.analyze_image(image_url)
                response_text = self._generate_image_response(image_analysis, user)
            else:
                response_text = (
                    "Gracias por compartir esta imagen. "
                    "Actualmente no puedo analizar imágenes, pero puedo ayudarte con texto."
                )
            
            # Enviar respuesta
            send_result = self.whatsapp_service.send_text_message(
                response_text, 
                recipient_id=user.phone_number
            )
            
            # Extraer success del resultado (puede ser booleano o diccionario)
            success = send_result.get("success", True) if isinstance(send_result, dict) else bool(send_result)
            
            return {
                "success": success,
                "response": response_text,
                "message_type": "image",
                "user_id": user.phone_number,
                "media_analyzed": self.vision_service is not None
            }
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_image_message")
            else:
                return self._create_error_response("Error procesando imagen", "IMAGE_PROCESSING_ERROR")
    
    def _process_audio_message(
        self, 
        message: Dict[str, Any], 
        media_info: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """Procesar mensaje de audio."""
        try:
            response_text = (
                "Gracias por el mensaje de audio. "
                "Actualmente no puedo procesar audio, pero puedes enviarme un mensaje de texto."
            )
            
            send_result = self.whatsapp_service.send_text_message(
                response_text, 
                recipient_id=user.phone_number
            )
            
            # Extraer success del resultado (puede ser booleano o diccionario)
            success = send_result.get("success", True) if isinstance(send_result, dict) else bool(send_result)
            
            return {
                "success": success,
                "response": response_text,
                "message_type": "audio",
                "user_id": user.phone_number
            }
            
        except Exception as e:
            logger.error(f"Error procesando audio: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_audio_message")
            else:
                return self._create_error_response("Error procesando audio", "AUDIO_PROCESSING_ERROR")
    
    def _process_document_message(
        self, 
        message: Dict[str, Any], 
        media_info: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """Procesar mensaje de documento."""
        try:
            response_text = (
                "Gracias por compartir este documento. "
                "Actualmente no puedo procesar documentos, pero puedes enviarme un mensaje de texto."
            )
            
            send_result = self.whatsapp_service.send_text_message(
                response_text, 
                recipient_id=user.phone_number
            )
            
            # Extraer success del resultado (puede ser booleano o diccionario)
            success = send_result.get("success", True) if isinstance(send_result, dict) else bool(send_result)
            
            return {
                "success": success,
                "response": response_text,
                "message_type": "document",
                "user_id": user.phone_number
            }
            
        except Exception as e:
            logger.error(f"Error procesando documento: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_document_message")
            else:
                return self._create_error_response("Error procesando documento", "DOCUMENT_PROCESSING_ERROR")
    
    def _process_unsupported_media(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """Procesar medio no soportado."""
        try:
            response_text = (
                "Este tipo de medio no está soportado. "
                "Puedes enviarme texto, imágenes, audio o documentos."
            )
            
            send_result = self.whatsapp_service.send_text_message(
                response_text, 
                recipient_id=user.phone_number
            )
            
            # Extraer success del resultado (puede ser booleano o diccionario)
            success = send_result.get("success", True) if isinstance(send_result, dict) else bool(send_result)
            
            return {
                "success": success,
                "response": response_text,
                "message_type": "unsupported_media",
                "user_id": user.phone_number
            }
            
        except Exception as e:
            logger.error(f"Error procesando medio no soportado: {e}")
            if self.error_handler:
                return self.error_handler.handle_error(e, "process_unsupported_media")
            else:
                return self._create_error_response("Error procesando medio", "MEDIA_PROCESSING_ERROR")
    
    def _search_relevant_info(self, query: str) -> List[Dict[str, Any]]:
        """
        Buscar información relevante para la consulta.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            List[Dict[str, Any]]: Información relevante encontrada
        """
        # TODO: Implementar búsqueda en base de conocimientos
        # Por ahora retornar lista vacía
        return []
    
    def _generate_image_response(self, image_analysis: Dict[str, Any], user: User) -> str:
        """
        Generar respuesta para análisis de imagen.
        
        Args:
            image_analysis: Análisis de la imagen
            user: Usuario que envió la imagen
            
        Returns:
            str: Respuesta generada
        """
        try:
            # Extraer información del análisis
            description = image_analysis.get("description", "")
            tags = image_analysis.get("tags", [])
            
            if description:
                response = f"Veo en la imagen: {description}. "
                if tags:
                    response += f"Elementos identificados: {', '.join(tags[:5])}. "
                response += "¿En qué puedo ayudarte con respecto a esta imagen?"
            else:
                response = "He analizado la imagen que compartiste. ¿En qué puedo ayudarte?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando respuesta de imagen: {e}")
            return "He analizado la imagen que compartiste. ¿En qué puedo ayudarte?"
    
    def _update_session_context(
        self, 
        session: UserSession, 
        user_message: str, 
        bot_response: str
    ) -> None:
        """
        Actualizar contexto de la sesión.
        
        Args:
            session: Sesión del usuario
            user_message: Mensaje del usuario
            bot_response: Respuesta del bot
        """
        try:
            if not session.context:
                session.context = {}
            
            # Agregar mensajes al contexto
            if "conversation" not in session.context:
                session.context["conversation"] = []
            
            session.context["conversation"].append({
                "user": user_message,
                "bot": bot_response,
                "timestamp": session.created_at.isoformat() if session.created_at else None
            })
            
            # Mantener solo los últimos 10 mensajes
            if len(session.context["conversation"]) > 10:
                session.context["conversation"] = session.context["conversation"][-10:]
            
            # Actualizar sesión
            self.user_service.update_session(session)
            
        except Exception as e:
            logger.error(f"Error actualizando contexto de sesión: {e}")
    
    def _get_system_context(self) -> str:
        """
        Obtener contexto del sistema para OpenAI.
        
        Returns:
            str: Contexto del sistema
        """
        return """
        Eres un asistente virtual pastoral para la comunidad cristiana VEA Connect. 
        Tu propósito es servir con amor, compasión y sabiduría bíblica.
        
        RESPONSABILIDADES:
        - Responder preguntas sobre ministerios y actividades de la iglesia
        - Proporcionar información sobre eventos y horarios de servicios
        - Ayudar con donaciones y ofrendas
        - Ofrecer apoyo espiritual y oración
        - Compartir recursos bíblicos y devocionales
        
        TONO Y ESTILO:
        - Amoroso y acogedor como un pastor
        - Respetuoso y compasivo
        - Basado en principios bíblicos
        - Alentador y edificante
        - Profesional pero cálido
        
        RESPUESTAS:
        - Siempre en español
        - Incluir versículos bíblicos cuando sea apropiado
        - Ofrecer oración cuando sea solicitado
        - Conectar con líderes específicos cuando sea necesario
        - Ser específico sobre eventos y horarios
        - Mostrar el amor de Cristo en cada interacción
        """
    
    def _create_error_response(self, message: str, error_code: str) -> Dict[str, Any]:
        """
        Crear respuesta de error.
        
        Args:
            message: Mensaje de error
            error_code: Código de error
            
        Returns:
            Dict[str, Any]: Respuesta de error
        """
        if self.error_handler:
            return self.error_handler.create_error_response(message, error_code)
        else:
            return {
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message
                }
            } 