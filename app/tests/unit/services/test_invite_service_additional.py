"""
Unit tests for missing functions in invite service.

This module provides additional tests for the invite service functionality
that was not already covered in the test_invite_service.py file.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException
from typing import List, Dict, Any, Tuple

from app.services.invites import InviteService
from app.models.invite import PatientInvite
from app.tests.fixtures.invite_fixtures import create_mock_invite


@pytest.mark.unit
def test_resend_invite_pending():
    """Test resending a pending invitation"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service with mock repositories
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Create a mock invite
    mock_invite = create_mock_invite(
        id="invite-123",
        status="pending",
        email="patient@example.com",
        first_name="John",
        last_name="Doe"
    )
    
    # Mock get_by_id to return our test invite
    mock_invite_repo.get_by_id.return_value = mock_invite
    
    # Mock the update_invite method
    updated_invite = create_mock_invite(
        id="invite-123",
        status="pending",
        email="patient@example.com",
        first_name="John",
        last_name="Doe",
        expires_at=datetime.utcnow() + timedelta(days=14),  # New expiration date
        custom_message="Updated message"
    )
    mock_invite_repo.update_invite.return_value = updated_invite
    
    # Execute method under test
    result = service.resend_invite("invite-123", "Updated message")
    
    # Verify result
    assert result == updated_invite
    
    # Verify repository calls
    mock_invite_repo.get_by_id.assert_called_once_with("invite-123")
    mock_invite_repo.update_invite.assert_called_once()
    
    # Verify the correct update was performed
    update_call = mock_invite_repo.update_invite.call_args[0]
    assert update_call[0] == "invite-123"  # First arg is invite ID
    assert isinstance(update_call[1]["expires_at"], datetime)
    assert update_call[1]["expires_at"] > datetime.utcnow()  # Expiry is in the future
    assert update_call[1]["custom_message"] == "Updated message"


@pytest.mark.unit
def test_resend_invite_expired():
    """Test resending an expired invitation"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service with mock repositories
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Create a mock expired invite
    mock_invite = create_mock_invite(
        id="invite-123",
        status="expired",
        email="patient@example.com",
        first_name="John",
        last_name="Doe",
        clinician_id="clinician-123"
    )
    
    # Mock get_by_id to return our test invite
    mock_invite_repo.get_by_id.return_value = mock_invite
    
    # Mock the create_invite method
    new_invite = create_mock_invite(
        id="new-invite-456",
        status="pending",
        email="patient@example.com",
        first_name="John",
        last_name="Doe",
        clinician_id="clinician-123"
    )
    mock_invite_repo.create_invite.return_value = new_invite
    
    # Execute method under test
    result = service.resend_invite("invite-123", "New message")
    
    # Verify result
    assert result == new_invite
    
    # Verify repository calls
    mock_invite_repo.get_by_id.assert_called_once_with("invite-123")
    mock_invite_repo.create_invite.assert_called_once()
    
    # Verify the correct invite data was created
    create_call = mock_invite_repo.create_invite.call_args[0][0]
    assert create_call["email"] == "patient@example.com"
    assert create_call["first_name"] == "John"
    assert create_call["last_name"] == "Doe"
    assert create_call["clinician_id"] == "clinician-123"
    assert create_call["custom_message"] == "New message"
    assert isinstance(create_call["expires_at"], datetime)
    assert create_call["expires_at"] > datetime.utcnow()  # Expiry is in the future


@pytest.mark.unit
def test_resend_invite_not_found():
    """Test exception when trying to resend a non-existent invitation"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service with mock repositories
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Mock get_by_id to return None (invite not found)
    mock_invite_repo.get_by_id.return_value = None
    
    # Execute method under test - should raise exception
    with pytest.raises(HTTPException) as excinfo:
        service.resend_invite("nonexistent-id", "New message")
    
    # Verify exception
    assert excinfo.value.status_code == 404
    assert "Invitation not found" in excinfo.value.detail
    
    # Verify repository call
    mock_invite_repo.get_by_id.assert_called_once_with("nonexistent-id")
    mock_invite_repo.create_invite.assert_not_called()
    mock_invite_repo.update_invite.assert_not_called()


@pytest.mark.unit
def test_revoke_invite():
    """Test revoking a pending invitation"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service with mock repositories
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Create a mock pending invite
    mock_invite = create_mock_invite(
        id="invite-123",
        status="pending",
        email="patient@example.com"
    )
    
    # Mock get_by_id to return our test invite
    mock_invite_repo.get_by_id.return_value = mock_invite
    
    # Mock the revoke_invite method
    revoked_invite = create_mock_invite(
        id="invite-123",
        status="revoked",
        email="patient@example.com"
    )
    mock_invite_repo.revoke_invite.return_value = revoked_invite
    
    # Execute method under test
    result = service.revoke_invite("invite-123")
    
    # Verify result
    assert result == revoked_invite
    
    # Verify repository calls
    mock_invite_repo.get_by_id.assert_called_once_with("invite-123")
    mock_invite_repo.revoke_invite.assert_called_once_with("invite-123")


@pytest.mark.unit
def test_revoke_invite_not_found():
    """Test exception when trying to revoke a non-existent invitation"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service with mock repositories
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Mock get_by_id to return None (invite not found)
    mock_invite_repo.get_by_id.return_value = None
    
    # Execute method under test - should raise exception
    with pytest.raises(HTTPException) as excinfo:
        service.revoke_invite("nonexistent-id")
    
    # Verify exception
    assert excinfo.value.status_code == 404
    assert "Invitation not found" in excinfo.value.detail
    
    # Verify repository call
    mock_invite_repo.get_by_id.assert_called_once_with("nonexistent-id")
    mock_invite_repo.revoke_invite.assert_not_called()


