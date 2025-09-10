"""
AI Chat Configuration

Configuration settings for the AI-driven chat system.
"""
import os
import logging
from typing import Optional, Dict, Any
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
from pydantic import Field

logger = logging.getLogger(__name__)


class AIConfig(BaseSettings):
    """Configuration for AI/LLM settings."""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    openai_temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(500, env="OPENAI_MAX_TOKENS")
    
    # LangChain Configuration
    langchain_api_key: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = Field("genascope-chat", env="LANGCHAIN_PROJECT")
    langchain_tracing_v2: bool = Field(True, env="LANGCHAIN_TRACING_V2")
    
    # Model fallback configuration
    backup_model: str = Field("gpt-4o-mini", env="BACKUP_MODEL")
    max_retries: int = Field(3, env="AI_MAX_RETRIES")
    request_timeout: int = Field(30, env="AI_REQUEST_TIMEOUT")
    
    # Circuit breaker configuration
    circuit_breaker_failure_threshold: int = Field(5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    circuit_breaker_recovery_timeout: int = Field(60, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")
    
    # Service availability
    fail_fast_on_startup: bool = Field(True, env="FAIL_FAST_ON_STARTUP")


class VectorStoreConfig(BaseSettings):
    """Configuration for vector stores and RAG."""
    
    # Vector store settings
    vector_store_type: str = Field("chroma", env="VECTOR_STORE_TYPE")  # chroma, faiss, pinecone
    vector_store_path: str = Field("./vector_db", env="VECTOR_STORE_PATH")
    embedding_model: str = Field("text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # RAG settings
    chunk_size: int = Field(1000, env="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="RAG_CHUNK_OVERLAP")
    max_retrievals: int = Field(5, env="RAG_MAX_RETRIEVALS")
    similarity_threshold: float = Field(0.7, env="RAG_SIMILARITY_THRESHOLD")
    
    # Pinecone configuration (if using Pinecone)
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = Field("genascope-knowledge", env="PINECONE_INDEX_NAME")


class ChatConfig(BaseSettings):
    """Configuration for chat behavior."""
    
    # Session limits
    max_conversation_turns: int = Field(20, env="MAX_CONVERSATION_TURNS")
    session_timeout_hours: int = Field(24, env="SESSION_TIMEOUT_HOURS")
    max_active_sessions_per_patient: int = Field(3, env="MAX_ACTIVE_SESSIONS_PER_PATIENT")
    
    # Message limits
    max_message_length: int = Field(2000, env="MAX_MESSAGE_LENGTH")
    min_message_length: int = Field(1, env="MIN_MESSAGE_LENGTH")
    
    # AI response settings
    response_timeout_seconds: int = Field(30, env="RESPONSE_TIMEOUT_SECONDS")
    min_confidence_threshold: float = Field(0.5, env="MIN_CONFIDENCE_THRESHOLD")
    
    # Content moderation
    enable_content_moderation: bool = Field(True, env="ENABLE_CONTENT_MODERATION")
    blocked_words: list = Field([], env="BLOCKED_WORDS")


class ExtractionConfig(BaseSettings):
    """Configuration for information extraction."""
    
    # NLP model settings
    spacy_model: str = Field("en_core_web_sm", env="SPACY_MODEL")
    enable_ner: bool = Field(True, env="ENABLE_NER")
    enable_regex_extraction: bool = Field(True, env="ENABLE_REGEX_EXTRACTION")
    enable_llm_extraction: bool = Field(True, env="ENABLE_LLM_EXTRACTION")
    
    # Extraction thresholds
    entity_confidence_threshold: float = Field(0.8, env="ENTITY_CONFIDENCE_THRESHOLD")
    validation_strictness: str = Field("medium", env="VALIDATION_STRICTNESS")  # low, medium, high
    
    # Performance settings
    extraction_timeout_seconds: int = Field(10, env="EXTRACTION_TIMEOUT_SECONDS")
    max_entities_per_message: int = Field(20, env="MAX_ENTITIES_PER_MESSAGE")


class SecurityConfig(BaseSettings):
    """Security configuration for AI chat."""
    
    # Data privacy
    anonymize_before_ai: bool = Field(True, env="ANONYMIZE_BEFORE_AI")
    mask_pii: bool = Field(True, env="MASK_PII")
    retain_original_messages: bool = Field(True, env="RETAIN_ORIGINAL_MESSAGES")
    
    # Audit logging
    enable_audit_logging: bool = Field(True, env="ENABLE_AUDIT_LOGGING")
    log_ai_requests: bool = Field(True, env="LOG_AI_REQUESTS")
    log_extraction_results: bool = Field(False, env="LOG_EXTRACTION_RESULTS")
    
    # Rate limiting
    max_requests_per_minute: int = Field(60, env="MAX_REQUESTS_PER_MINUTE")
    max_sessions_per_hour: int = Field(10, env="MAX_SESSIONS_PER_HOUR")


class CacheConfig(BaseSettings):
    """Configuration for caching."""
    
    # Redis configuration
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Cache settings
    enable_response_caching: bool = Field(True, env="ENABLE_RESPONSE_CACHING")
    response_cache_ttl: int = Field(3600, env="RESPONSE_CACHE_TTL")  # seconds
    
    enable_rag_caching: bool = Field(True, env="ENABLE_RAG_CACHING")
    rag_cache_ttl: int = Field(7200, env="RAG_CACHE_TTL")  # seconds
    
    enable_session_caching: bool = Field(True, env="ENABLE_SESSION_CACHING")
    session_cache_ttl: int = Field(1800, env="SESSION_CACHE_TTL")  # seconds


class MonitoringConfig(BaseSettings):
    """Configuration for monitoring and observability."""
    
    # Metrics
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_endpoint: str = Field("/metrics", env="METRICS_ENDPOINT")
    
    # Alerting thresholds
    high_response_time_ms: int = Field(5000, env="HIGH_RESPONSE_TIME_MS")
    low_confidence_threshold: float = Field(0.6, env="LOW_CONFIDENCE_THRESHOLD")
    error_rate_threshold: float = Field(0.05, env="ERROR_RATE_THRESHOLD")
    
    # Sentry configuration
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    sentry_environment: str = Field("development", env="SENTRY_ENVIRONMENT")


class ExternalToolsConfig(BaseSettings):
    """Configuration for external medical tools and calculators."""
    
    # Risk calculator APIs
    tyrer_cuzick_api_url: Optional[str] = Field(None, env="TYRER_CUZICK_API_URL")
    tyrer_cuzick_api_key: Optional[str] = Field(None, env="TYRER_CUZICK_API_KEY")
    
    gail_model_api_url: Optional[str] = Field(None, env="GAIL_MODEL_API_URL")
    gail_model_api_key: Optional[str] = Field(None, env="GAIL_MODEL_API_KEY")
    
    # External service timeouts
    external_api_timeout: int = Field(15, env="EXTERNAL_API_TIMEOUT")
    external_api_retries: int = Field(2, env="EXTERNAL_API_RETRIES")
    
    # Fallback behavior
    enable_mock_calculators: bool = Field(True, env="ENABLE_MOCK_CALCULATORS")


class AIChatSettings:
    """Main configuration class for AI chat system."""
    
    def __init__(self):
        self.ai = AIConfig()
        self.vector_store = VectorStoreConfig()
        self.chat = ChatConfig()
        self.extraction = ExtractionConfig()
        self.security = SecurityConfig()
        self.cache = CacheConfig()
        self.monitoring = MonitoringConfig()
        self.external_tools = ExternalToolsConfig()
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.ai.openai_api_key,
            "model": self.ai.openai_model,
            "temperature": self.ai.openai_temperature,
            "max_tokens": self.ai.openai_max_tokens,
            "request_timeout": self.ai.request_timeout
        }
    
    def get_vector_store_config(self) -> Dict[str, Any]:
        """Get vector store configuration dictionary."""
        return {
            "type": self.vector_store.vector_store_type,
            "path": self.vector_store.vector_store_path,
            "embedding_model": self.vector_store.embedding_model,
            "chunk_size": self.vector_store.chunk_size,
            "chunk_overlap": self.vector_store.chunk_overlap
        }
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """Get extraction configuration dictionary."""
        return {
            "spacy_model": self.extraction.spacy_model,
            "enable_ner": self.extraction.enable_ner,
            "enable_regex": self.extraction.enable_regex_extraction,
            "enable_llm": self.extraction.enable_llm_extraction,
            "confidence_threshold": self.extraction.entity_confidence_threshold
        }
    
    @property
    def environment(self) -> str:
        """Get the current environment."""
        return os.getenv("ENVIRONMENT", "development")
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    @property
    def is_openai_configured(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.ai.openai_api_key is not None and self.ai.openai_api_key.strip() != ""
    
    @property
    def should_use_mock_mode(self) -> bool:
        """
        Determine if mock mode should be used.
        Only allow mock mode in development/testing environments when OpenAI is not configured.
        """
        return (
            self.environment in ["development", "testing"] and
            not self.is_openai_configured
        )
    
    async def validate_openai_connection(self) -> bool:
        """
        Validate OpenAI connection by making a test request.
        Returns True if connection is valid, False otherwise.
        """
        if not self.is_openai_configured:
            return False
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.ai.openai_api_key)
            
            # Make a minimal test request
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Use efficient model for testing
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                timeout=5
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI connection validation failed: {e}")
            return False
    
    def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration."""
        return {
            "failure_threshold": self.ai.circuit_breaker_failure_threshold,
            "recovery_timeout": self.ai.circuit_breaker_recovery_timeout,
        }
    
    def validate_production_config(self) -> list[str]:
        """
        Validate configuration for production environment.
        Returns list of configuration errors.
        """
        errors = []
        
        if not self.is_openai_configured:
            errors.append("OpenAI API key is required in production")
        
        if self.should_use_mock_mode:
            errors.append("Mock mode is not allowed in production")
        
        if self.ai.fail_fast_on_startup is False:
            errors.append("fail_fast_on_startup should be enabled in production")
        
        if self.security.anonymize_before_ai is False:
            errors.append("anonymize_before_ai should be enabled in production")
        
        if self.security.enable_audit_logging is False:
            errors.append("enable_audit_logging should be enabled in production")
        
        return errors
    
    def get_environment_recommendations(self) -> Dict[str, Any]:
        """Get configuration recommendations based on environment."""
        if self.is_production():
            return {
                "fail_fast_on_startup": True,
                "anonymize_before_ai": True,
                "enable_audit_logging": True,
                "enable_metrics": True,
                "circuit_breaker_failure_threshold": 3,
                "mock_mode_allowed": False
            }
        elif self.environment == "staging":
            return {
                "fail_fast_on_startup": True,
                "anonymize_before_ai": True,
                "enable_audit_logging": True,
                "enable_metrics": True,
                "circuit_breaker_failure_threshold": 5,
                "mock_mode_allowed": False
            }
        else:  # development/testing
            return {
                "fail_fast_on_startup": False,
                "anonymize_before_ai": False,
                "enable_audit_logging": False,
                "enable_metrics": False,
                "circuit_breaker_failure_threshold": 10,
                "mock_mode_allowed": True
            }


# Mock response templates for different specialties
MOCK_RESPONSE_TEMPLATES = {
    "oncology": {
        "welcome": "Hello! I'm here to help with your breast cancer risk assessment. Let's start by gathering some basic information.",
        "follow_up": "Thank you for that information. {extracted_info} Can you tell me more about {next_topic}?",
        "assessment": "Based on our conversation, here's what I've learned: {summary}. Would you like to discuss next steps?",
        "closing": "Thank you for completing this assessment. Your information has been recorded for review."
    },
    "genetics": {
        "welcome": "Welcome to genetic counseling intake. I'll help gather information about your family history and concerns.",
        "follow_up": "I understand you mentioned {extracted_info}. Can you provide more details about {next_topic}?",
        "assessment": "Your family history shows: {summary}. This information will help determine appropriate genetic testing options.",
        "closing": "Thank you for providing this detailed family history. A genetic counselor will review your information."
    },
    "general": {
        "welcome": "Hello! I'm here to help with your health assessment. Let's begin.",
        "follow_up": "Thanks for sharing that. {extracted_info} What else should we discuss about {next_topic}?",
        "assessment": "Here's a summary of our conversation: {summary}. Are there other concerns you'd like to address?",
        "closing": "Thank you for completing this assessment. Your healthcare team will follow up as needed."
    }
}

# Create global settings instance
ai_chat_settings = AIChatSettings()


# Additional configuration templates for different assessment types
BRCA_SCREENING_CONFIG = {
    "strategy_name": "BRCA Risk Assessment",
    "ai_model_config": {
        "model_name": "gpt-5-nano",
        "temperature": 0.7,
        "max_tokens": 400
    },
    "extraction_rules": [
        {
            "entity_type": "age",
            "extraction_method": "regex",
            "pattern": r"\b(\d{1,3})\s*(?:years?\s*old|yo|y\.o\.)\b",
            "validation_rules": {"min_value": 18, "max_value": 100},
            "priority": 1
        },
        {
            "entity_type": "family_history",
            "extraction_method": "llm",
            "pattern": "Extract family history of cancer, including relation, cancer type, and age at diagnosis",
            "priority": 2
        },
        {
            "entity_type": "personal_history",
            "extraction_method": "llm",
            "pattern": "Extract personal medical history relevant to cancer risk",
            "priority": 3
        }
    ],
    "assessment_criteria": {
        "criteria_type": "brca_screening",
        "required_fields": ["age", "family_history"],
        "rules": [
            {
                "condition": "age >= 25 AND family_history.breast_cancer",
                "outcome": "meets_criteria",
                "confidence": 0.8
            }
        ],
        "risk_models": ["tyrer_cuzick"],
        "recommendations": {
            "meets_criteria": [
                "Consider genetic counseling",
                "Discuss BRCA1/2 testing"
            ],
            "does_not_meet": [
                "Continue routine screening",
                "Reassess family history changes"
            ]
        }
    },
    "required_information": [
        "age",
        "family_history",
        "personal_history",
        "pregnancy_history",
        "medication_history"
    ],
    "max_conversation_turns": 15
}

CARDIAC_RISK_CONFIG = {
    "strategy_name": "Cardiac Risk Assessment",
    "ai_model_config": {
        "model_name": "gpt-5-nano",
        "temperature": 0.6,
        "max_tokens": 350
    },
    "extraction_rules": [
        {
            "entity_type": "cardiovascular_symptoms",
            "extraction_method": "llm",
            "pattern": "Extract cardiovascular symptoms: chest pain, shortness of breath, palpitations, etc.",
            "priority": 1
        },
        {
            "entity_type": "risk_factors",
            "extraction_method": "llm",
            "pattern": "Extract cardiovascular risk factors: smoking, diabetes, hypertension, family history",
            "priority": 2
        }
    ],
    "assessment_criteria": {
        "criteria_type": "cardiac_risk",
        "required_fields": ["symptoms", "risk_factors", "age"],
        "rules": [
            {
                "condition": "chest_pain AND (age > 40 OR risk_factors.high)",
                "outcome": "urgent_evaluation",
                "confidence": 0.9
            }
        ],
        "risk_models": ["framingham"],
        "recommendations": {
            "urgent_evaluation": [
                "Seek immediate medical attention",
                "ECG and cardiac enzymes recommended"
            ],
            "routine_follow_up": [
                "Schedule appointment within 1-2 weeks",
                "Continue monitoring symptoms"
            ]
        }
    }
}


# Global configuration instance
_ai_config = None
_chat_config = None


def get_ai_chat_settings():
    """Get AI chat configuration settings."""
    global _ai_config, _chat_config
    
    if _ai_config is None:
        _ai_config = AIConfig()
    if _chat_config is None:
        _chat_config = ChatConfig()
    
    return _chat_config


def get_ai_config():
    """Get AI configuration settings."""
    global _ai_config
    
    if _ai_config is None:
        _ai_config = AIConfig()
    
    return _ai_config


def get_chat_config():
    """Get chat configuration settings."""
    global _chat_config
    
    if _chat_config is None:
        _chat_config = ChatConfig()
    
    return _chat_config
