"""
Integration tests for the appointments API.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
import json
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.auth import get_current_active_user
from app.db.database import get_db
from app.tests.test_utils import MockDBSession

client = TestClient(app)

# Mock authenticated user for tests
mock_user = {
    "id": "test_user_id",
    "email": "test@example.com",
    "name": "Test User",
    "role": "clinician"
}

# Override the dependency
@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield
    app.dependency_overrides = {}

@pytest.fixture
def mock_db():
    db_session = MockDBSession()
    return db_session

# Tests with mock service layer approach
@pytest.mark.integration
class TestAppointmentsAPIIntegration:
    """
    Integration tests for the appointments API endpoints, with proper mocking
    """
    
    @patch('app.services.appointments.AppointmentService.get_availability')
    def test_get_availability_integration(self, mock_get_avail):
        """Test getting clinician availability with proper mocking"""
        # Set up test data
        today = date.today().isoformat()
        clinician_id = "clinician-123"
        clinician_name = "Dr. Test Clinician"
        
        # Mock time slots
        mock_time_slots = [
            {"time": "09:00", "available": True},
            {"time": "09:30", "available": False},
            {"time": "10:00", "available": True},
        ]
        
        # Configure mock return value
        mock_get_avail.return_value = (clinician_name, mock_time_slots)
        
        # Make request
        response = client.get(f"/api/availability?clinician_id={clinician_id}&date={today}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["clinician_id"] == clinician_id
        assert data["date"] == today
        assert "time_slots" in data
        assert len(data["time_slots"]) > 0
    
    @patch('app.services.appointments.AppointmentService.book_appointment')
    def test_book_appointment_integration(self, mock_book):
        """Test booking an appointment with proper service mocking"""
        # Create test data
        today = date.today().isoformat()
        clinician_id = "clinician-123"
        patient_id = "patient-123"
        appointment_data = {
            "clinician_id": clinician_id,
            "date": today,
            "time": "10:00",
            "patient_id": patient_id,
            "appointment_type": "virtual",
            "notes": "Test appointment"
        }
        
        # Create mock response
        now = datetime.now()
        mock_result = {
            "id": "test-id-123",
            "clinician_id": clinician_id,
            "clinician_name": "Dr. Test Clinician",
            "patient_id": patient_id,
            "patient_name": "Test Patient",
            "date": datetime.strptime(today, "%Y-%m-%d").date(),
            "time": datetime.strptime("10:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "scheduled",
            "notes": "Test appointment",
            "confirmation_code": "TEST123",
            "created_at": now,
            "updated_at": now
        }
        
        # Configure mock
        mock_book.return_value = mock_result
        
        # Execute request
        response = client.post("/api/book_appointment", json=appointment_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["clinician_id"] == appointment_data["clinician_id"]
        assert data["patient_id"] == appointment_data["patient_id"]
    
    @patch('app.services.appointments.AppointmentService.set_availability')
    def test_set_availability_integration(self, mock_set_avail):
        """
        Test setting availability with proper service mocking
        """
        clinician_id = "clinician-123"
        today = date.today().isoformat()
        availability_data = {
            "date": today,
            "time_slots": ["09:00", "09:30", "10:00"],
            "recurring": False
        }
        
        # Create mock response
        mock_response = {
            "message": "Availability set successfully",
            "date": today,
            "time_slots": availability_data["time_slots"]
        }
        
        # Configure mock
        mock_set_avail.return_value = mock_response
        
        # Make request
        response = client.post(f"/api/availability/set?clinician_id={clinician_id}", json=availability_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Availability set successfully" in data["message"]
    
    @patch('app.services.appointments.AppointmentService.update_appointment')
    def test_update_appointment_status_integration(self, mock_update):
        """
        Test updating appointment status with proper service mocking
        """
        # Create a mock appointment
        clinician_id = "clinician-123"
        appointment_id = "test-appointment-id"
        test_date = date.today()
        now = datetime.now()
        
        # Setup mock return value for the update
        mock_update.return_value = {
            "id": appointment_id,
            "clinician_id": clinician_id,
            "clinician_name": "Dr. Test Clinician",
            "patient_id": "patient-123",
            "patient_name": "Test Patient",
            "date": test_date,
            "time": datetime.strptime("09:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "canceled",
            "notes": "Test appointment",
            "confirmation_code": "TEST123",
            "created_at": now,
            "updated_at": now
        }
        
        # Update the status using a JSON body
        new_status = "canceled"
        update_data = {"status": new_status}
        update_response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
            
        # Check response
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["id"] == appointment_id
        assert update_data["status"] == new_status
    
    @patch('app.services.appointments.AppointmentService.get_availability')
    @patch('app.services.appointments.AppointmentService.book_appointment')
    @patch('app.services.appointments.AppointmentService.update_appointment')
    def test_appointment_workflow_integration(self, mock_update, mock_book, mock_get_avail):
        """
        Test the full appointment scheduling workflow with proper service mocking
        """
        # 1. Configure mock for availability
        clinician_id = "clinician-123"
        test_date = date.today().isoformat()
        clinician_name = "Dr. Test Clinician"
        
        # Mock time slots
        mock_time_slots = [
            {"time": "09:00", "available": True},
            {"time": "09:30", "available": True},
            {"time": "10:00", "available": True}
        ]
        mock_get_avail.return_value = (clinician_name, mock_time_slots)
        
        # 2. Configure mock for booking
        now = datetime.now()
        appointment_id = "test-appointment-id"
        mock_book.return_value = {
            "id": appointment_id,
            "clinician_id": clinician_id,
            "clinician_name": clinician_name,
            "patient_id": "patient-123",
            "patient_name": "Test Patient",
            "date": datetime.strptime(test_date, "%Y-%m-%d").date(),
            "time": datetime.strptime("09:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "scheduled",
            "notes": "Test appointment",
            "confirmation_code": "TEST123",
            "created_at": now,
            "updated_at": now
        }
        
        # 3. Configure mock for update
        mock_update.return_value = {
            "id": appointment_id,
            "clinician_id": clinician_id,
            "clinician_name": clinician_name,
            "patient_id": "patient-123",
            "patient_name": "Test Patient",
            "date": datetime.strptime(test_date, "%Y-%m-%d").date(),
            "time": datetime.strptime("09:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": "canceled",
            "notes": "Test appointment",
            "confirmation_code": "TEST123",
            "created_at": now,
            "updated_at": now
        }
        
        # 1. Check clinician availability
        avail_response = client.get(f"/api/availability?clinician_id={clinician_id}&date={test_date}")
        assert avail_response.status_code == 200
        avail_data = avail_response.json()
        
        # 2. Book an appointment with an available slot
        appointment_data = {
            "clinician_id": clinician_id,
            "date": test_date,
            "time": "09:00",  # From mock data
            "patient_id": "patient-123",
            "appointment_type": "virtual"
        }
        
        book_response = client.post("/api/book_appointment", json=appointment_data)
        assert book_response.status_code == 200
        book_data = book_response.json()
        assert book_data["id"] == appointment_id
        
        # 3. Cancel the appointment using JSON body
        update_data = {"status": "canceled"}
        cancel_response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
        assert cancel_response.status_code == 200
        cancel_data = cancel_response.json()
        assert cancel_data["status"] == "canceled"
