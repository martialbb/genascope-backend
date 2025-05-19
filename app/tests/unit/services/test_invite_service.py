"""
Unit tests for the Invite service
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid

# We'll use mocks instead of actual models
# from app.models.invite import PatientInvite
from app.schemas import UserRole
# from app.models.user import User, UserRole


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return MagicMock()


@pytest.fixture
def invite_service(mock_db):
    """Create an InviteService instance with mock repositories"""
    # Import here to avoid SQLAlchemy initialization issues
    from app.services.invites import InviteService
    
    service = InviteService(mock_db)
    service.invite_repository = MagicMock()
    service.user_repository = MagicMock()
    service.user_service = MagicMock()
    return service


def test_create_invite(invite_service):
    """Test creating a new patient invitation"""
    # Arrange
    clinician_id = "test-clinician-id"
    clinician = MagicMock()
    clinician.id = clinician_id
    clinician.email = "clinician@example.com"
    clinician.name = "Test Clinician"
    clinician.role = UserRole.CLINICIAN  # Using enum value instead of string
    
    invite_data = {
        "email": "patient@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
        "clinician_id": clinician_id,
        "custom_message": "Please join our practice"
    }
    
    mock_invite = MagicMock()
    mock_invite.id = "test-invite-id"
    mock_invite.email = invite_data["email"]
    mock_invite.first_name = invite_data["first_name"]
    mock_invite.last_name = invite_data["last_name"]
    mock_invite.phone = invite_data["phone"]
    mock_invite.clinician_id = clinician_id
    mock_invite.invite_token = "test-token"
    mock_invite.status = "pending"
    mock_invite.custom_message = invite_data["custom_message"]
    mock_invite.created_at = datetime.utcnow()
    mock_invite.expires_at = datetime.utcnow() + timedelta(days=14)
    
    invite_service.user_repository.get_by_id.return_value = clinician
    invite_service.invite_repository.get_active_by_email.return_value = None
    invite_service.invite_repository.create_invite.return_value = mock_invite
    
    # Act
    result = invite_service.create_invite(invite_data)
    
    # Assert
    assert result == mock_invite
    invite_service.user_repository.get_by_id.assert_called_once_with(clinician_id)
    invite_service.invite_repository.get_active_by_email.assert_called_once_with(invite_data["email"])
    invite_service.invite_repository.create_invite.assert_called_once_with(invite_data)


def test_create_invite_invalid_clinician(invite_service):
    """Test exception when clinician doesn't exist"""
    # Arrange
    clinician_id = "invalid-clinician-id"
    
    invite_data = {
        "email": "patient@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "clinician_id": clinician_id
    }
    
    invite_service.user_repository.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        invite_service.create_invite(invite_data)
    
    assert excinfo.value.status_code == 404
    assert "Clinician not found" in str(excinfo.value.detail)


def test_create_invite_existing_invite(invite_service):
    """Test handling existing invite for the same email"""
    # Arrange
    clinician_id = "test-clinician-id"
    clinician = MagicMock()
    clinician.id = clinician_id
    clinician.email = "clinician@example.com"
    clinician.name = "Test Clinician"
    clinician.role = UserRole.CLINICIAN
    
    invite_data = {
        "email": "patient@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "clinician_id": clinician_id
    }
    
    existing_invite = MagicMock()
    existing_invite.id="existing-invite-id"
    existing_invite.email=invite_data["email"]
    existing_invite.first_name=invite_data["first_name"]
    existing_invite.last_name=invite_data["last_name"]
    existing_invite.clinician_id=clinician_id
    existing_invite.invite_token="existing-token"
    existing_invite.status="pending"
    existing_invite.created_at=datetime.utcnow()
    existing_invite.expires_at=datetime.utcnow() + timedelta(days=14)
    
    invite_service.user_repository.get_by_id.return_value = clinician
    invite_service.invite_repository.get_active_by_email.return_value = existing_invite
    
    # Act
    result = invite_service.create_invite(invite_data)
    
    # Assert
    assert result == existing_invite
    invite_service.user_repository.get_by_id.assert_called_once_with(clinician_id)
    invite_service.invite_repository.get_active_by_email.assert_called_once_with(invite_data["email"])
    invite_service.invite_repository.create_invite.assert_not_called()


