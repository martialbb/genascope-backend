# fixtures/lab_fixtures.py
"""
Lab-related test fixtures.

This module provides comprehensive fixtures for lab integration, lab order,
and lab result tests. These fixtures include mock repositories, services,
and data objects for testing lab-related functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Any, Optional, Generator

from ..mock_models import (
    create_mock_lab_integration,
    create_mock_lab_order,
    create_mock_lab_result,
    create_mock_user
)
from ..utils import safe_import, MockRepository


@pytest.fixture
def mock_lab_db():
    """Create a mock database for lab operations."""
    return MagicMock()


@pytest.fixture
def mock_lab_integrations():
    """Return a list of mock lab integrations."""
    return [
        create_mock_lab_integration(id="lab1", name="LabCorp", status="active", 
                                   api_key="lab_api_key_1", webhook_url="https://labcorp.example.com/webhook"),
        create_mock_lab_integration(id="lab2", name="Quest Diagnostics", status="active",
                                   api_key="lab_api_key_2", webhook_url="https://quest.example.com/webhook"),
        create_mock_lab_integration(id="lab3", name="Inactive Lab", status="inactive",
                                   api_key="lab_api_key_3", webhook_url="https://inactive.example.com/webhook")
    ]


@pytest.fixture
def mock_lab_orders():
    """Return a list of mock lab orders."""
    return [
        create_mock_lab_order(
            id="order1",
            patient_id="patient1",
            clinician_id="clinician1",
            integration_id="lab1",
            status="pending",
            order_details={"test_type": "genetic_panel", "priority": "normal"},
            created_at=datetime.now() - timedelta(days=1)
        ),
        create_mock_lab_order(
            id="order2",
            patient_id="patient2",
            clinician_id="clinician1",
            integration_id="lab1",
            status="completed",
            order_details={"test_type": "specific_gene", "priority": "urgent"},
            external_id="LAB-EXT-123",
            created_at=datetime.now() - timedelta(days=5)
        ),
        create_mock_lab_order(
            id="order3",
            patient_id="patient1",
            clinician_id="clinician2",
            integration_id="lab2",
            status="processing",
            order_details={"test_type": "comprehensive_panel", "priority": "normal"},
            created_at=datetime.now() - timedelta(days=2)
        )
    ]


@pytest.fixture
def mock_lab_results():
    """Return a list of mock lab results."""
    return [
        create_mock_lab_result(
            id="result1",
            order_id="order1",
            status="pending",
            result_data={
                "status": "sample_received",
                "estimated_completion": (datetime.now() + timedelta(days=7)).isoformat()
            },
            created_at=datetime.now() - timedelta(hours=12)
        ),
        create_mock_lab_result(
            id="result2",
            order_id="order2",
            status="completed",
            result_data={
                "genes": [
                    {"gene": "BRCA1", "variant": "c.68_69delAG", "significance": "pathogenic"},
                    {"gene": "BRCA2", "variant": "none", "significance": "negative"}
                ],
                "summary": "Positive for BRCA1 pathogenic variant",
                "recommendations": "Genetic counseling recommended"
            },
            created_at=datetime.now() - timedelta(days=4)
        ),
        create_mock_lab_result(
            id="result3",
            order_id="order3",
            status="processing",
            result_data={
                "status": "analysis_in_progress",
                "percent_complete": 60,
                "estimated_completion": (datetime.now() + timedelta(days=1)).isoformat()
            },
            created_at=datetime.now() - timedelta(days=1)
        )
    ]


@pytest.fixture
def mock_lab_service():
    """
    Create a mock lab service with repository mocks.
    Use this fixture when you want to test components that depend on the lab service.
    """
    mock_service = MagicMock()
    
    # Configure common service methods
    mock_service.get_integrations.return_value = [
        create_mock_lab_integration(id="lab1", name="LabCorp", status="active"),
        create_mock_lab_integration(id="lab2", name="Quest Diagnostics", status="active")
    ]
    
    mock_service.get_orders.return_value = [
        create_mock_lab_order(id="order1", patient_id="patient1", status="pending"),
        create_mock_lab_order(id="order2", patient_id="patient2", status="completed")
    ]
    
    mock_service.get_order_by_id.side_effect = lambda id: {
        "order1": create_mock_lab_order(id="order1", status="pending"),
        "order2": create_mock_lab_order(id="order2", status="completed")
    }.get(id)
    
    mock_service.get_results_for_order.side_effect = lambda order_id: {
        "order1": [create_mock_lab_result(id="result1", order_id="order1", status="pending")],
        "order2": [create_mock_lab_result(id="result2", order_id="order2", status="completed")]
    }.get(order_id, [])
    
    mock_service.create_order.side_effect = lambda **kwargs: create_mock_lab_order(
        id=str(uuid.uuid4()),
        patient_id=kwargs.get("patient_id"),
        clinician_id=kwargs.get("clinician_id"),
        integration_id=kwargs.get("integration_id"),
        status="pending",
        order_details=kwargs.get("order_details", {})
    )
    
    mock_service.update_order_status.side_effect = lambda order_id, status: {
        "order1": create_mock_lab_order(id="order1", status=status),
        "order2": create_mock_lab_order(id="order2", status=status)
    }.get(order_id)
    
    return mock_service


@pytest.fixture
def lab_integration_repository_mock():
    """
    Create a mock lab integration repository with realistic behavior.
    
    This fixture is useful for service tests that need a more
    sophisticated mock repository with stateful behavior.
    """
    repo = MagicMock()
    
    # Store labs in a "database"
    labs = [
        create_mock_lab_integration(
            id="lab1", 
            name="LabCorp", 
            status="active",
            api_key="lab_api_key_1",
            webhook_url="https://labcorp.example.com/webhook"
        ),
        create_mock_lab_integration(
            id="lab2", 
            name="Quest Diagnostics", 
            status="active",
            api_key="lab_api_key_2",
            webhook_url="https://quest.example.com/webhook"
        ),
        create_mock_lab_integration(
            id="lab3", 
            name="Inactive Lab", 
            status="inactive",
            api_key="lab_api_key_3",
            webhook_url="https://inactive.example.com/webhook"
        )
    ]
    
    # Configure stateful mock methods
    def get_all():
        return labs.copy()
    
    def get_by_id(id):
        return next((lab for lab in labs if lab.id == id), None)
    
    def get_by_name(name):
        return next((lab for lab in labs if lab.name == name), None)
    
    def get_active_labs():
        return [lab for lab in labs if lab.status == "active"]
    
    def create(lab_data):
        new_lab = create_mock_lab_integration(**lab_data)
        labs.append(new_lab)
        return new_lab
    
    def update(id, data):
        lab = get_by_id(id)
        if lab:
            for key, value in data.items():
                setattr(lab, key, value)
            lab.updated_at = datetime.now()
            return lab
        return None
    
    def delete(id):
        lab = get_by_id(id)
        if lab:
            labs.remove(lab)
            return True
        return False
    
    # Assign methods to the mock
    repo.get_all.side_effect = get_all
    repo.get_by_id.side_effect = get_by_id
    repo.get_by_name.side_effect = get_by_name
    repo.get_active_labs.side_effect = get_active_labs
    repo.create.side_effect = create
    repo.update.side_effect = update
    repo.delete.side_effect = delete
    
    return repo


@pytest.fixture
def lab_order_repository_mock():
    """
    Create a mock lab order repository with realistic behavior.
    
    This fixture is useful for service tests that need a more
    sophisticated mock repository with stateful behavior.
    """
    repo = MagicMock()
    
    # Store orders in a "database"
    orders = [
        create_mock_lab_order(
            id="order1",
            patient_id="patient1",
            clinician_id="clinician1",
            integration_id="lab1",
            status="pending",
            order_details={"test_type": "genetic_panel", "priority": "normal"},
            created_at=datetime.now() - timedelta(days=1)
        ),
        create_mock_lab_order(
            id="order2",
            patient_id="patient2",
            clinician_id="clinician1",
            integration_id="lab1",
            status="completed",
            order_details={"test_type": "specific_gene", "priority": "urgent"},
            external_id="LAB-EXT-123",
            created_at=datetime.now() - timedelta(days=5)
        ),
        create_mock_lab_order(
            id="order3",
            patient_id="patient1",
            clinician_id="clinician2",
            integration_id="lab2",
            status="processing",
            order_details={"test_type": "comprehensive_panel", "priority": "normal"},
            created_at=datetime.now() - timedelta(days=2)
        )
    ]
    
    # Configure stateful mock methods
    def get_all():
        return orders.copy()
    
    def get_by_id(id):
        return next((order for order in orders if order.id == id), None)
    
    def get_by_patient_id(patient_id):
        return [order for order in orders if order.patient_id == patient_id]
    
    def get_by_status(status):
        return [order for order in orders if order.status == status]
    
    def create(order_data):
        if "id" not in order_data:
            order_data["id"] = str(uuid.uuid4())
        new_order = create_mock_lab_order(**order_data)
        orders.append(new_order)
        return new_order
    
    def update(id, data):
        order = get_by_id(id)
        if order:
            for key, value in data.items():
                setattr(order, key, value)
            order.updated_at = datetime.now()
            return order
        return None
    
    # Assign methods to the mock
    repo.get_all.side_effect = get_all
    repo.get_by_id.side_effect = get_by_id
    repo.get_by_patient_id.side_effect = get_by_patient_id
    repo.get_by_status.side_effect = get_by_status
    repo.create.side_effect = create
    repo.update.side_effect = update
    
    return repo


@pytest.fixture
def lab_enhanced_service_with_mocks(mock_lab_db):
    """
    Create a LabEnhancedService instance with advanced mock repositories.
    
    This fixture integrates the stateful mock repositories to provide
    a comprehensive mock service for integration tests.
    
    Args:
        mock_lab_db: Mock database session
        
    Returns:
        LabEnhancedService: Service configured with stateful mocks
    """
    try:
        # Import the service class
        from app.services.labs_enhanced import LabEnhancedService
        
        # Create service with mock db
        service = LabEnhancedService(mock_lab_db)
        
        # Set up repositories with stateful mocks
        from ..utils import MockRepository
        
        # Create mock repositories
        lab_integration_repo = lab_integration_repository_mock()
        lab_order_repo = lab_order_repository_mock()
        lab_result_repo = MagicMock()
        user_repo = MagicMock()
        
        # Configure user repository to return mock users
        user_data = {
            "patient1": create_mock_user(id="patient1", role="patient", name="Patient One"),
            "patient2": create_mock_user(id="patient2", role="patient", name="Patient Two"),
            "clinician1": create_mock_user(id="clinician1", role="clinician", name="Dr. Clinician"),
            "clinician2": create_mock_user(id="clinician2", role="clinician", name="Dr. Specialist")
        }
        user_repo.get_by_id.side_effect = lambda id: user_data.get(id)
        
        # Assign repositories to service
        service.lab_integration_repository = lab_integration_repo
        service.lab_order_repository = lab_order_repo
        service.lab_result_repository = lab_result_repo
        service.user_repository = user_repo
        
        return service
    except ImportError as e:
        pytest.skip(f"Unable to import LabEnhancedService: {e}")
        return MagicMock()


def update_mock_object(mock_obj, update_data):
    """
    Helper function to update a mock object with new data.
    
    Args:
        mock_obj: The mock object to update
        update_data: Dictionary with new values
        
    Returns:
        The updated mock object
    """
    for key, value in update_data.items():
        setattr(mock_obj, key, value)
    
    # Update the updated_at timestamp
    if hasattr(mock_obj, "updated_at"):
        mock_obj.updated_at = datetime.now()
    
    return mock_obj
