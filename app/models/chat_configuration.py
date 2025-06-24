"""Chat Configuration database models."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, DateTime, JSON, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.db.database import Base
import uuid
from datetime import datetime


class ChatStrategy(Base):
    """Chat strategy model for configurable patient screening workflows"""
    __tablename__ = "chat_strategies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=False, default="")  # Required by database
    patient_introduction = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    specialty = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    account = relationship("Account", foreign_keys=[account_id])
    knowledge_sources = relationship(
        "KnowledgeSource", 
        secondary="strategy_knowledge_sources",
        back_populates="strategies"
    )
    targeting_rules = relationship("TargetingRule", back_populates="strategy", cascade="all, delete-orphan")
    outcome_actions = relationship("OutcomeAction", back_populates="strategy", cascade="all, delete-orphan")
    executions = relationship("StrategyExecution", back_populates="strategy", cascade="all, delete-orphan")
    analytics = relationship("StrategyAnalytics", back_populates="strategy", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="strategy")
    chat_questions = relationship("ChatQuestion", back_populates="strategy")


class KnowledgeSource(Base):
    """Knowledge source model for guidelines, protocols, and custom documents with hybrid storage"""
    __tablename__ = "knowledge_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # DB column is 'name' 
    source_type = Column(String, nullable=False)  # DB column is 'source_type'
    description = Column(Text, nullable=True)
    
    # File Storage - existing columns in DB
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_path = Column(String, nullable=True)
    s3_bucket = Column(String, nullable=True)
    s3_key = Column(String, nullable=True)
    s3_url = Column(String, nullable=True)
    source_metadata = Column(JSON, nullable=True)  # Renamed from metadata to avoid SQLAlchemy conflicts
    
    # Processing status
    processing_status = Column(String, nullable=False, default='pending')
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    content_summary = Column(Text, nullable=True)
    
    # Access control
    is_active = Column(Boolean, nullable=False, default=True)
    access_level = Column(String, nullable=False, default='private')
    
    # Audit fields
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    account = relationship("Account", foreign_keys=[account_id])
    strategies = relationship(
        "ChatStrategy", 
        secondary="strategy_knowledge_sources",
        back_populates="knowledge_sources"
    )
    
    # Properties for compatibility with frontend
    @property
    def title(self):
        return self.name
    
    @property
    def type(self):
        return self.source_type
    chat_questions = relationship("ChatQuestion", back_populates="knowledge_source")


class StrategyKnowledgeSource(Base):
    """Junction table for many-to-many relationship between strategies and knowledge sources"""
    __tablename__ = "strategy_knowledge_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String, ForeignKey("chat_strategies.id", ondelete="CASCADE"), nullable=False)
    knowledge_source_id = Column(String, ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Float, nullable=True, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('strategy_id', 'knowledge_source_id'),
    )


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
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=True)
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
    session = relationship("ChatSession", foreign_keys="ChatSession.strategy_execution_id", back_populates="strategy_execution", uselist=False)
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
