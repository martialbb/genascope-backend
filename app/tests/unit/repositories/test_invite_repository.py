"""
Unit tests for the invite repository.

This module tests the InviteRepository class which handles database
operations for patient invitations.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid

from app.repositories.invites import InviteRepository
from app.models.invite import PatientInvite


@pytest.mark.unit
def test_get_by_token():
    """Test retrieving an invitation by token"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create mock query results
    mock_invite = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_first = MagicMock(return_value=mock_invite)
    
    # Set up the query chain
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first = mock_first
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Execute method under test
    result = repo.get_by_token("test-token-123")
    
    # Verify the result
    assert result == mock_invite
    
    # Verify query was called correctly
    mock_db.query.assert_called_once_with(PatientInvite)
    mock_query.filter.assert_called_once()


@pytest.mark.unit
def test_get_by_email():
    """Test retrieving all invitations for an email address"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create mock query results
    mock_invites = [MagicMock(), MagicMock()]
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_all = MagicMock(return_value=mock_invites)
    
    # Set up the query chain
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.all = mock_all
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Execute method under test
    result = repo.get_by_email("test@example.com")
    
    # Verify the result
    assert result == mock_invites
    
    # Verify query was called correctly
    mock_db.query.assert_called_once_with(PatientInvite)
    mock_query.filter.assert_called_once()


@pytest.mark.unit
def test_get_active_by_email():
    """Test retrieving active invitation for an email address"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create mock query results
    mock_invite = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order_by = MagicMock()
    mock_first = MagicMock(return_value=mock_invite)
    
    # Set up the query chain
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order_by
    mock_order_by.first = mock_first
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Execute method under test
    result = repo.get_active_by_email("test@example.com")
    
    # Verify the result
    assert result == mock_invite
    
    # Verify query was called correctly
    mock_db.query.assert_called_once_with(PatientInvite)
    mock_query.filter.assert_called_once()
    mock_filter.order_by.assert_called_once()


@pytest.mark.unit
def test_get_by_clinician():
    """Test retrieving invitations by clinician ID"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create mock query results
    mock_invites = [MagicMock(), MagicMock()]
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order_by = MagicMock()
    mock_all = MagicMock(return_value=mock_invites)
    
    # Set up the query chain
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_order_by
    mock_order_by.all = mock_all
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Execute method under test
    result = repo.get_by_clinician("clinician-123")
    
    # Verify the result
    assert result == mock_invites
    
    # Verify query was called correctly
    mock_db.query.assert_called_once_with(PatientInvite)
    mock_query.filter.assert_called_once()


@pytest.mark.unit
def test_get_by_clinician_with_status():
    """Test retrieving invitations by clinician ID with status filter"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create mock query results
    mock_invites = [MagicMock()]
    mock_query = MagicMock()
    mock_filter1 = MagicMock()
    mock_filter2 = MagicMock()
    mock_order_by = MagicMock()
    mock_all = MagicMock(return_value=mock_invites)
    
    # Set up the query chain
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter1
    mock_filter1.filter.return_value = mock_filter2
    mock_filter2.order_by.return_value = mock_order_by
    mock_order_by.all = mock_all
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Execute method under test
    result = repo.get_by_clinician("clinician-123", status="pending")
    
    # Verify the result
    assert result == mock_invites
    
    # Verify query was called correctly
    mock_db.query.assert_called_once_with(PatientInvite)
    mock_query.filter.assert_called_once()
    mock_filter1.filter.assert_called_once()
    mock_filter2.order_by.assert_called_once()


