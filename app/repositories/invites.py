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
        from sqlalchemy.orm import joinedload
        return self.db.query(PatientInvite).options(
            joinedload(PatientInvite.patient)
        ).filter(PatientInvite.invite_token == token).first()
    
    def get_by_patient_id(self, patient_id: str) -> List[PatientInvite]:
        """Get all invitations for a patient by patient ID"""
        return self.db.query(PatientInvite).filter(PatientInvite.patient_id == patient_id).all()
    
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
        from sqlalchemy.orm import joinedload
        from app.models.patient import Patient  # Import here to avoid circular imports
        
        # Ensure clinician_id is a string to match VARCHAR column type
        clinician_id_str = str(clinician_id)
        
        query = self.db.query(PatientInvite).options(
            joinedload(PatientInvite.patient)
        ).filter(PatientInvite.clinician_id == clinician_id_str)
        
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
    
    def list_invites_paginated(self, page: int = 1, limit: int = 10, filters: Dict[str, Any] = None,
                              sort_by: str = "created_at", sort_order: str = "desc") -> tuple[List[PatientInvite], int]:
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
        from app.models.patient import Patient  # Import here to avoid circular imports
        
        filters = filters or {}
        query = self.db.query(PatientInvite).join(Patient, PatientInvite.patient_id == Patient.id)
        
        # Apply filters
        if "status" in filters:
            query = query.filter(PatientInvite.status == filters["status"])
        
        if "clinician_id" in filters:
            # Cast UUID to string to handle type mismatch with VARCHAR column
            clinician_id_str = str(filters["clinician_id"])
            query = query.filter(PatientInvite.clinician_id == clinician_id_str)
        
        # Add account-based filtering for role-based access control
        if "account_id" in filters:
            query = query.filter(Patient.account_id == filters["account_id"])
        
        if "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    PatientInvite.email.ilike(search_term)
                )
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting - handle patient fields vs invite fields
        if sort_by in ["first_name", "last_name"]:
            sort_column = getattr(Patient, sort_by)
        else:
            sort_column = getattr(PatientInvite, sort_by, PatientInvite.created_at)
            
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (page - 1) * limit
        invites = query.offset(offset).limit(limit).all()
        
        return invites, total_count
    
    def get_invites_by_clinician(self, clinician_id: str, status: Optional[str] = None) -> List[PatientInvite]:
        """
        Get invites for a specific clinician, optionally filtered by status
        
        Args:
            clinician_id: The clinician's ID
            status: Optional status filter
            
        Returns:
            List of PatientInvite objects
        """
        return self.get_by_clinician(clinician_id, status)
    
    def get_by_id(self, invite_id: str) -> Optional[PatientInvite]:
        """Get an invitation by ID with patient relationship loaded"""
        from sqlalchemy.orm import joinedload
        from app.models.patient import Patient  # Import here to avoid circular imports
        return self.db.query(PatientInvite).options(
            joinedload(PatientInvite.patient)
        ).filter(PatientInvite.id == invite_id).first()
