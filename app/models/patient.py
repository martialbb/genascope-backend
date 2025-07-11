"""Patient database models."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON, Date
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime
from sqlalchemy.sql import func
from enum import Enum
# Prevent circular imports by not directly importing PatientInvite


class PatientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived" 
    PENDING = "pending"


class Patient(Base):
    """Patient model for storing basic patient information"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=True, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default=PatientStatus.ACTIVE.value)
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    clinician_id = Column(String, ForeignKey("users.id"), nullable=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, unique=True)  # Link to user account when created
    clinician = relationship("User", foreign_keys=[clinician_id], backref="assigned_patients")
    user = relationship("User", foreign_keys=[user_id], backref="patient_record")
    account = relationship("Account", backref="patients")
    
    # Relationships with other models
    # chat_sessions = relationship("ChatSession", back_populates="patient", cascade="all, delete-orphan")  # Old chat system
    chat_sessions = relationship("AIChatSession", back_populates="patient", cascade="all, delete-orphan")  # AI chat system
    # Using string lookup for related class to avoid circular imports
    invites = relationship("PatientInvite", back_populates="patient", cascade="all, delete-orphan")
    
    @property
    def full_name(self):
        """Get the patient's full name."""
        return f"{self.first_name} {self.last_name}"
