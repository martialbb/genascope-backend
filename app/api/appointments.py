from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import uuid
import json
from sqlalchemy.orm import Session
from app.api.auth import require_full_access, User
from app.db.database import get_db
from app.models.appointment import Appointment, Availability, RecurringAvailability
from app.services.appointments import AppointmentService
from app.schemas import (
    TimeSlot, AvailabilityListResponse, AppointmentCreate, AppointmentResponse, 
    AppointmentSummary, AvailabilityRequest, AppointmentType, AppointmentStatus,
    AvailabilityResponse, AppointmentUpdate, AppointmentCancellation, AppointmentRescheduling,
    OrganizationAppointmentListResponse
)

router = APIRouter(prefix="/api", tags=["appointments"])

# Endpoints
@router.get("/availability", response_model=AvailabilityListResponse)
async def get_availability(
    clinician_id: str, 
    date_str: str = Query(..., alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Get available time slots for a clinician on a specific date
    """
    # Parse the requested date
    try:
        requested_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    clinician_name, time_slots = appointment_service.get_availability(clinician_id, requested_date)
    
    return AvailabilityListResponse(
        date=date_str,
        clinician_id=clinician_id,
        clinician_name=clinician_name,
        time_slots=time_slots
    )

@router.post("/book_appointment", response_model=AppointmentResponse)
async def book_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Book an appointment for a patient with a clinician
    """
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    result = appointment_service.book_appointment(appointment_data)
    
    return AppointmentResponse(**result)

@router.post("/availability/set")
async def set_clinician_availability(
    availability: AvailabilityRequest,
    clinician_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Set availability for a clinician. This endpoint would be limited to clinicians setting their own
    availability or administrators managing clinician schedules.
    """
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    return appointment_service.set_availability(clinician_id, availability)

@router.get("/appointments/clinician/{clinician_id}")
async def get_clinician_appointments(
    clinician_id: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Get all appointments for a clinician within a date range
    """
    # Convert date strings to datetime objects
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    return appointment_service.get_clinician_appointments(clinician_id, start_date_obj, end_date_obj)

@router.get("/appointments/patient/{patient_id}")
async def get_patient_appointments(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Get all appointments for a patient
    """
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    return appointment_service.get_patient_appointments(patient_id)

@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Update an appointment's details (date, time, type, status, notes)
    """
    appointment_service = AppointmentService(db)
    return appointment_service.update_appointment(appointment_id, appointment_update)


@router.post("/appointments/cancel")
async def cancel_appointment(
    cancellation: AppointmentCancellation,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Cancel an appointment with optional reason
    """
    appointment_service = AppointmentService(db)
    return appointment_service.cancel_appointment(cancellation)


@router.post("/appointments/reschedule")
async def reschedule_appointment(
    rescheduling: AppointmentRescheduling,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    Reschedule an appointment to a new date and time
    """
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    return appointment_service.reschedule_appointment(rescheduling)


@router.get("/organization/appointments", response_model=OrganizationAppointmentListResponse)
async def list_organization_appointments(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of appointments per page"),
    status: Optional[str] = Query(None, description="Filter by appointment status"),
    date_from: Optional[str] = Query(None, description="Filter appointments from this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter appointments until this date (YYYY-MM-DD)"),
    clinician_id: Optional[str] = Query(None, description="Filter by specific clinician ID"),
    patient_id: Optional[str] = Query(None, description="Filter by specific patient ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_access)
):
    """
    List all appointments for the current user's organization with pagination and filters.
    
    This endpoint allows organization administrators and staff to view all appointments 
    for patients belonging to their organization.
    
    **Parameters:**
    - **page**: Page number (starts from 1)
    - **page_size**: Number of appointments per page (max 100)
    - **status**: Filter by appointment status (scheduled, confirmed, completed, canceled, etc.)
    - **date_from**: Start date filter in YYYY-MM-DD format
    - **date_to**: End date filter in YYYY-MM-DD format  
    - **clinician_id**: Filter by specific clinician
    - **patient_id**: Filter by specific patient
    
    **Returns:**
    - Paginated list of appointments with patient and clinician details
    - Pagination metadata (total count, pages, etc.)
    """
    # Ensure user has access to organization data
    if not current_user.account_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. User must be associated with an organization."
        )
    
    # Parse date filters if provided
    date_from_parsed = None
    date_to_parsed = None
    
    try:
        if date_from:
            date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_to:
            date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Use appointment service to get organization appointments
    appointment_service = AppointmentService(db)
    result = appointment_service.list_organization_appointments(
        account_id=current_user.account_id,
        page=page,
        page_size=page_size,
        status_filter=status,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        clinician_id=clinician_id,
        patient_id=patient_id
    )
    
    return result
