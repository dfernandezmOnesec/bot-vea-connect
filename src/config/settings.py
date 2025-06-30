from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Azure
    azure_webjobs_storage: Optional[str] = Field(None, env="AzureWebJobsStorage")
    azure_storage_connection_string: str = Field(..., env="AZURE_STORAGE_CONNECTION_STRING")
    blob_account_name: str = Field(..., env="BLOB_ACCOUNT_NAME")
    blob_account_key: str = Field(..., env="BLOB_ACCOUNT_KEY")
    blob_container_name: str = Field(..., env="BLOB_CONTAINER_NAME")
    queue_name: str = Field(..., env="QUEUE_NAME")

    # OpenAI
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: Optional[str] = Field(None, env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_chat_deployment: str = Field(..., env="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_chat_api_version: str = Field(..., env="AZURE_OPENAI_CHAT_API_VERSION")
    azure_openai_chat_endpoint: str = Field(..., env="AZURE_OPENAI_CHAT_ENDPOINT")
    azure_openai_embeddings_api_key: str = Field(..., env="AZURE_OPENAI_EMBEDDINGS_API_KEY")
    azure_openai_embeddings_api_version: str = Field(..., env="AZURE_OPENAI_EMBEDDINGS_API_VERSION")
    azure_openai_embeddings_endpoint: str = Field(..., env="AZURE_OPENAI_EMBEDDINGS_ENDPOINT")
    openai_embeddings_engine_doc: str = Field(..., env="OPENAI_EMBEDDINGS_ENGINE_DOC")

    # Redis
    redis_host: str = Field(..., env="REDIS_HOST")
    redis_port: str = Field(..., env="REDIS_PORT")
    redis_username: Optional[str] = Field("", env="REDIS_USERNAME")
    redis_password: Optional[str] = Field("", env="REDIS_PASSWORD")
    redis_ssl: bool = Field(False, env="REDIS_SSL")
    redis_connection_string: Optional[str] = Field(None, env="REDIS_CONNECTION_STRING")

    # WhatsApp
    whatsapp_token: Optional[str] = Field(None, env="WHATSAPP_TOKEN")
    whatsapp_verify_token: Optional[str] = Field(None, env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_phone_number_id: Optional[str] = Field(None, env="WHATSAPP_PHONE_NUMBER_ID")
    access_token: str = Field(..., env="ACCESS_TOKEN")
    verify_token: str = Field(..., env="VERIFY_TOKEN")
    phone_number_id: str = Field(..., env="PHONE_NUMBER_ID")
    recipient_waid: str = Field(..., env="RECIPIENT_WAID")
    version: str = Field(..., env="VERSION")

    # KeyVault & Insights
    azure_keyvault_url: str = Field(..., env="AZURE_KEYVAULT_URL")
    applicationinsights_connection_string: str = Field(..., env="APPLICATIONINSIGHTS_CONNECTION_STRING")

    # Computer Vision
    azure_computer_vision_endpoint: Optional[str] = Field(None, env="AZURE_COMPUTER_VISION_ENDPOINT")
    azure_computer_vision_api_key: Optional[str] = Field(None, env="AZURE_COMPUTER_VISION_API_KEY")
    computer_vision_endpoint: str = Field(..., env="COMPUTER_VISION_ENDPOINT")
    computer_vision_key: str = Field(..., env="COMPUTER_VISION_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

settings = Settings()

def get_settings() -> Settings:
    """
    Obtener la instancia de configuración.
    
    Returns:
        Settings: Instancia de configuración
    """
    return settings 