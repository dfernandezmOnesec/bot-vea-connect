# Configuración de Event Grid para Azure Communication Services

Este documento te guía paso a paso para configurar Event Grid y recibir eventos de WhatsApp desde Azure Communication Services.

## 🎯 Objetivo

Configurar un flujo completo donde:
1. Los usuarios envían mensajes a WhatsApp
2. Azure Communication Services recibe los mensajes
3. Event Grid notifica a tu Function App
4. Tu bot procesa el mensaje con IA y responde

## 📋 Prerrequisitos

- ✅ Azure Subscription activa
- ✅ Azure Communication Services configurado con WhatsApp
- ✅ Function App desplegada (tu bot actual)
- ✅ Azure CLI instalado y configurado

## 🚀 Configuración Paso a Paso

### 1. Instalar Dependencias de Configuración

```bash
pip install -r requirements-setup.txt
```

### 2. Ejecutar Script de Configuración Automática

```bash
python setup_event_grid.py
```

El script te pedirá:
- **Subscription ID**: Tu ID de suscripción de Azure
- **Resource Group**: El grupo de recursos donde están tus servicios
- **ACS Resource Name**: Nombre de tu recurso de Azure Communication Services
- **Function App Name**: Nombre de tu Function App
- **Location**: Ubicación (ej: westus2, eastus)

### 3. Configuración Manual en Azure Portal

Si prefieres hacerlo manualmente:

#### 3.1 Crear Event Grid Topic

1. Ve al [Portal de Azure](https://portal.azure.com)
2. Busca "Event Grid Topics"
3. Crea un nuevo topic:
   - **Nombre**: `tu-acs-whatsapp-events`
   - **Resource Group**: El mismo que tu ACS
   - **Location**: La misma que tu ACS
   - **Event Schema**: Event Grid Schema

#### 3.2 Crear Event Subscription

1. En tu Event Grid Topic, ve a "Event Subscriptions"
2. Crea una nueva suscripción:
   - **Nombre**: `acs-whatsapp-subscription`
   - **Event Schema**: Event Grid Schema
   - **Endpoint Type**: Web Hook
   - **Endpoint URL**: `https://tu-function-app.azurewebsites.net/runtime/webhooks/eventgrid?functionName=acs_event_grid_handler`
   - **Event Types**: 
     - `Microsoft.Communication.AdvancedMessageReceived`
     - `Microsoft.Communication.AdvancedMessageDeliveryStatusUpdated`
     - `Microsoft.Communication.AdvancedMessageReadStatusUpdated`

#### 3.3 Configurar ACS para Eventos

1. Ve a tu recurso de Azure Communication Services
2. Navega a "Events" o "Event Grid"
3. Crea una nueva suscripción de eventos:
   - **Topic**: El Event Grid Topic que creaste
   - **Event Types**: Selecciona los eventos de WhatsApp que quieres recibir

### 4. Configurar Variables de Entorno

Agrega estas variables a tu archivo `.env` o configuración de la Function App:

```bash
# Azure Communication Services
ACS_ENDPOINT=https://tu-acs-resource.communication.azure.com/
ACS_CHANNEL_ID=tu_channel_id
ACS_ACCESS_KEY=tu_access_key
ACS_CONNECTION_STRING=tu_connection_string

# Event Grid
EVENT_GRID_TOPIC_ENDPOINT=https://tu-topic.westus2-1.eventgrid.azure.net/api/events
EVENT_GRID_TOPIC_KEY=tu_topic_key
EVENT_GRID_WEBHOOK_SECRET=tu_webhook_secret
```

### 5. Obtener las Claves

#### Event Grid Topic Key:
1. Ve a tu Event Grid Topic
2. Navega a "Access Keys"
3. Copia la "Key 1"

#### ACS Access Key:
1. Ve a tu Azure Communication Services
2. Navega a "Keys"
3. Copia la "Primary Key"

## 🔧 Verificación

### 1. Probar la Función Localmente

```bash
# Envío de prueba
curl -X POST http://localhost:7071/api/acs_event_grid_handler \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "Microsoft.Communication.AdvancedMessageReceived",
    "data": {
      "message": {
        "type": "text",
        "content": {
          "text": "Hola bot"
        }
      },
      "from": {
        "phoneNumber": "+1234567890"
      }
    }
  }'
```

### 2. Verificar Logs

Revisa los logs de tu Function App para verificar que:
- Los eventos se están recibiendo correctamente
- Los mensajes se están procesando con IA
- Las respuestas se están enviando de vuelta

## 🐛 Solución de Problemas

### Error: "Event Grid subscription not found"
- Verifica que la Event Subscription esté creada correctamente
- Asegúrate de que la URL del webhook sea correcta

### Error: "ACS not sending events"
- Verifica que ACS esté configurado para enviar eventos al Event Grid Topic
- Revisa que los tipos de eventos estén habilitados

### Error: "Function not receiving events"
- Verifica que la función `acs_event_grid_handler` esté desplegada
- Revisa los logs de la Function App para errores

## 📊 Monitoreo

### Métricas Importantes:
- **Event Grid**: Eventos enviados/recibidos
- **Function App**: Ejecuciones exitosas/fallidas
- **ACS**: Mensajes enviados/recibidos

### Logs a Revisar:
- Event Grid delivery logs
- Function App execution logs
- ACS message logs

## 🔒 Seguridad

### Recomendaciones:
1. **Usa Managed Identity** cuando sea posible
2. **Rotación de claves** regular
3. **Validación de webhooks** con secretos
4. **Filtrado de eventos** por tipo y origen

### Configuración de Seguridad:
```bash
# Generar webhook secret
openssl rand -hex 32
```

## 📚 Recursos Adicionales

- [Azure Event Grid Documentation](https://docs.microsoft.com/en-us/azure/event-grid/)
- [Azure Communication Services Documentation](https://docs.microsoft.com/en-us/azure/communication-services/)
- [Azure Functions Event Grid Trigger](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-event-grid)

## 🆘 Soporte

Si tienes problemas:
1. Revisa los logs de Azure
2. Verifica la configuración paso a paso
3. Consulta la documentación oficial
4. Abre un issue en el repositorio 