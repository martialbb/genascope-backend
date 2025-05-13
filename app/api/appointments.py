from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from app.api.auth import get_current_active_user, User
from app.db.database import get_db
from app.models.appointment import Appointment, Availability, RecurringAvailability

router = APIRouter(prefix="/api", tags=["appointments"])

# Models
class TimeSlot(BaseModel):
    time: str
    available: bool

class AvailabilityResponse(BaseModel):
    date: str
    clinician_id: str
    clinician_name: str
    time_slots: List[TimeSlot]

class AppointmentRequest(BaseModel):
    clinician_id: str
    date: str  # ISO format date: YYYY-MM-DD
    time: str  # 24-hour format: HH:MM
    patient_id: str
    appointment_type: str = "virtual"  # "virtual" or "in-person"
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: str
    clinician_id: str
    clinician_name: str
    patient_id: str
    patient_name: str
    date_time: str  # ISO format: YYYY-MM-DDTHH:MM:00Z
    appointment_type: str
    status: str
    confirmation_code: str

class ClinicianAvailabilityRequest(BaseModel):
    date: str  # ISO format date: YYYY-MM-DD
    time_slots: List[str]  # List of time slots in 24-hour format: ["09:00", "09:30", ...]
    recurring: bool = False
    recurring_days: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    recurring_until: Optional[str] = None  # ISO format date: YYYY-MM-DD

