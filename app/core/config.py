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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
