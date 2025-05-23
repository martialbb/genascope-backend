"""
End-to-end tests for the appointments API.
"""
import pytest
from fastapi.testclient import TestClient
import json
import jwt
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import settings
from app.tests.test_utils import MockDBSession

client = TestClient(app)

# Helper functions for E2E tests
def get_auth_token(email="clinician@example.com", password="password123", role="clinician"):
    try:
        from datetime import UTC  # Python 3.11+ approach
        payload = {
            "sub": email,
            "username": email,
            "full_name": f"Test {role.capitalize()}",
            "email": email,
            "disabled": False,
            "exp": datetime.now(UTC) + timedelta(minutes=30)
        }
    except ImportError:
        # Fallback for older Python versions
        payload = {
            "sub": email,
            "username": email,
            "full_name": f"Test {role.capitalize()}",
            "email": email,
            "disabled": False,
            "exp": datetime.utcnow() + timedelta(minutes=30)  # legacy approach
        }
    
    # Make sure we're using the same secret key as defined in auth.py
    from app.api.auth import SECRET_KEY, ALGORITHM
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def override_dependency():
    """Override authentication dependency for E2E tests"""
    from app.api.auth import get_current_active_user
    from app.db.database import get_db
    
    # Create a mock user for authentication
    mock_user = {
        "username": "test@example.com",
        "email": "test@example.com",
        "full_name": "Test User",
        "disabled": False
    }
    
    # Create a mock DB session
    mock_db = MockDBSession()
    
    # Override dependencies for testing
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    
    yield
    
    # Clean up after tests
    app.dependency_overrides = {}

@pytest.mark.e2e
class TestAppointmentsE2E:
    """
    End-to-end tests for the appointments API.
    These tests use proper mocking of the service layer instead of relying on database interactions.
    """
    
    @patch('app.services.appointments.AppointmentService.set_availability')
    @patch('app.services.appointments.AppointmentService.get_availability')
    @patch('app.services.appointments.AppointmentService.book_appointment')
    @patch('app.services.appointments.AppointmentService.update_appointment')
    def test_appointment_scheduling_workflow(self, mock_update, mock_book, mock_get_avail, mock_set_avail):
        """
        Test the complete flow of setting availability and booking an appointment
        """
        # Setup test data
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        clinician_id = "clinician_123"
        patient_id = "patient_123"
        appointment_id = "test-appointment-id"
        now = datetime.now()
        clinician_name = "Dr. Test Clinician"
        
        # 1. Get authorization token for clinician
        clinician_token = get_auth_token(role="clinician")
        clinician_headers = auth_headers(clinician_token)
        
        # 2. Configure mock for setting availability
        availability_data = {
            "date": tomorrow,
            "time_slots": ["09:00", "09:30", "10:00", "10:30"],
            "recurring": False
        }
        mock_set_avail_result = {
            "message": "Availability set successfully",
            "date": tomorrow,
            "time_slots": availability_data["time_slots"]
        }
        mock_set_avail.return_value = mock_set_avail_result
        
        # 3. Clinician sets availability
        set_avail_response = client.post(
            f"/api/availability/set?clinician_id={clinician_id}",
            headers=clinician_headers,
            json=availability_data
        )
        
        assert set_avail_response.status_code == 200
        assert "Availability set successfully" in set_avail_response.json()["message"]
        
        # 4. Get patient authorization token
        patient_token = get_auth_token(
            email="patient@example.com",
            password="password123",
            role="patient"
        )
        patient_headers = auth_headers(patient_token)
        
        # 5. Configure mock for getting availability
        mock_time_slots = [
            {"time": "09:00", "available": True},
            {"time": "09:30", "available": True},
            {"time": "10:00", "available": True},
            {"time": "10:30", "available": True},
        ]
        mock_get_avail.return_value = (clinician_name, mock_time_slots)
        
        # 6. Patient checks clinician availability
        avail_response = client.get(
            f"/api/availability?clinician_id={clinician_id}&date={tomorrow}",
            headers=patient_headers
        )
        
        assert avail_response.status_code == 200
        avail_data = avail_response.json()
        assert len(avail_data["time_slots"]) > 0
        
        # 7. Configure mock for booking appointment
        appointment_time = "09:00"
        appointment_data = {
            "clinician_id": clinician_id,
            "date": tomorrow,
            "time": appointment_time,
            "patient_id": patient_id,
            "appointment_type": "virtual",
            "notes": "E2E Test Appointment"
        }
        
        mock_booking_response = {
            "id": appointment_id,
            "clinician_id": clinician_id,
            "clinician_name": clinician_name,
            "patient_id": patient_id,
            "patient_name": "Test Patient",
            "date": datetime.strptime(tomorrow, "%Y-%m-%d").date(),
            "time": datetime.strptime(appointment_time, "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "scheduled",
            "notes": appointment_data["notes"],
            "confirmation_code": "ABC123",
            "created_at": now,
            "updated_at": now
        }
        mock_book.return_value = mock_booking_response
        
        # 8. Patient books an appointment
        book_response = client.post(
            "/api/book_appointment",
            headers=patient_headers,
            json=appointment_data
        )
        
        assert book_response.status_code == 200
        book_data = book_response.json()
        assert book_data["id"] == appointment_id
        assert book_data["clinician_id"] == clinician_id
        assert book_data["patient_id"] == patient_id
        assert book_data["status"] == "scheduled"
        
        # 9. Configure mock for updating appointment
        new_status = "canceled"
        mock_update_response = {
            **mock_booking_response,  # Use the same data as the booking response
            "status": new_status,     # But update the status
            "updated_at": now         # And the updated_at timestamp
        }
        mock_update.return_value = mock_update_response
        
        # 10. Patient cancels the appointment (using JSON body instead of query params)
        update_data = {"status": new_status}
        cancel_response = client.put(
            f"/api/appointments/{appointment_id}",
            headers=patient_headers,
            json=update_data
        )
        
        assert cancel_response.status_code == 200
        cancel_data = cancel_response.json()
        assert cancel_data["id"] == appointment_id
        assert cancel_data["status"] == new_status
