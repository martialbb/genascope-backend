"""
AI Chat Session Models

Database models for AI-driven chat sessions, messages, and analytics.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class SessionType(str, Enum):
    """Types of chat sessions."""
    screening = "screening"
    assessment = "assessment"
    follow_up = "follow_up"
    consultation = "consultation"


class SessionStatus(str, Enum):
    """Status of chat sessions."""
    active = "active"
    completed = "completed"
    paused = "paused"
    error = "error"
    cancelled = "cancelled"


class MessageRole(str, Enum):
    """Role of message sender."""
    user = "user"
    assistant = "assistant"
    system = "system"


class MessageType(str, Enum):
    """Type of chat message."""
    question = "question"
    response = "response"
    summary = "summary"
    assessment = "assessment"
    clarification = "clarification"


class ExtractionMethod(str, Enum):
    """Method for extracting information."""
    llm = "llm"
    regex = "regex"
    ner = "ner"
    hybrid = "hybrid"


class AIChatSession(Base):
    """AI-driven chat session with a patient."""
    __tablename__ = "ai_chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("chat_strategies.id"), nullable=False)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    
    # Session configuration
    session_type = Column(ENUM(SessionType, name='sessiontype'), nullable=False)
    status = Column(ENUM(SessionStatus, name='sessionstatus'), nullable=False, default=SessionStatus.active.value)
    
    # Context and state
    chat_context = Column(JSON)  # Current conversation state
    extracted_data = Column(JSON)  # Structured information extracted
    assessment_results = Column(JSON)  # AI assessment outcomes
    strategy_snapshot = Column(JSON)  # Configuration at session start
    
    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("ChatStrategy", back_populates="chat_sessions")
    patient = relationship("Patient", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    analytics = relationship("SessionAnalytics", back_populates="session", uselist=False)
    
    def __repr__(self):
        return f"<AIChatSession(id={self.id}, type={self.session_type}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": str(self.id),
            "strategy_id": str(self.strategy_id),
            "patient_id": str(self.patient_id),
            "session_type": self.session_type,
            "status": self.status,
            "chat_context": self.chat_context,
            "extracted_data": self.extracted_data,
            "assessment_results": self.assessment_results,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


class ChatMessage(Base):
    """Individual message in a chat session."""
    __tablename__ = "ai_chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("ai_chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(ENUM(MessageRole, name='messagerole'), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(ENUM(MessageType, name='messagetype'), nullable=False)
    
    # AI processing metadata
    prompt_template = Column(Text)  # Template used for generation
    rag_sources = Column(JSON)  # Knowledge sources referenced
    confidence_score = Column(Float)  # AI confidence in response (0.0-1.0)
    
    # Information extraction
    extracted_entities = Column(JSON)  # NER results
    extracted_intent = Column(String(100))  # Intent classification
    
    # Performance metrics
    processing_time_ms = Column(Integer)  # Time to generate response
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    session = relationship("AIChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, type={self.message_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "role": self.role,
            "content": self.content,
            "message_type": self.message_type,
            "confidence_score": self.confidence_score,
            "extracted_entities": self.extracted_entities,
            "extracted_intent": self.extracted_intent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ExtractionRule(Base):
    """Rules for extracting information from patient responses."""
    __tablename__ = "ai_extraction_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey("chat_strategies.id"), nullable=False)
    
    # Rule definition
    entity_type = Column(String(100), nullable=False)  # age, family_history, symptoms
    extraction_method = Column(ENUM(ExtractionMethod, name='extractionmethod'), nullable=False)
    pattern = Column(Text)  # Regex pattern or LLM prompt
    validation_rules = Column(JSON)  # Data validation criteria
    
    # Priority and conditions
    priority = Column(Integer, nullable=False, default=1)
    trigger_conditions = Column(JSON)  # When to apply this rule
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("ChatStrategy", back_populates="extraction_rules")
    
    def __repr__(self):
        return f"<ExtractionRule(id={self.id}, entity_type={self.entity_type}, method={self.extraction_method})>"


class SessionAnalytics(Base):
    """Analytics and metrics for chat sessions."""
    __tablename__ = "ai_session_analytics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("ai_chat_sessions.id"), nullable=False)
    
    # Conversation metrics
    total_messages = Column(Integer, nullable=False, default=0)
    conversation_duration_seconds = Column(Integer)
    completion_rate = Column(Float)  # Percentage of required info collected
    
    # Quality metrics
    extraction_accuracy = Column(Float)  # Accuracy of information extraction
    patient_satisfaction_score = Column(Float)  # If collected via feedback
    ai_confidence_avg = Column(Float)  # Average AI confidence across messages
    
    # Outcome metrics
    criteria_met = Column(Boolean)  # Whether assessment criteria were met
    recommendations_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("AIChatSession", back_populates="analytics")
    
    def __repr__(self):
        return f"<SessionAnalytics(session_id={self.session_id}, completion_rate={self.completion_rate})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "session_id": str(self.session_id),
            "total_messages": self.total_messages,
            "conversation_duration_seconds": self.conversation_duration_seconds,
            "completion_rate": self.completion_rate,
            "extraction_accuracy": self.extraction_accuracy,
            "patient_satisfaction_score": self.patient_satisfaction_score,
            "ai_confidence_avg": self.ai_confidence_avg,
            "criteria_met": self.criteria_met,
            "recommendations_count": self.recommendations_count
        }


class DocumentChunk(Base):
    """Document chunk with vector embedding for RAG."""
    __tablename__ = "ai_document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_source_id = Column(String, ForeignKey("knowledge_sources.id"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Vector embedding (pgvector)
    embedding = Column(Text)  # Will store as text for now, would be Vector(1536) with pgvector
    
    # Metadata
    chunk_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    knowledge_source = relationship("KnowledgeSource", backref="document_chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, chunk_index={self.chunk_index})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "id": str(self.id),
            "knowledge_source_id": self.knowledge_source_id,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "chunk_metadata": self.chunk_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Add relationships to existing models
def add_ai_chat_relationships():
    """Add AI chat relationships to existing models."""
    
    # Relationships are defined in chat_configuration.py to avoid circular imports
    
    # Add to Patient model (assuming it exists)
    try:
        from app.models.patient import Patient
        Patient.chat_sessions = relationship("AIChatSession", back_populates="patient")
    except ImportError:
        # Patient model doesn't exist yet
        pass
