from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Enum
from app.db.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    LAB_TECH = "lab_tech"

class Account(Base):
    """Organization or healthcare facility account"""
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="account", cascade="all, delete-orphan")

class User(Base):
    """Application user model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="users")
    
    # For patients
    clinician_id = Column(String, ForeignKey("users.id"), nullable=True)
    patients = relationship("User", 
                           foreign_keys=[clinician_id],
                           backref="clinician",
                           remote_side=[id])

class PatientProfile(Base):
    """Extended patient information"""
    __tablename__ = "patient_profiles"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    medical_history = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class UserProfile:
    def __init__(self, id, user_id, **kwargs):
        self.id = id
        self.user_id = user_id
        for k, v in kwargs.items():
            setattr(self, k, v)
