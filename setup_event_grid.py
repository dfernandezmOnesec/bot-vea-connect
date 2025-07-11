#!/usr/bin/env python3
"""
Script de configuración para Event Grid y Azure Communication Services

Este script te ayuda a configurar Event Grid para recibir eventos de WhatsApp
desde Azure Communication Services.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from azure.identity import DefaultAzureCredential
from azure.mgmt.eventgrid import EventGridManagementClient
from azure.mgmt.communication import CommunicationServiceManagementClient
from azure.mgmt.resource import ResourceManagementClient

def setup_event_grid_for_acs():
    """
    Configura Event Grid para Azure Communication Services.
    """
    print("🚀 Configurando Event Grid para Azure Communication Services...")
    
    # Configuración
    subscription_id = input("Ingresa tu Subscription ID: ")
    resource_group = input("Ingresa el nombre del Resource Group: ")
    acs_resource_name = input("Ingresa el nombre del recurso de Azure Communication Services: ")
    function_app_name = input("Ingresa el nombre de tu Function App: ")
    location = input("Ingresa la ubicación (ej: westus2): ")
    
    try:
        # Inicializar credenciales
        credential = DefaultAzureCredential()
        
        # Clientes de Azure
        eventgrid_client = EventGridManagementClient(credential, subscription_id)
        communication_client = CommunicationServiceManagementClient(credential, subscription_id)
        resource_client = ResourceManagementClient(credential, subscription_id)
        
        print("✅ Credenciales de Azure configuradas correctamente")
        
        # 1. Crear Event Grid Topic
        topic_name = f"{acs_resource_name}-whatsapp-events"
        topic_endpoint = create_event_grid_topic(
            eventgrid_client, resource_group, topic_name, location
        )
        
        # 2. Crear Event Subscription
        subscription_name = f"{acs_resource_name}-whatsapp-subscription"
        create_event_subscription(
            eventgrid_client, resource_group, topic_name, subscription_name,
            function_app_name, location
        )
        
        # 3. Configurar ACS para enviar eventos
        configure_acs_events(
            communication_client, resource_group, acs_resource_name, topic_endpoint
        )
        
        print("\n🎉 ¡Configuración completada!")
        print(f"Event Grid Topic: {topic_name}")
        print(f"Endpoint: {topic_endpoint}")
        
        # Generar configuración para .env
        generate_env_config(topic_endpoint)
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")

def create_event_grid_topic(
    client: EventGridManagementClient,
    resource_group: str,
    topic_name: str,
    location: str
) -> str:
    """
    Crea un Event Grid Topic.
    """
    print(f"📝 Creando Event Grid Topic: {topic_name}")
    
    topic = client.topics.begin_create_or_update(
        resource_group,
        topic_name,
        {
            "location": location,
            "inputSchema": "EventGridSchema"
        }
    ).result()
    
    endpoint = topic.endpoint
    print(f"✅ Event Grid Topic creado: {endpoint}")
    return endpoint

def create_event_subscription(
    client: EventGridManagementClient,
    resource_group: str,
    topic_name: str,
    subscription_name: str,
    function_app_name: str,
    location: str
):
    """
    Crea una suscripción de eventos para la Function App.
    """
    print(f"📝 Creando Event Subscription: {subscription_name}")
    
    # URL del webhook de la Function App
    webhook_url = f"https://{function_app_name}.azurewebsites.net/api/whatsapp-bot"
    
    event_subscription = client.event_subscriptions.begin_create_or_update(
        resource_group,
        topic_name,
        subscription_name,
        {
            "destination": {
                "endpointType": "WebHook",
                "properties": {
                    "endpointUrl": webhook_url
                }
            },
            "filter": {
                "includedEventTypes": [
                    "Microsoft.Communication.AdvancedMessageReceived",
                    "Microsoft.Communication.AdvancedMessageDeliveryStatusUpdated",
                    "Microsoft.Communication.AdvancedMessageReadStatusUpdated"
                ]
            }
        }
    ).result()
    
    print(f"✅ Event Subscription creada: {subscription_name}")

def configure_acs_events(
    client: CommunicationServiceManagementClient,
    resource_group: str,
    acs_name: str,
    topic_endpoint: str
):
    """
    Configura Azure Communication Services para enviar eventos a Event Grid.
    """
    print(f"📝 Configurando eventos en ACS: {acs_name}")
    
    # Obtener el recurso de ACS
    acs_resource = client.communication_services.get(resource_group, acs_name)
    
    # Configurar eventos (esto requeriría la API específica de ACS)
    print("ℹ️  Nota: La configuración de eventos en ACS debe hacerse manualmente")
    print(f"   - Ve al portal de Azure")
    print(f"   - Navega a tu recurso de Azure Communication Services")
    print(f"   - Ve a 'Events' o 'Event Grid'")
    print(f"   - Configura los eventos para enviar a: {topic_endpoint}")

def generate_env_config(topic_endpoint: str):
    """
    Genera la configuración para el archivo .env
    """
    print("\n📋 Configuración para tu archivo .env:")
    print("=" * 50)
    print(f"EVENT_GRID_TOPIC_ENDPOINT={topic_endpoint}")
    print("EVENT_GRID_TOPIC_KEY=<obtén la clave desde el portal de Azure>")
    print("EVENT_GRID_WEBHOOK_SECRET=<genera una clave secreta>")
    print("=" * 50)

def get_topic_key(subscription_id: str, resource_group: str, topic_name: str) -> str:
    """
    Obtiene la clave del Event Grid Topic.
    """
    try:
        credential = DefaultAzureCredential()
        client = EventGridManagementClient(credential, subscription_id)
        
        keys = client.topics.list_shared_access_keys(resource_group, topic_name)
        return keys.key1
    except Exception as e:
        print(f"❌ Error obteniendo la clave del topic: {e}")
        return ""

if __name__ == "__main__":
    print("🔧 Configurador de Event Grid para Azure Communication Services")
    print("=" * 60)
    
    setup_event_grid_for_acs() 