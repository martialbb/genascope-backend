from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import uuid
import json
from sqlalchemy.orm import Session
from app.api.auth import get_current_active_user, User
from app.db.database import get_db
from app.models.appointment import Appointment, Availability, RecurringAvailability
from app.services.appointments import AppointmentService
from app.schemas import (
    TimeSlot, AvailabilityListResponse, AppointmentCreate, AppointmentResponse, 
    AppointmentSummary, AvailabilityRequest, AppointmentType, AppointmentStatus,
    AvailabilityResponse, AppointmentUpdate, AppointmentCancellation, AppointmentRescheduling
)

router = APIRouter(prefix="/api", tags=["appointments"])

# Endpoints
@router.get("/availability", response_model=AvailabilityListResponse)
async def get_availability(
    clinician_id: str, 
    date_str: str = Query(..., alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
):
    """
    Reschedule an appointment to a new date and time
    """
    # Use appointment service to handle business logic
    appointment_service = AppointmentService(db)
    return appointment_service.reschedule_appointment(rescheduling)
