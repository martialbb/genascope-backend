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
from app.tests.test_utils import MockDBSession, MockQuery, get_mock_db, MockAppointment, MockAvailability
from app.models.appointment import Appointment, Availability, RecurringAvailability

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
def override_dependency(mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    # Use the same mock_db instance from the mock_db fixture
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

# Mock DB fixture
@pytest.fixture
def mock_db():
    db_session = MockDBSession()
    yield db_session

# Tests with database integration
@pytest.mark.integration
class TestAppointmentsAPIIntegration:
    """
    Integration tests for the appointments API endpoints, testing DB interaction
    """
    
    @patch('app.api.appointments.get_db')
    def test_get_availability_integration(self, mock_get_db, mock_db):
        """Test getting clinician availability with DB integration"""
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Create mock availability data
        today = date.today().isoformat()
        clinician_id = "clinician-123"
        
        # Set up mock returns
        test_availability = [
            MockAvailability(
                id="avail-1",
                clinician_id=clinician_id,
                date=date.fromisoformat(today),
                time=datetime.strptime("09:00", "%H:%M").time(),
                available=True
            ),
            MockAvailability(
                id="avail-2",
                clinician_id=clinician_id,
                date=date.fromisoformat(today),
                time=datetime.strptime("09:30", "%H:%M").time(),
                available=False
            ),
        ]
        mock_db.set_query_result("Availability", test_availability)
        
        # Make request
        response = client.get(f"/api/availability?clinician_id={clinician_id}&date={today}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["clinician_id"] == clinician_id
        assert data["date"] == today
        assert "time_slots" in data
        assert len(data["time_slots"]) > 0
    
    @patch('app.api.appointments.get_db')
    def test_book_appointment_integration(self, mock_get_db, mock_db):
        """Test booking an appointment with DB integration"""
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Set up test data
        today = date.today().isoformat()
        appointment_data = {
            "clinician_id": "clinician-123",
            "date": today,
            "time": "10:00",
            "patient_id": "patient-123",
            "appointment_type": "virtual",
            "notes": "Test appointment"
        }
        
        # Make request
        response = client.post("/api/book_appointment", json=appointment_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "appointment_id" in data
        assert data["clinician_id"] == appointment_data["clinician_id"]
        assert data["patient_id"] == appointment_data["patient_id"]
        
        # Check that DB operations were called
        assert mock_db.committed == True
        
    @patch('app.api.appointments.get_db')
    def test_set_availability_integration(self, mock_get_db, mock_db):
        """Test setting clinician availability with DB integration"""
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Set up test data
        today = date.today().isoformat()
        availability_data = {
            "date": today,
            "time_slots": ["09:00", "09:30", "10:00"],
            "recurring": False
        }
        
        # Make request
        response = client.post("/api/availability/set?clinician_id=clinician-123", json=availability_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Check that DB operations were called
        assert mock_db.committed == True
        
    @patch('app.api.appointments.get_db')
    def test_update_appointment_status_integration(self, mock_get_db, mock_db):
        """Test updating appointment status with DB integration"""
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Set up mock data
        appointment_id = "appt-123"
        test_appointment = MockAppointment(
            id=appointment_id,
            clinician_id="clinician-123",
            patient_id="patient-123",
            date=date.today(),
            time="10:00",
            status="scheduled"
        )
        mock_db.set_query_result("Appointment", [test_appointment])
        
        # Make request
        response = client.put(f"/api/appointments/{appointment_id}?status=completed")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        
        # Check that DB operations were called
        assert mock_db.committed == True
        
    @patch('app.api.appointments.get_db')
    def test_appointment_workflow_integration(self, mock_get_db, mock_db):
        """Test the full appointment workflow with DB integration"""
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Step 1: Set clinician availability
        today = date.today().isoformat()
        availability_data = {
            "date": today,
            "time_slots": ["09:00", "09:30", "10:00"],
            "recurring": False
        }
        
        response = client.post("/api/availability/set?clinician_id=clinician-123", json=availability_data)
        assert response.status_code == 200
        
        # Step 2: Get availability
        response = client.get(f"/api/availability?clinician_id=clinician-123&date={today}")
        assert response.status_code == 200
        
        # Step 3: Book an appointment
        appointment_data = {
            "clinician_id": "clinician-123",
            "date": today,
            "time": "10:00",
            "patient_id": "patient-123",
            "appointment_type": "virtual",
            "notes": "Integrated test appointment"
        }
        
        response = client.post("/api/book_appointment", json=appointment_data)
        assert response.status_code == 200
        data = response.json()
        appointment_id = data["appointment_id"]
        
        # Step 4: Update appointment status
        response = client.put(f"/api/appointments/{appointment_id}?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        clinician_id = "clinician-123"
        test_date = date.today().isoformat()
        
        avail_response = client.get(f"/api/availability?clinician_id={clinician_id}&date={test_date}")
        assert avail_response.status_code == 200
        
        # Now book an appointment
        appointment_data = {
            "clinician_id": clinician_id,
            "date": test_date,
            "time": "09:00",  # First available slot
            "patient_id": "patient-123",
            "appointment_type": "virtual"
        }
        
        book_response = client.post("/api/book_appointment", json=appointment_data)
        assert book_response.status_code == 200
        
        book_data = book_response.json()
        assert book_data["clinician_id"] == clinician_id
        assert book_data["patient_id"] == appointment_data["patient_id"]
        
        # Check that database session was used correctly
        assert mock_db.committed
    
    @patch("app.api.appointments.get_db")
    def test_set_availability_integration(self, mock_get_db, mock_db):
        """
        Test setting availability with database integration
        """
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        clinician_id = "clinician-123"
        availability_data = {
            "date": date.today().isoformat(),
            "time_slots": ["09:00", "09:30", "10:00"],
            "recurring": False
        }
        
        response = client.post(f"/api/availability/set?clinician_id={clinician_id}", json=availability_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Check that database session was committed
        assert mock_db.committed
    
    @patch("app.api.appointments.get_db")
    def test_update_appointment_status_integration(self, mock_get_db, mock_db):
        """
        Test updating appointment status with database integration
        """
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Create a mock appointment to use in the test
        clinician_id = "clinician-123"
        appointment_id = "test-appointment-id"
        test_date = date.today()
        
        # Create and add a mock appointment to the database
        mock_appointment = MockAppointment(
            id=appointment_id,
            clinician_id=clinician_id,
            patient_id="patient-123",
            date=test_date,
            time=datetime.strptime("09:00", "%H:%M").time(),
            status="scheduled"
        )
        
        # Add the mock appointment to our mock database
        mock_db._query_results["Appointment"] = [mock_appointment]
        
        # Setup dates for the API call
        start_date = test_date.isoformat()
        end_date = (test_date + timedelta(days=30)).isoformat()
        
        # Update the status
        new_status = "canceled"
        update_response = client.put(f"/api/appointments/{appointment_id}?status={new_status}")
        
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["appointment_id"] == appointment_id
        assert update_data["status"] == new_status
        
        # Check that database session was committed
        assert mock_db.committed
    
    @patch("app.api.appointments.get_db")
    def test_appointment_workflow_integration(self, mock_get_db, mock_db):
        """
        Test the full appointment scheduling workflow
        """
        mock_get_db.return_value = mock_db
        
        # 1. Check clinician availability
        clinician_id = "clinician-123"
        test_date = date.today().isoformat()
        
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
        appointment_id = book_data["appointment_id"]
        
        # 3. View the booked appointment in patient's list
        patient_id = appointment_data["patient_id"]
        patient_appts_response = client.get(f"/api/appointments/patient/{patient_id}")
        assert patient_appts_response.status_code == 200
        
        # 4. Cancel the appointment
        cancel_response = client.put(f"/api/appointments/{appointment_id}?status=canceled")
        assert cancel_response.status_code == 200
        cancel_data = cancel_response.json()
        assert cancel_data["status"] == "canceled"
        
        # Check that all database operations were committed
        assert mock_db.committed
