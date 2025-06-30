"""
WhatsAppBot Azure Function.

Handles WhatsApp webhook verification (GET) and message processing (POST) with RAG.
On POST, generates embeddings for user questions, performs similarity search in Redis,
and generates context-aware responses using OpenAI.
"""

import azure.functions as func
import logging
import json
from typing import Dict, Any, List, Optional
from src.shared_code.openai_service import openai_service
from src.shared_code.redis_service import redis_service
from src.shared_code.whatsapp_service import whatsapp_service
from src.config.settings import settings

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    WhatsAppBot function for handling webhook verification and processing incoming WhatsApp messages with context-aware RAG.
    
    This function:
    1. Verifies WhatsApp webhook on GET requests
    2. Processes incoming messages on POST requests
    3. Generates embeddings for user questions
    4. Performs similarity search in Redis for relevant context
    5. Generates context-aware responses using OpenAI
    6. Sends responses back via WhatsApp
    
    Args:
        req (func.HttpRequest): The incoming HTTP request.
        
    Returns:
        func.HttpResponse: The HTTP response with appropriate status code.
        
    Raises:
        Exception: If message processing fails.
    """
    try:
        if req.method == "GET":
            return handle_webhook_verification(req)
        elif req.method == "POST":
            return handle_message_processing(req)
        else:
            logger.warning(f"Unsupported HTTP method: {req.method}")
            return func.HttpResponse("Method not allowed", status_code=405)
            
    except Exception as e:
        error_message = f"Error in WhatsAppBot: {str(e)}"
        logger.error(error_message)
        return func.HttpResponse(error_message, status_code=500)

def handle_webhook_verification(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle WhatsApp webhook verification.
    
    Args:
        req (func.HttpRequest): The incoming HTTP request.
        
    Returns:
        func.HttpResponse: The HTTP response with challenge or error.
    """
    try:
        mode = req.params.get("hub.mode")
        token = req.params.get("hub.verify_token")
        challenge = req.params.get("hub.challenge")
        
        logger.info("Received webhook verification request")
        
        if not all([mode, token, challenge]):
            logger.warning("Webhook verification failed: missing parameters")
            return func.HttpResponse("Missing parameters", status_code=400)
        
        if token == settings.verify_token:
            logger.info("Webhook verified successfully")
            return func.HttpResponse(challenge, status_code=200)
        else:
            logger.warning("Webhook verification failed: invalid token")
            return func.HttpResponse("Verification token mismatch", status_code=403)
            
    except Exception as e:
        logger.error(f"Error in webhook verification: {e}")
        return func.HttpResponse("Internal server error", status_code=500)

