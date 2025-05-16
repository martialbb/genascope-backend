"""
Mock models for testing.
"""
from datetime import datetime

class Appointment:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test_appointment_id')
        self.clinician_id = kwargs.get('clinician_id', 'test_clinician_id')
        self.patient_id = kwargs.get('patient_id', 'test_patient_id')
        self.date = kwargs.get('date')
        self.time = kwargs.get('time')
        self.appointment_type = kwargs.get('appointment_type', 'virtual')
        self.status = kwargs.get('status', 'scheduled')
        self.notes = kwargs.get('notes', '')
        self.confirmation_code = kwargs.get('confirmation_code', 'ABC123')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

class Availability:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test_availability_id')
        self.clinician_id = kwargs.get('clinician_id', 'test_clinician_id')
        self.date = kwargs.get('date')
        self.time = kwargs.get('time')
        self.available = kwargs.get('available', True)
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')

class RecurringAvailability:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test_recurring_id')
        self.clinician_id = kwargs.get('clinician_id', 'test_clinician_id')
        self.day_of_week = kwargs.get('day_of_week')  # 0=Monday, 6=Sunday
        self.time = kwargs.get('time')
        self.valid_until = kwargs.get('valid_until')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')

class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test_user_id')
        self.email = kwargs.get('email', 'test@example.com')
        self.name = kwargs.get('name', 'Test User')
        self.role = kwargs.get('role', 'patient')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
