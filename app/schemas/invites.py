"""
Pydantic schema models for invitation-related data transfer objects.

These schemas define the structure for request and response payloads
related to patient invitations and onboarding processes.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InviteStatus(str, Enum):
    """Enumeration of possible invitation statuses"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PatientInviteBase(BaseModel):
    """Base model for patient invitation data"""
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None


class PatientInviteCreate(PatientInviteBase):
    """Schema for patient invitation creation"""
    provider_id: str
    send_email: bool = True
    custom_message: Optional[str] = None
    expiry_days: int = 14
    

class PatientInviteResponse(PatientInviteBase):
    """Schema for patient invitation response data"""
    invite_id: str
    invite_url: str
    provider_id: str
    provider_name: str
    status: InviteStatus
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BulkInviteCreate(BaseModel):
    """Schema for creating multiple invitations at once"""
    patients: List[PatientInviteCreate]
    send_emails: bool = True
    custom_message: Optional[str] = None


class BulkInviteResponse(BaseModel):
    """Schema for bulk invitation response"""
    successful: List[PatientInviteResponse]
    failed: List[Dict[str, Any]]
    total_sent: int
    total_failed: int


class InviteResend(BaseModel):
    """Schema for resending an invitation"""
    invite_id: str
    custom_message: Optional[str] = None


class InviteVerification(BaseModel):
    """Schema for verifying an invitation token"""
    token: str


class InviteVerificationResponse(BaseModel):
    """Schema for invitation verification response"""
    valid: bool
    invite_id: Optional[str] = None
    patient_name: Optional[str] = None
    provider_name: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PatientRegistration(BaseModel):
    """Schema for patient registration from invitation"""
    invite_id: str
    password: str
    confirm_password: str
    date_of_birth: str  # ISO format date: YYYY-MM-DD
    agree_to_terms: bool = False
    
    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        values = info.data
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v
        
    @field_validator('agree_to_terms')
    def must_agree_to_terms(cls, v):
        if not v:
            raise ValueError('must agree to terms and conditions')
        return v