def test_verify_invite_valid(invite_service):
    """Test verifying a valid invitation token"""
    # Arrange
    token = "valid-token"
    mock_invite = MagicMock()
    mock_invite.id = "test-invite-id"
    mock_invite.email = "patient@example.com"
    mock_invite.first_name = "John"
    mock_invite.last_name = "Doe"
    mock_invite.clinician_id = "test-clinician-id"
    mock_invite.invite_token = token
    mock_invite.status = "pending"
    mock_invite.created_at = datetime.utcnow()
    mock_invite.expires_at = datetime.utcnow() + timedelta(days=14)
    
    invite_service.invite_repository.get_by_token.return_value = mock_invite
    
    # Act
    is_valid, invite, error = invite_service.verify_invite(token)
    
    # Assert
    assert is_valid is True
    assert invite == mock_invite
    assert error is None
    invite_service.invite_repository.get_by_token.assert_called_once_with(token)


def test_verify_invite_invalid_token(invite_service):
    """Test verifying an invalid invitation token"""
    # Arrange
    token = "invalid-token"
    invite_service.invite_repository.get_by_token.return_value = None
    
    # Act
    is_valid, invite, error = invite_service.verify_invite(token)
    
    # Assert
    assert is_valid is False
    assert invite is None
    assert error == "Invalid invitation token"
    invite_service.invite_repository.get_by_token.assert_called_once_with(token)


def test_verify_invite_non_pending_status(invite_service):
    """Test verifying a token with non-pending status"""
    # Arrange
    token = "accepted-token"
    mock_invite = MagicMock()
    mock_invite.id = "test-invite-id"
    mock_invite.email = "patient@example.com"
    mock_invite.first_name = "John"
    mock_invite.last_name = "Doe"
    mock_invite.clinician_id = "test-clinician-id"
    mock_invite.invite_token = token
    mock_invite.status = "accepted"  # Already accepted
    mock_invite.created_at = datetime.utcnow()
    mock_invite.expires_at = datetime.utcnow() + timedelta(days=14)
    
    invite_service.invite_repository.get_by_token.return_value = mock_invite
    
    # Act
    is_valid, invite, error = invite_service.verify_invite(token)
    
    # Assert
    assert is_valid is False
    assert invite == mock_invite
    assert error == "Invitation has been accepted"
    invite_service.invite_repository.get_by_token.assert_called_once_with(token)


def test_verify_invite_expired(invite_service):
    """Test verifying an expired invitation token"""
    # Arrange
    token = "expired-token"
    mock_invite = MagicMock()
    mock_invite.id = "test-invite-id"
    mock_invite.email = "patient@example.com"
    mock_invite.first_name = "John"
    mock_invite.last_name = "Doe"
    mock_invite.clinician_id = "test-clinician-id"
    mock_invite.invite_token = token
    mock_invite.status = "pending"
    mock_invite.created_at = datetime.utcnow() - timedelta(days=15)
    mock_invite.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
    
    invite_service.invite_repository.get_by_token.return_value = mock_invite
    
    # Act
    is_valid, invite, error = invite_service.verify_invite(token)
    
    # Assert
    assert is_valid is False
    assert invite == mock_invite
    assert error == "Invitation has expired"
    invite_service.invite_repository.get_by_token.assert_called_once_with(token)
    invite_service.invite_repository.mark_as_expired.assert_called_once_with(mock_invite.id)


