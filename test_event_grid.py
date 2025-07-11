#!/usr/bin/env python3
"""
Script de prueba para Event Grid y Azure Communication Services

Este script envía eventos de prueba para verificar que la configuración
de Event Grid está funcionando correctamente.
"""

import json
import requests
import time
from typing import Dict, Any
from datetime import datetime, timezone

def test_event_grid_webhook():
    """
    Prueba el webhook de Event Grid enviando un evento de prueba.
    """
    print("🧪 Probando Event Grid Webhook...")
    
    # URL de tu Function App (ajusta según tu configuración)
    function_app_url = input("Ingresa la URL de tu Function App (ej: https://tu-app.azurewebsites.net): ")
    
    # Crear evento de prueba
    test_event = create_test_event()
    
    # URL del webhook
    webhook_url = f"{function_app_url}/runtime/webhooks/eventgrid?functionName=acs_event_grid_handler"
    
    print(f"📤 Enviando evento de prueba a: {webhook_url}")
    print(f"📋 Evento: {json.dumps(test_event, indent=2)}")
    
    try:
        # Enviar evento
        response = requests.post(
            webhook_url,
            json=test_event,
            headers={
                "Content-Type": "application/json",
                "aeg-event-type": "Notification"
            },
            timeout=30
        )
        
        print(f"📥 Respuesta: {response.status_code}")
        print(f"📄 Contenido: {response.text}")
        
        if response.status_code == 200:
            print("✅ ¡Evento enviado exitosamente!")
        else:
            print(f"❌ Error al enviar evento: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def create_test_event() -> Dict[str, Any]:
    """
    Crea un evento de prueba que simula un mensaje de WhatsApp recibido.
    """
    return {
        "id": f"test-event-{int(time.time())}",
        "eventType": "Microsoft.Communication.AdvancedMessageReceived",
        "subject": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test",
        "eventTime": datetime.now(timezone.utc).isoformat() + "Z",
        "dataVersion": "1.0",
        "data": {
            "messageId": f"msg-{int(time.time())}",
            "from": {
                "phoneNumber": "+1234567890",
                "kind": "phoneNumber"
            },
            "to": [
                {
                    "phoneNumber": "+0987654321",
                    "kind": "phoneNumber"
                }
            ],
            "message": {
                "type": "text",
                "content": {
                    "text": "Hola bot, este es un mensaje de prueba"
                }
            },
            "receivedTimestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }
    }

def test_acs_message_sending():
    """
    Prueba el envío de mensajes via Azure Communication Services.
    """
    print("\n📱 Probando envío de mensajes via ACS...")
    
    # Obtener configuración
    acs_endpoint = input("Ingresa el ACS Endpoint: ")
    acs_channel_id = input("Ingresa el ACS Channel ID: ")
    acs_access_key = input("Ingresa el ACS Access Key: ")
    phone_number = input("Ingresa el número de teléfono de destino (+1234567890): ")
    message = input("Ingresa el mensaje de prueba: ")
    
    try:
        from shared_code.acs_whatsapp_client import send_whatsapp_message_via_acs
        
        # Configurar variables de entorno temporalmente
        import os
        os.environ["ACS_ENDPOINT"] = acs_endpoint
        os.environ["ACS_CHANNEL_ID"] = acs_channel_id
        os.environ["ACS_ACCESS_KEY"] = acs_access_key
        
        # Enviar mensaje
        response = send_whatsapp_message_via_acs(phone_number, message)
        
        print(f"✅ Mensaje enviado exitosamente!")
        print(f"📄 Respuesta: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")

def test_local_function():
    """
    Prueba la función localmente.
    """
    print("\n🏠 Probando función localmente...")
    print("⚠️  Esta prueba requiere configuración adicional de tipos")
    print("   Se recomienda probar directamente en Azure")

def main():
    """
    Menú principal de pruebas.
    """
    print("🧪 Probador de Event Grid y Azure Communication Services")
    print("=" * 60)
    
    while True:
        print("\nOpciones:")
        print("1. Probar webhook de Event Grid")
        print("2. Probar envío de mensajes via ACS")
        print("3. Verificar configuración")
        print("4. Ejecutar todas las pruebas")
        print("5. Salir")
        
        choice = input("\nSelecciona una opción (1-5): ")
        
        if choice == "1":
            test_event_grid_webhook()
        elif choice == "2":
            test_acs_message_sending()
        elif choice == "3":
            test_local_function()
        elif choice == "4":
            print("\n🔄 Ejecutando todas las pruebas...")
            test_event_grid_webhook()
            test_acs_message_sending()
            print("\n✅ Todas las pruebas completadas")
        elif choice == "5":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main() 