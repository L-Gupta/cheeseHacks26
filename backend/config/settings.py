import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Patient Follow-up Agent"
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+pg8000://user:password@localhost/dbname")
    
    # Twilio Settings
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Google Cloud Settings
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Vertex AI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    VERTEX_AI_MODEL: str = os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash")
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENV: str = os.getenv("PINECONE_ENV", "")
    
    # Deepgram
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # Hostname (for Twilio Webhooks)
    HOST_DOMAIN: str = os.getenv("HOST_DOMAIN", "") # e.g. "my-app-xyz.a.run.app"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
