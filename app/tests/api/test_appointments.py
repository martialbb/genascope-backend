"""
Tests for the appointments API.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.auth import get_current_active_user
from app.schemas import TimeSlot, AppointmentCreate, AvailabilityResponse, AppointmentResponse
from app.core.config import settings

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

class TestAppointmentsAPIUpdated:
    """
    Test cases for the appointments API endpoints
    """
    
    @patch('app.services.appointments.AppointmentService.get_availability')
    def test_get_availability(self, mock_get_avail):
        """
        Test getting clinician availability for a specific date
        """
        clinician_id = "clinician-123"
        test_date = date.today().isoformat()
        clinician_name = "Dr. Test Clinician"
        
        # Mock the time slots
        mock_time_slots = [
            {"time": "09:00", "available": True},
            {"time": "09:30", "available": False},
            {"time": "10:00", "available": True},
            {"time": "10:30", "available": True},
            {"time": "11:00", "available": False}
        ]
        
        # Configure mock return value
        mock_get_avail.return_value = (clinician_name, mock_time_slots)
        
        # Make the request
        response = client.get(f"/api/availability?clinician_id={clinician_id}&date={test_date}")
        
        # Assert on the response
        assert response.status_code == 200
        data = response.json()
        assert data["clinician_id"] == clinician_id
        assert data["date"] == test_date
        assert "time_slots" in data
        assert isinstance(data["time_slots"], list)
        assert len(data["time_slots"]) > 0
        assert all(isinstance(slot["time"], str) for slot in data["time_slots"])
        assert all(isinstance(slot["available"], bool) for slot in data["time_slots"])
        
        # Check proper time slot format
        for slot in data["time_slots"]:
            assert len(slot["time"]) == 5  # Should be in format "HH:MM"
            hour, minute = slot["time"].split(":")
            assert 0 <= int(hour) <= 23
            assert 0 <= int(minute) <= 59
    
    def test_get_availability_invalid_date(self):
        """
        Test error handling for invalid date format
        """
        clinician_id = "clinician-123"
        invalid_date = "not-a-date"
        
        response = client.get(f"/api/availability?clinician_id={clinician_id}&date={invalid_date}")
        
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]
        
    @patch('app.services.appointments.AppointmentService.get_availability')
    def test_get_availability_weekend_date(self, mock_get_avail):
        """
        Test getting availability for a weekend date
        """
        clinician_id = "clinician-123"
        clinician_name = "Dr. Test Clinician"
        
        # Find the next Saturday
        test_date = date.today()
        while test_date.weekday() != 5:  # 5 is Saturday
            test_date += timedelta(days=1)
            
        # Mock the time slots (might be empty on weekends)
        mock_time_slots = [
            {"time": "09:00", "available": False},
            {"time": "09:30", "available": False},
            {"time": "10:00", "available": False},
        ]
        
        # Configure mock return value
        mock_get_avail.return_value = (clinician_name, mock_time_slots)
            
        response = client.get(f"/api/availability?clinician_id={clinician_id}&date={test_date.isoformat()}")
        
        # Even on weekends, the API should return a successful response
        assert response.status_code == 200
        data = response.json()
        assert "time_slots" in data
    
    @patch('app.services.appointments.AppointmentService.book_appointment')
    def test_book_appointment(self, mock_book):
        """
        Test booking an appointment
        """
        # Prepare test data
        today = date.today().isoformat()
        appointment_data = {
            "clinician_id": "clinician-123",
            "date": today,
            "time": "10:00",
            "patient_id": "patient-123",
            "appointment_type": "virtual",
            "notes": "Test appointment"
        }
        
        # Create mock return value
        now = datetime.now()
        mock_result = {
            "id": "test-id-123",
            "clinician_id": "clinician-123",
            "clinician_name": "Dr. Test Clinician",
            "patient_id": "patient-123",
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
        
        # Make request
        response = client.post("/api/book_appointment", json=appointment_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["clinician_id"] == appointment_data["clinician_id"]
        assert data["patient_id"] == appointment_data["patient_id"]
        assert data["appointment_type"] == appointment_data["appointment_type"]
        assert data["status"] == "scheduled"
        assert "confirmation_code" in data
    
    @patch('app.services.appointments.AppointmentService.set_availability')
    def test_set_clinician_availability(self, mock_set_avail):
        """
        Test setting clinician availability
        """
        clinician_id = "clinician-123"
        availability_data = {
            "date": date.today().isoformat(),
            "time_slots": ["09:00", "09:30", "10:00"],
            "recurring": False
        }
        
        # Create mock response
        mock_response = {
            "message": "Availability set successfully",
            "date": availability_data["date"],
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
        assert data["date"] == availability_data["date"]
        assert data["time_slots"] == availability_data["time_slots"]
    
    @patch('app.services.appointments.AppointmentService.set_availability')
    def test_set_recurring_availability(self, mock_set_avail):
        """
        Test setting recurring availability
        """
        clinician_id = "clinician-123"
        today = date.today()
        end_date = today + timedelta(days=14)
        
        availability_data = {
            "date": today.isoformat(),
            "time_slots": ["09:00", "09:30", "10:00"],
            "recurring": True,
            "recurring_days": [1, 3, 5],  # Mon, Wed, Fri
            "recurring_until": end_date.isoformat()
        }
        
        # Create mock response
        mock_response = {
            "message": "Recurring availability set successfully",
            "dates_affected": 6,
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
        assert "Recurring availability set successfully" in data["message"]
        assert "dates_affected" in data
        assert data["dates_affected"] > 0
    
    @patch('app.services.appointments.AppointmentService.get_clinician_appointments')
    def test_get_clinician_appointments(self, mock_get_appointments):
        """
        Test getting a clinician's appointments
        """
        clinician_id = "clinician-123"
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=30)).isoformat()
        
        # Create mock response
        mock_appointments = [
            {
                "appointment_id": "appt-1",
                "patient_id": "patient-123",
                "patient_name": "Test Patient",
                "date_time": f"{start_date}T09:00:00Z",
                "appointment_type": "virtual",
                "status": "scheduled"
            },
            {
                "appointment_id": "appt-2",
                "patient_id": "patient-456",
                "patient_name": "Another Patient",
                "date_time": f"{start_date}T10:00:00Z",
                "appointment_type": "in-person",
                "status": "completed"
            }
        ]
        
        mock_response = {
            "clinician_id": clinician_id,
            "appointments": mock_appointments
        }
        
        # Configure mock
        mock_get_appointments.return_value = mock_response
        
        # Make request
        response = client.get(
            f"/api/appointments/clinician/{clinician_id}?start_date={start_date}&end_date={end_date}"
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "clinician_id" in data
        assert "appointments" in data
        assert isinstance(data["appointments"], list)
    
    @patch('app.services.appointments.AppointmentService.get_patient_appointments')
    def test_get_patient_appointments(self, mock_get_appointments):
        """
        Test getting a patient's appointments
        """
        patient_id = "patient-123"
        
        # Create mock response
        mock_appointments = [
            {
                "appointment_id": "appt-1",
                "clinician_id": "clinician-123",
                "clinician_name": "Dr. Test Clinician",
                "date_time": f"{date.today().isoformat()}T09:00:00Z",
                "appointment_type": "virtual",
                "status": "scheduled"
            },
            {
                "appointment_id": "appt-2",
                "clinician_id": "clinician-456",
                "clinician_name": "Dr. Another Clinician",
                "date_time": f"{(date.today() + timedelta(days=7)).isoformat()}T10:00:00Z",
                "appointment_type": "in-person",
                "status": "scheduled"
            }
        ]
        
        mock_response = {
            "patient_id": patient_id,
            "appointments": mock_appointments
        }
        
        # Configure mock
        mock_get_appointments.return_value = mock_response
        
        # Make request
        response = client.get(f"/api/appointments/patient/{patient_id}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "patient_id" in data
        assert "appointments" in data
        assert isinstance(data["appointments"], list)
    
    @patch('app.services.appointments.AppointmentService.update_appointment')
    def test_update_appointment_status(self, mock_update):
        """
        Test updating an appointment status
        """
        appointment_id = "12345"
        new_status = "canceled"
        
        # Create mock response
        now = datetime.now()
        mock_response = {
            "id": appointment_id,
            "clinician_id": "clinician-123",
            "clinician_name": "Dr. Test Clinician",
            "patient_id": "patient-123",
            "patient_name": "Test Patient",
            "date": date.today(),
            "time": datetime.strptime("09:00", "%H:%M").time(),
            "appointment_type": "virtual",
            "status": new_status,
            "notes": "Test appointment",
            "confirmation_code": "TEST123",
            "created_at": now,
            "updated_at": now
        }
        
        # Configure mock
        mock_update.return_value = mock_response
        
        # Make request with JSON body
        update_data = {"status": new_status}
        response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == appointment_id
        assert data["status"] == new_status
        assert "updated_at" in data
    
    def test_update_appointment_invalid_status(self):
        """
        Test error handling for invalid appointment status
        """
        appointment_id = "12345"
        invalid_status = "invalid-status"  # This is not a valid enum value
        
        # Make request with invalid status value
        update_data = {"status": invalid_status}
        response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
        
        # The FastAPI validation should catch this before it reaches our handler
        assert response.status_code == 422
        error_data = response.json()
        assert "validation_error" in str(error_data).lower() or "invalid" in str(error_data).lower()
