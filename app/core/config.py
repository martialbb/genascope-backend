from typing import List
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings
    """
    # Database
    DATABASE_URI: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"  # Default JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:4321"]
    
    # Lab API
    LAB_API_KEY: str
    LAB_API_URL: str
    
    # Frontend URL (for invite links, etc.)
    FRONTEND_URL: str = "http://localhost:4321"
    
    # Email configuration
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@cancer-genix.com"
    EMAIL_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
