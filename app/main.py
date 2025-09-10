from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api import api_router
from app.core.ai_chat_config import ai_chat_settings
from app.db.database import get_db
import logging

app = FastAPI(
    title="Genascope API",
    description="""
    Backend API for Genascope cancer screening platform.
    
    ## Features
    
    * **Chat Assessment**: Conduct interactive patient assessments
    * **Accounts Management**: Create, list, update and delete organization accounts
    * **User Management**: Comprehensive CRUD operations for users with role-based access
    * **Eligibility Analysis**: Process assessment results to determine screening eligibility
    * **Appointments**: Schedule and manage appointments
    * **Laboratory Integration**: Order and track test results
    
    ## Authentication
    
    Most endpoints require authentication using JWT Bearer tokens.
    Login via POST /api/auth/token to receive an access token.
    """,
    version="0.2.0",
    contact={
        "name": "Genascope Support",
        "email": "support@genascope.example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://genascope.example.com/license",
    },
    swagger_ui_parameters={"defaultModelsExpandDepth": 1},
    redirect_slashes=False,  # Disable automatic trailing slash redirects
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4321", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4321",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    # Ensure CORS headers are added even to error responses
    allow_origin_regex="",  # Allow origins based on regex pattern if needed
)

# Include API router
app.include_router(api_router)

@app.get("/health", tags=["system"])
async def health_check():
    """
    Simple health check endpoint to verify API is running.
    Returns status 'ok' when the service is operational.
    """
    return {"status": "ok"}

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with fail-fast approach for production."""
    
    logger.info(f"Starting application in {ai_chat_settings.environment} environment")
    
    # Validate production configuration
    if ai_chat_settings.is_production():
        config_errors = ai_chat_settings.validate_production_config()
        if config_errors:
            logger.error("Production configuration validation failed:")
            for error in config_errors:
                logger.error(f"  - {error}")
            raise RuntimeError(
                f"Invalid production configuration: {'; '.join(config_errors)}"
            )
        logger.info("Production configuration validation passed")
    
    # Check AI configuration - fail fast in production
    if not ai_chat_settings.is_openai_configured:
        if ai_chat_settings.is_production():
            logger.error("OpenAI API key not configured in production environment")
            raise RuntimeError(
                "Missing required OpenAI configuration. "
                "Set OPENAI_API_KEY environment variable."
            )
        else:
            logger.warning(
                "OpenAI API key not configured. Running in development mock mode. "
                "Set OPENAI_API_KEY environment variable for full AI functionality."
            )
    
    # Validate OpenAI connection if configured and fail_fast is enabled
    if ai_chat_settings.is_openai_configured and ai_chat_settings.ai.fail_fast_on_startup:
        logger.info("Validating OpenAI connection...")
        if not await ai_chat_settings.validate_openai_connection():
            error_msg = "OpenAI connection validation failed"
            if ai_chat_settings.is_production():
                logger.error(error_msg)
                raise RuntimeError(f"{error_msg}. Check API key and network connectivity.")
            else:
                logger.warning(f"{error_msg}. Continuing in mock mode for development.")
    
    # Only use mock mode in development/testing environments
    if ai_chat_settings.should_use_mock_mode:
        if ai_chat_settings.is_production():
            logger.error("Mock mode attempted in production environment")
            raise RuntimeError("Mock mode not allowed in production")
        else:
            logger.info("AI Chat system initialized in MOCK MODE (development only)")
    else:
        logger.info("AI Chat system initialized with OpenAI integration")
    
    # Initialize database extensions
    from app.db.database import engine
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector extension initialized")
        except Exception as e:
            logger.warning(f"pgvector extension initialization failed: {e}")
    
    # Initialize services based on configuration and environment
    if not ai_chat_settings.should_use_mock_mode:
        try:
            # Initialize real AI services
            from app.services.rag_service import RAGService
            rag_service = RAGService(next(get_db()))
            logger.info("RAG service initialized")
            
            # TODO: Knowledge processing service will be added later
            logger.info("Knowledge processing service skipped (not implemented)")
            
        except Exception as e:
            error_msg = f"Failed to initialize AI services: {e}"
            logger.error(error_msg)
            
            if ai_chat_settings.is_production():
                # In production, fail fast
                raise RuntimeError(f"Critical service initialization failed: {e}")
            else:
                # In development, warn but continue
                logger.warning("AI services failed to initialize, continuing in mock mode")
    else:
        logger.info("Skipping AI service initialization (mock mode)")
    
    logger.info("Application startup completed successfully")
