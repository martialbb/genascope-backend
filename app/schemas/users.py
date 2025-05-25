"""
Pydantic schema models for user data transfer objects.

These schemas define the structure for request and response payloads
related to user accounts, including patients and clinicians.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class UserRole(str, Enum):
    """Enumeration of possible user roles in the system"""
    PATIENT = "patient"
    CLINICIAN = "clinician" 
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    LAB_TECH = "lab_tech"


class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User's role in the system")
    account_id: Optional[str] = Field(None, description="ID of the organization account")
    is_active: bool = Field(True, description="Whether the user account is active")
    clinician_id: Optional[str] = Field(None, description="For patients, the ID of their assigned clinician")
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Schema for creating new users"""
    password: str = Field(..., description="User's password", min_length=8)
    

class UserUpdate(BaseModel):
    """Schema for updating existing users"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    account_id: Optional[str] = None
    is_active: Optional[bool] = None
    clinician_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    """Schema for user data from the database"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """Schema for user data in responses"""
    id: str
    
    model_config = ConfigDict(from_attributes=True)


class PatientProfileBase(BaseModel):
    """Base schema for patient profile data"""
    date_of_birth: Optional[date] = Field(None, description="Patient's date of birth")
    gender: Optional[str] = Field(None, description="Patient's gender")
    phone_number: Optional[str] = Field(None, description="Patient's phone number")
    address: Optional[str] = Field(None, description="Patient's address")
    medical_history: Optional[str] = Field(None, description="Summary of patient's medical history")
    
    model_config = ConfigDict(from_attributes=True)


class PatientProfileCreate(PatientProfileBase):
    """Schema for creating patient profiles"""
    pass


class PatientProfileUpdate(PatientProfileBase):
    """Schema for updating patient profiles"""
    pass


class PatientProfileInDB(PatientProfileBase):
    """Schema for patient profile data from the database"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PatientProfileResponse(PatientProfileBase):
    """Schema for patient profile data in responses"""
    id: str
    user_id: str
    
    model_config = ConfigDict(from_attributes=True)


class PatientCreate(UserCreate):
    """Schema for creating patients with profile information"""
    role: UserRole = UserRole.PATIENT
    profile: Optional[PatientProfileCreate] = None


class PatientResponse(BaseModel):
    """Schema for patient data with profile in responses"""
    user: UserResponse
    profile: Optional[PatientProfileResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    """Base schema for account data"""
    name: str = Field(..., description="Account name")
    domain: str = Field(..., description="Account domain")
    is_active: bool = Field(True, description="Whether the account is active")
    
    model_config = ConfigDict(from_attributes=True)


class AccountCreate(AccountBase):
    """Schema for creating new accounts"""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating existing accounts"""
    name: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class AccountInDB(AccountBase):
    """Schema for account data from the database"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccountResponse(AccountBase):
    """Schema for account data in responses"""
    id: str
    
    model_config = ConfigDict(from_attributes=True)


class AccountWithUsers(AccountResponse):
    """Schema for account data with users in responses"""
    users: List[UserResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
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
