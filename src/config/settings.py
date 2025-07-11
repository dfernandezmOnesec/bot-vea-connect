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
    azure_storage_connection_string: Optional[str] = Field(default=None, alias="AZURE_STORAGE_CONNECTION_STRING")
    blob_account_name: Optional[str] = Field(default=None, alias="BLOB_ACCOUNT_NAME")
    blob_account_key: Optional[str] = Field(default=None, alias="BLOB_ACCOUNT_KEY")
    blob_container_name: Optional[str] = Field(default=None, alias="BLOB_CONTAINER_NAME")
    queue_name: Optional[str] = Field(default="doc-processing", alias="QUEUE_NAME")

    # OpenAI
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: Optional[str] = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_chat_deployment: Optional[str] = Field(default=None, alias="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_chat_api_version: Optional[str] = Field(default=None, alias="AZURE_OPENAI_CHAT_API_VERSION")
    azure_openai_chat_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_CHAT_ENDPOINT")
    azure_openai_embeddings_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_EMBEDDINGS_API_KEY")
    azure_openai_embeddings_api_version: Optional[str] = Field(default=None, alias="AZURE_OPENAI_EMBEDDINGS_API_VERSION")
    azure_openai_embeddings_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_EMBEDDINGS_ENDPOINT")
    openai_embeddings_engine_doc: Optional[str] = Field(default=None, alias="OPENAI_EMBEDDINGS_ENGINE_DOC")

    # Redis
    redis_host: Optional[str] = Field(default=None, alias="REDIS_HOST")
    redis_port: Optional[str] = Field(default=None, alias="REDIS_PORT")
    redis_username: Optional[str] = Field(default=None, alias="REDIS_USERNAME")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_ssl: Optional[bool] = Field(default=False, alias="REDIS_SSL")
    redis_connection_string: Optional[str] = Field(default=None, alias="REDIS_CONNECTION_STRING")

    # WhatsApp (unificado)
    whatsapp_token: Optional[str] = Field(default=None, alias="WHATSAPP_TOKEN")
    whatsapp_verify_token: Optional[str] = Field(default=None, alias="WHATSAPP_VERIFY_TOKEN")
    whatsapp_phone_number_id: Optional[str] = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_version: Optional[str] = Field(default="v18.0", alias="WHATSAPP_VERSION")

    # KeyVault & Insights
    azure_keyvault_url: Optional[str] = Field(default=None, alias="AZURE_KEYVAULT_URL")
    applicationinsights_connection_string: Optional[str] = Field(default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING")

    # Computer Vision
    azure_computer_vision_endpoint: Optional[str] = Field(default=None, alias="AZURE_COMPUTER_VISION_ENDPOINT")
    azure_computer_vision_api_key: Optional[str] = Field(default=None, alias="AZURE_COMPUTER_VISION_API_KEY")

    # Azure Communication Services (ACS)
    acs_endpoint: Optional[str] = Field(default=None, alias="ACS_ENDPOINT")
    acs_channel_id: Optional[str] = Field(default=None, alias="ACS_CHANNEL_ID")
    acs_access_key: Optional[str] = Field(default=None, alias="ACS_ACCESS_KEY")
    acs_connection_string: Optional[str] = Field(default=None, alias="ACS_CONNECTION_STRING")

    # Event Grid
    event_grid_topic_endpoint: Optional[str] = Field(default=None, alias="EVENT_GRID_TOPIC_ENDPOINT")
    event_grid_topic_key: Optional[str] = Field(default=None, alias="EVENT_GRID_TOPIC_KEY")
    event_grid_webhook_secret: Optional[str] = Field(default=None, alias="EVENT_GRID_WEBHOOK_SECRET")

settings = Settings()

def get_settings() -> Settings:
    """
    Get the settings instance.
    Returns:
        Settings: Settings instance
    """
    return settings 