"""
Pydantic schema models for patient-related data transfer objects.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class PatientStatusEnum(str, Enum):
    """Patient status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    PENDING = "pending"


class PatientImportBase(BaseModel):
    """Base model for patient import data"""
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    external_id: Optional[str] = None  # ID in the clinic's system
    

class PatientImport(PatientImportBase):
    """Single patient import data"""
    clinician_id: str = None  # Set to null if no specific clinician assigned


class PatientBulkImport(BaseModel):
    """Bulk patient import data"""
    patients: List[PatientImport]
    clinician_id: Optional[str] = None  # Default clinician to assign


class PatientBase(BaseModel):
    """Base model for patient data"""
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: PatientStatusEnum = PatientStatusEnum.ACTIVE
    external_id: Optional[str] = None


class PatientCreate(PatientBase):
    """Model for creating a new patient"""
    clinician_id: str
    date_of_birth: Optional[date] = None
    account_id: Optional[str] = None
    notes: Optional[str] = None


class PatientUpdate(BaseModel):
    """Model for updating a patient"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    status: Optional[PatientStatusEnum] = None
    clinician_id: Optional[str] = None
    notes: Optional[str] = None


class PatientInDB(PatientBase):
    """Model for patient data from the database"""
    id: str
    clinician_id: Optional[str] = None
    account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    date_of_birth: Optional[date] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientResponse(PatientInDB):
    """Model for patient data in API responses"""
    clinician_name: Optional[str] = None
    has_pending_invite: bool = False
    

class PatientImportResponse(BaseModel):
    """Response for patient import operations"""
    successful: List[PatientResponse] 
    failed: List[Dict[str, Any]]
    total_imported: int
    total_failed: int


class PatientCSVImportResponse(BaseModel):
    """Response for CSV import operations"""
    successful_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    sample_patients: List[PatientResponse]
