"""Chat database models."""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime
from app.models.user import User  # Ensure this import is present and correct


class ChatSession(Base):
    """Chat session model to track user conversations"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"))
    clinician_id = Column(String, ForeignKey("users.id"), nullable=True)
    session_type = Column(String, nullable=False)  # assessment, follow-up, etc.
    status = Column(String, nullable=False, default="active")  # active, completed, archived
    session_metadata = Column(JSON, nullable=True)  # Additional metadata about the session
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    patient = relationship("User", foreign_keys=[patient_id], backref="chat_sessions")
    clinician = relationship("User", foreign_keys=[clinician_id], backref="managed_chat_sessions")
    answers = relationship("ChatAnswer", back_populates="session", cascade="all, delete-orphan")


class ChatQuestion(Base):
    """Chat question model for persisting question templates"""
    __tablename__ = "chat_questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    answer_type = Column(String, nullable=False, default="text")  # text, boolean, single_choice, multiple_choice, date, number
    options = Column(JSON, nullable=True)  # For single/multiple choice questions
    required = Column(Boolean, default=True)
    category = Column(String, nullable=True)  # For grouping related questions
    next_question_logic = Column(JSON, nullable=True)  # Logic for determining next question
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    answers = relationship("ChatAnswer", back_populates="question")


class ChatAnswer(Base):
    """Chat answer model for storing user responses"""
    __tablename__ = "chat_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    question_id = Column(String, ForeignKey("chat_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    answer_value = Column(JSON, nullable=True)  # For structured answers (e.g., choice selections, dates)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="answers")
    question = relationship("ChatQuestion", back_populates="answers")


class RiskAssessment(Base):
    """Risk assessment model for storing eligibility and risk data"""
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    is_eligible = Column(Boolean, nullable=False)
    nccn_eligible = Column(Boolean, nullable=False)
    tyrer_cuzick_score = Column(Integer, nullable=True)
    tyrer_cuzick_threshold = Column(Integer, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("User", backref="risk_assessments")
    session = relationship("ChatSession", backref="risk_assessment")
