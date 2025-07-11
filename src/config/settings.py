from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    # Azure
    azure_webjobs_storage: Optional[str] = Field(default=None, alias="AzureWebJobsStorage")
    azure_storage_connection_string: str = Field(alias="AZURE_STORAGE_CONNECTION_STRING")
    blob_account_name: str = Field(alias="BLOB_ACCOUNT_NAME")
    blob_account_key: str = Field(alias="BLOB_ACCOUNT_KEY")
    blob_container_name: str = Field(alias="BLOB_CONTAINER_NAME")
    queue_name: str = Field(default="doc-processing", alias="QUEUE_NAME")

    # OpenAI
    azure_openai_endpoint: str = Field(alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: Optional[str] = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_chat_deployment: str = Field(alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_chat_api_version: str = Field(alias="AZURE_OPENAI_CHAT_API_VERSION")
    azure_openai_chat_endpoint: str = Field(alias="AZURE_OPENAI_CHAT_ENDPOINT")
    azure_openai_embeddings_api_key: str = Field(alias="AZURE_OPENAI_EMBEDDINGS_API_KEY")
    azure_openai_embeddings_api_version: str = Field(alias="AZURE_OPENAI_EMBEDDINGS_API_VERSION")
    azure_openai_embeddings_endpoint: str = Field(alias="AZURE_OPENAI_EMBEDDINGS_ENDPOINT")
    openai_embeddings_engine_doc: str = Field(alias="OPENAI_EMBEDDINGS_ENGINE_DOC")

    # Redis
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: str = Field(alias="REDIS_PORT")
    redis_username: Optional[str] = Field(default="", alias="REDIS_USERNAME")
    redis_password: Optional[str] = Field(default="", alias="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, alias="REDIS_SSL")
    redis_connection_string: Optional[str] = Field(default=None, alias="REDIS_CONNECTION_STRING")

    # WhatsApp (unificado)
    whatsapp_token: str = Field(alias="WHATSAPP_TOKEN")
    whatsapp_verify_token: str = Field(alias="WHATSAPP_VERIFY_TOKEN")
    whatsapp_phone_number_id: str = Field(alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_version: str = Field(default="v18.0", alias="WHATSAPP_VERSION")

    # KeyVault & Insights
    azure_keyvault_url: str = Field(alias="AZURE_KEYVAULT_URL")
    applicationinsights_connection_string: str = Field(alias="APPLICATIONINSIGHTS_CONNECTION_STRING")

    # Computer Vision
    azure_computer_vision_endpoint: str = Field(alias="AZURE_COMPUTER_VISION_ENDPOINT")
    azure_computer_vision_api_key: str = Field(alias="AZURE_COMPUTER_VISION_API_KEY")

settings = Settings()

def get_settings() -> Settings:
    """
    Obtener la instancia de configuración.
    
    Returns:
        Settings: Instancia de configuración
    """
    return settings 