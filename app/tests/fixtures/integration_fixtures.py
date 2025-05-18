# Integration test fixtures
"""
Fixtures for integration tests.

This module provides fixtures specifically for integration tests,
which test how components work together.
"""
import pytest
from unittest.mock import MagicMock, patch
import os
from typing import Generator, Dict, Any, List

# Import the safe_import utility
from ..utils import safe_import


@pytest.fixture(scope="session")
def integration_db():
    """
    Set up an integration test database.
    
    This fixture provides a database session for integration tests.
    It uses an SQLite database file that's created specifically for tests.
    
    Returns:
        Session: A SQLAlchemy session connected to the test database
    """
    try:
        # Import database module
        from app.db.database import Base, get_db
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Use a file-based SQLite database for integration tests
        test_db_path = "test_integration.db"
        
        # Create database URL
        database_url = f"sqlite:///{test_db_path}"
        
        # Create engine and session
        engine = create_engine(database_url)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = TestingSessionLocal()
        
        yield db
        
        # Clean up
        db.close()
        
        # Remove the database file after tests
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
    except ImportError as e:
        pytest.skip(f"Unable to create integration database: {e}")
        yield MagicMock()


@pytest.fixture
def integration_repositories(integration_db):
    """
    Set up repositories for integration tests.
    
    This fixture creates repository instances for integration tests.
    It returns a dictionary with repository instances.
    
    Args:
        integration_db: Database session for integration tests
    
    Returns:
        Dict[str, Any]: Dictionary containing repository instances
    """
    repositories = {}
    
    try:
        # Import repository classes
        from app.repositories.user import UserRepository
        from app.repositories.lab import (
            LabIntegrationRepository, 
            LabOrderRepository, 
            LabResultRepository
        )
        
        # Create repository instances
        repositories["user"] = UserRepository(integration_db)
        repositories["lab_integration"] = LabIntegrationRepository(integration_db)
        repositories["lab_order"] = LabOrderRepository(integration_db)
        repositories["lab_result"] = LabResultRepository(integration_db)
        
    except ImportError as e:
        pytest.skip(f"Unable to import repositories: {e}")
    
    return repositories


@pytest.fixture
def integration_services(integration_db, integration_repositories):
    """
    Set up services for integration tests.
    
    This fixture creates service instances for integration tests.
    It returns a dictionary with service instances.
    
    Args:
        integration_db: Database session for integration tests
        integration_repositories: Repository instances for tests
    
    Returns:
        Dict[str, Any]: Dictionary containing service instances
    """
    services = {}
    
    try:
        # Import service classes
        from app.services.user import UserService
        from app.services.auth import AuthService
        from app.services.labs_enhanced import LabEnhancedService
        
        # Create service instances
        services["user"] = UserService(integration_db)
        services["auth"] = AuthService(integration_db)
        services["lab"] = LabEnhancedService(integration_db)
        
        # Replace repositories with test repositories
        services["lab"].lab_integration_repository = integration_repositories["lab_integration"]
        services["lab"].lab_order_repository = integration_repositories["lab_order"]
        services["lab"].lab_result_repository = integration_repositories["lab_result"]
        services["lab"].user_repository = integration_repositories["user"]
        
    except ImportError as e:
        pytest.skip(f"Unable to import services: {e}")
    
    return services


@pytest.fixture
def setup_test_data(integration_db, integration_repositories):
    """
    Set up test data for integration tests.
    
    This fixture creates test data in the integration database.
    
    Args:
        integration_db: Database session for integration tests
        integration_repositories: Repository instances for tests
    
    Returns:
        Dict[str, Any]: Dictionary containing test data references
    """
    # Import models
    try:
        from app.models.user import User, UserRole
        from app.models.lab import LabIntegration, LabOrderStatus
        
        # Create test users
        user_repo = integration_repositories["user"]
        admin = User(
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN,
            hashed_password="hashed_admin_password"
        )
        clinician = User(
            email="clinician@example.com",
            name="Test Clinician",
            role=UserRole.CLINICIAN,
            hashed_password="hashed_clinician_password"
        )
        patient = User(
            email="patient@example.com",
            name="Test Patient",
            role=UserRole.PATIENT,
            hashed_password="hashed_patient_password"
        )
        
        # Add users to database
        integration_db.add(admin)
        integration_db.add(clinician)
        integration_db.add(patient)
        
        # Create lab integration
        lab_repo = integration_repositories["lab_integration"]
        lab = LabIntegration(
            name="Test Lab",
            api_key="test_api_key",
            webhook_url="https://example.com/webhook",
            status="active"
        )
        
        # Add lab to database
        integration_db.add(lab)
        integration_db.commit()
        
        # Return test data references
        return {
            "users": {
                "admin": admin,
                "clinician": clinician,
                "patient": patient
            },
            "labs": {
                "test_lab": lab
            }
        }
        
    except ImportError as e:
        pytest.skip(f"Unable to set up test data: {e}")
        return {}