def handle_message_processing(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle incoming WhatsApp message processing with RAG.
    
    Args:
        req (func.HttpRequest): The incoming HTTP request.
        
    Returns:
        func.HttpResponse: The HTTP response.
    """
    try:
        # Parse request body
        try:
            body = req.get_json()
        except Exception as e:
            logger.error(f"Invalid JSON payload: {e}")
            return func.HttpResponse("Invalid JSON", status_code=400)
        
        logger.info("Received WhatsApp message event")
        
        # Process webhook event
        processed_event = whatsapp_service.process_webhook_event(body)
        
        if processed_event["event_type"] != "message":
            logger.info(f"Ignoring non-message event: {processed_event['event_type']}")
            return func.HttpResponse("OK", status_code=200)
        
        # Process text messages only
        if processed_event["message_type"] != "text":
            logger.info(f"Ignoring non-text message: {processed_event['message_type']}")
            return func.HttpResponse("OK", status_code=200)
        
        user_question = processed_event["message_content"]
        sender_id = processed_event["sender_id"]
        message_id = processed_event["message_id"]
        
        if not user_question:
            logger.warning("Empty message content received")
            return func.HttpResponse("OK", status_code=200)
        
        logger.info(f"Processing message from {sender_id}: {user_question[:50]}...")
        
        # Generate response using RAG
        response = generate_rag_response(user_question)
        
        # Send response back to user
        try:
            whatsapp_service.send_text_message(response, sender_id)
            logger.info(f"Response sent successfully to {sender_id}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return func.HttpResponse("Error sending message", status_code=500)
        
        # Mark message as read
        try:
            if message_id:
                whatsapp_service.mark_message_as_read(message_id)
                logger.info(f"Message marked as read: {message_id}")
        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")
        
        return func.HttpResponse("OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error in message processing: {e}")
        return func.HttpResponse("Internal server error", status_code=500)

def generate_rag_response(user_question: str) -> str:
    """
    Generate a response using RAG (Retrieval Augmented Generation).
    
    Args:
        user_question (str): The user's question.
        
    Returns:
        str: The generated response.
        
    Raises:
        Exception: If response generation fails.
    """
    try:
        # Generate embedding for user question
        question_embedding = openai_service.generate_embeddings(user_question)
        logger.info("Generated embedding for user question")
        
        # Perform similarity search in Redis
        search_results = redis_service.semantic_search(question_embedding, top_k=3)
        logger.info(f"Found {len(search_results)} relevant documents")
        
        if search_results and any(result["score"] > 0.7 for result in search_results):
            # Use RAG with context
            context_prompt = build_context_prompt(search_results, user_question)
            response = generate_contextual_response(context_prompt, user_question)
            logger.info("Generated context-aware response using RAG")
        else:
            # Fallback to general chat completion
            response = generate_general_response(user_question)
            logger.info("Generated general response (no relevant context found)")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        return "Lo siento, estoy teniendo problemas para procesar tu pregunta. Por favor, intenta de nuevo más tarde."

def build_context_prompt(search_results: List[Dict[str, Any]], user_question: str) -> str:
    """
    Build a context prompt from search results.
    
    Args:
        search_results (List[Dict[str, Any]]): Results from similarity search.
        user_question (str): The user's question.
        
    Returns:
        str: The formatted context prompt.
    """
    try:
        # Filter results with good similarity scores
        relevant_results = [result for result in search_results if result["score"] > 0.7]
        
        if not relevant_results:
            return ""
        
        # Build context from top results
        context_parts = []
        for i, result in enumerate(relevant_results[:3], 1):
            context_parts.append(f"Documento {i}:\n{result['text'][:500]}...")
        
        context_text = "\n\n".join(context_parts)
        
        prompt = f"""Eres VEA Connect AI Assistant. Usa el siguiente contexto para responder la pregunta del usuario. Si el contexto no es suficiente, responde de manera elegante.

Contexto:
{context_text}

Pregunta del Usuario:
{user_question}

Responde de manera clara, concisa y útil basándote en el contexto proporcionado."""
        
        return prompt
        
    except Exception as e:
        logger.error(f"Error building context prompt: {e}")
        return ""

def generate_contextual_response(context_prompt: str, user_question: str) -> str:
    """
    Generate a response using context-aware chat completion.
    
    Args:
        context_prompt (str): The context prompt with relevant information.
        user_question (str): The user's question.
        
    Returns:
        str: The generated response.
    """
    try:
        messages = [
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": user_question}
        ]
        
        response = openai_service.generate_chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"Error generating contextual response: {e}")
        return "Lo siento, no pude generar una respuesta basada en el contexto. ¿Puedes reformular tu pregunta?"

def generate_general_response(user_question: str) -> str:
    """
    Generate a general response without specific context.
    
    Args:
        user_question (str): The user's question.
        
    Returns:
        str: The generated response.
    """
    try:
        messages = [
            {"role": "system", "content": "Eres VEA Connect AI Assistant, un asistente virtual amigable y útil. Responde de manera clara y concisa en español."},
            {"role": "user", "content": user_question}
        ]
        
        response = openai_service.generate_chat_completion(
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"Error generating general response: {e}")
        return "Hola! Soy el asistente de VEA Connect. ¿En qué puedo ayudarte hoy?" 