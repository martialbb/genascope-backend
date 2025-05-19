"""
Fixtures for patient invitation tests.

This module provides fixtures for creating mock patient invitations
for use in tests across the application.
"""
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any, Optional

from app.models.invite import PatientInvite


def create_mock_invite(
    id: Optional[str] = None,
    clinician_id: str = "clinician-123",
    email: str = "patient@example.com",
    first_name: str = "Test",
    last_name: str = "Patient",
    phone: Optional[str] = None,
    invite_token: Optional[str] = None,
    status: str = "pending",
    expires_at: Optional[datetime] = None,
    accepted_at: Optional[datetime] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    custom_message: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None
) -> PatientInvite:
    """
    Create a mock PatientInvite instance for testing.
    
    Args:
        id: Unique identifier for the invite
        clinician_id: ID of the clinician who created the invite
        email: Email address of the invited patient
        first_name: First name of the invited patient
        last_name: Last name of the invited patient
        phone: Phone number of the invited patient
        invite_token: Token for accepting the invitation
        status: Current status of the invitation (pending, accepted, expired, revoked)
        expires_at: When the invitation expires
        accepted_at: When the invitation was accepted
        created_at: When the invitation was created
        updated_at: When the invitation was last updated
        custom_message: Optional custom message for the invitation
        meta_data: Optional metadata for the invitation
        
    Returns:
        A PatientInvite instance with the provided attributes
    """
    # Default values
    if id is None:
        id = str(uuid.uuid4())
    
    if invite_token is None:
        invite_token = str(uuid.uuid4())
    
    if expires_at is None:
        expires_at = datetime.utcnow() + timedelta(days=14)
    
    if created_at is None:
        created_at = datetime.utcnow()
    
    if updated_at is None:
        updated_at = created_at
    
    # Create PatientInvite instance
    invite = PatientInvite(
        id=id,
        clinician_id=clinician_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        invite_token=invite_token,
        status=status,
        expires_at=expires_at,
        accepted_at=accepted_at,
        created_at=created_at,
        updated_at=updated_at,
        custom_message=custom_message,
        meta_data=meta_data
    )
    
    return invite


def create_mock_invite_dict(
    id: Optional[str] = None,
    clinician_id: str = "clinician-123",
    email: str = "patient@example.com",
    first_name: str = "Test",
    last_name: str = "Patient",
    phone: Optional[str] = None,
    invite_token: Optional[str] = None,
    status: str = "pending",
    expires_at: Optional[datetime] = None,
    accepted_at: Optional[datetime] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    custom_message: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a dictionary representing a patient invitation for testing.
    
    This is useful for testing API responses or when passing data to
    repository methods.
    
    Args:
        Same as create_mock_invite()
        
    Returns:
        A dictionary with the provided attributes
    """
    # Default values
    if id is None:
        id = str(uuid.uuid4())
    
    if invite_token is None:
        invite_token = str(uuid.uuid4())
    
    if expires_at is None:
        expires_at = datetime.utcnow() + timedelta(days=14)
    
    if created_at is None:
        created_at = datetime.utcnow()
    
    if updated_at is None:
        updated_at = created_at
    
    # Create dictionary
    invite_dict = {
        "id": id,
        "clinician_id": clinician_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "invite_token": invite_token,
        "status": status,
        "expires_at": expires_at,
        "accepted_at": accepted_at,
        "created_at": created_at,
        "updated_at": updated_at
    }
    
    if phone is not None:
        invite_dict["phone"] = phone
    
    if custom_message is not None:
        invite_dict["custom_message"] = custom_message
        
    if meta_data is not None:
        invite_dict["meta_data"] = meta_data
    
    return invite_dict
