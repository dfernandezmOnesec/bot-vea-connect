# bot-vea-connect

## Requisitos previos

- Python 3.12+
- Azure CLI (opcional, para despliegue y gestión de recursos)
- Azure Storage Account, Azure Functions, Azure Redis, Azure OpenAI configurados
- Acceso a las claves y endpoints de los servicios Azure
- (Opcional) Docker y Azure Storage Explorer

## Setup local paso a paso

1. **Clona el repositorio:**
   ```sh
   git clone <URL_DEL_REPO>
   cd bot-vea-connect
   ```

2. **Crea y activa un entorno virtual:**
   ```sh
   python -m venv venv
   # En Windows
   venv\Scripts\activate
   # En Linux/Mac
   source venv/bin/activate
   ```

3. **Instala las dependencias:**
   ```sh
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Copia y configura las variables de entorno:**
   - Copia el archivo `.env.example` a `.env` y completa los valores requeridos.
   - O configura `local.settings.json` para Azure Functions local.

5. **Configura los servicios de Azure:**
   - Asegúrate de tener los recursos de Azure necesarios y sus credenciales en las variables de entorno.

## Variables de entorno requeridas

Las principales variables (ver `.env.example` para la lista completa):

- `AZURE_STORAGE_CONNECTION_STRING`  
- `BLOB_ACCOUNT_NAME`  
- `BLOB_ACCOUNT_KEY`  
- `BLOB_CONTAINER_NAME`  
- `QUEUE_NAME`  
- `AZURE_OPENAI_ENDPOINT`  
- `AZURE_OPENAI_API_KEY`  
- `AZURE_OPENAI_CHAT_DEPLOYMENT`  
- `AZURE_OPENAI_CHAT_API_VERSION`  
- `REDIS_HOST`  
- `REDIS_PORT`  
- `REDIS_PASSWORD`  
- `WHATSAPP_TOKEN`  
- `WHATSAPP_VERIFY_TOKEN`  
- `WHATSAPP_PHONE_NUMBER_ID`  
- `ACCESS_TOKEN`  
- `VERIFY_TOKEN`  
- `RECIPIENT_WAID`  
- `AZURE_KEYVAULT_URL`  
- `APPLICATIONINSIGHTS_CONNECTION_STRING`  
- `COMPUTER_VISION_ENDPOINT`  
- `COMPUTER_VISION_KEY`  

Consulta `.env.example` para la lista y formato exacto.

## Cómo ejecutar tests

- **Tests unitarios:**
  ```sh
  pytest tests/unit
  ```
- **Tests de integración:**
  ```sh
  pytest tests/integration
  ```
- **Tests end-to-end (E2E):**
  ```sh
  pytest tests/e2e
  ```
- **Cobertura:**
  ```sh
  pytest --cov=src
  ```

## Cómo desplegar

1. **Login en Azure:**
   ```sh
   az login
   ```
2. **Publicar la Function App:**
   ```sh
   func azure functionapp publish <NOMBRE_DE_TU_FUNCTION_APP>
   ```
3. **Configura las variables de entorno en Azure:**
   - Usa el portal de Azure o el CLI para establecer las variables de entorno necesarias.

4. **Verifica el despliegue:**
   - Consulta los logs en Azure Portal o con `func azure functionapp logstream <NOMBRE_DE_TU_FUNCTION_APP>`

---

**¡Listo! Tu bot estará funcionando en Azure y puedes probarlo enviando mensajes de WhatsApp o subiendo documentos al Blob Storage configurado.**