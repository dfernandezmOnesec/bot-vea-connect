"""
Función Azure para el bot de WhatsApp de la comunidad cristiana VEA Connect.
Proporciona respuestas inteligentes sobre ministerios, donaciones, eventos y apoyo espiritual.
"""
import azure.functions as func
import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

# Importar módulos compartidos
from shared_code.whatsapp_service import WhatsAppService
from shared_code.openai_service import OpenAIService
from shared_code.redis_service import RedisService
from shared_code.vision_service import VisionService
from shared_code.user_service import UserService, User, UserSession
from shared_code.utils import (
    setup_logging,
    parse_whatsapp_message,
    extract_media_info,
    format_response,
    create_error_response,
    validate_phone_number,
    sanitize_text,
    generate_session_id,
    rate_limit_check
)
from config.settings import get_settings


# Configurar logging
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppBot:
    """
    Bot de WhatsApp para la comunidad cristiana VEA Connect.
    Proporciona asistencia inteligente sobre ministerios, eventos y apoyo espiritual.
    """
    
    def __init__(self):
        """Inicializar el bot con todos los servicios necesarios."""
        try:
            # Obtener configuración
            self.settings = get_settings()
            
            # Inicializar servicios
            self.whatsapp_service = WhatsAppService()
            self.openai_service = OpenAIService()  # Descomentado para integración
            self.redis_service = RedisService()
            # self.vision_service = VisionService()  # Comentado temporalmente para tests de integración
            self.user_service = UserService()
            
            # Contexto del sistema para OpenAI
            self.system_context = self._get_system_context()
            
            logger.info("WhatsAppBot inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar WhatsAppBot: {str(e)}")
            raise
    
    def _get_system_context(self) -> str:
        """
        Obtener el contexto del sistema para OpenAI.
        
        Returns:
            str: Contexto del sistema con información sobre la comunidad
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
        
        INFORMACIÓN DE LA IGLESIA:
        - Nombre: VEA Connect
        - Enfoque: Comunidad cristiana que conecta personas con Dios y entre sí
        - Ministerios: Jóvenes, niños, familias, música, misiones, grupos pequeños
        - Servicios: Domingos 9:00 AM y 11:00 AM, Miércoles 7:00 PM
        - Ubicación: [Dirección de la iglesia]
        
        RESPUESTAS:
        - Siempre en español
        - Incluir versículos bíblicos cuando sea apropiado
        - Ofrecer oración cuando sea solicitado
        - Conectar con líderes específicos cuando sea necesario
        - Ser específico sobre eventos y horarios
        - Mostrar el amor de Cristo en cada interacción
        
        LIMITACIONES:
        - No dar consejos médicos o legales
        - No hacer diagnósticos
        - Derivar casos complejos a líderes de la iglesia
        - Mantener confidencialidad de la información personal
        """
    
    def process_message(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Procesar mensaje entrante de WhatsApp.
        
        Args:
            req: Request HTTP de Azure Functions
            
        Returns:
            func.HttpResponse: Respuesta HTTP
        """
        try:
            logger.info("Procesando mensaje entrante de WhatsApp")
            
            # Manejar verificación del webhook (GET)
            if req.method == "GET":
                return self._handle_webhook_verification(req)
            
            # Manejar mensajes (POST)
            if req.method == "POST":
                # Obtener datos del request
                body = req.get_json()
                if not body:
                    return func.HttpResponse(
                        "Cuerpo de request inválido",
                        status_code=400
                    )
                
                # Parsear mensaje
                parsed_message = parse_whatsapp_message(body)
                if not parsed_message:
                    logger.warning("No se pudo parsear el mensaje")
                    return func.HttpResponse(
                        "Mensaje no válido",
                        status_code=400
                    )
                
                # Procesar mensaje
                response = self._handle_message(parsed_message)
                
                return func.HttpResponse(
                    json.dumps(response),
                    mimetype="application/json",
                    status_code=200
                )
            
            # Método no soportado
            return func.HttpResponse(
                "Método no permitido",
                status_code=405
            )
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            logger.error(traceback.format_exc())
            
            error_response = create_error_response(
                "Error interno del servidor",
                error_code="INTERNAL_ERROR"
            )
            
            return func.HttpResponse(
                json.dumps(error_response),
                mimetype="application/json",
                status_code=500
            )
    
    def _handle_webhook_verification(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Manejar verificación del webhook de WhatsApp.
        
        Args:
            req: Request HTTP
            
        Returns:
            func.HttpResponse: Respuesta de verificación
        """
        try:
            # Obtener parámetros de verificación
            mode = req.params.get("hub.mode")
            token = req.params.get("hub.verify_token")
            challenge = req.params.get("hub.challenge")
            
            # Verificar token
            if mode == "subscribe" and token == self.settings.whatsapp_verify_token:
                logger.info("Webhook verificado correctamente")
                return func.HttpResponse(
                    challenge,
                    status_code=200
                )
            else:
                logger.warning("Token de verificación inválido")
                return func.HttpResponse(
                    "Forbidden",
                    status_code=403
                )
                
        except Exception as e:
            logger.error(f"Error en verificación de webhook: {str(e)}")
            return func.HttpResponse(
                "Error interno",
                status_code=500
            )
    
    def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manejar mensaje parseado de WhatsApp.
        
        Args:
            message: Mensaje parseado
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            # Extraer información del mensaje
            message_type = message.get("type")
            from_number = message.get("from")
            timestamp = message.get("timestamp")
            
            logger.info(f"Procesando mensaje tipo '{message_type}' de {from_number}")
            
            # Validar que from_number no sea None
            if not from_number:
                logger.warning("Número de teléfono no encontrado en el mensaje")
                return create_error_response("Número de teléfono no encontrado")
            
            # Validar número de teléfono
            if not validate_phone_number(from_number):
                logger.warning(f"Número de teléfono inválido: {from_number}")
                return create_error_response("Número de teléfono inválido")
            
            # Verificar rate limiting
            if not rate_limit_check(
                self.redis_service.redis_client,
                from_number,
                max_requests=10,
                window_seconds=60
            ):
                logger.warning(f"Rate limit excedido para {from_number}")
                return self._send_rate_limit_message(from_number)
            
            # Obtener o crear usuario
            user = self._get_or_create_user(from_number)
            
            # Obtener o crear sesión
            session = self._get_or_create_session(from_number)
            
            # Procesar según el tipo de mensaje
            if message_type == "text":
                return self._handle_text_message(message, user, session)
            elif message_type in ["image", "audio", "document"]:
                return self._handle_media_message(message, user, session)
            else:
                return self._handle_unsupported_message(message, user, session)
                
        except Exception as e:
            logger.error(f"Error manejando mensaje: {str(e)}")
            return create_error_response("Error procesando mensaje")
    
    def _get_or_create_user(self, phone_number: str) -> User:
        """
        Obtener usuario existente o crear uno nuevo.
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            User: Usuario encontrado o creado
        """
        try:
            # Buscar usuario existente
            user_data = self.user_service.get_user(phone_number)
            
            if user_data:
                # Convertir diccionario a objeto User
                user = User(
                    phone_number=user_data.get("user_id", phone_number),
                    name=user_data.get("name", "Usuario"),
                    preferences={"language": "es", "notifications": True}
                )
                logger.info(f"Usuario encontrado: {user.name}")
                return user
            
            # Crear nuevo usuario
            new_user = User(
                phone_number=phone_number,
                name="Usuario de WhatsApp",
                preferences={"language": "es", "notifications": True}
            )
            
            self.user_service.create_user(new_user)
            logger.info(f"Nuevo usuario creado: {phone_number}")
            
            return new_user
            
        except Exception as e:
            logger.error(f"Error obteniendo/creando usuario: {str(e)}")
            # Crear usuario temporal
            return User(
                phone_number=phone_number,
                name="Usuario Temporal",
                preferences={"language": "es"}
            )
    
    def _get_or_create_session(self, phone_number: str) -> UserSession:
        """
        Obtener sesión existente o crear una nueva.
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            UserSession: Sesión encontrada o creada
        """
        try:
            # Buscar sesión activa
            user_sessions = self.user_service.get_user_sessions(phone_number)
            
            # user_sessions ya es una lista de objetos UserSession
            active_session = next(
                (s for s in user_sessions if s.is_active),
                None
            )
            
            if active_session:
                logger.info(f"Sesión activa encontrada: {active_session.session_id}")
                return active_session
            
            # Crear nueva sesión - create_session devuelve un objeto UserSession
            new_session = self.user_service.create_session(phone_number)
            logger.info(f"Nueva sesión creada: {new_session.session_id}")
            
            return new_session
            
        except Exception as e:
            logger.error(f"Error obteniendo/creando sesión: {str(e)}")
            # Crear sesión temporal
            return UserSession(
                session_id=generate_session_id(),
                user_phone=phone_number,
                context={}
            )
    
    def _handle_text_message(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Manejar mensaje de texto.
        
        Args:
            message: Mensaje parseado
            user: Usuario
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            text_content = message.get("content", "").strip()
            
            if not text_content:
                return self._send_welcome_message(message["from"])
            
            # Sanitizar texto
            sanitized_text = sanitize_text(text_content)
            
            # Actualizar contexto de sesión
            if session.context is None:
                session.context = {}
            session.context["last_message"] = sanitized_text
            session.context["last_message_time"] = datetime.now().isoformat()
            
            # Buscar información relevante en Redis
            relevant_info = self._search_relevant_info(sanitized_text)
            
            # Generar respuesta con OpenAI
            response_text = self._generate_response(
                sanitized_text, 
                user, 
                session, 
                relevant_info
            )
            
            # Enviar respuesta por WhatsApp
            self._send_whatsapp_message(message["from"], response_text)
            
            # Actualizar sesión
            self._update_session_context(session, sanitized_text, response_text)
            
            return format_response(
                "Mensaje procesado correctamente",
                success=True,
                data={"response_sent": True}
            )
            
        except Exception as e:
            logger.error(f"Error manejando mensaje de texto: {str(e)}")
            return self._send_error_message(message["from"])
    
    def _handle_media_message(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Manejar mensaje con medios (imagen, audio, documento).
        
        Args:
            message: Mensaje parseado
            user: Usuario
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            message_type = message.get("type")
            media_info = extract_media_info(message)
            
            if not media_info:
                return self._send_unsupported_media_message(message["from"])
            
            # Procesar según el tipo de medio
            if message_type == "image":
                return self._handle_image_message(message, media_info, user, session)
            elif message_type == "audio":
                return self._handle_audio_message(message, media_info, user, session)
            elif message_type == "document":
                return self._handle_document_message(message, media_info, user, session)
            else:
                return self._send_unsupported_media_message(message["from"])
                
        except Exception as e:
            logger.error(f"Error manejando mensaje de medios: {str(e)}")
            return self._send_error_message(message["from"])
    
    def _handle_image_message(
        self, 
        message: Dict[str, Any], 
        media_info: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Manejar mensaje de imagen.
        
        Args:
            message: Mensaje parseado
            media_info: Información del medio
            user: Usuario
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            # Por ahora, responder con mensaje de imagen recibida
            # TODO: Implementar descarga y análisis de imagen cuando esté disponible
            response_text = (
                "Gracias por compartir esta imagen. Veo que has enviado una foto. "
                "Por el momento, te recomiendo enviar tu pregunta por texto para que "
                "pueda ayudarte mejor. ¿En qué puedo servirte?"
            )
            
            # Enviar respuesta
            self._send_whatsapp_message(message["from"], response_text)
            
            return format_response(
                "Imagen recibida, respuesta enviada",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            return self._send_error_message(message["from"])
    
    def _handle_audio_message(
        self, 
        message: Dict[str, Any], 
        media_info: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Manejar mensaje de audio.
        
        Args:
            message: Mensaje parseado
            media_info: Información del medio
            user: Usuario
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            # Por ahora, responder con mensaje de audio no soportado
            response_text = (
                "Gracias por tu mensaje de voz. Por el momento, "
                "te recomiendo enviar tu mensaje por texto para que "
                "pueda ayudarte mejor. ¿En qué puedo servirte?"
            )
            
            self._send_whatsapp_message(message["from"], response_text)
            
            return format_response(
                "Audio recibido, respuesta enviada",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error manejando audio: {str(e)}")
            return self._send_error_message(message["from"])
    
    def _handle_document_message(
        self, 
        message: Dict[str, Any], 
        media_info: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Manejar mensaje de documento.
        
        Args:
            message: Mensaje parseado
            media_info: Información del medio
            user: Usuario
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            filename = media_info.get("filename", "documento")
            
            response_text = (
                f"Gracias por compartir el documento '{filename}'. "
                "Para procesar documentos, por favor contacta directamente "
                "con nuestros líderes de ministerio. ¿Hay algo más en lo que pueda ayudarte?"
            )
            
            self._send_whatsapp_message(message["from"], response_text)
            
            return format_response(
                "Documento recibido, respuesta enviada",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error manejando documento: {str(e)}")
            return self._send_error_message(message["from"])
    
    def _handle_unsupported_message(
        self, 
        message: Dict[str, Any], 
        user: User, 
        session: UserSession
    ) -> Dict[str, Any]:
        """
        Manejar mensaje no soportado.
        
        Args:
            message: Mensaje parseado
            user: Usuario
            session: Sesión del usuario
            
        Returns:
            Dict[str, Any]: Respuesta del bot
        """
        try:
            response_text = (
                "Gracias por tu mensaje. Por favor, envía texto, "
                "imágenes o documentos para que pueda ayudarte mejor. "
                "¿En qué puedo servirte?"
            )
            
            self._send_whatsapp_message(message["from"], response_text)
            
            return format_response(
                "Mensaje no soportado, respuesta enviada",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error manejando mensaje no soportado: {str(e)}")
            return self._send_error_message(message["from"])
    
    def _search_relevant_info(self, query: str) -> List[Dict[str, Any]]:
        """
        Buscar información relevante en Redis usando embeddings.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            List[Dict[str, Any]]: Información relevante encontrada
        """
        try:
            # Generar embedding de la consulta
            query_embedding = self.openai_service.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Buscar información similar en Redis
            relevant_docs = self.redis_service.search_similar_documents(
                query_embedding,
                top_k=3
            )
            
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error buscando información relevante: {str(e)}")
            return []
    
    def _generate_response(
        self, 
        user_message: str, 
        user: User, 
        session: UserSession, 
        relevant_info: List[Dict[str, Any]]
    ) -> str:
        """
        Generar respuesta usando OpenAI.
        
        Args:
            user_message: Mensaje del usuario
            user: Usuario
            session: Sesión del usuario
            relevant_info: Información relevante encontrada
            
        Returns:
            str: Respuesta generada
        """
        try:
            # Construir contexto de conversación
            conversation_context = self._build_conversation_context(
                user_message, user, session, relevant_info
            )
            
            # Generar respuesta con OpenAI
            response = self.openai_service.generate_chat_completion(
                messages=[
                    {"role": "system", "content": self.system_context},
                    {"role": "user", "content": conversation_context}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            if not response:
                return self._get_fallback_response(user_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return self._get_fallback_response(user_message)
    
    def _generate_image_response(
        self, 
        image_analysis: Dict[str, Any], 
        user: User
    ) -> str:
        """
        Generar respuesta basada en análisis de imagen.
        
        Args:
            image_analysis: Análisis de la imagen
            user: Usuario
            
        Returns:
            str: Respuesta generada
        """
        try:
            # Construir prompt para análisis de imagen
            image_description = image_analysis.get("description", "")
            tags = ", ".join(image_analysis.get("tags", []))
            
            prompt = f"""
            Analiza esta imagen y proporciona una respuesta pastoral y edificante.
            
            Descripción de la imagen: {image_description}
            Etiquetas: {tags}
            
            Responde como un pastor amoroso, conectando lo que ves en la imagen 
            con principios bíblicos y el amor de Dios. Sé alentador y edificante.
            """
            
            response = self.openai_service.generate_chat_completion(
                messages=[
                    {"role": "system", "content": self.system_context},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            if not response:
                return (
                    "Gracias por compartir esta imagen. Que Dios te bendiga "
                    "y te guíe en tu caminar con Él. ¿En qué más puedo ayudarte?"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generando respuesta de imagen: {str(e)}")
            return (
                "Gracias por compartir esta imagen. Que Dios te bendiga "
                "y te guíe en tu caminar con Él. ¿En qué más puedo ayudarte?"
            )
    
    def _build_conversation_context(
        self, 
        user_message: str, 
        user: User, 
        session: UserSession, 
        relevant_info: List[Dict[str, Any]]
    ) -> str:
        """
        Construir contexto de conversación para OpenAI.
        
        Args:
            user_message: Mensaje del usuario
            user: Usuario
            session: Sesión del usuario
            relevant_info: Información relevante encontrada
            
        Returns:
            str: Contexto de conversación
        """
        try:
            context_parts = []
            
            # Información del usuario
            context_parts.append(f"Usuario: {user.name} (Tel: {user.phone_number})")
            
            # Información relevante encontrada
            if relevant_info:
                context_parts.append("Información relevante de la iglesia:")
                for info in relevant_info:
                    context_parts.append(f"- {info.get('content', '')}")
            
            # Historial de conversación (últimos 3 mensajes)
            if session.context is None:
                session.context = {}
            conversation_history = session.context.get("conversation_history", [])
            if conversation_history:
                context_parts.append("Historial reciente de la conversación:")
                for msg in conversation_history[-3:]:
                    context_parts.append(f"- {msg}")
            
            # Mensaje actual
            context_parts.append(f"Mensaje actual del usuario: {user_message}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error construyendo contexto: {str(e)}")
            return f"Mensaje del usuario: {user_message}"
    
    def _update_session_context(
        self, 
        session: UserSession, 
        user_message: str, 
        bot_response: str
    ):
        """
        Actualizar contexto de la sesión.
        
        Args:
            session: Sesión del usuario
            user_message: Mensaje del usuario
            bot_response: Respuesta del bot
        """
        try:
            # Actualizar historial de conversación
            if session.context is None:
                session.context = {}
            conversation_history = session.context.get("conversation_history", [])
            conversation_history.extend([user_message, bot_response])
            
            # Mantener solo los últimos 10 mensajes
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
            
            session.context["conversation_history"] = conversation_history
            session.context["last_update"] = datetime.now().isoformat()
            
            # Guardar sesión actualizada
            self.user_service.update_session(session)
            
        except Exception as e:
            logger.error(f"Error actualizando contexto de sesión: {str(e)}")
    
    def _send_whatsapp_message(self, to_number: str, message: str) -> bool:
        """
        Enviar mensaje por WhatsApp.
        
        Args:
            to_number: Número de destino
            message: Mensaje a enviar
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            result = self.whatsapp_service.send_text_message(message, to_number)
            
            # Verificar si la respuesta indica éxito
            if result and "messages" in result:
                logger.info(f"Mensaje enviado a {to_number}")
                return True
            else:
                logger.error(f"Error enviando mensaje a {to_number}")
                return False
            
        except Exception as e:
            logger.error(f"Error enviando mensaje WhatsApp: {str(e)}")
            return False
    
    def _send_welcome_message(self, to_number: str) -> Dict[str, Any]:
        """
        Enviar mensaje de bienvenida.
        
        Args:
            to_number: Número de destino
            
        Returns:
            Dict[str, Any]: Respuesta
        """
        try:
            welcome_message = (
                "¡Bienvenido a VEA Connect! 🙏\n\n"
                "Soy tu asistente virtual pastoral, aquí para servirte con amor "
                "y conectarte con nuestra comunidad cristiana.\n\n"
                "Puedo ayudarte con:\n"
                "• Información sobre ministerios y eventos\n"
                "• Horarios de servicios\n"
                "• Donaciones y ofrendas\n"
                "• Oración y apoyo espiritual\n"
                "• Conexión con líderes\n\n"
                "¿En qué puedo servirte hoy?"
            )
            
            self._send_whatsapp_message(to_number, welcome_message)
            
            return format_response(
                "Mensaje de bienvenida enviado",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de bienvenida: {str(e)}")
            return self._send_error_message(to_number)
    
    def _send_error_message(self, to_number: str) -> Dict[str, Any]:
        """
        Enviar mensaje de error.
        
        Args:
            to_number: Número de destino
            
        Returns:
            Dict[str, Any]: Respuesta
        """
        try:
            error_message = (
                "Lo siento, estoy teniendo dificultades técnicas en este momento. "
                "Por favor, intenta de nuevo en unos minutos o contacta directamente "
                "con nuestros líderes de ministerio. Que Dios te bendiga. 🙏"
            )
            
            self._send_whatsapp_message(to_number, error_message)
            
            return format_response(
                "Mensaje de error enviado",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de error: {str(e)}")
            return create_error_response("Error enviando mensaje")
    
    def _send_rate_limit_message(self, to_number: str) -> Dict[str, Any]:
        """
        Enviar mensaje de rate limit excedido.
        
        Args:
            to_number: Número de destino
            
        Returns:
            Dict[str, Any]: Respuesta
        """
        try:
            rate_limit_message = (
                "Estás enviando mensajes muy rápidamente. "
                "Por favor, espera un momento antes de enviar otro mensaje. "
                "Estoy aquí para ayudarte. 🙏"
            )
            
            self._send_whatsapp_message(to_number, rate_limit_message)
            
            return format_response(
                "Mensaje de rate limit enviado",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de rate limit: {str(e)}")
            return create_error_response("Error enviando mensaje")
    
    def _send_unsupported_media_message(self, to_number: str) -> Dict[str, Any]:
        """
        Enviar mensaje para medios no soportados.
        
        Args:
            to_number: Número de destino
            
        Returns:
            Dict[str, Any]: Respuesta
        """
        try:
            unsupported_message = (
                "Gracias por tu mensaje. Por favor, envía texto o imágenes "
                "para que pueda ayudarte mejor. ¿En qué puedo servirte?"
            )
            
            self._send_whatsapp_message(to_number, unsupported_message)
            
            return format_response(
                "Mensaje de medio no soportado enviado",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de medio no soportado: {str(e)}")
            return self._send_error_message(to_number)
    
    def _get_fallback_response(self, user_message: str) -> str:
        """
        Obtener respuesta de respaldo cuando OpenAI falla.
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            str: Respuesta de respaldo
        """
        # Respuestas de respaldo basadas en palabras clave
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ["evento", "actividad", "servicio"]):
            return (
                "Gracias por preguntar sobre nuestros eventos. "
                "Nuestros servicios son los domingos a las 9:00 AM y 11:00 AM, "
                "y los miércoles a las 7:00 PM. Para información específica "
                "sobre eventos especiales, te recomiendo contactar directamente "
                "con nuestros líderes de ministerio. Que Dios te bendiga. 🙏"
            )
        
        elif any(word in user_message_lower for word in ["donación", "ofrenda", "diezmo"]):
            return (
                "Gracias por tu interés en las donaciones. "
                "Puedes hacer tus ofrendas durante los servicios o contactar "
                "directamente con nuestro ministerio de finanzas. "
                "Que Dios multiplique tu generosidad. 🙏"
            )
        
        elif any(word in user_message_lower for word in ["oración", "orar", "bendición"]):
            return (
                "Gracias por pedir oración. Estoy orando por ti en este momento. "
                "Que Dios te dé paz, sabiduría y fortaleza. "
                "Si necesitas oración específica, nuestros líderes están disponibles "
                "para orar contigo. Que Dios te bendiga abundantemente. 🙏"
            )
        
        else:
            return (
                "Gracias por tu mensaje. Estoy aquí para servirte y ayudarte "
                "en tu caminar con Dios. Si tienes alguna pregunta específica "
                "sobre nuestros ministerios, eventos o necesitas apoyo espiritual, "
                "no dudes en preguntarme. Que Dios te bendiga. 🙏"
            )


# Instancia global del bot (lazy initialization para testing)
bot = None


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Función principal de Azure Functions.
    
    Args:
        req: Request HTTP
        
    Returns:
        func.HttpResponse: Respuesta HTTP
    """
    global bot
    if bot is None:
        bot = WhatsAppBot()
    return bot.process_message(req)


def build_context_prompt(search_results: List[Dict[str, Any]], user_question: str) -> str:
    """
    Construir prompt contextual basado en resultados de búsqueda.
    
    Args:
        search_results: Resultados de búsqueda semántica
        user_question: Pregunta del usuario
        
    Returns:
        Prompt contextual formateado
    """
    try:
        if not search_results:
            return f"Pregunta del usuario: {user_question}\n\nNo se encontró información relevante en la base de conocimientos."
        
        # Filtrar resultados relevantes (score > 0.7)
        relevant_results = [r for r in search_results if r.get("score", 0) > 0.7]
        
        if not relevant_results:
            return f"Pregunta del usuario: {user_question}\n\nNo se encontró información suficientemente relevante en la base de conocimientos."
        
        # Construir contexto
        context_parts = [f"Pregunta del usuario: {user_question}\n\nInformación relevante de la base de conocimientos:"]
        
        for i, result in enumerate(relevant_results[:3], 1):  # Máximo 3 resultados
            text = result.get("text", "")
            source = result.get("metadata", {}).get("filename", "documento")
            context_parts.append(f"{i}. {text} (Fuente: {source})")
        
        context_parts.append("\nPor favor, responde basándote en la información proporcionada. Si la información no es suficiente, indícalo claramente.")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error construyendo prompt contextual: {str(e)}")
        return f"Pregunta del usuario: {user_question}"


def generate_rag_response(user_question: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Generar respuesta usando RAG (Retrieval-Augmented Generation).
    
    Args:
        user_question: Pregunta del usuario
        search_results: Resultados de búsqueda semántica
        
    Returns:
        Respuesta generada
    """
    try:
        # Construir prompt contextual
        context_prompt = build_context_prompt(search_results, user_question)
        
        # Generar respuesta contextual
        response = generate_contextual_response(context_prompt)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generando respuesta RAG: {str(e)}")
        return generate_general_response(user_question)


def generate_contextual_response(context_prompt: str) -> str:
    """
    Generar respuesta contextual usando OpenAI.
    
    Args:
        context_prompt: Prompt con contexto
        
    Returns:
        Respuesta generada
    """
    try:
        # Aquí se usaría el servicio de OpenAI para generar la respuesta
        # Por ahora, retornamos una respuesta de ejemplo
        return "Basándome en la información disponible, puedo ayudarte con tu consulta. ¿Hay algo específico que te gustaría saber?"
        
    except Exception as e:
        logger.error(f"Error generando respuesta contextual: {str(e)}")
        return "Lo siento, no pude procesar tu consulta en este momento."


def generate_general_response(user_question: str) -> str:
    """
    Generar respuesta general cuando no hay contexto específico.
    
    Args:
        user_question: Pregunta del usuario
        
    Returns:
        Respuesta general
    """
    try:
        # Aquí se usaría el servicio de OpenAI para generar una respuesta general
        # Por ahora, retornamos una respuesta de ejemplo
        return "Gracias por tu mensaje. Soy un bot de asistencia para la comunidad cristiana. ¿En qué puedo ayudarte hoy?"
        
    except Exception as e:
        logger.error(f"Error generando respuesta general: {str(e)}")
        return "Lo siento, no pude procesar tu consulta en este momento." 