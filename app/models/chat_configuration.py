"""Chat Configuration database models - cleaned up version."""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


class ChatStrategy(Base):
    """Chat strategy model for configurable patient screening workflows"""
    __tablename__ = "chat_strategies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    patient_introduction = Column(Text, nullable=True)
    specialty = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), nullable=True)  # User who created the strategy
    version = Column(Integer, nullable=False, default=1)  # Version number for strategy revisions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("AIChatSession", back_populates="strategy")
    extraction_rules = relationship("ExtractionRule", back_populates="strategy", cascade="all, delete-orphan")
    targeting_rules = relationship("TargetingRule", back_populates="strategy", cascade="all, delete-orphan")
    outcome_actions = relationship("OutcomeAction", back_populates="strategy", cascade="all, delete-orphan")
    executions = relationship("StrategyExecution", back_populates="strategy", cascade="all, delete-orphan")
    analytics = relationship("StrategyAnalytics", back_populates="strategy", cascade="all, delete-orphan")
    knowledge_sources = relationship("StrategyKnowledgeSource", back_populates="strategy", cascade="all, delete-orphan")


class KnowledgeSource(Base):
    """Knowledge source model for guidelines, protocols, and custom documents"""
    __tablename__ = "knowledge_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=False, default='custom_document')
    access_level = Column(String(50), nullable=False, default='public')
    file_path = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    processing_status = Column(String(50), nullable=False, default='pending')
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    content_summary = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    uploaded_by = Column(String(36), nullable=True)  # Foreign key reference without constraint for now
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Properties for compatibility with frontend
    @property
    def title(self):
        return self.name
    
    @property
    def type(self):
        return self.content_type or 'document'


class TargetingRule(Base):
    """Targeting rule model for patient selection criteria"""
    __tablename__ = "targeting_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String, ForeignKey("chat_strategies.id", ondelete="CASCADE"), nullable=False)
    field = Column(String, nullable=False)  # 'appointment_type', 'patient_age', 'diagnosis', etc.
    operator = Column(String, nullable=False)  # 'is', 'is_not', 'is_between', 'contains', etc.
    value = Column(JSONB, nullable=False)  # Flexible value storage (string, array, object)
    sequence = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("ChatStrategy", back_populates="targeting_rules")


class OutcomeAction(Base):
    """Outcome action model for post-assessment actions"""
    __tablename__ = "outcome_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String, ForeignKey("chat_strategies.id", ondelete="CASCADE"), nullable=False)
    condition = Column(String, nullable=False)  # 'meets_criteria', 'does_not_meet_criteria', 'incomplete_data'
    action_type = Column(String, nullable=False)  # 'create_task', 'flag_chart', 'send_message', 'schedule_followup'
    details = Column(JSONB, nullable=False)  # Action-specific configuration
    sequence = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("ChatStrategy", back_populates="outcome_actions")


class StrategyExecution(Base):
    """Strategy execution model for tracking strategy runs"""
    __tablename__ = "strategy_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String, ForeignKey("chat_strategies.id"), nullable=False)
    session_id = Column(String, ForeignKey("ai_chat_sessions.id"), nullable=True)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    triggered_by = Column(String, ForeignKey("users.id"), nullable=True)  # Clinician who initiated
    trigger_criteria = Column(JSONB, nullable=True)  # Criteria that triggered this strategy
    execution_status = Column(String, nullable=False, default='in_progress')  # 'in_progress', 'completed', 'failed'
    outcome_result = Column(String, nullable=True)  # 'meets_criteria', 'does_not_meet_criteria', 'incomplete_data'
    executed_actions = Column(JSONB, nullable=True)  # Record of actions taken
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("ChatStrategy", back_populates="executions")
    patient = relationship("User", foreign_keys=[patient_id])
    initiator = relationship("User", foreign_keys=[triggered_by])


class StrategyAnalytics(Base):
    """Strategy analytics model for performance tracking"""
    __tablename__ = "strategy_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String, ForeignKey("chat_strategies.id"), nullable=False)
    date = Column(Date, nullable=False)
    patients_screened = Column(Integer, nullable=False, default=0)
    criteria_met = Column(Integer, nullable=False, default=0)
    criteria_not_met = Column(Integer, nullable=False, default=0)
    incomplete_data = Column(Integer, nullable=False, default=0)
    avg_duration_minutes = Column(Integer, nullable=True)
    tasks_created = Column(Integer, nullable=False, default=0)
    charts_flagged = Column(Integer, nullable=False, default=0)
    messages_sent = Column(Integer, nullable=False, default=0)
    followups_scheduled = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("ChatStrategy", back_populates="analytics")

    __table_args__ = (
        UniqueConstraint('strategy_id', 'date'),
    )


class StrategyKnowledgeSource(Base):
    """Association model linking strategies to knowledge sources"""
    __tablename__ = "strategy_knowledge_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String, ForeignKey("chat_strategies.id", ondelete="CASCADE"), nullable=False)
    knowledge_source_id = Column(String, ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)  # Relevance weight for RAG
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("ChatStrategy", back_populates="knowledge_sources")
    knowledge_source = relationship("KnowledgeSource")

    __table_args__ = (
        UniqueConstraint('strategy_id', 'knowledge_source_id'),
    )
