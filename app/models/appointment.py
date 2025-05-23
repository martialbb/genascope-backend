"""
Database models for appointments.
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Date, Time, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(String(36), primary_key=True)
    clinician_id = Column(String(36), index=True)
    patient_id = Column(String(36), index=True)
    date = Column(Date, nullable=False)  # Added for compatibility with repo/service/tests
    date_time = Column(DateTime, nullable=False)  # Changed from date+time to single field
    time = Column(Time, nullable=False)  # Added for compatibility with service/tests
    appointment_type = Column(String(20), default="virtual")
    status = Column(String(20), default="scheduled")
    notes = Column(Text, nullable=True)
    confirmation_code = Column(String(10), nullable=False)  # Added field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Availability(Base):
    __tablename__ = "clinician_availability"

    id = Column(String(36), primary_key=True)
    clinician_id = Column(String(36), index=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
class RecurringAvailability(Base):
    __tablename__ = "recurring_availability"
    
    id = Column(String(36), primary_key=True)
    clinician_id = Column(String(36), index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    time = Column(Time, nullable=False)
    start_date = Column(Date, nullable=True)  # Added field
    valid_until = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)  # Added for compatibility with service/tests
    days_of_week = Column(Text, nullable=True)  # JSON-encoded list of days
    time_slots = Column(Text, nullable=True)  # JSON-encoded list of time slots
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