def test_accept_invite(invite_service):
    """Test accepting an invitation and creating a patient account"""
    # Arrange
    invite_id = "test-invite-id"
    mock_invite = MagicMock()
    mock_invite.id = invite_id
    mock_invite.email = "patient@example.com"
    mock_invite.first_name = "John"
    mock_invite.last_name = "Doe"
    mock_invite.clinician_id = "test-clinician-id"
    mock_invite.invite_token = "test-token"
    mock_invite.status = "pending"
    mock_invite.created_at = datetime.utcnow()
    mock_invite.expires_at = datetime.utcnow() + timedelta(days=14)
    
    user_data = {
        "password": "securepassword",
        "date_of_birth": "1980-01-01"
    }
    
    mock_user = MagicMock()
    mock_user.id="new-patient-id"
    mock_user.email=mock_invite.email
    mock_user.name=f"{mock_invite.first_name} {mock_invite.last_name}"
    mock_user.role=UserRole.PATIENT

    mock_patient = {
        "user": mock_user,
        "profile": {
            "date_of_birth": user_data["date_of_birth"],
            "phone_number": mock_invite.phone
        }
    }
    
    invite_service.invite_repository.get_by_id.return_value = mock_invite
    invite_service.user_repository.get_by_email.return_value = None
    invite_service.user_service.create_patient.return_value = mock_patient
    
    # Act
    result = invite_service.accept_invite(invite_id, user_data)
    
    # Assert
    assert result == mock_patient
    invite_service.invite_repository.get_by_id.assert_called_once_with(invite_id)
    invite_service.user_repository.get_by_email.assert_called_once_with(mock_invite.email)
    
    # Check patient creation parameters
    patient_data = invite_service.user_service.create_patient.call_args[0][0]
    profile_data = invite_service.user_service.create_patient.call_args[0][1]
    
    assert patient_data["email"] == mock_invite.email
    assert patient_data["name"] == f"{mock_invite.first_name} {mock_invite.last_name}"
    assert patient_data["password"] == user_data["password"]
    assert patient_data["role"] == UserRole.PATIENT
    assert patient_data["clinician_id"] == mock_invite.clinician_id
    
    assert profile_data["date_of_birth"] == user_data["date_of_birth"]
    assert profile_data["phone_number"] == mock_invite.phone
    
    # Verify invite marked as accepted
    invite_service.invite_repository.mark_as_accepted.assert_called_once_with(invite_id)


def test_accept_invite_invalid_invite(invite_service):
    """Test exception when invite doesn't exist"""
    # Arrange
    invite_id = "invalid-invite-id"
    user_data = {"password": "securepassword"}
    
    invite_service.invite_repository.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        invite_service.accept_invite(invite_id, user_data)
    
    assert excinfo.value.status_code == 404
    assert "Invitation not found" in str(excinfo.value.detail)


def test_accept_invite_non_pending_status(invite_service):
    """Test exception when invite is not pending"""
    # Arrange
    invite_id = "expired-invite-id"
    mock_invite = MagicMock()
    mock_invite.id = invite_id
    mock_invite.email = "patient@example.com"
    mock_invite.first_name = "John"
    mock_invite.last_name = "Doe"
    mock_invite.clinician_id = "test-clinician-id"
    mock_invite.invite_token = "test-token"
    mock_invite.status = "expired"  # Not pending
    mock_invite.created_at = datetime.utcnow()
    mock_invite.expires_at = datetime.utcnow() - timedelta(days=1)
    
    user_data = {"password": "securepassword"}
    
    invite_service.invite_repository.get_by_id.return_value = mock_invite
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        invite_service.accept_invite(invite_id, user_data)
    
    assert excinfo.value.status_code == 400
    assert "Invitation has been expired" in str(excinfo.value.detail)


def test_accept_invite_expired(invite_service):
    """Test exception when invite is expired"""
    # Arrange
    invite_id = "expired-invite-id"
    mock_invite = MagicMock()
    mock_invite.id = invite_id
    mock_invite.email = "patient@example.com"
    mock_invite.first_name = "John"
    mock_invite.last_name = "Doe"
    mock_invite.clinician_id = "test-clinician-id"
    mock_invite.invite_token = "test-token"
    mock_invite.status = "pending"
    mock_invite.created_at = datetime.utcnow() - timedelta(days=15)
    mock_invite.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired
    
    user_data = {"password": "securepassword"}
    
    invite_service.invite_repository.get_by_id.return_value = mock_invite
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        invite_service.accept_invite(invite_id, user_data)
    
    assert excinfo.value.status_code == 400
    assert "Invitation has expired" in str(excinfo.value.detail)
    invite_service.invite_repository.mark_as_expired.assert_called_once_with(invite_id)
