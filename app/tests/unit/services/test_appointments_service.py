import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
from app.services.appointments import AppointmentService
from app.models.appointment import Appointment, Availability, RecurringAvailability
from app.schemas import AppointmentCreate, AvailabilityRequest, AppointmentUpdate, AppointmentStatus

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def service(mock_db):
    s = AppointmentService(mock_db)
    s.repository = MagicMock()
    s.user_service = MagicMock()
    return s

def test_get_availability(service):
    service.user_service.get_clinician_name.return_value = 'Dr. X'
    service.repository.get_availability_for_date.return_value = []
    service.repository.get_booked_appointments.return_value = []
    clinician, slots = service.get_availability('cid', date.today())
    assert clinician == 'Dr. X'
    assert isinstance(slots, list)

def test_book_appointment(service):
    service.repository.create_appointment = MagicMock()
    service.user_service.get_patient_name.return_value = 'Patient X'
    service.user_service.get_clinician_name.return_value = 'Dr. X'
    appt_data = AppointmentCreate(
        clinician_id='cid', patient_id='pid', date='2024-01-01', time='09:00', appointment_type='virtual', notes='note')
    result = service.book_appointment(appt_data)
    assert result['clinician_name'] == 'Dr. X'
    assert result['patient_name'] == 'Patient X'
    assert result['status'] == AppointmentStatus.SCHEDULED

def test_set_availability(service):
    service.repository.set_availability = MagicMock()
    avail = AvailabilityRequest(date='2024-01-01', time_slots=['09:00'], recurring=False, recurring_days=None, recurring_until=None)
    result = service.set_availability('cid', avail)
    assert result['message']

def test_set_availability_invalid_date(service):
    avail = AvailabilityRequest(date='bad-date', time_slots=['09:00'], recurring=False, recurring_days=None, recurring_until=None)
    with pytest.raises(Exception):
        service.set_availability('cid', avail)

def test_set_recurring_availability(service):
    service.repository.set_availability = MagicMock()
    service.repository.set_recurring_availability = MagicMock()
    avail = AvailabilityRequest(date='2024-01-01', time_slots=['09:00'], recurring=True, recurring_days=[0], recurring_until='2024-01-08')
    result = service._set_recurring_availability('cid', avail)
    assert result['message']
    assert result['dates_affected'] > 0

def test_get_clinician_appointments(service):
    appt = MagicMock(id='aid', patient_id='pid', date=date.today(), time=datetime.now().time(), appointment_type='virtual', status='scheduled')
    service.repository.get_clinician_appointments.return_value = [appt]
    service.user_service.get_patient_name.return_value = 'Patient X'
    result = service.get_clinician_appointments('cid', date.today(), date.today())
    assert 'appointments' in result
    assert result['appointments'][0]['patient_name'] == 'Patient X'

def test_get_patient_appointments(service):
    appt = MagicMock(id='aid', clinician_id='cid', date=date.today(), time=datetime.now().time(), appointment_type='virtual', status='scheduled')
    service.repository.get_patient_appointments.return_value = [appt]
    service.user_service.get_clinician_name.return_value = 'Dr. X'
    result = service.get_patient_appointments('pid')
    assert 'appointments' in result
    assert result['appointments'][0]['clinician_name'] == 'Dr. X'

def test_update_appointment_success(service):
    appt = MagicMock(id='aid', clinician_id='cid', patient_id='pid', date=date.today(), time=datetime.now().time(), appointment_type='virtual', status='scheduled', notes='n', confirmation_code='c', created_at=datetime.now(), updated_at=datetime.now())
    service.repository.get_appointment_by_id.return_value = appt
    service.repository.update_appointment.return_value = appt
    service.user_service.get_clinician_name.return_value = 'Dr. X'
    service.user_service.get_patient_name.return_value = 'Patient X'
    update = AppointmentUpdate(date='2024-01-02', time='10:00', appointment_type=None, status=None, notes='updated')
    result = service.update_appointment('aid', update)
    assert result['clinician_name'] == 'Dr. X'
    assert result['patient_name'] == 'Patient X'
    assert result['notes'] == 'updated'

def test_update_appointment_not_found(service):
    service.repository.get_appointment_by_id.return_value = None
    update = AppointmentUpdate(date=None, time=None, appointment_type=None, status=None, notes=None)
    with pytest.raises(Exception):
        service.update_appointment('aid', update)

def test_generate_confirmation_code(service):
    code = service._generate_confirmation_code(8)
    assert isinstance(code, str)
    assert len(code) == 8
