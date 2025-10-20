from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: PostgresDsn
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Clinic Triage System"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth (opcjonalne)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # ML Models - ścieżki relatywne do roota projektu
    MODEL_PATH: str = "../models"
    SCALER_PATH: str = "../models/scaler.pkl"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
