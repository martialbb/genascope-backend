import pytest
from unittest.mock import MagicMock
from app.repositories.appointments import AppointmentRepository
from app.models.appointment import Appointment, Availability, RecurringAvailability
from datetime import date

@pytest.fixture
def db():
    return MagicMock()

def test_get_availability_for_date(db):
    repo = AppointmentRepository(db)
    clinician_id = 'clinician-1'
    requested_date = date.today()
    repo.db.query().filter().all.return_value = ['mock_availability']
    result = repo.get_availability_for_date(clinician_id, requested_date)
    assert result == ['mock_availability']

def test_get_booked_appointments(db):
    repo = AppointmentRepository(db)
    clinician_id = 'clinician-1'
    requested_date = date.today()
    repo.db.query().filter().all.return_value = ['mock_appointment']
    result = repo.get_booked_appointments(clinician_id, requested_date)
    assert result == ['mock_appointment']

def test_create_appointment(db):
    repo = AppointmentRepository(db)
    appointment = MagicMock()
    repo.db.add = MagicMock()
    repo.db.commit = MagicMock()
    repo.db.refresh = MagicMock()
    result = repo.create_appointment(appointment)
    repo.db.add.assert_called_once_with(appointment)
    repo.db.commit.assert_called_once()
    repo.db.refresh.assert_called_once_with(appointment)
    assert result == appointment

def test_set_availability(db):
    repo = AppointmentRepository(db)
    availability = MagicMock()
    repo.db.add = MagicMock()
    repo.db.commit = MagicMock()
    repo.db.refresh = MagicMock()
    result = repo.set_availability(availability)
    repo.db.add.assert_called_once_with(availability)
    repo.db.commit.assert_called_once()
    repo.db.refresh.assert_called_once_with(availability)
    assert result == availability

def test_set_recurring_availability(db):
    repo = AppointmentRepository(db)
    pattern = MagicMock()
    repo.db.add = MagicMock()
    repo.db.commit = MagicMock()
    repo.db.refresh = MagicMock()
    result = repo.set_recurring_availability(pattern)
    repo.db.add.assert_called_once_with(pattern)
    repo.db.commit.assert_called_once()
    repo.db.refresh.assert_called_once_with(pattern)
    assert result == pattern

def test_get_clinician_appointments(db):
    repo = AppointmentRepository(db)
    clinician_id = 'clinician-1'
    start_date = date.today()
    end_date = date.today()
    repo.db.query().filter().all.return_value = ['mock_appointment']
    result = repo.get_clinician_appointments(clinician_id, start_date, end_date)
    assert result == ['mock_appointment']

def test_get_patient_appointments(db):
    repo = AppointmentRepository(db)
    patient_id = 'patient-1'
    repo.db.query().filter().all.return_value = ['mock_appointment']
    result = repo.get_patient_appointments(patient_id)
    assert result == ['mock_appointment']

def test_get_appointment_by_id(db):
    repo = AppointmentRepository(db)
    appointment_id = 'appt-1'
    repo.db.query().filter().first.return_value = 'mock_appointment'
    result = repo.get_appointment_by_id(appointment_id)
    assert result == 'mock_appointment'

def test_update_appointment(db):
    repo = AppointmentRepository(db)
    appointment = MagicMock()
    repo.db.commit = MagicMock()
    result = repo.update_appointment(appointment)
    repo.db.commit.assert_called_once()
    assert result == appointment
