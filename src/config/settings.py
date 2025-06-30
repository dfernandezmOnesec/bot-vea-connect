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

    # WhatsApp
    access_token: str = Field(..., env="ACCESS_TOKEN")
    verify_token: str = Field(..., env="VERIFY_TOKEN")
    phone_number_id: str = Field(..., env="PHONE_NUMBER_ID")
    recipient_waid: str = Field(..., env="RECIPIENT_WAID")
    version: str = Field(..., env="VERSION")

    # KeyVault & Insights
    azure_keyvault_url: str = Field(..., env="AZURE_KEYVAULT_URL")
    applicationinsights_connection_string: str = Field(..., env="APPLICATIONINSIGHTS_CONNECTION_STRING")

    # Computer Vision
    computer_vision_endpoint: str = Field(..., env="COMPUTER_VISION_ENDPOINT")
    computer_vision_key: str = Field(..., env="COMPUTER_VISION_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

settings = Settings() 