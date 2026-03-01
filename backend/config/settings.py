import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Patient Follow-up Agent"
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Twilio Settings
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    DOCTOR_ALERT_PHONE_NUMBER: str = ""
    
    # Google Cloud Settings
    GOOGLE_PROJECT_ID: str = ""
    GCP_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Vertex AI Settings
    VERTEX_AI_MODEL: str = "gemini-2.5-flash"
    
    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENV: str = ""

    # Hostname (for Twilio Webhooks)
    HOST_DOMAIN: str = "" # e.g. "my-app-xyz.a.run.app"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_value(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if lowered in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

settings = Settings()

if settings.GOOGLE_APPLICATION_CREDENTIALS:
    credentials_path = Path(settings.GOOGLE_APPLICATION_CREDENTIALS)
    if not credentials_path.is_absolute():
        credentials_path = ROOT_DIR / credentials_path
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
    if not credentials_path.exists():
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS path does not exist on this machine.")
if settings.GOOGLE_PROJECT_ID:
    os.environ["GOOGLE_PROJECT_ID"] = settings.GOOGLE_PROJECT_ID
