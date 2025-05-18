# fixtures/appointment_fixtures.py
"""
Appointment-related test fixtures.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, date, timedelta

from ..mock_models import (
    create_mock_appointment,
    create_mock_availability,
    create_mock_recurring_availability
)


@pytest.fixture
def mock_appointment_db():
    """Create a mock database for appointment operations."""
    return MagicMock()


@pytest.fixture
def mock_today():
    """Return today's date."""
    return date.today()


@pytest.fixture
def mock_appointments(mock_today):
    """Return a list of mock appointments."""
    today = mock_today
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    return [
        create_mock_appointment(
            id="appt1",
            clinician_id="clinician1",
            patient_id="patient1",
            date_obj=today,
            time="09:00",
            status="scheduled"
        ),
        create_mock_appointment(
            id="appt2",
            clinician_id="clinician1",
            patient_id="patient2",
            date_obj=tomorrow,
            time="14:30",
            status="scheduled"
        ),
        create_mock_appointment(
            id="appt3",
            clinician_id="clinician2",
            patient_id="patient1",
            date_obj=next_week,
            time="11:00",
            status="scheduled"
        )
    ]


@pytest.fixture
def mock_availabilities(mock_today):
    """Return a list of mock availabilities."""
    today = mock_today
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    return [
        create_mock_availability(
            id="avail1",
            clinician_id="clinician1",
            date_obj=today,
            time="09:00"
        ),
        create_mock_availability(
            id="avail2",
            clinician_id="clinician1",
            date_obj=today,
            time="10:00"
        ),
        create_mock_availability(
            id="avail3",
            clinician_id="clinician1",
            date_obj=tomorrow,
            time="14:30"
        ),
        create_mock_availability(
            id="avail4",
            clinician_id="clinician2",
            date_obj=next_week,
            time="11:00"
        )
    ]


@pytest.fixture
def mock_recurring_availabilities():
    """Return a list of mock recurring availabilities."""
    return [
        create_mock_recurring_availability(
            id="recurring1",
            clinician_id="clinician1",
            day_of_week=0,  # Monday
            time="09:00"
        ),
        create_mock_recurring_availability(
            id="recurring2",
            clinician_id="clinician1",
            day_of_week=2,  # Wednesday
            time="14:00"
        ),
        create_mock_recurring_availability(
            id="recurring3",
            clinician_id="clinician2",
            day_of_week=4,  # Friday
            time="10:00"
        )
    ]
