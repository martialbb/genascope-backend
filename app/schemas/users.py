"""
Pydantic schema models for user data transfer objects.

These schemas define the structure for request and response payloads
related to user accounts, including patients and clinicians.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum


class UserRole(str, Enum):
    """Enumeration of possible user roles in the system"""
    PATIENT = "patient"
    CLINICIAN = "clinician" 
    ADMIN = "admin"
    LAB_TECH = "lab_tech"


class UserBase(BaseModel):
    """Base model for user data shared across requests and responses"""
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = Field(default=UserRole.PATIENT)
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation requests"""
    password: str
    confirm_password: str

    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        values = info.data
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v


class UserUpdate(BaseModel):
    """Schema for user update requests"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema for password change requests"""
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        values = info.data
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('passwords do not match')
        return v


class UserResponse(UserBase):
    """Schema for user response data"""
    id: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PatientProfile(BaseModel):
    """Schema for additional patient profile data"""
    id: str
    date_of_birth: date
    medical_record_number: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    class Config:
        orm_mode = True


class ClinicianProfile(BaseModel):
    """Schema for additional clinician profile data"""
    id: str
    specialty: str
    license_number: str
    npi_number: Optional[str] = None
    biography: Optional[str] = None
    accepting_new_patients: bool = True
    
    class Config:
        orm_mode = True


class PatientResponse(UserResponse):
    """Complete patient response including profile data"""
    profile: Optional[PatientProfile] = None


class ClinicianResponse(UserResponse):
    """Complete clinician response including profile data"""
    profile: Optional[ClinicianProfile] = None


class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    token_type: str
    user_id: str
    role: UserRole


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[int] = None
