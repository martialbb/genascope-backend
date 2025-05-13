import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
import json
from unittest.mock import MagicMock, patch

from app.main import app
from app.api.auth import get_current_active_user
from app.db.database import get_db, SessionLocal

# Create a test client
@pytest.fixture
def client():
    return TestClient(app)

# Mock authenticated users for different roles
@pytest.fixture
def mock_clinician_user():
    return {
        "id": "clinician_test_id",
        "email": "clinician@example.com",
        "name": "Test Clinician",
        "role": "clinician"
    }

@pytest.fixture
def mock_patient_user():
    return {
        "id": "patient_test_id",
        "email": "patient@example.com",
        "name": "Test Patient",
        "role": "patient"
    }

@pytest.fixture
def mock_admin_user():
    return {
        "id": "admin_test_id",
        "email": "admin@example.com",
        "name": "Test Admin",
        "role": "admin"
    }

# Fixtures for auth override
@pytest.fixture
def auth_as_clinician(mock_clinician_user):
    app.dependency_overrides[get_current_active_user] = lambda: mock_clinician_user
    yield
    app.dependency_overrides = {}

@pytest.fixture
def auth_as_patient(mock_patient_user):
    app.dependency_overrides[get_current_active_user] = lambda: mock_patient_user
    yield
    app.dependency_overrides = {}

@pytest.fixture
def auth_as_admin(mock_admin_user):
    app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
    yield
    app.dependency_overrides = {}

# Mock data fixtures
@pytest.fixture
def mock_clinician_data():
    return {
        "clinician_id": "clinician-123",
        "clinician_name": "Dr. Jane Smith",
        "speciality": "Genetic Counselor",
        "email": "drsmith@example.com"
    }

@pytest.fixture
def mock_patient_data():
    return {
        "patient_id": "patient-123",
        "patient_name": "John Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1980-01-01"
    }

@pytest.fixture
def mock_appointment_data():
    today = date.today()
    return {
        "clinician_id": "clinician-123",
        "date": today.isoformat(),
        "time": "10:00",
        "patient_id": "patient-123",
        "appointment_type": "virtual",
        "notes": "Test appointment notes"
    }

@pytest.fixture
def mock_availability_data():
    return {
        "date": date.today().isoformat(),
        "clinician_id": "clinician-123",
        "clinician_name": "Dr. Jane Smith",
        "time_slots": [
            {"time": "09:00", "available": True},
            {"time": "09:30", "available": False},
            {"time": "10:00", "available": True},
            {"time": "10:30", "available": True}
        ]
    }

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    return session
