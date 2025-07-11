import logging
import azure.functions as func
import json
from shared_code.azure_blob_storage import blob_storage_service
from shared_code.redis_service import redis_service

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger = logging.getLogger(__name__)
    logger.info("Solicitud de eliminación recibida")
    
    blob_name = req.params.get("blob_name")
    document_id = req.params.get("document_id")

    if not blob_name and not document_id:
        logger.error("Faltan parámetros: blob_name o document_id")
        return func.HttpResponse(
            json.dumps({"error": "Se requiere blob_name o document_id como parámetro."}),
            status_code=400,
            mimetype="application/json"
        )

    # Si no se proporciona document_id, se puede derivar de blob_name si tu lógica lo permite
    if not document_id and blob_name:
        # Aquí podrías derivar el document_id a partir del blob_name si tienes esa lógica
        document_id = blob_name  # Ajusta esto según tu lógica real

    try:
        # Eliminar de Blob Storage
        if blob_name:
            blob_storage_service.delete_blob(blob_name)
            logger.info(f"Blob eliminado: {blob_name}")
        # Eliminar de Redis
        if document_id:
            redis_service.delete_document(document_id)
            logger.info(f"Documento eliminado de Redis: {document_id}")
        return func.HttpResponse(
            json.dumps({"message": "Documento eliminado correctamente de Blob Storage y Redis."}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error eliminando documento: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        ) 