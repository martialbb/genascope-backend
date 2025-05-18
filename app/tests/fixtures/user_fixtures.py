# fixtures/user_fixtures.py
"""
User-related test fixtures.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from ..mock_models import create_mock_user, create_mock_user_profile


@pytest.fixture
def mock_user_db():
    """Create a mock database with users."""
    return MagicMock()


@pytest.fixture
def admin_user():
    """Create a mock admin user."""
    return create_mock_user(
        id="admin-123",
        email="admin@example.com",
        name="Admin User",
        role="admin"
    )


@pytest.fixture
def clinician_user():
    """Create a mock clinician user."""
    return create_mock_user(
        id="clinician-123",
        email="clinician@example.com",
        name="Test Clinician",
        role="clinician"
    )


@pytest.fixture
def patient_user():
    """Create a mock patient user."""
    return create_mock_user(
        id="patient-123",
        email="patient@example.com",
        name="Test Patient",
        role="patient"
    )


@pytest.fixture
def mock_users():
    """Create a list of mock users."""
    return [
        create_mock_user(id="user1", email="user1@example.com", role="patient"),
        create_mock_user(id="user2", email="user2@example.com", role="clinician"),
        create_mock_user(id="user3", email="user3@example.com", role="admin")
    ]


@pytest.fixture
def user_with_profile():
    """Create a mock user with a profile."""
    user = create_mock_user(id="profile-user", email="profile@example.com")
    profile = create_mock_user_profile(
        id="profile-123",
        user_id=user.id,
        date_of_birth="1990-01-01",
        phone="555-123-4567",
        address="123 Test St, City, ST 12345",
        preferences={"notifications": True, "theme": "light"}
    )
    user.profile = profile
    return user
