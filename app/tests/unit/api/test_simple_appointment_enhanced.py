# test_simple_appointment_enhanced.py
"""
Enhanced test for appointment creation endpoint using the new testing framework
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, time
from unittest.mock import patch, MagicMock

# Import our fixtures
from ...fixtures.api_fixtures import (
    api_client, 
    authenticated_client,
    override_auth_dependency
)
from ...mock_models import (
    create_mock_user,
    create_mock_appointment
)


@pytest.mark.unit
@pytest.mark.api
class TestAppointmentEndpoints:
    """
    Tests for appointment API endpoints using the enhanced testing framework.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        """Set up the test environment for each test."""
        self.client = api_client
        
        # Create a mock user for authentication
        self.mock_user = create_mock_user(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            role="clinician"
        )
        
        # Override the auth dependency
        from app.api.auth import get_current_active_user
        from app.main import app
        
        app.dependency_overrides[get_current_active_user] = lambda: self.mock_user
        
        yield
        
        # Clean up
        app.dependency_overrides = {}
    
    def test_simple_book_appointment(self):
        """Test booking an appointment with mock service."""
        
        # Create a mock appointment for the service to return
        today = date.today()
        mock_appt = create_mock_appointment(
            id="test-id-123",
            clinician_id="clinician-123",
            patient_id="patient-123",
            date_obj=today,
            time_str="10:00",
            appointment_type="virtual",
            notes="Test appointment"
        )
        
        # Mock the appointment service
        mock_service = MagicMock()
        mock_service.book_appointment.return_value = {
            "id": mock_appt.id,
            "clinician_id": mock_appt.clinician_id,
            "clinician_name": mock_appt.clinician_name,
            "patient_id": mock_appt.patient_id,
            "patient_name": mock_appt.patient_name,
            "date": mock_appt.date,
            "time": mock_appt.time,
            "appointment_type": mock_appt.appointment_type,
            "status": mock_appt.status,
            "notes": mock_appt.notes,
            "confirmation_code": mock_appt.confirmation_code,
            "created_at": mock_appt.created_at,
            "updated_at": mock_appt.updated_at
        }
        
        # Mock the database session factory
        mock_db = MagicMock()
        
        # Apply our mocks
        with patch('app.api.appointments.AppointmentService', return_value=mock_service), \
             patch('app.api.appointments.get_db', return_value=mock_db):
             
            # Set up test data
            appointment_data = {
                "clinician_id": "clinician-123",
                "date": today.isoformat(),
                "time": "10:00",
                "patient_id": "patient-123",
                "appointment_type": "virtual",
                "notes": "Test appointment"
            }
            
            # Make request
            response = self.client.post("/api/book_appointment", json=appointment_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["id"] == mock_appt.id
            assert data["clinician_id"] == mock_appt.clinician_id
            assert data["patient_id"] == mock_appt.patient_id
    
    def test_mock_patch_book_appointment(self):
        """Test booking an appointment by patching the service method directly."""
        
        # Set up test data
        today = date.today()
        appointment_data = {
            "clinician_id": "clinician-123",
            "date": today.isoformat(),
            "time": "10:00",
            "patient_id": "patient-123",
            "appointment_type": "virtual",
            "notes": "Test appointment"
        }
        
        # Setup mock return value using our mock model factory
        mock_result = create_mock_appointment(
            id="test-id-123",
            clinician_id="clinician-123",
            patient_id="patient-123",
            date_obj=today,
            time_str="10:00",
            appointment_type="virtual",
            notes="Test appointment",
            status="scheduled",
            confirmation_code="TEST123"
        )
        
        # Convert the mock to a dict for the return value
        mock_return = {
            "id": mock_result.id,
            "clinician_id": mock_result.clinician_id,
            "clinician_name": mock_result.clinician_name,
            "patient_id": mock_result.patient_id,
            "patient_name": mock_result.patient_name,
            "date": mock_result.date,
            "time": mock_result.time,
            "appointment_type": mock_result.appointment_type,
            "status": mock_result.status,
            "notes": mock_result.notes,
            "confirmation_code": mock_result.confirmation_code,
            "created_at": mock_result.created_at,
            "updated_at": mock_result.updated_at
        }
        
        # Patch the AppointmentService.book_appointment method directly
        with patch('app.services.appointments.AppointmentService.book_appointment', return_value=mock_return):
            response = self.client.post("/api/book_appointment", json=appointment_data)
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["id"] == mock_result.id
            assert data["clinician_id"] == appointment_data["clinician_id"]
            assert data["patient_id"] == appointment_data["patient_id"]
    
    def test_validation_errors(self):
        """Test validation errors when booking an appointment."""
        
        # Set up invalid data (missing required fields)
        invalid_data = {
            "clinician_id": "clinician-123",
            # Missing date
            "time": "10:00",
            # Missing patient_id
            "appointment_type": "virtual"
        }
        
        # Make request
        response = self.client.post("/api/book_appointment", json=invalid_data)
        
        # Check response
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data
        
        # The response should contain validation errors
        errors = data["detail"]
        error_fields = [error["loc"][1] for error in errors]
        assert "date" in error_fields  # Should have error for missing date
        assert "patient_id" in error_fields  # Should have error for missing patient_id