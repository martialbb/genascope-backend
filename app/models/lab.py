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
    patient_id = Column(String, ForeignKey("users.id"), nullable=False)
    clinician_id = Column(String, ForeignKey("users.id"), nullable=False)
    lab_id = Column(String, ForeignKey("lab_integrations.id"), nullable=True)
    external_order_id = Column(String, nullable=True)  # ID from external lab system
    order_number = Column(String, nullable=False, unique=True)  # Human-readable order number
    test_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=OrderStatus.PENDING)
    requisition_details = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    collection_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="lab_orders")
    clinician = relationship("User", foreign_keys=[clinician_id], backref="ordered_labs")
    lab = relationship("LabIntegration", backref="orders")
    results = relationship("LabResult", back_populates="order", cascade="all, delete-orphan")


class LabResult(Base):
    """Lab result model for storing test results"""
    __tablename__ = "lab_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("lab_orders.id"), nullable=False)
    result_status = Column(String, nullable=False, default=ResultStatus.PENDING)
    result_data = Column(JSON, nullable=True)
    report_url = Column(String, nullable=True)  # URL to download the report
    summary = Column(Text, nullable=True)
    abnormal = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("LabOrder", back_populates="results")
    reviewer = relationship("User", backref="reviewed_results")
