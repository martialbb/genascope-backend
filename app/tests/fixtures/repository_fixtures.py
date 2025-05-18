# fixtures/repository_fixtures.py
"""
Repository fixtures for testing.
"""
import pytest
from unittest.mock import MagicMock
from ..utils import MockRepository
from ..mock_models import (
    create_mock_user,
    create_mock_lab_integration,
    create_mock_lab_order,
    create_mock_lab_result,
    create_mock_appointment,
    create_mock_availability
)


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository"""
    repo = MagicMock()
    
    # Set up mock users
    mock_users = {
        "patient1": create_mock_user(id="patient1", name="Patient One", role="patient"),
        "patient2": create_mock_user(id="patient2", name="Patient Two", role="patient"),
        "clinician1": create_mock_user(id="clinician1", name="Dr. One", role="clinician"),
        "clinician2": create_mock_user(id="clinician2", name="Dr. Two", role="clinician"),
        "admin1": create_mock_user(id="admin1", name="Admin One", role="admin")
    }
    
    # Configure mock methods
    repo.get_all.return_value = list(mock_users.values())
    repo.get_by_id.side_effect = lambda id: mock_users.get(id)
    repo.get_by_email.side_effect = lambda email: next(
        (u for u in mock_users.values() if u.email == email), None
    )
    repo.get_by_role.side_effect = lambda role: [
        u for u in mock_users.values() if u.role == role
    ]
    
    return repo


@pytest.fixture
def mock_lab_integration_repository():
    """Create a mock lab integration repository"""
    repo = MagicMock()
    
    # Set up mock lab integrations
    mock_integrations = {
        "lab1": create_mock_lab_integration(id="lab1", name="Lab One", status="active"),
        "lab2": create_mock_lab_integration(id="lab2", name="Lab Two", status="inactive"),
        "lab3": create_mock_lab_integration(id="lab3", name="Lab Three", status="active")
    }
    
    # Configure mock methods
    repo.get_all.return_value = list(mock_integrations.values())
    repo.get_by_id.side_effect = lambda id: mock_integrations.get(id)
    repo.get_active.return_value = [
        i for i in mock_integrations.values() if i.status == "active"
    ]
    
    return repo


@pytest.fixture
def mock_lab_order_repository():
    """Create a mock lab order repository"""
    repo = MagicMock()
    
    # Set up mock lab orders
    mock_orders = {
        "order1": create_mock_lab_order(
            id="order1", 
            patient_id="patient1", 
            clinician_id="clinician1", 
            integration_id="lab1",
            status="pending"
        ),
        "order2": create_mock_lab_order(
            id="order2", 
            patient_id="patient1", 
            clinician_id="clinician1",
            integration_id="lab1", 
            status="completed"
        ),
        "order3": create_mock_lab_order(
            id="order3", 
            patient_id="patient2", 
            clinician_id="clinician2",
            integration_id="lab3", 
            status="cancelled"
        )
    }
    
    # Configure mock methods
    repo.get_all.return_value = list(mock_orders.values())
    repo.get_by_id.side_effect = lambda id: mock_orders.get(id)
    
    repo.get_by_patient.side_effect = lambda patient_id: [
        o for o in mock_orders.values() if o.patient_id == patient_id
    ]
    
    repo.get_by_clinician.side_effect = lambda clinician_id: [
        o for o in mock_orders.values() if o.clinician_id == clinician_id
    ]
    
    return repo


@pytest.fixture
def mock_lab_result_repository():
    """Create a mock lab result repository"""
    repo = MagicMock()
    
    # Set up mock lab results
    mock_results = {
        "result1": create_mock_lab_result(
            id="result1", 
            order_id="order2",
            result_data={"test_type": "BRCA1", "result": "POSITIVE"}
        ),
        "result2": create_mock_lab_result(
            id="result2", 
            order_id="order2",
            result_data={"test_type": "BRCA2", "result": "NEGATIVE"}
        )
    }
    
    # Configure mock methods
    repo.get_all.return_value = list(mock_results.values())
    repo.get_by_id.side_effect = lambda id: mock_results.get(id)
    
    repo.get_by_order.side_effect = lambda order_id: [
        r for r in mock_results.values() if r.order_id == order_id
    ]
    
    return repo


@pytest.fixture
def mock_appointment_repository():
    """Create a mock appointment repository"""
    repo = MagicMock()
    
    # Set up mock appointments
    mock_appointments = {
        "appt1": create_mock_appointment(
            id="appt1",
            patient_id="patient1",
            clinician_id="clinician1",
            date_obj="2025-05-20",
            time="09:00",
            status="scheduled"
        ),
        "appt2": create_mock_appointment(
            id="appt2",
            patient_id="patient2",
            clinician_id="clinician1",
            date_obj="2025-05-21",
            time="10:00",
            status="completed"
        ),
        "appt3": create_mock_appointment(
            id="appt3",
            patient_id="patient1",
            clinician_id="clinician2",
            date_obj="2025-05-22",
            time="11:00",
            status="cancelled"
        )
    }
    
    # Configure mock methods
    repo.get_all.return_value = list(mock_appointments.values())
    repo.get_by_id.side_effect = lambda id: mock_appointments.get(id)
    
    repo.get_by_patient.side_effect = lambda patient_id: [
        a for a in mock_appointments.values() if a.patient_id == patient_id
    ]
    
    repo.get_by_clinician.side_effect = lambda clinician_id: [
        a for a in mock_appointments.values() if a.clinician_id == clinician_id
    ]
    
    return repo


@pytest.fixture
def mock_availability_repository():
    """Create a mock availability repository"""
    repo = MagicMock()
    
    # Set up mock availabilities
    mock_availabilities = {
        "avail1": create_mock_availability(
            id="avail1",
            clinician_id="clinician1",
            date_obj="2025-05-20",
            time="09:00",
            available=True
        ),
        "avail2": create_mock_availability(
            id="avail2",
            clinician_id="clinician1",
            date_obj="2025-05-20",
            time="10:00",
            available=False
        ),
        "avail3": create_mock_availability(
            id="avail3",
            clinician_id="clinician2",
            date_obj="2025-05-21",
            time="11:00",
            available=True
        )
    }
    
    # Configure mock methods
    repo.get_all.return_value = list(mock_availabilities.values())
    repo.get_by_id.side_effect = lambda id: mock_availabilities.get(id)
    
    repo.get_by_clinician_and_date.side_effect = lambda clinician_id, date_str: [
        a for a in mock_availabilities.values() 
        if a.clinician_id == clinician_id and a.date == date_str
    ]
    
    return repo


@pytest.fixture
def mock_repositories():
    """Create a dictionary of all mock repositories for convenience"""
    # Create mock repositories using MockRepository from utils
    user_repo = MockRepository([
        create_mock_user(id="patient1", name="Patient One", role="patient"),
        create_mock_user(id="clinician1", name="Dr. One", role="clinician"),
        create_mock_user(id="admin1", name="Admin One", role="admin")
    ])
    
    lab_integration_repo = MockRepository([
        create_mock_lab_integration(id="lab1", name="Lab One", status="active"),
        create_mock_lab_integration(id="lab2", name="Lab Two", status="inactive")
    ])
    
    lab_order_repo = MockRepository([
        create_mock_lab_order(
            id="order1", 
            patient_id="patient1", 
            clinician_id="clinician1", 
            status="pending"
        ),
        create_mock_lab_order(
            id="order2", 
            patient_id="patient1", 
            clinician_id="clinician1", 
            status="completed"
        )
    ])
    
    appointment_repo = MockRepository([
        create_mock_appointment(
            id="appt1",
            patient_id="patient1",
            clinician_id="clinician1",
            date_obj="2025-05-20",
            status="scheduled"
        )
    ])
    
    return {
        "user_repository": user_repo,
        "lab_integration_repository": lab_integration_repo,
        "lab_order_repository": lab_order_repo,
        "lab_result_repository": MockRepository([]),
        "appointment_repository": appointment_repo,
        "availability_repository": MockRepository([])
    }
