from datetime import date, datetime, time
from typing import List, Optional, Type
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.models.appointment import Appointment, Availability, RecurringAvailability


class AppointmentRepository:
    """
    Repository class for appointment-related database operations
    """
    def __init__(self, db: Session):
        self.db = db
        # We could extend BaseRepository, but since we're dealing with multiple
        # models (Appointment, Availability, RecurringAvailability), we'll keep
        # this implementation simple for now

    def get_availability_for_date(self, clinician_id: str, requested_date: date) -> List[Availability]:
        """
        Get availability records for a clinician on a specific date
        """
        return self.db.query(Availability).filter(
            Availability.clinician_id == clinician_id,
            Availability.date == requested_date
        ).all()
    
    def get_booked_appointments(self, clinician_id: str, requested_date: date) -> List[Appointment]:
        """
        Get all non-canceled appointments for a clinician on a specific date
        """
        return self.db.query(Appointment).filter(
            Appointment.clinician_id == clinician_id,
            func.date(Appointment.date_time) == requested_date,
            Appointment.status != "canceled"
        ).all()
    
    def create_appointment(self, appointment: Appointment) -> Appointment:
        """
        Create a new appointment in the database
        """
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
    
    def set_availability(self, availability: Availability) -> Availability:
        """
        Set availability for a clinician
        """
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        return availability
    
    def set_recurring_availability(self, pattern: RecurringAvailability) -> RecurringAvailability:
        """
        Set recurring availability pattern
        """
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        return pattern
    
    def get_clinician_appointments(self, clinician_id: str, start_date: date, end_date: date) -> List[Appointment]:
        """
        Get all appointments for a clinician within a date range
        """
        return self.db.query(Appointment).filter(
            Appointment.clinician_id == clinician_id,
            func.date(Appointment.date_time) >= start_date,
            func.date(Appointment.date_time) <= end_date
        ).all()
    
    def get_patient_appointments(self, patient_id: str) -> List[Appointment]:
        """
        Get all appointments for a patient
        """
        return self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).all()
    
    def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """
        Get an appointment by ID
        """
        return self.db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()
    
    def update_appointment(self, appointment: Appointment) -> Appointment:
        """
        Update an appointment in the database
        """
        self.db.commit()
        return appointment
    
    def list_organization_appointments(
        self,
        account_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        clinician_id: Optional[str] = None,
        patient_id: Optional[str] = None
    ) -> dict:
        """
        List appointments for an organization with pagination and filters
        """
        from app.models.patient import Patient
        from app.models.user import User
        from sqlalchemy import or_
        
        # Start with base query joining both patients and clinicians to filter by account
        # An appointment belongs to an organization if either the patient OR the clinician belongs to that organization
        query = self.db.query(Appointment).outerjoin(
            Patient, Appointment.patient_id == Patient.id
        ).outerjoin(
            User, Appointment.clinician_id == User.id
        ).filter(
            or_(
                Patient.account_id == account_id,
                User.account_id == account_id
            )
        )
        
        # Apply filters
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
            
        if date_from:
            query = query.filter(func.date(Appointment.date_time) >= date_from)
            
        if date_to:
            query = query.filter(func.date(Appointment.date_time) <= date_to)
            
        if clinician_id:
            query = query.filter(Appointment.clinician_id == clinician_id)
            
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        
        # Order by appointment date and time (most recent first)
        query = query.order_by(Appointment.date_time.desc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        appointments = query.offset(offset).limit(page_size).all()
        
        # Eager load related patient data to avoid N+1 queries
        for appointment in appointments:
            # Force load the patient relationship
            _ = appointment.patient
        
        return {
            "appointments": appointments,
            "total_count": total_count
        }
