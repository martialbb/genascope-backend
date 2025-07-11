"""Lab integration database models."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON, Integer, Float
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime
from enum import Enum


class TestType(str, Enum):
    """Enumeration of lab test types"""
    BRCA = "brca"
    GENETIC_PANEL = "genetic_panel"
    MAMMOGRAM = "mammogram"
    ULTRASOUND = "ultrasound"
    MRI = "mri"
    BIOPSY = "biopsy"
    BLOOD_TEST = "blood_test"


class OrderStatus(str, Enum):
    """Enumeration of lab order statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    COLLECTED = "collected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ResultStatus(str, Enum):
    """Enumeration of lab result statuses"""
    PENDING = "pending"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"


class LabIntegration(Base):
    """Lab integration settings model"""
    __tablename__ = "lab_integrations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    api_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LabOrder(Base):
    """Lab order model for tracking test orders"""
    __tablename__ = "lab_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True)  # Fixed: references patients table
    order_type = Column(String, nullable=False)  # Matches actual DB column
    status = Column(String, nullable=True, default="pending")
    lab_reference = Column(String, nullable=True)  # Matches actual DB column
    ordered_by = Column(String, ForeignKey("users.id"), nullable=True)  # Matches actual DB column
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - need to import Patient model
    # patient = relationship("Patient", foreign_keys=[patient_id], backref="lab_orders")
    clinician = relationship("User", foreign_keys=[ordered_by], backref="ordered_labs")


class LabResult(Base):
    """Lab result model for storing test results"""
    __tablename__ = "lab_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_order_id = Column(String, ForeignKey("lab_orders.id"), nullable=True)  # Matches actual DB column
    test_name = Column(String, nullable=False)  # Matches actual DB column
    result_value = Column(String, nullable=True)  # Matches actual DB column
    unit = Column(String, nullable=True)  # Matches actual DB column  
    reference_range = Column(String, nullable=True)  # Matches actual DB column
    status = Column(String, nullable=True, default="final")  # Matches actual DB column
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("LabOrder", backref="results")
