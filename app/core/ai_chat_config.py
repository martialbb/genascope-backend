"""
AI Chat Configuration

Configuration settings for the AI-driven chat system.
"""
import os
from typing import Optional, Dict, Any
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
from pydantic import Field


class AIConfig(BaseSettings):
    """Configuration for AI/LLM settings."""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(500, env="OPENAI_MAX_TOKENS")
    
    # LangChain Configuration
    langchain_api_key: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = Field("genascope-chat", env="LANGCHAIN_PROJECT")
    langchain_tracing_v2: bool = Field(True, env="LANGCHAIN_TRACING_V2")
    
    # Model fallback configuration
    backup_model: str = Field("gpt-3.5-turbo", env="BACKUP_MODEL")
    max_retries: int = Field(3, env="AI_MAX_RETRIES")
    request_timeout: int = Field(30, env="AI_REQUEST_TIMEOUT")


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
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return os.getenv("ENVIRONMENT", "development") == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return os.getenv("ENVIRONMENT", "development") == "production"


# Global settings instance (lazy initialization)
_ai_chat_settings = None

def get_ai_chat_settings() -> AIChatSettings:
    """Get the global AI chat settings instance."""
    global _ai_chat_settings
    if _ai_chat_settings is None:
        _ai_chat_settings = AIChatSettings()
    return _ai_chat_settings


# Template configurations for common scenarios

BREAST_CANCER_SCREENING_CONFIG = {
    "strategy_name": "Breast Cancer Risk Assessment",
    "ai_model_config": {
        "model_name": "gpt-4",
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
        "model_name": "gpt-4",
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