@pytest.mark.unit
def test_create_invite():
    """Test creating a new patient invitation"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Test data
    invite_data = {
        "clinician_id": "clinician-123",
        "email": "patient@example.com",
        "first_name": "Test",
        "last_name": "Patient",
        "status": "pending"
    }
    
    # Mock uuid generation to get predictable IDs
    mock_uuid = "test-uuid-123"
    with patch('uuid.uuid4', return_value=mock_uuid):
        # Execute method under test
        result = repo.create_invite(invite_data)
        
        # Verify result is the PatientInvite that was added to the session
        assert isinstance(result, PatientInvite)
        assert result.id == str(mock_uuid)
        assert result.invite_token == str(mock_uuid)
        assert result.email == invite_data["email"]
        assert result.status == "pending"
        
        # Verify session operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


@pytest.mark.unit
def test_update_invite():
    """Test updating a patient invitation"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create a mock invite
    mock_invite = MagicMock()
    mock_invite.id = "invite-123"
    
    # Create repository with mock db and mock get_by_id
    repo = InviteRepository(mock_db)
    repo.get_by_id = MagicMock(return_value=mock_invite)
    
    # Test data
    update_data = {
        "status": "accepted",
        "notes": "Updated notes"
    }
    
    # Execute method under test
    result = repo.update_invite("invite-123", update_data)
    
    # Verify the result
    assert result == mock_invite
    
    # Verify invite was updated correctly
    assert mock_invite.status == "accepted"
    assert mock_invite.notes == "Updated notes"
    assert hasattr(mock_invite, "updated_at")
    
    # Verify session operations
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.unit
def test_update_invite_not_found():
    """Test updating a non-existent patient invitation"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create repository with mock db and mock get_by_id
    repo = InviteRepository(mock_db)
    repo.get_by_id = MagicMock(return_value=None)
    
    # Execute method under test
    result = repo.update_invite("nonexistent-id", {"status": "accepted"})
    
    # Verify the result is None
    assert result is None
    
    # Verify session operations
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


@pytest.mark.unit
def test_mark_as_accepted():
    """Test marking an invitation as accepted"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Mock update_invite method
    mock_invite = MagicMock()
    repo.update_invite = MagicMock(return_value=mock_invite)
    
    # Execute method under test
    result = repo.mark_as_accepted("invite-123")
    
    # Verify the result
    assert result == mock_invite
    
    # Verify update_invite was called with correct parameters
    repo.update_invite.assert_called_once()
    args, kwargs = repo.update_invite.call_args
    assert args[0] == "invite-123"
    assert args[1]["status"] == "accepted"
    assert "accepted_at" in args[1]


@pytest.mark.unit
def test_mark_as_expired():
    """Test marking an invitation as expired"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Mock update_invite method
    mock_invite = MagicMock()
    repo.update_invite = MagicMock(return_value=mock_invite)
    
    # Execute method under test
    result = repo.mark_as_expired("invite-123")
    
    # Verify the result
    assert result == mock_invite
    
    # Verify update_invite was called with correct parameters
    repo.update_invite.assert_called_once()
    args, kwargs = repo.update_invite.call_args
    assert args[0] == "invite-123"
    assert args[1]["status"] == "expired"


@pytest.mark.unit
def test_revoke_invite():
    """Test revoking a patient invitation"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Mock update_invite method
    mock_invite = MagicMock()
    repo.update_invite = MagicMock(return_value=mock_invite)
    
    # Execute method under test
    result = repo.revoke_invite("invite-123")
    
    # Verify the result
    assert result == mock_invite
    
    # Verify update_invite was called with correct parameters
    repo.update_invite.assert_called_once()
    args, kwargs = repo.update_invite.call_args
    assert args[0] == "invite-123"
    assert args[1]["status"] == "revoked"


@pytest.mark.unit
def test_cleanup_expired_invites():
    """Test cleaning up expired invitations"""
    # Create a mock session
    mock_db = MagicMock()
    
    # Create mock expired invites
    mock_invite1 = MagicMock()
    mock_invite1.id = "invite-1"
    mock_invite2 = MagicMock()
    mock_invite2.id = "invite-2"
    mock_invites = [mock_invite1, mock_invite2]
    
    # Create mock query results
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_all = MagicMock(return_value=mock_invites)
    
    # Set up the query chain
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.all = mock_all
    
    # Create repository with mock db
    repo = InviteRepository(mock_db)
    
    # Mock mark_as_expired method
    repo.mark_as_expired = MagicMock(return_value=MagicMock())
    
    # Execute method under test
    result = repo.cleanup_expired_invites()
    
    # Verify the result is the count of expired invites
    assert result == 2
    
    # Verify mark_as_expired was called for each invite
    assert repo.mark_as_expired.call_count == 2
    repo.mark_as_expired.assert_any_call("invite-1")
    repo.mark_as_expired.assert_any_call("invite-2")