@pytest.mark.unit
def test_revoke_invite_non_pending():
    """Test exception when trying to revoke a non-pending invitation"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service with mock repositories
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Create a mock accepted invite
    mock_invite = create_mock_invite(
        id="invite-123",
        status="accepted",
        email="patient@example.com"
    )
    
    # Mock get_by_id to return our test invite
    mock_invite_repo.get_by_id.return_value = mock_invite
    
    # Execute method under test - should raise exception
    with pytest.raises(HTTPException) as excinfo:
        service.revoke_invite("invite-123")
    
    # Verify exception
    assert excinfo.value.status_code == 400
    assert "Invitation has already been accepted" in excinfo.value.detail
    
    # Verify repository call
    mock_invite_repo.get_by_id.assert_called_once_with("invite-123")
    mock_invite_repo.revoke_invite.assert_not_called()


@pytest.mark.unit
def test_create_bulk_invites():
    """Test creating multiple invitations at once"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service and inject mocks
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Mock the original create_invite method
    original_create_invite = service.create_invite
    
    # Create mock invites as return values
    mock_invite1 = create_mock_invite(
        id="invite-1",
        email="patient1@example.com",
        first_name="John",
        last_name="Doe"
    )
    mock_invite2 = create_mock_invite(
        id="invite-2",
        email="patient2@example.com",
        first_name="Jane",
        last_name="Smith"
    )
    
    # Create bulk data
    bulk_data = [
        {
            "email": "patient1@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "clinician_id": "clinician-123"
        },
        {
            "email": "patient2@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "clinician_id": "clinician-123"
        }
    ]
    
    # Mock create_invite to return our mock invites
    service.create_invite = MagicMock(side_effect=[mock_invite1, mock_invite2])
    
    # Execute method under test
    successful, failed = service.create_bulk_invites(bulk_data, "clinician-123")
    
    # Verify results
    assert len(successful) == 2
    assert mock_invite1 in successful
    assert mock_invite2 in successful
    assert len(failed) == 0
    
    # Verify create_invite was called for each entry in bulk_data
    assert service.create_invite.call_count == 2
    
    # Restore original method
    service.create_invite = original_create_invite


@pytest.mark.unit
def test_create_bulk_invites_with_errors():
    """Test creating multiple invitations with some failures"""
    # Create mock repositories
    mock_db = MagicMock()
    mock_invite_repo = MagicMock()
    
    # Create the service and inject mocks
    service = InviteService(mock_db)
    service.invite_repository = mock_invite_repo
    
    # Mock the original create_invite method
    original_create_invite = service.create_invite
    
    # Create a mock invite as return value for the successful one
    mock_invite = create_mock_invite(
        id="invite-1",
        email="patient1@example.com",
        first_name="John",
        last_name="Doe"
    )
    
    # Create bulk data
    bulk_data = [
        {
            "email": "patient1@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "clinician_id": "clinician-123"
        },
        {
            "email": "invalid@example.com",
            "first_name": "",  # This will cause an error
            "last_name": "Smith",
            "clinician_id": "clinician-123"
        }
    ]
    
    # Mock create_invite to return our mock invite for the first call
    # and raise an exception for the second call
    error = HTTPException(status_code=400, detail="First name is required")
    service.create_invite = MagicMock(side_effect=[mock_invite, error])
    
    # Execute method under test
    successful, failed = service.create_bulk_invites(bulk_data, "clinician-123")
    
    # Verify results
    assert len(successful) == 1
    assert mock_invite in successful
    assert len(failed) == 1
    assert failed[0]["data"] == bulk_data[1]
    assert "First name is required" in failed[0]["error"]
    
    # Verify create_invite was called for each entry in bulk_data
    assert service.create_invite.call_count == 2
    
    # Restore original method
    service.create_invite = original_create_invite


@pytest.mark.unit
def test_generate_invite_url():
    """Test generating an invitation URL"""
    # Create mock repositories
    mock_db = MagicMock()
    
    # Create the service
    service = InviteService(mock_db)
    
    # Create a mock invite
    mock_invite = create_mock_invite(
        invite_token="abc123"
    )
    
    # Execute method under test
    result = service.generate_invite_url(mock_invite, "https://example.com")
    
    # Verify result
    assert result == "https://example.com/invite/abc123"
