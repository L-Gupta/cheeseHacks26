import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Patient Follow-up Agent"
    DEBUG: bool = False
    
    # Database Settings (leave empty to use local SQLite for testing)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Twilio Settings
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Google Cloud Settings
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Vertex AI / Gemini Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")  # REST API; 429 on 2.5 → try gemini-1.5-flash-latest
    VERTEX_AI_MODEL: str = os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash")
    # Real Twilio calls: True = use Vertex (GCP), False = use Gemini REST API (key). Default False so key-only works.
    USE_VERTEX_FOR_CALLS: bool = os.getenv("USE_VERTEX_FOR_CALLS", "false").lower() in ("true", "1")
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENV: str = os.getenv("PINECONE_ENV", "")
    
    # Deepgram
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # Hostname (for Twilio Webhooks)
    HOST_DOMAIN: str = os.getenv("HOST_DOMAIN", "") # e.g. "my-app-xyz.a.run.app"

    # Load .env from project root (cheese/) so it works regardless of cwd
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    model_config = SettingsConfigDict(env_file=os.path.join(_root, ".env"))

settings = Settings()
