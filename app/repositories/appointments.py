from datetime import date, datetime, time
from typing import List, Optional, Type
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
            Appointment.date == requested_date,
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
            Appointment.date >= start_date,
            Appointment.date <= end_date
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
