import pytest

@pytest.fixture
def mock_clinician_user():
    return {
        "id": "clinician-123",
        "role": "clinician",
        "email": "clinician@example.com",
        "name": "Dr. Clinician",
        # Add more fields as needed for your tests
    }

@pytest.fixture
def mock_patient_user():
    return {
        "id": "patient-456",
        "role": "patient",
        "email": "patient@example.com",
        "name": "John Patient",
        # Add more fields as needed for your tests
    }
