"""
Direct test for appointment booking with proper mocking
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.auth import get_current_active_user

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
def override_auth():
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield
    app.dependency_overrides = {}

@pytest.mark.unit
def test_book_appointment_direct_mock():
    """Test booking an appointment with direct service mocking"""
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
