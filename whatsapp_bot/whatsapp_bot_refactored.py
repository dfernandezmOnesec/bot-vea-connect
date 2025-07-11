"""
Bot de WhatsApp refactorizado para la comunidad cristiana VEA Connect.

Esta versión utiliza inyección de dependencias y servicios separados
para mejorar la modularidad, testabilidad y mantenibilidad del código.
"""

import azure.functions as func
import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import traceback

# Importar módulos compartidos
from shared_code.dependency_container import get_dependency_container, get_service, get_service_safe
from shared_code.interfaces import IWhatsAppService, IUserService, IOpenAIService, IVisionService, IBlobStorageService, IRedisService, IMessageProcessor, IErrorHandler
from shared_code.user_service import User, UserSession
from shared_code.utils import (
    setup_logging,
    parse_whatsapp_message,
    extract_media_info,
    format_response,
    create_error_response,
    validate_phone_number,
    sanitize_text,
    generate_session_id,
    rate_limit_check,
    sanitize_phone_number,
    sanitize_log_message,
    sanitize_session_id
)
from config.settings import get_settings


# Configurar logging
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppBotRefactored:
    """
    Bot de WhatsApp refactorizado para la comunidad cristiana VEA Connect.
    
    Esta versión utiliza inyección de dependencias y servicios separados
    para mejorar la modularidad y testabilidad.
    """
    
    def __init__(self, dependency_container=None):
        """
        Inicializar el bot con inyección de dependencias.
        
        Args:
            dependency_container: Contenedor de dependencias (opcional)
        """
        try:
            # Obtener configuración
            self.settings = get_settings()
            
            # Usar contenedor de dependencias o el global
            self.container = dependency_container or get_dependency_container()
            
            # Obtener servicios principales
            self.whatsapp_service: IWhatsAppService = get_service("whatsapp")
            self.user_service: IUserService = get_service("user")
            self.openai_service: IOpenAIService = get_service("openai")
            self.error_handler: IErrorHandler = get_service("error_handler")
            
            # Obtener servicios opcionales
            self.vision_service: Optional[IVisionService] = get_service_safe("vision")
            self.blob_storage_service: Optional[IBlobStorageService] = get_service_safe("blob_storage")
            self.redis_service: Optional[IRedisService] = get_service_safe("redis")
            
            # Obtener procesador de mensajes
            self.message_processor: IMessageProcessor = get_service("message_processor")
            
            # Inicializar contexto de conversación y rate limiter
            self.conversation_context = {}
            self.rate_limiter = {}
            
            logger.info("WhatsAppBotRefactored initialized successfully")
            
        except Exception as e:
            logger.error(f"Error al inicializar WhatsAppBotRefactored: {e}")
            raise
    
    def process_message(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Procesar mensaje entrante de WhatsApp via HTTP webhook.
        
        Args:
            req: Request HTTP de Azure Functions
            
        Returns:
            func.HttpResponse: Respuesta HTTP
        """
        try:
            logger.info("Procesando mensaje entrante de WhatsApp")
            logger.info(f"Headers: {dict(req.headers)}")
            logger.info(f"Query params: {dict(req.params)}")
            
            # Sanitizar el body del request antes de loggearlo
            try:
                body = req.get_body().decode('utf-8')
                sanitized_body = sanitize_log_message(body)
                logger.info(f"Request body: {sanitized_body}")
            except Exception as e:
                logger.warning(f"Could not decode request body: {e}")
            
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
            
            error_response = self.error_handler.create_error_response(
                "Error interno del servidor",
                error_code="INTERNAL_ERROR"
            )
            
            return func.HttpResponse(
                json.dumps(error_response),
                mimetype="application/json",
                status_code=500
            )
    
    def process_event_grid_event(self, event: func.EventGridEvent) -> func.HttpResponse:
        """
        Procesar evento de Event Grid desde Azure Communication Services.
        
        Args:
            event: Event Grid event de Azure Functions
            
        Returns:
            func.HttpResponse: Respuesta HTTP
        """
        try:
            logger.info(f"Procesando Event Grid event: {event.event_type}")
            logger.info(f"Event subject: {event.subject}")
            
            # Manejar diferentes tipos de eventos
            if event.event_type == "Microsoft.Communication.AdvancedMessageReceived":
                return self._handle_acs_message_received(event)
            elif event.event_type == "Microsoft.Communication.AdvancedMessageDeliveryStatusUpdated":
                return self._handle_acs_delivery_status_update(event)
            elif event.event_type == "Microsoft.Communication.AdvancedMessageReadStatusUpdated":
                return self._handle_acs_read_status_update(event)
            else:
                logger.info(f"Evento no manejado: {event.event_type}")
                return func.HttpResponse(
                    json.dumps({"status": "ignored", "event_type": event.event_type}),
                    mimetype="application/json",
                    status_code=200
                )
                
        except Exception as e:
            logger.error(f"Error procesando Event Grid event: {str(e)}")
            logger.error(traceback.format_exc())
            
            error_response = self.error_handler.create_error_response(
                "Error procesando evento",
                error_code="EVENT_PROCESSING_ERROR"
            )
            
            return func.HttpResponse(
                json.dumps(error_response),
                mimetype="application/json",
                status_code=500
            )
    
    def _handle_acs_message_received(self, event: func.EventGridEvent) -> func.HttpResponse:
        """
        Manejar mensaje recibido desde Azure Communication Services.
        
        Args:
            event: Event Grid event con datos del mensaje
            
        Returns:
            func.HttpResponse: Respuesta HTTP
        """
        try:
            # Extraer datos del evento
            event_data = event.get_json()
            logger.info(f"Event data: {event_data}")
            
            # Extraer información del mensaje
            message_data = event_data.get("data", {})
            phone_number = message_data.get("from", {}).get("phoneNumber")
            message_type = message_data.get("type")
            message_text = message_data.get("content", "")
            
            if not phone_number:
                logger.warning("No se pudo extraer número de teléfono del evento")
                return func.HttpResponse(
                    json.dumps({"status": "error", "message": "Phone number not found"}),
                    mimetype="application/json",
                    status_code=400
                )
            
            # Procesar según el tipo de mensaje
            if message_type == "text":
                response = self._process_acs_text_message(phone_number, message_text)
            elif message_type in ["image", "audio", "document"]:
                response = self._process_acs_media_message(phone_number, message_type)
            else:
                response = self._process_acs_unsupported_message(phone_number)
            
            return func.HttpResponse(
                json.dumps(response),
                mimetype="application/json",
                status_code=200
            )
            
        except Exception as e:
            logger.error(f"Error procesando mensaje ACS: {e}")
            error_response = self.error_handler.create_error_response(
                "Error procesando mensaje ACS",
                error_code="ACS_PROCESSING_ERROR"
            )
            return func.HttpResponse(
                json.dumps(error_response),
                mimetype="application/json",
                status_code=500
            )
    
    def _process_acs_text_message(self, phone_number: str, message_text: str) -> Dict[str, Any]:
        """
        Procesar mensaje de texto desde ACS.
        
        Args:
            phone_number: Número de teléfono del remitente
            message_text: Texto del mensaje
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Obtener o crear usuario
            user = self._get_or_create_user(phone_number)
            session = self._get_or_create_session(phone_number)
            
            # Crear mensaje estructurado
            message = {
                "text": {"body": message_text},
                "from": phone_number,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Procesar mensaje usando el procesador
            result = self.message_processor.process_text_message(message, user, session)
            
            return {
                "status": "success" if result.get("success") else "error",
                "response": result
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de texto ACS: {e}")
            return self.error_handler.handle_error(e, "process_acs_text_message")
    
    def _process_acs_media_message(self, phone_number: str, media_type: str) -> Dict[str, Any]:
        """
        Procesar mensaje multimedia desde ACS.
        
        Args:
            phone_number: Número de teléfono del remitente
            media_type: Tipo de medio
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Obtener o crear usuario
            user = self._get_or_create_user(phone_number)
            session = self._get_or_create_session(phone_number)
            
            # Crear mensaje estructurado
            message = {
                media_type: {"type": media_type},
                "from": phone_number,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Procesar mensaje usando el procesador
            result = self.message_processor.process_media_message(message, user, session)
            
            return {
                "status": "success" if result.get("success") else "error",
                "response": result
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje multimedia ACS: {e}")
            return self.error_handler.handle_error(e, "process_acs_media_message")
    
    def _process_acs_unsupported_message(self, phone_number: str) -> Dict[str, Any]:
        """
        Procesar mensaje no soportado desde ACS.
        
        Args:
            phone_number: Número de teléfono del remitente
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Obtener o crear usuario
            user = self._get_or_create_user(phone_number)
            session = self._get_or_create_session(phone_number)
            
            # Crear mensaje estructurado
            message = {
                "unsupported": {"type": "unknown"},
                "from": phone_number,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Procesar mensaje usando el procesador
            result = self.message_processor.process_unsupported_message(message, user, session)
            
            return {
                "status": "success" if result.get("success") else "error",
                "response": result
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje no soportado ACS: {e}")
            return self.error_handler.handle_error(e, "process_acs_unsupported_message")
    
    def _handle_acs_delivery_status_update(self, event: func.EventGridEvent) -> func.HttpResponse:
        """
        Manejar actualización de estado de entrega desde ACS.
        
        Args:
            event: Event Grid event con datos del estado
            
        Returns:
            func.HttpResponse: Respuesta HTTP
        """
        try:
            event_data = event.get_json()
            logger.info(f"Delivery status update: {event_data}")
            
            return func.HttpResponse(
                json.dumps({"status": "processed", "event_type": "delivery_status_update"}),
                mimetype="application/json",
                status_code=200
            )
            
        except Exception as e:
            logger.error(f"Error procesando actualización de estado de entrega: {e}")
            error_response = self.error_handler.create_error_response(
                "Error procesando actualización de estado",
                error_code="DELIVERY_STATUS_ERROR"
            )
            return func.HttpResponse(
                json.dumps(error_response),
                mimetype="application/json",
                status_code=500
            )
    
    def _handle_acs_read_status_update(self, event: func.EventGridEvent) -> func.HttpResponse:
        """
        Manejar actualización de estado de lectura desde ACS.
        
        Args:
            event: Event Grid event con datos del estado
            
        Returns:
            func.HttpResponse: Respuesta HTTP
        """
        try:
            event_data = event.get_json()
            logger.info(f"Read status update: {event_data}")
            
            return func.HttpResponse(
                json.dumps({"status": "processed", "event_type": "read_status_update"}),
                mimetype="application/json",
                status_code=200
            )
            
        except Exception as e:
            logger.error(f"Error procesando actualización de estado de lectura: {e}")
            error_response = self.error_handler.create_error_response(
                "Error procesando actualización de estado",
                error_code="READ_STATUS_ERROR"
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
            req: Request HTTP con parámetros de verificación
            
        Returns:
            func.HttpResponse: Respuesta de verificación
        """
        try:
            # Obtener parámetros de verificación
            mode = req.params.get("hub.mode")
            token = req.params.get("hub.verify_token")
            challenge = req.params.get("hub.challenge")
            
            logger.info(f"Webhook verification - mode: {mode}, token: {token}, challenge: {challenge}")
            
            # Verificar webhook usando el servicio de WhatsApp
            if mode and token and challenge:
                verification_result = self.whatsapp_service.verify_webhook(mode, token, challenge)
            else:
                verification_result = None
            
            if verification_result:
                logger.info("Webhook verification successful")
                return func.HttpResponse(
                    verification_result,
                    status_code=200
                )
            else:
                logger.warning("Webhook verification failed")
                return func.HttpResponse(
                    "Verification failed",
                    status_code=403
                )
                
        except Exception as e:
            logger.error(f"Error en verificación de webhook: {e}")
            return func.HttpResponse(
                "Verification error",
                status_code=500
            )
    
    def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manejar mensaje procesado.
        
        Args:
            message: Mensaje parseado
            
        Returns:
            Dict[str, Any]: Respuesta procesada
        """
        try:
            # Extraer información del mensaje
            phone_number = message.get("from")
            message_type = message.get("type")
            
            if not phone_number:
                return self.error_handler.create_error_response(
                    "Número de teléfono no encontrado",
                    error_code="MISSING_PHONE_NUMBER"
                )
            
            # Validar número de teléfono
            if not validate_phone_number(phone_number):
                return self.error_handler.create_error_response(
                    "Número de teléfono inválido",
                    error_code="INVALID_PHONE_NUMBER"
                )
            
            # Verificar rate limiting
            if not rate_limit_check(self.redis_service, phone_number):
                return self._send_rate_limit_message(phone_number)
            
            # Obtener o crear usuario y sesión
            user = self._get_or_create_user(phone_number)
            session = self._get_or_create_session(phone_number)
            
            # Procesar según el tipo de mensaje
            if message_type == "text":
                return self.message_processor.process_text_message(message, user, session)
            elif message_type in ["image", "audio", "document"]:
                return self.message_processor.process_media_message(message, user, session)
            else:
                return self.message_processor.process_unsupported_message(message, user, session)
                
        except Exception as e:
            logger.error(f"Error manejando mensaje: {e}")
            return self.error_handler.handle_error(e, "handle_message")
    
    def _get_or_create_user(self, phone_number: str) -> User:
        """
        Obtener usuario existente o crear uno nuevo.
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            User: Usuario encontrado o creado
        """
        try:
            # Sanitizar número de teléfono
            sanitized_phone = sanitize_phone_number(phone_number)
            
            # Verificar si el usuario existe
            user_data = self.user_service.get_user(sanitized_phone)
            
            if user_data:
                # Usuario existe, actualizar última actividad
                self.user_service.update_last_activity(sanitized_phone)
                return User.from_dict(user_data)
            else:
                # Crear nuevo usuario
                new_user = User(
                    phone_number=sanitized_phone,
                    name=f"Usuario {sanitized_phone[-4:]}",  # Nombre temporal
                    created_at=datetime.now(timezone.utc)
                )
                
                if self.user_service.create_user(new_user):
                    logger.info(f"Nuevo usuario creado: {sanitize_phone_number(sanitized_phone)}")
                    return new_user
                else:
                    raise Exception("No se pudo crear el usuario")
                    
        except Exception as e:
            logger.error(f"Error obteniendo/creando usuario: {e}")
            raise
    
    def _get_or_create_session(self, phone_number: str) -> UserSession:
        """
        Obtener sesión existente o crear una nueva.
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            UserSession: Sesión encontrada o creada
        """
        try:
            # Sanitizar número de teléfono
            sanitized_phone = sanitize_phone_number(phone_number)
            
            # Obtener sesiones existentes
            sessions = self.user_service.get_user_sessions(sanitized_phone)
            
            # Buscar sesión activa
            active_session = None
            for session in sessions:
                if session.is_active:
                    active_session = session
                    break
            
            if active_session:
                return active_session
            else:
                # Crear nueva sesión
                new_session = self.user_service.create_session(sanitized_phone)
                logger.info(f"Nueva sesión creada: {sanitize_session_id(new_session.session_id)}")
                return new_session
                
        except Exception as e:
            logger.error(f"Error obteniendo/creando sesión: {e}")
            raise
    
    def _send_rate_limit_message(self, phone_number: str) -> Dict[str, Any]:
        """
        Enviar mensaje de rate limit.
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            Dict[str, Any]: Respuesta de rate limit
        """
        try:
            message = (
                "Has enviado demasiados mensajes. "
                "Por favor, espera un momento antes de enviar otro mensaje."
            )
            
            success = self.whatsapp_service.send_text_message(message, phone_number)
            
            return {
                "success": success,
                "response": message,
                "message_type": "rate_limit",
                "user_id": phone_number
            }
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de rate limit: {e}")
            return self.error_handler.handle_error(e, "send_rate_limit_message")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud del bot y sus servicios.
        
        Returns:
            Dict[str, Any]: Estado de salud del bot
        """
        try:
            # Verificar salud del contenedor de dependencias
            container_health = self.container.health_check()
            
            # Verificar servicios principales
            services_health = {
                "whatsapp_service": self.whatsapp_service.health_check() if hasattr(self.whatsapp_service, 'health_check') else True,
                "user_service": self.user_service.health_check() if hasattr(self.user_service, 'health_check') else True,
                "openai_service": self.openai_service.health_check() if hasattr(self.openai_service, 'health_check') else True,
                "error_handler": True,  # ErrorHandler no tiene health_check por defecto
                "message_processor": True  # El procesador no tiene health_check por defecto
            }
            
            # Verificar servicios opcionales
            if self.vision_service:
                services_health["vision_service"] = self.vision_service.health_check() if hasattr(self.vision_service, 'health_check') else True
            else:
                services_health["vision_service"] = False
            
            if self.blob_storage_service:
                services_health["blob_storage_service"] = self.blob_storage_service.health_check() if hasattr(self.blob_storage_service, 'health_check') else True
            else:
                services_health["blob_storage_service"] = False
            
            if self.redis_service:
                services_health["redis_service"] = self.redis_service.health_check() if hasattr(self.redis_service, 'health_check') else True
            else:
                services_health["redis_service"] = False
            
            # Determinar estado general
            all_services_healthy = all(
                health is True for health in services_health.values() 
                if health is not None
            )
            
            return {
                "bot_healthy": all_services_healthy and container_health.get("container_healthy", False),
                "container_health": container_health,
                "services_health": services_health,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en health check del bot: {e}")
            return {
                "bot_healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Función principal para Azure Functions
def main(req: Optional[func.HttpRequest] = None, event: Optional[func.EventGridEvent] = None) -> func.HttpResponse:
    """
    Función principal para Azure Functions.
    
    Args:
        req: Request HTTP (para webhook de WhatsApp)
        event: Event Grid event (para eventos de ACS)
        
    Returns:
        func.HttpResponse: Respuesta HTTP
    """
    try:
        # Crear instancia del bot refactorizado
        bot = WhatsAppBotRefactored()
        
        # Procesar según el tipo de entrada
        if req:
            return bot.process_message(req)
        elif event:
            return bot.process_event_grid_event(event)
        else:
            return func.HttpResponse(
                "No se proporcionó request ni event",
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Error en función principal: {e}")
        logger.error(traceback.format_exc())
        
        # Crear manejador de errores para respuesta
        from shared_code.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(
            "Error interno del servidor",
            error_code="MAIN_FUNCTION_ERROR"
        )
        
        return func.HttpResponse(
            json.dumps(error_response),
            mimetype="application/json",
            status_code=500
        ) 