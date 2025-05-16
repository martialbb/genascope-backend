"""
Pydantic schema models for appointment data transfer objects.

These schemas define the structure for request and response payloads
related to appointments, availability, and scheduling.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
from enum import Enum


class AppointmentType(str, Enum):
    """Enumeration of possible appointment types"""
    VIRTUAL = "virtual"
    IN_PERSON = "in-person"
    HOME_VISIT = "home-visit"


class AppointmentStatus(str, Enum):
    """Enumeration of possible appointment statuses"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed" 
    CANCELED = "canceled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no-show"


class TimeSlot(BaseModel):
    """Schema for available time slots"""
    time: str  # Format: "HH:MM" (24-hour)
    available: bool


class AvailabilityBase(BaseModel):
    """Base schema for clinician availability"""
    clinician_id: str
    date: date
    time: time
    available: bool = True


class AvailabilityCreate(AvailabilityBase):
    """Schema for creating availability records"""
    pass


class AvailabilityResponse(AvailabilityBase):
    """Schema for availability responses"""
    id: str
    
    model_config = ConfigDict(from_attributes=True)


class AvailabilityRequest(BaseModel):
    """Schema for setting clinician availability"""
    date: str  # ISO format date: YYYY-MM-DD
    time_slots: List[str]  # List of time slots in 24-hour format: ["09:00", "09:30", ...]
    recurring: bool = False
    recurring_days: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    recurring_until: Optional[str] = None  # ISO format date: YYYY-MM-DD

    @field_validator('time_slots')
    def validate_time_slots(cls, v):
        """Validate that time slots are in the correct format"""
        import re
        pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
        for slot in v:
            if not pattern.match(slot):
                raise ValueError(f'Invalid time format: {slot}. Use 24-hour format (HH:MM)')
        return v

    @field_validator('recurring_days')
    def validate_recurring_days(cls, v, info):
        """Validate recurring days"""
        values = info.data
        if values.get('recurring') and not v:
            raise ValueError('recurring_days must be provided when recurring is True')
        
        if v:
            for day in v:
                if day < 0 or day > 6:
                    raise ValueError(f'Invalid day value: {day}. Must be between 0 (Monday) and 6 (Sunday)')
        return v

    @field_validator('recurring_until')
    def validate_recurring_until(cls, v, info):
        """Validate recurring end date"""
        values = info.data
        if values.get('recurring') and not v:
            raise ValueError('recurring_until must be provided when recurring is True')
        return v


class AvailabilityListResponse(BaseModel):
    """Schema for listing availability by date"""
    date: str
    clinician_id: str
    clinician_name: str
    time_slots: List[TimeSlot]


class RecurringAvailabilityBase(BaseModel):
    """Base schema for recurring availability"""
    clinician_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    time: time
    valid_until: Optional[date] = None


class RecurringAvailabilityCreate(RecurringAvailabilityBase):
    """Schema for creating recurring availability"""
    pass


class RecurringAvailabilityResponse(RecurringAvailabilityBase):
    """Schema for recurring availability responses"""
    id: str

    model_config = ConfigDict(from_attributes=True)


class AppointmentBase(BaseModel):
    """Base schema for appointment data"""
    clinician_id: str
    patient_id: str
    date: date
    time: time
    appointment_type: AppointmentType = AppointmentType.VIRTUAL
    notes: Optional[str] = None


class AppointmentCreate(BaseModel):
    """Schema for appointment creation requests"""
    clinician_id: str
    date: str  # ISO format date: YYYY-MM-DD
    time: str  # 24-hour format: HH:MM
    patient_id: str
    appointment_type: AppointmentType = AppointmentType.VIRTUAL
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Schema for appointment update requests"""
    date: Optional[str] = None  # ISO format date: YYYY-MM-DD
    time: Optional[str] = None  # 24-hour format: HH:MM
    appointment_type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Schema for appointment responses"""
    id: str
    clinician_id: str
    clinician_name: str
    patient_id: str
    patient_name: str
    date: date
    time: time
    appointment_type: AppointmentType
    status: AppointmentStatus
    notes: Optional[str] = None
    confirmation_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentSummary(BaseModel):
    """Schema for appointment summary responses"""
    id: str
    date_time: str  # ISO format: YYYY-MM-DDTHH:MM:00Z
    clinician_name: str
    appointment_type: AppointmentType
    status: AppointmentStatus

    model_config = ConfigDict(from_attributes=True)


class AppointmentCancellation(BaseModel):
    """Schema for appointment cancellation request"""
    appointment_id: str
    reason: Optional[str] = None
    notify_patient: bool = True
    notify_clinician: bool = True


class AppointmentRescheduling(BaseModel):
    """Schema for appointment rescheduling request"""
    appointment_id: str
    new_date: str  # ISO format date: YYYY-MM-DD
    new_time: str  # 24-hour format: HH:MM
    reason: Optional[str] = None
    notify_patient: bool = True
    notify_clinician: bool = True