# Endpoints
@router.get("/availability", response_model=AvailabilityResponse)
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
    
    try:
        # Mock clinician data - would come from database
        clinician_names = {
            "clinician1": "Dr. Jane Smith",
            "clinician2": "Dr. John Davis",
            "clinician-123": "Dr. Test Doctor"
        }
        clinician_name = clinician_names.get(clinician_id, "Unknown Doctor")
        
        # Define standard time slots
        standard_times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                          "13:00", "13:30", "14:00", "14:30", "15:00", "15:30"]
        
        # Get clinician availability records from database
        availability_records = db.query(Availability).filter(
            Availability.clinician_id == clinician_id,
            Availability.date == requested_date
        ).all()
        
        # Get booked appointments for this clinician on this date
        booked_appointments = db.query(Appointment).filter(
            Appointment.clinician_id == clinician_id,
            Appointment.date == requested_date,
            Appointment.status != "canceled"
        ).all()
        
        # Convert booked appointments to a set of unavailable times
        booked_times = {appt.time.strftime("%H:%M") for appt in booked_appointments}
        
        # Create time slots based on availability and bookings
        time_slots = []
        for time_str in standard_times:
            # Check if this time is available in the clinician's schedule and not booked
            is_available = time_str not in booked_times
            
            # If we have specific availability records, use those instead
            if availability_records:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
                matching_availability = next(
                    (a for a in availability_records if a.time.strftime("%H:%M") == time_str), 
                    None
                )
                if matching_availability:
                    is_available = matching_availability.available
                else:
                    is_available = False  # If not explicitly set as available, it's unavailable
                    
            time_slots.append(TimeSlot(time=time_str, available=is_available))
        
        return AvailabilityResponse(
            date=date_str,
            clinician_id=clinician_id,
            clinician_name=clinician_name,
            time_slots=time_slots
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")

@router.post("/book_appointment", response_model=AppointmentResponse)
async def book_appointment(
    appointment_data: AppointmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Book an appointment for a patient with a clinician
    """
    # In a real implementation, you would:
    # 1. Validate the time slot is available
    # 2. Create an appointment record in the database
    # 3. Send confirmation emails
    # 4. Update the clinician's availability
    
    # Generate a unique appointment ID
    appointment_id = str(uuid.uuid4())
    
    # Create appointment record in database
    try:
        new_appointment = Appointment(
            id=appointment_id,
            clinician_id=appointment_data.clinician_id,
            patient_id=appointment_data.patient_id,
            date=datetime.strptime(appointment_data.date, "%Y-%m-%d").date(),
            time=datetime.strptime(appointment_data.time, "%H:%M").time(),
            appointment_type=appointment_data.appointment_type,
            status="scheduled",
            notes=appointment_data.notes
        )
        db.add(new_appointment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")
    
    # Generate a confirmation code (6 alphanumeric characters)
    import random
    import string
    confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Mock patient name - would come from database
    patient_name = "John Doe"
    
    # Mock clinician name - would come from database
    clinician_name = "Dr. Jane Smith"
    
    # Format the date and time as ISO format
    date_time = f"{appointment_data.date}T{appointment_data.time}:00Z"
    
    return AppointmentResponse(
        appointment_id=appointment_id,
        clinician_id=appointment_data.clinician_id,
        clinician_name=clinician_name,
        patient_id=appointment_data.patient_id,
        patient_name=patient_name,
        date_time=date_time,
        appointment_type=appointment_data.appointment_type,
        status="scheduled",
        confirmation_code=confirmation_code
    )

@router.post("/availability/set")
async def set_clinician_availability(
    availability: ClinicianAvailabilityRequest,
    clinician_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Set availability for a clinician. This endpoint would be limited to clinicians setting their own
    availability or administrators managing clinician schedules.
    """
    # In a real implementation, you would:
    # 1. Validate the user has permissions (is the clinician or an admin)
    # 2. Update the clinician_availability table
    
    # Add the non-recurring availability to the database first
    try:
        # Parse the date
        availability_date = datetime.strptime(availability.date, "%Y-%m-%d").date()
        
        # Add each time slot to the database
        for time_slot in availability.time_slots:
            time_obj = datetime.strptime(time_slot, "%H:%M").time()
            new_availability = Availability(
                id=str(uuid.uuid4()),
                clinician_id=clinician_id,
                date=availability_date,
                time=time_obj,
                available=True
            )
            db.add(new_availability)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to set availability: {str(e)}")
    
    # For recurring availability, you'd create entries for each applicable day
    if availability.recurring and availability.recurring_days and availability.recurring_until:
        try:
            start_date = datetime.strptime(availability.date, "%Y-%m-%d").date()
            end_date = datetime.strptime(availability.recurring_until, "%Y-%m-%d").date()
            
            # Calculate all dates that match the recurring pattern
            recurring_dates = []
            current = start_date
            while current <= end_date:
                if current.weekday() in availability.recurring_days:
                    recurring_dates.append(current)
                current += timedelta(days=1)
            
            # Add each recurring date to the database
            for recur_date in recurring_dates:
                # Skip the first date as it was already added above
                if recur_date == start_date:
                    continue
                    
                # Add each time slot for this recurring date
                for time_slot in availability.time_slots:
                    time_obj = datetime.strptime(time_slot, "%H:%M").time()
                    new_availability = Availability(
                        id=str(uuid.uuid4()),
                        clinician_id=clinician_id,
                        date=recur_date,
                        time=time_obj,
                        available=True
                    )
                    db.add(new_availability)
            
            # Create a record for the recurring pattern
            recurring_pattern = RecurringAvailability(
                id=str(uuid.uuid4()),
                clinician_id=clinician_id,
                start_date=start_date,
                end_date=end_date,
                days_of_week=json.dumps(availability.recurring_days),
                time_slots=json.dumps(availability.time_slots)
            )
            db.add(recurring_pattern)
            
            # Commit all the recurring availability to the database
            db.commit()
                
            return {
                "message": "Recurring availability set successfully",
                "dates_affected": len(recurring_dates),
                "time_slots": availability.time_slots
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to set recurring availability: {str(e)}")
    else:
        # Single day availability
        return {
            "message": "Availability set successfully",
            "date": availability.date,
            "time_slots": availability.time_slots
        }

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
    
    # Query the database for appointments
    try:
        appointments = db.query(Appointment).filter(
            Appointment.clinician_id == clinician_id,
            Appointment.date >= start_date_obj,
            Appointment.date <= end_date_obj
        ).all()
        
        # Mock patient names - in real system would join with patient table
        patient_names = {
            "patient1": "John Doe",
            "patient2": "Jane Smith",
            "patient-123": "Test Patient"
        }
        
        # Format appointments for the API response
        formatted_appointments = []
        for appt in appointments:
            patient_name = patient_names.get(appt.patient_id, "Unknown Patient")
            
            # Format date and time
            date_time = f"{appt.date.isoformat()}T{appt.time.strftime('%H:%M')}:00Z"
            
            formatted_appointments.append({
                "appointment_id": appt.id,
                "patient_id": appt.patient_id,
                "patient_name": patient_name,
                "date_time": date_time,
                "appointment_type": appt.appointment_type if hasattr(appt, "appointment_type") else "virtual",
                "status": appt.status
            })
        
        return {
            "clinician_id": clinician_id,
            "appointments": formatted_appointments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve appointments: {str(e)}")

@router.get("/appointments/patient/{patient_id}")
async def get_patient_appointments(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all appointments for a patient
    """
    # Query the database for appointments
    try:
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).all()
        
        # Mock clinician names - in real system would join with clinician table
        clinician_names = {
            "clinician1": "Dr. Jane Smith",
            "clinician2": "Dr. John Davis",
            "clinician-123": "Dr. Test Doctor"
        }
        
        # Format appointments for the API response
        formatted_appointments = []
        for appt in appointments:
            clinician_name = clinician_names.get(appt.clinician_id, "Unknown Clinician")
            
            # Format date and time
            date_time = f"{appt.date.isoformat()}T{appt.time.strftime('%H:%M')}:00Z"
            
            formatted_appointments.append({
                "appointment_id": appt.id,
                "clinician_id": appt.clinician_id,
                "clinician_name": clinician_name,
                "date_time": date_time,
                "appointment_type": appt.appointment_type if hasattr(appt, "appointment_type") else "virtual",
                "status": appt.status
            })
        
        return {
            "patient_id": patient_id,
            "appointments": formatted_appointments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve appointments: {str(e)}")

@router.put("/appointments/{appointment_id}")
async def update_appointment_status(
    appointment_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the status of an appointment (e.g., cancel, reschedule)
    """
    # Validate status
    valid_statuses = ["scheduled", "completed", "canceled", "rescheduled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # In a real implementation, you would update the database
    try:
        # Update appointment status in the database
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment.status = status
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update appointment: {str(e)}")
    
    return {
        "appointment_id": appointment_id,
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
