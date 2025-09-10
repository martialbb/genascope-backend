"""
AI Chat Session Schemas

Pydantic schemas for AI-driven chat sessions, messages, and related functionality.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from pydantic import BaseModel, Field, validator

from app.models.ai_chat import SessionType, SessionStatus, MessageRole, MessageType, ExtractionMethod


# Request/Response Schemas

class StartChatRequest(BaseModel):
    """Request to start a new chat session."""
    strategy_id: str = Field(..., description="ID of the chat strategy to use")
    patient_id: str = Field(..., description="ID of the patient")
    session_type: SessionType = Field(SessionType.screening.value, description="Type of chat session")
    initial_context: Optional[Dict[str, Any]] = Field(None, description="Initial context for the chat")

    class Config:
        json_json_schema_extra = {
            "example": {
                "strategy_id": "550e8400-e29b-41d4-a716-446655440000",
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "session_type": "screening",
                "initial_context": {
                    "referral_reason": "Breast cancer risk assessment",
                    "appointment_type": "genetic_counseling"
                }
            }
        }


class SendMessageRequest(BaseModel):
    """Request to send a message in a chat session."""
    message: str = Field(..., min_length=1, max_length=2000, description="Patient's message")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

    class Config:
        json_json_schema_extra = {
            "example": {
                "message": "My mother had breast cancer when she was 45 years old.",
                "message_metadata": {
                    "input_method": "text",
                    "client_timestamp": "2025-06-29T12:00:00Z"
                }
            }
        }


class ChatSessionResponse(BaseModel):
    """Response schema for chat session."""
    id: str
    strategy_id: str
    patient_id: str
    session_type: SessionType
    status: SessionStatus
    
    # Context and state
    chat_context: Optional[Dict[str, Any]]
    extracted_data: Optional[Dict[str, Any]]
    assessment_results: Optional[Dict[str, Any]]
    
    # Timestamps
    started_at: datetime
    completed_at: Optional[datetime]
    last_activity: datetime
    
    # Computed fields
    message_count: Optional[int] = Field(None, description="Total number of messages in session")
    progress_percentage: Optional[float] = Field(None, description="Completion progress (0-100)")
    initial_message: Optional[str] = Field(None, description="Initial proactive message from AI assistant")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "strategy_id": "550e8400-e29b-41d4-a716-446655440001",
                "patient_id": "550e8400-e29b-41d4-a716-446655440002",
                "session_type": "screening",
                "status": "active",
                "chat_context": {
                    "goal": "Assess breast cancer risk",
                    "collected_data": {"age": 35, "family_history": True},
                    "progress": 60
                },
                "started_at": "2025-06-29T12:00:00Z",
                "last_activity": "2025-06-29T12:15:00Z",
                "message_count": 8,
                "progress_percentage": 60.0
            }
        }


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    id: str
    session_id: str
    role: MessageRole
    content: str
    message_type: MessageType
    created_at: datetime
    
    # AI processing metadata
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    rag_sources: Optional[List[Dict[str, Any]]] = Field(None, description="Knowledge sources used")
    processing_time_ms: Optional[int] = Field(None, description="Time taken to generate response")
    
    # Information extraction
    extracted_entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities from message")
    extracted_intent: Optional[str] = Field(None, description="Detected intent")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "role": "assistant",
                "content": "Thank you for sharing that information. Can you tell me what type of breast cancer your mother had?",
                "message_type": "question",
                "created_at": "2025-06-29T12:15:00Z",
                "confidence_score": 0.95,
                "processing_time_ms": 1250,
                "extracted_entities": {
                    "family_member": "mother",
                    "cancer_type": "breast",
                    "age_at_diagnosis": 45
                }
            }
        }


class SessionAnalyticsResponse(BaseModel):
    """Response schema for session analytics."""
    session_id: str
    total_messages: int
    conversation_duration_seconds: Optional[int]
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    ai_confidence_avg: Optional[float] = Field(None, ge=0.0, le=1.0)
    criteria_met: Optional[bool]
    recommendations_count: int

    class Config:
        from_attributes = True


# Configuration Schemas

class AIModelConfig(BaseModel):
    """Configuration for AI model settings."""
    model_name: str = Field("gpt-4", description="LLM model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(500, ge=1, le=4000, description="Maximum tokens in response")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 300,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }


class ExtractionRuleConfig(BaseModel):
    """Configuration for information extraction rules."""
    entity_type: str = Field(..., description="Type of entity to extract")
    extraction_method: ExtractionMethod = Field(..., description="Method for extraction")
    pattern: Optional[str] = Field(None, description="Regex pattern or LLM prompt")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation criteria")
    priority: int = Field(1, ge=1, le=10, description="Rule priority (1=highest)")
    trigger_conditions: Optional[Dict[str, Any]] = Field(None, description="When to apply rule")

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "age",
                "extraction_method": "regex",
                "pattern": r"\\b(\\d{1,3})\\s*(?:years?\\s*old|yo|y\\.o\\.)\\b",
                "validation_rules": {"min_value": 0, "max_value": 150},
                "priority": 1,
                "trigger_conditions": {"message_contains": ["age", "old", "years"]}
            }
        }


class AssessmentCriteria(BaseModel):
    """Criteria for assessing patient data."""
    criteria_type: str = Field(..., description="Type of assessment criteria")
    required_fields: List[str] = Field(..., description="Required data fields")
    rules: List[Dict[str, Any]] = Field(..., description="Assessment rules")
    risk_models: Optional[List[str]] = Field(None, description="Risk calculation models to use")
    recommendations: Dict[str, List[str]] = Field(..., description="Recommendations based on outcomes")

    class Config:
        json_schema_extra = {
            "example": {
                "criteria_type": "brca_screening",
                "required_fields": ["age", "family_history", "personal_history"],
                "rules": [
                    {
                        "condition": "age >= 25 AND family_history.breast_cancer",
                        "outcome": "meets_criteria",
                        "confidence": 0.8
                    }
                ],
                "risk_models": ["tyrer_cuzick", "gail_model"],
                "recommendations": {
                    "meets_criteria": [
                        "Consider genetic counseling",
                        "Discuss genetic testing options"
                    ],
                    "does_not_meet": [
                        "Continue routine screening",
                        "Reassess in 5 years"
                    ]
                }
            }
        }


class ChatStrategyAIConfig(BaseModel):
    """AI configuration for chat strategies."""
    ai_model_config: AIModelConfig
    rag_enabled: bool = Field(True, description="Enable retrieval-augmented generation")
    extraction_rules: List[ExtractionRuleConfig] = Field([], description="Information extraction rules")
    assessment_criteria: AssessmentCriteria
    required_information: List[str] = Field(..., description="Required information to collect")
    max_conversation_turns: int = Field(20, ge=1, le=100, description="Maximum conversation turns")

    class Config:
        json_schema_extra = {
            "example": {
                "ai_model_config": {
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 300
                },
                "rag_enabled": True,
                "extraction_rules": [
                    {
                        "entity_type": "age",
                        "extraction_method": "regex",
                        "pattern": r"\\b(\\d{1,3})\\s*(?:years?\\s*old)\\b",
                        "priority": 1
                    }
                ],
                "assessment_criteria": {
                    "criteria_type": "brca_screening",
                    "required_fields": ["age", "family_history"],
                    "rules": [],
                    "recommendations": {}
                },
                "required_information": ["age", "family_history", "personal_history"],
                "max_conversation_turns": 15
            }
        }


# Assessment and Results Schemas

class RiskScore(BaseModel):
    """Risk score calculation result."""
    model_name: str = Field(..., description="Name of the risk model")
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Risk percentage")
    interpretation: str = Field(..., description="Human-readable interpretation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in calculation")

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "tyrer_cuzick",
                "score": 0.15,
                "score_percentage": 15.0,
                "interpretation": "15% lifetime risk of breast cancer",
                "confidence": 0.85
            }
        }


class AssessmentResult(BaseModel):
    """Result of criteria assessment."""
    meets_criteria: bool = Field(..., description="Whether patient meets criteria")
    criteria_checked: List[str] = Field(..., description="List of criteria that were evaluated")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in assessment")
    reasoning: str = Field(..., description="Explanation of the assessment")
    risk_scores: List[RiskScore] = Field([], description="Calculated risk scores")
    recommendations: List[str] = Field(..., description="Personalized recommendations")
    next_steps: List[str] = Field(..., description="Suggested next steps")

    class Config:
        json_schema_extra = {
            "example": {
                "meets_criteria": True,
                "criteria_checked": ["age_criteria", "family_history_criteria"],
                "confidence": 0.85,
                "reasoning": "Patient meets age and family history criteria for genetic counseling",
                "risk_scores": [
                    {
                        "model_name": "tyrer_cuzick",
                        "score": 0.15,
                        "score_percentage": 15.0,
                        "interpretation": "15% lifetime risk",
                        "confidence": 0.85
                    }
                ],
                "recommendations": [
                    "Schedule genetic counseling appointment",
                    "Consider BRCA1/2 testing"
                ],
                "next_steps": [
                    "Referral to genetic counselor",
                    "Insurance pre-authorization for testing"
                ]
            }
        }


# List and Search Schemas

class ChatSessionListRequest(BaseModel):
    """Request parameters for listing chat sessions."""
    patient_id: Optional[str] = Field(None, description="Filter by patient ID")
    strategy_id: Optional[str] = Field(None, description="Filter by strategy ID")
    session_type: Optional[SessionType] = Field(None, description="Filter by session type")
    status: Optional[SessionStatus] = Field(None, description="Filter by status")
    date_from: Optional[datetime] = Field(None, description="Filter sessions from this date")
    date_to: Optional[datetime] = Field(None, description="Filter sessions to this date")
    skip: int = Field(0, ge=0, description="Number of sessions to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of sessions to return")


class ChatSessionListResponse(BaseModel):
    """Response for listing chat sessions."""
    sessions: List[ChatSessionResponse]
    total_count: int = Field(..., description="Total number of sessions matching criteria")
    skip: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [],
                "total_count": 150,
                "skip": 0,
                "limit": 20
            }
        }


# Error Schemas

class ChatErrorResponse(BaseModel):
    """Error response for chat operations."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    session_id: Optional[str] = Field(None, description="Session ID if applicable")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "SESSION_NOT_FOUND",
                "error_message": "The specified chat session could not be found",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "details": {
                    "requested_session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2025-06-29T12:00:00Z"
                }
            }
        }


# Utility Schemas

class AIResponse(BaseModel):
    """Internal schema for AI response processing."""
    content: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    prompt_used: Optional[str] = None
    rag_sources: Optional[List[Dict[str, Any]]] = None
    processing_time_ms: Optional[int] = None
    extracted_entities: Optional[Dict[str, Any]] = None
    assessment_data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Thank you for that information. Can you tell me more about your family history?",
                "confidence": 0.92,
                "prompt_used": "Generate follow-up question about family history",
                "rag_sources": [
                    {
                        "source_id": "brca-guidelines-2024",
                        "relevance_score": 0.85,
                        "content_snippet": "Family history is a key factor..."
                    }
                ],
                "processing_time_ms": 1200
            }
        }
