"""
Simple test for appointment creation endpoint
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.auth import get_current_active_user

# Import our fixtures
from ...fixtures.api_fixtures import override_auth_dependency

client = TestClient(app)

# Mock authenticated user for tests
mock_user = {
    "id": "test_user_id",
    "email": "test@example.com",
    "name": "Test User",
    "role": "clinician"
}

# Override the dependency - kept for backward compatibility
# In future tests, use the override_auth_dependency fixture instead
@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield
    app.dependency_overrides = {}

@pytest.mark.unit
@pytest.mark.api
def test_simple_book_appointment():
    """Simplified test to isolate the issue"""
    
    # Mock AppointmentService
    class MockAppointmentService:
        def __init__(self, db=None):
            pass
            
        def book_appointment(self, appointment_data):
            now = datetime.now()
            parsed_date = datetime.strptime(appointment_data.date, "%Y-%m-%d").date()
            parsed_time = datetime.strptime(appointment_data.time, "%H:%M").time()
            
            return {
                "id": "test-id-123",
                "clinician_id": appointment_data.clinician_id,
                "clinician_name": "Dr. Test Clinician",
                "patient_id": appointment_data.patient_id,
                "patient_name": "Test Patient",
                "date": parsed_date,
                "time": parsed_time,
                "appointment_type": appointment_data.appointment_type,
                "status": "scheduled",
                "notes": appointment_data.notes,
                "confirmation_code": "TEST123",
                "created_at": now,
                "updated_at": now
            }
    
    # Mock the database session factory
    class MockDB:
        def __init__(self):
            pass
        
        def __iter__(self):
            yield self
    
    mock_db = MockDB()
    
    # Apply our mocks
    with patch('app.api.appointments.AppointmentService', MockAppointmentService), \
         patch('app.api.appointments.get_db', return_value=mock_db):
         
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
        
        # Print response details for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        print(f"Response text: {response.text}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
@pytest.mark.unit
@pytest.mark.api
def test_mock_patch_book_appointment():
    """Even simpler test using mock.patch directly"""
    
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
    
    # Setup mock return value
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
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Patch the AppointmentService directly
    with patch('app.services.appointments.AppointmentService.book_appointment', return_value=mock_result):
        response = client.post("/api/book_appointment", json=appointment_data)
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print(f"Success! Response: {response.json()}")
            
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["clinician_id"] == appointment_data["clinician_id"]
        assert data["patient_id"] == appointment_data["patient_id"]