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
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    appointment_type = Column(String(20), default="virtual")
    status = Column(String(20), default="scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Availability(Base):
    __tablename__ = "availability"
    
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
    valid_until = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
