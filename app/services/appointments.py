from datetime import date, datetime, time, timedelta
import uuid
import json
import random
import string
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.base import BaseService
from app.services.users import UserService
from app.repositories.appointments import AppointmentRepository
from app.models.appointment import Appointment, Availability, RecurringAvailability
from app.schemas import (
    TimeSlot, AppointmentCreate, AvailabilityRequest, AppointmentResponse, 
    AppointmentType, AppointmentStatus, AppointmentUpdate, AppointmentCancellation,
    AppointmentRescheduling, AppointmentSummary
)


class AppointmentService(BaseService):
    """
    Service class for appointment-related business logic
    """
    def __init__(self, db: Session):
        self.repository = AppointmentRepository(db)
        self.db = db  # Keep direct reference for transaction management
        self.user_service = UserService(db)
    
    def get_availability(self, clinician_id: str, requested_date: date) -> Tuple[str, List[TimeSlot]]:
        """
        Get available time slots for a clinician on a specific date
        
        Returns:
            Tuple[clinician_name, time_slots]
        """
        try:
            # Get clinician name from user service
            clinician_name = self.user_service.get_clinician_name(clinician_id)
            
            # Define standard time slots
            standard_times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                             "13:00", "13:30", "14:00", "14:30", "15:00", "15:30"]
            
            # Get availability and booked appointments from repository
            availability_records = self.repository.get_availability_for_date(clinician_id, requested_date)
            booked_appointments = self.repository.get_booked_appointments(clinician_id, requested_date)
            
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
            
            return clinician_name, time_slots
        except Exception as e:
            self.handle_exception(e, error_prefix="Failed to get availability")
    
    def book_appointment(self, appointment_data: AppointmentCreate) -> Dict[str, Any]:
        """
        Book an appointment for a patient with a clinician
        """
        try:
            # Generate a unique appointment ID
            appointment_id = str(uuid.uuid4())
            
            # Create appointment object
            new_appointment = Appointment(
                id=appointment_id,
                clinician_id=appointment_data.clinician_id,
                patient_id=appointment_data.patient_id,
                date=datetime.strptime(appointment_data.date, "%Y-%m-%d").date(),
                time=datetime.strptime(appointment_data.time, "%H:%M").time(),
                appointment_type=appointment_data.appointment_type,
                status="scheduled",
                notes=appointment_data.notes,
                confirmation_code=self._generate_confirmation_code()
            )
            
            # Save to database using repository
            self.repository.create_appointment(new_appointment)
            
            # Get names from user service
            patient_name = self.user_service.get_patient_name(appointment_data.patient_id)
            clinician_name = self.user_service.get_clinician_name(appointment_data.clinician_id)
            
            # Format the date and time for response
            parsed_date = datetime.strptime(appointment_data.date, "%Y-%m-%d").date()
            parsed_time = datetime.strptime(appointment_data.time, "%H:%M").time()
            now = datetime.now()
            
            return {
                "id": appointment_id,  # Changed from appointment_id to id to match schema
                "clinician_id": appointment_data.clinician_id,
                "clinician_name": clinician_name,
                "patient_id": appointment_data.patient_id,
                "patient_name": patient_name,
                "date": parsed_date,
                "time": parsed_time,
                "appointment_type": appointment_data.appointment_type,
                "status": AppointmentStatus.SCHEDULED,  # Using enum value instead of string
                "notes": appointment_data.notes,
                "confirmation_code": new_appointment.confirmation_code,
                "created_at": now,
                "updated_at": now
            }
        except Exception as e:
            self.handle_exception(e, error_prefix="Failed to create appointment")
    
    def set_availability(self, clinician_id: str, availability: AvailabilityRequest) -> Dict[str, Any]:
        """
        Set availability for a clinician
        """
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
                self.repository.set_availability(new_availability)
            
            # Handle recurring availability
            if availability.recurring and availability.recurring_days and availability.recurring_until:
                return self._set_recurring_availability(clinician_id, availability)
            else:
                # Single day availability
                return {
                    "message": "Availability set successfully",
                    "date": availability.date,
                    "time_slots": availability.time_slots
                }
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            self.handle_exception(e, error_prefix="Failed to set availability")
    
    def _set_recurring_availability(self, clinician_id: str, availability: AvailabilityRequest) -> Dict[str, Any]:
        """
        Set recurring availability for a clinician
        """
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
                    self.repository.set_availability(new_availability)
            
            # Create a record for the recurring pattern
            recurring_pattern = RecurringAvailability(
                id=str(uuid.uuid4()),
                clinician_id=clinician_id,
                start_date=start_date,
                end_date=end_date,
                days_of_week=json.dumps(availability.recurring_days),
                time_slots=json.dumps(availability.time_slots)
            )
            self.repository.set_recurring_availability(recurring_pattern)
            
            return {
                "message": "Recurring availability set successfully",
                "dates_affected": len(recurring_dates),
                "time_slots": availability.time_slots
            }
        except Exception as e:
            self.handle_exception(e, error_prefix="Failed to set recurring availability")
    
    def get_clinician_appointments(self, clinician_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get all appointments for a clinician within a date range
        """
        try:
            appointments = self.repository.get_clinician_appointments(
                clinician_id, start_date, end_date
            )
            
            # Use user service to get patient names
            user_service = self.user_service
            
            # Format appointments for the API response
            formatted_appointments = []
            for appt in appointments:
                patient_name = user_service.get_patient_name(appt.patient_id)
                
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
            self.handle_exception(e, error_prefix="Failed to retrieve clinician appointments")
    
    def get_patient_appointments(self, patient_id: str) -> Dict[str, Any]:
        """
        Get all appointments for a patient
        """
        try:
            appointments = self.repository.get_patient_appointments(patient_id)
            
            # Use user service for clinician names
            user_service = self.user_service
            
            # Format appointments for the API response
            formatted_appointments = []
            for appt in appointments:
                clinician_name = user_service.get_clinician_name(appt.clinician_id)
                
                # Format date and time
                date_time = f"{appt.date.isoformat()}T{appt.time.strftime('%H:%M')}:00Z"
                
                formatted_appointments.append({
                    "id": appt.id,  # Changed from appointment_id to id
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
            self.handle_exception(e, error_prefix="Failed to retrieve patient appointments")
    
    def update_appointment(self, appointment_id: str, appointment_update: "AppointmentUpdate") -> Dict[str, Any]:
        """
        Update an appointment with new details
        
        Args:
            appointment_id: The ID of the appointment to update
            appointment_update: The update data containing new values
            
        Returns:
            The updated appointment data
        """
        try:
            # Retrieve the appointment
            appointment = self.repository.get_appointment_by_id(appointment_id)
            if not appointment:
                raise HTTPException(status_code=404, detail=f"Appointment with ID {appointment_id} not found")
                
            # Update fields if provided
            if appointment_update.date:
                try:
                    appointment.date = datetime.strptime(appointment_update.date, "%Y-%m-%d").date()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
                    
            if appointment_update.time:
                try:
                    appointment.time = datetime.strptime(appointment_update.time, "%H:%M").time()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid time format. Use 24-hour format HH:MM")
                    
            if appointment_update.appointment_type:
                appointment.appointment_type = appointment_update.appointment_type.value
                
            if appointment_update.status:
                appointment.status = appointment_update.status.value
                
            if appointment_update.notes is not None:  # Allow empty string to clear notes
                appointment.notes = appointment_update.notes
                
            # Update the timestamp
            appointment.updated_at = datetime.utcnow()
            
            # Save changes
            updated_appointment = self.repository.update_appointment(appointment)
            
            # Format response using the AppointmentResponse model
            clinician_name = self.user_service.get_clinician_name(updated_appointment.clinician_id)
            patient_name = self.user_service.get_patient_name(updated_appointment.patient_id)
            
            return {
                "id": updated_appointment.id,
                "clinician_id": updated_appointment.clinician_id,
                "clinician_name": clinician_name,
                "patient_id": updated_appointment.patient_id,
                "patient_name": patient_name,
                "date": updated_appointment.date,
                "time": updated_appointment.time,
                "appointment_type": updated_appointment.appointment_type,
                "status": updated_appointment.status,
                "notes": updated_appointment.notes,
                "confirmation_code": getattr(updated_appointment, "confirmation_code", ""),
                "created_at": updated_appointment.created_at,
                "updated_at": updated_appointment.updated_at
            }
            
        except HTTPException as e:
            raise e
        except Exception as e:
            self.handle_exception(e, error_prefix="Failed to update appointment")
    
    def _generate_confirmation_code(self, length: int = 6) -> str:
        """Generate a random confirmation code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
