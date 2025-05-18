# Unit tests conftest.py
"""
Unit test specific fixtures and configuration.
Only mock objects should be used here, no real database connections.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Import shared fixtures
pytest.importorskip("pytest")

# Create a mock database session for unit tests
@pytest.fixture
def unit_db_session():
    """
    Create a mock database session for unit tests.
    This is different from the session used in integration tests,
    which might connect to a real test database.
    """
    mock_session = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.close = MagicMock()
    mock_session.query = MagicMock(return_value=MagicMock())
    return mock_session


@pytest.fixture
def mock_repositories():
    """
    Create a dictionary of mock repositories.
    This is useful for tests that need to mock multiple repositories.
    """
    repos = {
        "user_repository": MagicMock(),
        "lab_repository": MagicMock(),
        "appointment_repository": MagicMock(),
        "availability_repository": MagicMock(),
        "invite_repository": MagicMock(),
    }
    
    # Configure common repository methods
    for repo in repos.values():
        repo.get_all = MagicMock(return_value=[])
        repo.get = MagicMock(return_value=None)
        repo.create = MagicMock()
        repo.update = MagicMock()
        repo.delete = MagicMock()
    
    return repos


@pytest.fixture
def mock_service_dependencies(unit_db_session, mock_repositories):
    """
    Create a dictionary with common service dependencies.
    This is useful for initializing services in unit tests.
    """
    return {
        "db": unit_db_session,
        **mock_repositories
    }


# Patch environment variables that might be required by settings
@pytest.fixture(autouse=True)
def mock_env_settings():
    """
    Mock environment variables for Pydantic settings.
    This avoids validation errors when settings are imported.
    """
    with patch.dict('os.environ', {
        # Database
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/test_db',
        # Authentication
        'SECRET_KEY': 'testing_secret_key',
        'ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        # Services
        'API_BASE_URL': 'http://localhost:8000',
        # Email
        'SMTP_SERVER': 'localhost',
        'SMTP_PORT': '1025',
        'SENDER_EMAIL': 'test@example.com',
        # Lab integration
        'LAB_API_BASE_URL': 'http://localhost:9000',
        'LAB_API_KEY': 'test_api_key',
    }):
        yield
