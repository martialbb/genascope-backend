"""Patient invite database models."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime, timedelta
from app.models.user import User
# Avoiding circular imports - using string references in relationships instead


class PatientInvite(Base):
    """Patient invitation model"""
    __tablename__ = "invites"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, ForeignKey("users.id"), nullable=True)  # Changed from user_id to match DB
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)  # Link to pre-created patient
    email = Column(String, nullable=False, index=True)  # Redundant with patient.email but kept for performance
    invite_token = Column(String, nullable=False, unique=True)
    clinician_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, accepted, expired, revoked
    custom_message = Column(Text, nullable=True)
    session_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    provider = relationship("User", foreign_keys=[provider_id])  # Changed from user to provider
    clinician = relationship("User", foreign_keys=[clinician_id], backref="sent_invites")
    # Using string lookup for related class to avoid circular imports
    patient = relationship("Patient", foreign_keys=[patient_id], back_populates="invites")
