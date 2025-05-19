"""
Invite repository module for handling database operations for patient invitations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.invite import PatientInvite
from app.repositories.base import BaseRepository
import uuid
from datetime import datetime, timedelta


class InviteRepository(BaseRepository):
    """Repository for PatientInvite operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, PatientInvite)
    
    def get_by_token(self, token: str) -> Optional[PatientInvite]:
        """Get an invitation by token"""
        return self.db.query(PatientInvite).filter(PatientInvite.invite_token == token).first()
    
    def get_by_email(self, email: str) -> List[PatientInvite]:
        """Get all invitations for an email address"""
        return self.db.query(PatientInvite).filter(PatientInvite.email == email).all()
    
    def get_active_by_email(self, email: str) -> Optional[PatientInvite]:
        """Get the active invitation for an email address"""
        return self.db.query(PatientInvite).filter(
            and_(
                PatientInvite.email == email,
                PatientInvite.status == "pending",
                PatientInvite.expires_at > datetime.utcnow()
            )
        ).order_by(desc(PatientInvite.created_at)).first()
    
    def get_by_clinician(self, clinician_id: str, status: Optional[str] = None) -> List[PatientInvite]:
        """Get all invitations created by a clinician"""
        query = self.db.query(PatientInvite).filter(PatientInvite.clinician_id == clinician_id)
        
        if status:
            query = query.filter(PatientInvite.status == status)
        
        return query.order_by(desc(PatientInvite.created_at)).all()
    
    def create_invite(self, invite_data: Dict[str, Any]) -> PatientInvite:
        """Create a new patient invitation"""
        if "id" not in invite_data:
            invite_data["id"] = str(uuid.uuid4())
        
        if "invite_token" not in invite_data:
            invite_data["invite_token"] = str(uuid.uuid4())
        
        # Set expiration date if not provided
        if "expires_at" not in invite_data:
            invite_data["expires_at"] = datetime.utcnow() + timedelta(days=14)
        
        invite = PatientInvite(**invite_data)
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)
        return invite
    
    def update_invite(self, invite_id: str, update_data: Dict[str, Any]) -> Optional[PatientInvite]:
        """Update a patient invitation"""
        invite = self.get_by_id(invite_id)
        if not invite:
            return None
        
        for key, value in update_data.items():
            if hasattr(invite, key):
                setattr(invite, key, value)
        
        invite.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(invite)
        return invite
    
    def mark_as_accepted(self, invite_id: str) -> Optional[PatientInvite]:
        """Mark an invitation as accepted"""
        return self.update_invite(invite_id, {
            "status": "accepted",
            "accepted_at": datetime.utcnow()
        })
    
    def mark_as_expired(self, invite_id: str) -> Optional[PatientInvite]:
        """Mark an invitation as expired"""
        return self.update_invite(invite_id, {
            "status": "expired"
        })
    
    def revoke_invite(self, invite_id: str) -> Optional[PatientInvite]:
        """Revoke a patient invitation"""
        return self.update_invite(invite_id, {
            "status": "revoked"
        })
    
    def cleanup_expired_invites(self) -> int:
        """Mark all expired invitations as expired"""
        expired = self.db.query(PatientInvite).filter(
            and_(
                PatientInvite.status == "pending",
                PatientInvite.expires_at <= datetime.utcnow()
            )
        ).all()
        
        count = 0
        for invite in expired:
            self.mark_as_expired(invite.id)
            count += 1
        
        return count
