"""Chat Configuration database models - cleaned up version."""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime


class ChatStrategy(Base):
    """Chat strategy model for configurable patient screening workflows"""
    __tablename__ = "chat_strategies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("AIChatSession", back_populates="strategy")
    extraction_rules = relationship("ExtractionRule", back_populates="strategy", cascade="all, delete-orphan")


class KnowledgeSource(Base):
    """Knowledge source model for guidelines, protocols, and custom documents"""
    __tablename__ = "knowledge_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    processing_status = Column(String(50), nullable=False, default='pending')
    uploaded_by = Column(String(36), nullable=True)  # Foreign key reference without constraint for now
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Properties for compatibility with frontend
    @property
    def title(self):
        return self.name
    
    @property
    def type(self):
        return self.content_type or 'document'
