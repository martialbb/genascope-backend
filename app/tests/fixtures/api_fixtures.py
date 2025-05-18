# fixtures/api_fixtures.py
"""
API test fixtures.

This module provides fixtures for testing API endpoints, including
authenticated clients, request mocking, and dependency overrides.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable

from ..mock_models import create_mock_user
from ..utils import safe_import


@pytest.fixture
def api_client():
    """
    Create a basic FastAPI test client.
    
    This fixture provides a test client for making API requests without authentication.
    
    Returns:
        TestClient: A FastAPI test client
    """
    try:
        from app.main import app
        
        return TestClient(app)
    except ImportError as e:
        pytest.skip(f"Unable to import FastAPI app: {e}")
        return MagicMock()


@pytest.fixture
def mock_auth_token():
    """
    Create a mock JWT authentication token.
    
    This fixture provides a function to generate mock JWT tokens for testing.
    
    Returns:
        function: A function that generates mock JWT tokens
    """
    def create_token(user_id="test_user", role="patient", exp=None):
        """Generate a mock JWT token for testing."""
        if exp is None:
            exp = datetime.utcnow() + timedelta(hours=1)
            
        payload = {
            "sub": user_id,
            "role": role,
            "exp": exp.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        
        # Use a consistent secret key for testing
        secret_key = "test_secret_key"
        algorithm = "HS256"
        
        # Create token
        return jwt.encode(payload, secret_key, algorithm=algorithm)
    
    return create_token


@pytest.fixture
def authenticated_client(api_client, mock_auth_token):
    """
    Create an authenticated API test client.
    
    This fixture provides a test client with authorization headers set.
    
    Args:
        api_client: Base API client
        mock_auth_token: Token generation function
        
    Returns:
        TestClient: An authenticated test client
    """
    # Create a token for a test user
    token = mock_auth_token(user_id="test_user", role="patient")
    
    # Set authorization header
    api_client.headers["Authorization"] = f"Bearer {token}"
    
    return api_client


@pytest.fixture
def admin_client(api_client, mock_auth_token):
    """
    Create an API test client with admin privileges.
    
    This fixture provides a test client authenticated as an admin user.
    
    Args:
        api_client: Base API client
        mock_auth_token: Token generation function
        
    Returns:
        TestClient: An admin-authenticated test client
    """
    # Create a token for an admin user
    token = mock_auth_token(user_id="admin_user", role="admin")
    
    # Set authorization header
    api_client.headers["Authorization"] = f"Bearer {token}"
    
    return api_client


@pytest.fixture
def clinician_client(api_client, mock_auth_token):
    """
    Create an API test client with clinician privileges.
    
    This fixture provides a test client authenticated as a clinician user.
    
    Args:
        api_client: Base API client
        mock_auth_token: Token generation function
        
    Returns:
        TestClient: A clinician-authenticated test client
    """
    # Create a token for a clinician user
    token = mock_auth_token(user_id="clinician_user", role="clinician")
    
    # Set authorization header
    api_client.headers["Authorization"] = f"Bearer {token}"
    
    return api_client


@pytest.fixture
def override_auth_dependency():
    """
    Create a function to override the authentication dependency.
    
    This fixture provides a function that can be used to override the
    authentication dependency in FastAPI for testing.
    
    Returns:
        function: A function to override the auth dependency
    """
    def create_override(user_data=None):
        """Create an auth dependency override with the specified user data."""
        if user_data is None:
            user_data = create_mock_user(
                id="test_user_id",
                email="test@example.com",
                name="Test User",
                role="patient"
            )
            
        try:
            from app.main import app
            from app.api.auth import get_current_active_user
            
            # Override the dependency
            app.dependency_overrides[get_current_active_user] = lambda: user_data
            
            # Return a cleanup function
            def cleanup():
                app.dependency_overrides.pop(get_current_active_user, None)
                
            return cleanup
        except ImportError as e:
            pytest.skip(f"Unable to override auth dependency: {e}")
            return lambda: None
    
    return create_override


@pytest.fixture
def mock_service_factory():
    """
    Create a factory for mock services.
    
    This fixture provides a function to create mock services for API testing.
    
    Returns:
        function: A function that creates mock services
    """
    def create_mock_service(service_type="generic"):
        """Create a mock service of the specified type."""
        mock_service = MagicMock()
        
        if service_type == "user":
            # Configure user service methods
            mock_service.get_users.return_value = [
                create_mock_user(id="user1", email="user1@example.com"),
                create_mock_user(id="user2", email="user2@example.com")
            ]
            mock_service.get_user_by_id.side_effect = lambda id: next(
                (u for u in [
                    create_mock_user(id="user1", email="user1@example.com"),
                    create_mock_user(id="user2", email="user2@example.com")
                ] if u.id == id),
                None
            )
            mock_service.create_user.side_effect = lambda user_data: create_mock_user(**user_data)
            mock_service.update_user.side_effect = lambda id, data: create_mock_user(id=id, **data)
            mock_service.delete_user.return_value = True
            
        elif service_type == "appointment":
            # Configure appointment service methods
            from datetime import date, time
            
            mock_service.get_appointments.return_value = [
                {
                    "id": "appt1",
                    "clinician_id": "clinician1",
                    "patient_id": "patient1",
                    "date": date.today(),
                    "time": time(9, 0),
                    "status": "scheduled"
                },
                {
                    "id": "appt2",
                    "clinician_id": "clinician1",
                    "patient_id": "patient2",
                    "date": date.today() + timedelta(days=1),
                    "time": time(10, 0),
                    "status": "scheduled"
                }
            ]
            mock_service.get_appointment_by_id.side_effect = lambda id: next(
                (a for a in mock_service.get_appointments() if a["id"] == id),
                None
            )
            mock_service.book_appointment.side_effect = lambda data: {
                "id": "new-appt-id",
                "clinician_id": data.clinician_id,
                "patient_id": data.patient_id,
                "date": data.date,
                "time": data.time,
                "status": "scheduled"
            }
            
        # Configure generic methods
        mock_service.get_all.return_value = []
        mock_service.get_by_id.return_value = None
        mock_service.create.side_effect = lambda data: {**data, "id": "mock-id"}
        mock_service.update.side_effect = lambda id, data: {**data, "id": id}
        mock_service.delete.return_value = True
        
        return mock_service
    
    return create_mock_service


@pytest.fixture
def setup_api_test(api_client, override_auth_dependency, mock_service_factory):
    """
    Set up a complete environment for API testing.
    
    This fixture combines multiple fixtures to create a complete
    environment for testing API endpoints.
    
    Args:
        api_client: API test client
        override_auth_dependency: Function to override auth
        mock_service_factory: Function to create mock services
        
    Returns:
        dict: A dictionary with test clients and utilities
    """
    # Create a user for authentication
    test_user = create_mock_user(
        id="test-api-user",
        email="api-test@example.com",
        role="patient"
    )
    
    # Override auth dependency
    cleanup_auth = override_auth_dependency(test_user)
    
    # Create mock services
    user_service = mock_service_factory("user")
    appointment_service = mock_service_factory("appointment")
    
    # Set up service patches
    patches = []
    
    try:
        # Patch service dependencies
        from app.main import app
        
        # Get service dependencies to patch
        try:
            from app.api.dependencies import get_user_service
            patches.append(patch('app.api.dependencies.get_user_service', return_value=user_service))
        except ImportError:
            pass
            
        try:
            from app.api.dependencies import get_appointment_service
            patches.append(patch('app.api.dependencies.get_appointment_service', return_value=appointment_service))
        except ImportError:
            pass
        
        # Apply all patches
        for p in patches:
            p.start()
            
        # Return test environment
        return {
            "client": api_client,
            "user": test_user,
            "services": {
                "user": user_service,
                "appointment": appointment_service
            },
            "cleanup": lambda: (cleanup_auth(), [p.stop() for p in patches])
        }
        
    except ImportError as e:
        pytest.skip(f"Unable to set up API test: {e}")
        # Clean up any started patches
        for p in patches:
            try:
                p.stop()
            except:
                pass
                
        return {
            "client": api_client,
            "user": test_user,
            "services": {},
            "cleanup": lambda: None
        }
