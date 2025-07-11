import logging
import azure.functions as func
import json
import traceback
from shared_code.acs_whatsapp_client import send_whatsapp_message_via_acs

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger to send WhatsApp messages via ACS.
    Accepts POST requests with JSON body containing 'to' and 'message'.
    """
    logger: logging.Logger = logging.getLogger(__name__)
    try:
        req_body = req.get_json()
    except Exception:
        logger.error("Invalid JSON body.")
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body."}),
            status_code=400,
            mimetype="application/json"
        )
    to_number = req_body.get("to")
    message = req_body.get("message")
    if not to_number or not message:
        logger.error("Missing 'to' or 'message' in request body.")
        return func.HttpResponse(
            json.dumps({"error": "Missing 'to' or 'message' in request body."}),
            status_code=400,
            mimetype="application/json"
        )
    try:
        response = send_whatsapp_message_via_acs(to_number, message)
        logger.info(f"Message sent to {to_number} via ACS.")
        return func.HttpResponse(
            json.dumps({"success": True, "acs_response": response}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        logger.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        ) 