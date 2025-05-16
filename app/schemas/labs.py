"""
Pydantic schema models for lab-related data transfer objects.

These schemas define the structure for request and response payloads
related to lab orders, results, and tests.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class TestType(str, Enum):
    """Enumeration of possible lab test types"""
    BRCA = "brca"
    MAMMOGRAM = "mammogram"
    ULTRASOUND = "ultrasound"
    MRI = "mri"
    BIOPSY = "biopsy"
    BLOOD_PANEL = "blood_panel"
    GENETIC_PANEL = "genetic_panel"


class OrderStatus(str, Enum):
    """Enumeration of possible lab order statuses"""
    ORDERED = "ordered"
    SCHEDULED = "scheduled"
    SPECIMEN_COLLECTED = "specimen_collected"
    IN_PROCESS = "in_process"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class LabOrderBase(BaseModel):
    """Base schema for lab order data"""
    patient_id: str
    test_type: TestType
    clinician_id: str
    notes: Optional[str] = None


class LabOrderCreate(LabOrderBase):
    """Schema for lab order creation requests"""
    scheduled_date: Optional[str] = None  # ISO format date: YYYY-MM-DD
    facility_id: Optional[str] = None


class LabOrderUpdate(BaseModel):
    """Schema for lab order update requests"""
    status: Optional[OrderStatus] = None
    scheduled_date: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class LabOrderResponse(LabOrderBase):
    """Schema for lab order responses"""
    order_id: str
    status: OrderStatus
    ordered_at: datetime
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    patient_name: str
    clinician_name: str
    facility_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResultStatus(str, Enum):
    """Enumeration of possible result statuses"""
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    INCONCLUSIVE = "inconclusive"
    PENDING_REVIEW = "pending_review"
    CRITICAL = "critical"


class LabResultBase(BaseModel):
    """Base schema for lab result data"""
    order_id: str
    result_summary: str
    status: ResultStatus
    details: Dict[str, Any] = {}
    images: Optional[List[str]] = None
    notes: Optional[str] = None


class LabResultCreate(LabResultBase):
    """Schema for lab result creation"""
    technician_id: str


class LabResultResponse(LabResultBase):
    """Schema for lab result responses"""
    result_id: str
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    technician_name: str
    patient_id: str
    patient_name: str
    clinician_id: str
    clinician_name: str
    test_type: TestType

    model_config = ConfigDict(from_attributes=True)


class GeneticMarker(BaseModel):
    """Schema for genetic marker data"""
    marker_id: str
    name: str
    detected: bool
    risk_factor: float  # Scale from 0-1
    notes: Optional[str] = None


class GeneticTestResult(BaseModel):
    """Schema for detailed genetic test results"""
    markers: List[GeneticMarker]
    overall_risk_score: float
    recommendations: List[str]
    

class ImagingFinding(BaseModel):
    """Schema for findings in imaging tests"""
    finding_id: str
    location: str
    size_mm: Optional[float] = None
    description: str
    bi_rads_score: Optional[int] = None  # 0-6
    recommendation: Optional[str] = None
    image_url: Optional[str] = None


class ImagingTestResult(BaseModel):
    """Schema for detailed imaging test results"""
    findings: List[ImagingFinding]
    overall_impression: str
    follow_up_recommended: bool
    follow_up_timeframe: Optional[str] = None
