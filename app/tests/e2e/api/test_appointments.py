"""
End-to-end tests for the appointments API.
"""
import pytest
from fastapi.testclient import TestClient
import json
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.auth import get_current_active_user
from app.core.config import settings

client = TestClient(app)

# Mock users for testing
mock_clinician = {
    "id": "clinician-123",
    "email": "clinician@example.com",
    "name": "Dr. Test Clinician",
    "role": "clinician"
}

mock_patient = {
    "id": "patient-456",
    "email": "patient@example.com",
    "name": "Test Patient",
    "role": "patient"
}

# Override the dependency for testing
@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_current_active_user] = lambda: mock_clinician
    yield
    app.dependency_overrides = {}

@pytest.mark.e2e
class TestAppointmentsE2E:
    """
    End-to-end tests for the appointments API.
    These tests use proper mocking of the service layer instead of relying on database interactions.
    """
    
    @patch('app.services.appointments.AppointmentService.get_availability')
    @patch('app.services.appointments.AppointmentService.book_appointment')
    @patch('app.services.appointments.AppointmentService.update_appointment')
    def test_appointment_scheduling_workflow(self, mock_update, mock_book, mock_get_avail):
        """Test the complete flow of setting availability and booking an appointment"""
        # Setup test data
        clinician_id = "clinician-123"
        patient_id = "patient-456"
        test_date = date.today().isoformat()
        clinician_name = "Dr. Test Clinician"
        now = datetime.now()
        
        # 1. Configure mock for availability
        mock_time_slots = [
            {"time": "09:00", "available": True},
            {"time": "09:30", "available": True},
            {"time": "10:00", "available": True}
        ]
        mock_get_avail.return_value = (clinician_name, mock_time_slots)
        
        # 2. Configure mock for booking
        appointment_id = "e2e-test-appt-id"
        mock_book.return_value = {
            "id": appointment_id,
            "clinician_id": clinician_id,
            "clinician_name": "Dr. Test Clinician",
            "patient_id": patient_id,
            "patient_name": "Test Patient",
            "date": datetime.strptime(test_date, "%Y-%m-%d").date(),
            "time": datetime.strptime("09:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "scheduled",
            "notes": "E2E test appointment",
            "confirmation_code": "E2E123",
            "created_at": now,
            "updated_at": now
        }
        
        # 3. Configure mock for update
        mock_update.return_value = {
            "id": appointment_id,
            "clinician_id": clinician_id,
            "clinician_name": "Dr. Test Clinician",
            "patient_id": patient_id,
            "patient_name": "Test Patient",
            "date": datetime.strptime(test_date, "%Y-%m-%d").date(),
            "time": datetime.strptime("09:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "confirmed",
            "notes": "E2E test appointment",
            "confirmation_code": "E2E123",
            "created_at": now,
            "updated_at": now
        }
        
        # Step 1: Check clinician availability
        avail_response = client.get(f"/api/availability?clinician_id={clinician_id}&date={test_date}")
        assert avail_response.status_code == 200
        avail_data = avail_response.json()
        assert avail_data["clinician_id"] == clinician_id
        assert avail_data["date"] == test_date
        assert len(avail_data["time_slots"]) == len(mock_time_slots)
        
        # Step 2: Book an appointment
        appointment_data = {
            "clinician_id": clinician_id,
            "date": test_date,
            "time": "09:00",
            "patient_id": patient_id,
            "appointment_type": "virtual",
            "notes": "E2E test appointment"
        }
        
        book_response = client.post("/api/book_appointment", json=appointment_data)
        assert book_response.status_code == 200
        book_data = book_response.json()
        assert book_data["id"] == appointment_id
        assert book_data["status"] == "scheduled"
        
        # Step 3: Confirm the appointment
        update_data = {"status": "confirmed"}
        confirm_response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
        assert confirm_response.status_code == 200
        confirm_data = confirm_response.json()
        assert confirm_data["id"] == appointment_id
        assert confirm_data["status"] == "confirmed"
