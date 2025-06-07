"""
Invite service module for business logic related to patient invitations.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime, timedelta

from app.repositories.invites import InviteRepository
from app.repositories.users import UserRepository
from app.repositories.patients import PatientRepository
from app.models.invite import PatientInvite
from app.models.user import UserRole
from app.models.patient import Patient
from app.services.base import BaseService
from app.services.users import UserService
from app.services.patients import PatientService
from app.core.email import email_service
from app.core.config import settings
from datetime import datetime


class InviteService(BaseService):
    """
    Service for patient invitation operations
    """
    def __init__(self, db: Session):
        self.db = db
        self.invite_repository = InviteRepository(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
        self.patient_repository = PatientRepository(db)
    
    def create_invite(self, invite_data: Dict[str, Any]) -> PatientInvite:
        """
        Create a new patient invitation
        
        This function now expects a patient_id in the invite_data
        """
        # Check if clinician exists
        clinician = self.user_repository.get_by_id(invite_data["clinician_id"])
        if not clinician or clinician.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=404, detail="Clinician not found")
        
        # Check if patient exists
        patient = self.patient_repository.get_by_id(invite_data["patient_id"])
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
            
        # Validate patient has a valid email address
        if not patient.email:
            raise HTTPException(
                status_code=400, 
                detail=f"Patient {patient.first_name} {patient.last_name} does not have a valid email address. Please update the patient record with a valid email before creating an invite."
            )
            
        # Set email from patient (for consistency)
        invite_data["email"] = patient.email
        
        # Check if there's already an active invite for this patient
        active_invites = self.invite_repository.get_by_email(patient.email)
        active_invite = next((i for i in active_invites if i.status == "pending" and i.expires_at > datetime.utcnow()), None)
        
        if active_invite:
            # If it's from the same clinician, return the existing invite
            if active_invite.clinician_id == invite_data["clinician_id"]:
                return active_invite
            
            # Otherwise, revoke the old one
            self.invite_repository.revoke_invite(active_invite.id)
        
        # Create a new invite
        # Extract send_email flag before creating the invite
        send_email = invite_data.pop("send_email", True)
        
        # Create the invite with only valid PatientInvite model fields
        invite = self.invite_repository.create_invite(invite_data)
        
        # Send email notification
        if invite and send_email:
            patient_name = patient.full_name
            clinician_name = clinician.name
            
            # Generate invite URL using the frontend URL from settings
            invite_url = self.generate_invite_url(invite)
            
            # Format expiration date for display
            expires_at = invite.expires_at.strftime("%B %d, %Y at %I:%M %p")
            
            # Send the email
            email_service.send_invite_email(
                to_email=invite.email,
                patient_name=patient_name,
                clinician_name=clinician_name,
                invite_url=invite_url,
                expires_at=expires_at,
                custom_message=invite.custom_message
            )
        
        return invite
    
    def verify_invite(self, token: str) -> Tuple[bool, Optional[PatientInvite], Optional[str]]:
        """
        Verify an invitation token
        """
        invite = self.invite_repository.get_by_token(token)
        
        if not invite:
            return False, None, "Invalid invitation token"
        
        if invite.status != "pending":
            return False, invite, f"Invitation has been {invite.status}"
        
        if invite.expires_at < datetime.utcnow():
            # Mark as expired
            self.invite_repository.mark_as_expired(invite.id)
            return False, invite, "Invitation has expired"
        
        return True, invite, None
    
    def accept_invite(self, invite_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accept an invitation and create a user account for an existing patient
        """
        invite = self.invite_repository.get_by_id(invite_id)
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        if invite.status != "pending":
            raise HTTPException(status_code=400, detail=f"Invitation has been {invite.status}")
        
        if invite.expires_at < datetime.utcnow():
            # Mark as expired
            self.invite_repository.mark_as_expired(invite.id)
            raise HTTPException(status_code=400, detail="Invitation has expired")
        
        # Get the associated patient
        patient = self.patient_repository.get_by_id(invite.patient_id)
        if not patient:
            raise HTTPException(status_code=400, detail="Patient record not found")
        
        # Check if user with email already exists
        existing_user = self.user_repository.get_by_email(invite.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user account
        patient_data = {
            "email": patient.email,
            "name": patient.full_name,
            "password": user_data["password"],
            "role": UserRole.PATIENT,
            "clinician_id": invite.clinician_id
        }
        
        # Create profile data if available
        profile_data = None
        if "date_of_birth" in user_data:
            profile_data = {
                "date_of_birth": user_data["date_of_birth"],
                "phone_number": patient.phone
            }
        
        # Create patient account with profile
        user_account = self.user_service.create_patient(patient_data, profile_data)
        
        # Update patient record with user_id
        self.patient_repository.update(
            patient.id, 
            {"user_id": user_account["user"].id, "status": "active"}
        )
        
        # Mark invitation as accepted
        self.invite_repository.mark_as_accepted(invite.id)
        
        # Update invite with user_id
        self.invite_repository.update_invite(
            invite.id,
            {"user_id": user_account["user"].id}
        )
        
        return user_account
    
    def resend_invite(self, invite_id: str, custom_message: Optional[str] = None) -> PatientInvite:
        """
        Resend an invitation
        """
        invite = self.invite_repository.get_by_id(invite_id)
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        # If expired or revoked, create a new one
        if invite.status in ["expired", "revoked"]:
            # Get patient data from the relationship
            patient = self.patient_repository.get_by_id(invite.patient_id)
            if not patient:
                raise HTTPException(status_code=400, detail="Patient record not found")
                
            new_invite_data = {
                "email": invite.email,
                "patient_id": invite.patient_id,
                "clinician_id": invite.clinician_id,
                "custom_message": custom_message or invite.custom_message,
                "expires_at": datetime.utcnow() + timedelta(days=14)
            }
            
            invite = self.invite_repository.create_invite(new_invite_data)
        elif invite.status == "pending":
            # Update expiration date and message
            update_data = {
                "expires_at": datetime.utcnow() + timedelta(days=14)
            }
            
            if custom_message:
                update_data["custom_message"] = custom_message
                
            invite = self.invite_repository.update_invite(invite.id, update_data)
        
        # Send email notification
        if invite:
            clinician = self.user_repository.get_by_id(invite.clinician_id)
            if clinician:
                # Get patient data from the relationship
                patient = self.patient_repository.get_by_id(invite.patient_id)
                patient_name = patient.full_name if patient else "Patient"
                clinician_name = clinician.name
                
                # Generate invite URL using the frontend URL from settings
                invite_url = self.generate_invite_url(invite)
                
                # Format expiration date for display
                expires_at = invite.expires_at.strftime("%B %d, %Y at %I:%M %p")
                
                # Send the email
                email_service.send_invite_email(
                    to_email=invite.email,
                    patient_name=patient_name,
                    clinician_name=clinician_name,
                    invite_url=invite_url,
                    expires_at=expires_at,
                    custom_message=invite.custom_message
                )
        
        return invite
    
    def revoke_invite(self, invite_id: str) -> PatientInvite:
        """
        Revoke an invitation
        """
        invite = self.invite_repository.get_by_id(invite_id)
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        if invite.status != "pending":
            raise HTTPException(status_code=400, detail=f"Invitation has already been {invite.status}")
        
        return self.invite_repository.revoke_invite(invite.id)
    
    def create_bulk_invites(self, bulk_data: List[Dict[str, Any]], clinician_id: str) -> Tuple[List[PatientInvite], List[Dict[str, Any]]]:
        """
        Create multiple invitations at once
        """
        successful = []
        failed = []
        
        for invite_data in bulk_data:
            invite_data["clinician_id"] = clinician_id
            
            try:
                invite = self.create_invite(invite_data)
                successful.append(invite)
            except Exception as e:
                failed.append({
                    "data": invite_data,
                    "error": str(e)
                })
        
        return successful, failed
    
    def generate_invite_url(self, invite: PatientInvite, base_url: str = None) -> str:
        """
        Generate an invitation URL
        
        Args:
            invite: The invitation object
            base_url: Optional base URL, defaults to FRONTEND_URL from settings
            
        Returns:
            str: The complete invitation URL
        """
        # Use the provided base_url or the frontend URL from settings
        base = base_url if base_url else settings.FRONTEND_URL
        base = base.rstrip("/")  # Remove trailing slash if present
        
        return f"{base}/invite/{invite.invite_token}"
    
    def list_invites_paginated(self, page: int = 1, limit: int = 10, filters: Dict[str, Any] = None, 
                              sort_by: str = "created_at", sort_order: str = "desc") -> Tuple[List[PatientInvite], int]:
        """
        Get paginated list of invites with filtering and sorting
        
        Args:
            page: Page number (1-based)
            limit: Number of items per page
            filters: Dictionary of filter criteria
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            Tuple of (invites_list, total_count)
        """
        return self.invite_repository.list_invites_paginated(
            page=page,
            limit=limit,
            filters=filters or {},
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    def get_invite_by_id(self, invite_id: str) -> Optional[PatientInvite]:
        """
        Get a specific invite by ID
        
        Args:
            invite_id: The invite ID
            
        Returns:
            PatientInvite object or None if not found
        """
        return self.invite_repository.get_by_id(invite_id)
    
    def get_invites_by_clinician(self, clinician_id: str, status: Optional[str] = None) -> List[PatientInvite]:
        """
        Get invites for a specific clinician, optionally filtered by status
        
        Args:
            clinician_id: The clinician's ID
            status: Optional status filter
            
        Returns:
            List of PatientInvite objects
        """
        return self.invite_repository.get_invites_by_clinician(clinician_id, status)
