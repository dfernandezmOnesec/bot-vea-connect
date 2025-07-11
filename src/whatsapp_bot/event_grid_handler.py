import azure.functions as func
import logging
from .whatsapp_bot import WhatsAppBot

def main(event: func.EventGridEvent) -> func.HttpResponse:
    """
    Azure Function para manejar eventos de Event Grid (ACS).
    """
    logger = logging.getLogger(__name__)
    try:
        bot = WhatsAppBot()
        return bot.process_event_grid_event(event)
    except Exception as e:
        logger.error(f"Error en event_grid_handler: {str(e)}")
        return func.HttpResponse("Error interno", status_code=500) 