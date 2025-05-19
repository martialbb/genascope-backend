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
from app.models.invite import PatientInvite
from app.models.user import UserRole
from app.services.base import BaseService
from app.services.users import UserService


class InviteService(BaseService):
    """
    Service for patient invitation operations
    """
    def __init__(self, db: Session):
        self.db = db
        self.invite_repository = InviteRepository(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)
    
    def create_invite(self, invite_data: Dict[str, Any]) -> PatientInvite:
        """
        Create a new patient invitation
        """
        # Check if clinician exists
        clinician = self.user_repository.get_by_id(invite_data["clinician_id"])
        if not clinician or clinician.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=404, detail="Clinician not found")
        
        # Check if there's already an active invite for this email
        active_invite = self.invite_repository.get_active_by_email(invite_data["email"])
        if active_invite:
            # If it's from the same clinician, return the existing invite
            if active_invite.clinician_id == invite_data["clinician_id"]:
                return active_invite
            
            # Otherwise, revoke the old one
            self.invite_repository.revoke_invite(active_invite.id)
        
        # Create a new invite
        invite = self.invite_repository.create_invite(invite_data)
        
        # TODO: Send email notification
        
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
        Accept an invitation and create a patient account
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
        
        # Check if user with email already exists
        existing_user = self.user_repository.get_by_email(invite.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user account
        patient_data = {
            "email": invite.email,
            "name": f"{invite.first_name} {invite.last_name}",
            "password": user_data["password"],
            "role": UserRole.PATIENT,
            "clinician_id": invite.clinician_id
        }
        
        # Create profile data if available
        profile_data = None
        if "date_of_birth" in user_data:
            profile_data = {
                "date_of_birth": user_data["date_of_birth"],
                "phone_number": invite.phone
            }
        
        # Create patient account with profile
        patient = self.user_service.create_patient(patient_data, profile_data)
        
        # Mark invitation as accepted
        self.invite_repository.mark_as_accepted(invite.id)
        
        return patient
    
    def get_invites_by_clinician(self, clinician_id: str, status: Optional[str] = None) -> List[PatientInvite]:
        """
        Get all invitations created by a clinician
        """
        return self.invite_repository.get_by_clinician(clinician_id, status)
    
    def resend_invite(self, invite_id: str, custom_message: Optional[str] = None) -> PatientInvite:
        """
        Resend an invitation
        """
        invite = self.invite_repository.get_by_id(invite_id)
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        # If expired or revoked, create a new one
        if invite.status in ["expired", "revoked"]:
            new_invite_data = {
                "email": invite.email,
                "first_name": invite.first_name,
                "last_name": invite.last_name,
                "phone": invite.phone,
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
        
        # TODO: Send email notification
        
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
    
    def generate_invite_url(self, invite: PatientInvite, base_url: str) -> str:
        """
        Generate an invitation URL
        """
        return f"{base_url}/invite/{invite.invite_token}"
