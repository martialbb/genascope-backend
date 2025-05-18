"""
Global test fixtures for all test levels.
This file contains shared fixtures that can be used by unit, integration, and e2e tests.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
import json
from unittest.mock import MagicMock, patch
import os
import sys

# Add application to Python path properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import fixtures from fixture modules - will be available to all tests
from .fixtures.settings_fixtures import mock_settings, with_test_settings

# Patch environment variables to avoid settings validation errors
@pytest.fixture(autouse=True)
def global_env_settings():
    """
    Mock environment variables for all tests to avoid settings validation errors.
    This is an autouse fixture that will apply for all tests.
    """
    with patch.dict('os.environ', {
        # Database
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/test_db',
        # Authentication
        'SECRET_KEY': 'testing_secret_key',
        'ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        # Add other required environment variables
        'API_BASE_URL': 'http://localhost:8000',
        'ENVIRONMENT': 'test',
    }):
        yield

# Create a test client using a mock instead of the real app
@pytest.fixture
def client():
    app = MagicMock()
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
        "slots": [
            {"time": "09:00", "available": True},
            {"time": "10:00", "available": False},
            {"time": "11:00", "available": True}
        ]
    }

# Helper fixture for mock database
@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.close = MagicMock()
    db.query = MagicMock(return_value=MagicMock())
    return db

# Utility fixtures
@pytest.fixture
def utcnow():
    """Return the current UTC datetime"""
    return datetime.utcnow()

@pytest.fixture
def future_date(days=7):
    """Return a date in the future"""
    return date.today() + timedelta(days=days)

@pytest.fixture
def past_date(days=7):
    """Return a date in the past"""
    return date.today() - timedelta(days=days)

@pytest.fixture
def mock_time_slots():
    """Return mock time slots for testing"""
    return {
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
