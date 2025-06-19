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
    
    # File upload configuration
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB default
    
    # Storage configuration
    STORAGE_PROVIDER: str = "local"  # local, s3, minio, gcp
    STORAGE_BUCKET: str = "knowledge-sources"
    STORAGE_BASE_PATH: str = "/tmp/genascope_storage"  # For local storage
    
    # AWS S3 configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-west-2"
    AWS_S3_BUCKET: str = ""
    
    # AWS Role-based authentication (preferred over access keys)
    AWS_ROLE_ARN: str = ""
    AWS_ROLE_SESSION_NAME: str = "genascope-backend-session"
    AWS_ROLE_EXTERNAL_ID: str = ""  # Optional external ID for cross-account access
    
    # MinIO configuration  
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = ""
    MINIO_SECURE: bool = True
    
    # GCP configuration
    GCP_PROJECT_ID: str = ""
    GCP_STORAGE_BUCKET: str = ""
    GCP_CREDENTIALS_PATH: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Email configuration
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@cancer-genix.com"
    EMAIL_ENABLED: bool = False
    
    class Config:
        env_file = [".env.local", ".env"]  # Load .env.local first, then .env as fallback
        case_sensitive = True

# Create settings instance
settings = Settings()
