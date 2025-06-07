#!/usr/bin/env python
"""
Migration script for transitioning from the old email-based invite system to the new patient-first invite system.
This script:
1. Creates patient records for all previous invite recipients who don't have patient records
2. Links existing invites to the newly created patient records
3. Updates invite statuses to match the new system
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import SessionLocal, engine
from app.models.invite import PatientInvite
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.repositories.patients import PatientRepository
from app.repositories.invites import InviteRepository
from app.repositories.users import UserRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("patient_invite_migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("migration")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_patient_record(db: Session, invite: PatientInvite) -> Optional[Patient]:
    """
    Create a patient record from an invite if it doesn't exist
    """
    try:
        if not invite.email:
            logger.warning(f"Invite {invite.id} has no email address, skipping")
            return None
            
        # Check if patient with this email already exists
        patient_repo = PatientRepository(db)
        existing_patient = patient_repo.get_by_email(invite.email)
        
        if existing_patient:
            logger.info(f"Patient with email {invite.email} already exists with ID {existing_patient.id}")
            return existing_patient
            
        # Create patient record
        patient_data = {
            "email": invite.email,
            "first_name": invite.first_name or "",
            "last_name": invite.last_name or "",
            "phone": invite.phone or None,
            "status": "pending",
            "clinician_id": invite.clinician_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        new_patient = patient_repo.create(patient_data)
        logger.info(f"Created patient record for {invite.email} with ID {new_patient.id}")
        return new_patient
    except Exception as e:
        logger.error(f"Error creating patient record for {invite.email}: {str(e)}")
        return None


def link_invite_to_patient(db: Session, invite: PatientInvite, patient: Patient) -> bool:
    """
    Link an invite to a patient record
    """
    try:
        invite_repo = InviteRepository(db)
        
        # Update invite with patient_id
        invite_repo.update_invite(invite.id, {"patient_id": patient.id})
        logger.info(f"Linked invite {invite.id} to patient {patient.id}")
        return True
    except Exception as e:
        logger.error(f"Error linking invite {invite.id} to patient {patient.id}: {str(e)}")
        return False


def update_invite_status(db: Session, invite: PatientInvite) -> bool:
    """
    Update invite status based on expiration and user creation
    """
    try:
        invite_repo = InviteRepository(db)
        status_updated = False
        
        # Update expired invites
        if invite.expires_at < datetime.now(timezone.utc) and invite.status == "pending":
            invite_repo.update_invite(invite.id, {"status": "expired"})
            logger.info(f"Updated invite {invite.id} status to expired")
            status_updated = True
            
        # Update accepted invites
        if invite.user_id and invite.status == "pending":
            invite_repo.update_invite(invite.id, {"status": "accepted"})
            logger.info(f"Updated invite {invite.id} status to accepted")
            status_updated = True
            
        return status_updated
    except Exception as e:
        logger.error(f"Error updating status for invite {invite.id}: {str(e)}")
        return False


def run_migration():
    """
    Main migration function
    """
    logger.info("Starting patient-first invite system migration")
    
    # Get DB session
    db = next(get_db())
    
    try:
        # Get all invites
        invite_repo = InviteRepository(db)
        all_invites = invite_repo.get_all()
        
        logger.info(f"Found {len(all_invites)} invites to process")
        
        patients_created = 0
        invites_linked = 0
        statuses_updated = 0
        
        # Process each invite
        for invite in all_invites:
            # Skip invites that already have patient_id
            if invite.patient_id:
                logger.info(f"Invite {invite.id} already has patient_id {invite.patient_id}, skipping creation")
                
                # Still update status if needed
                if update_invite_status(db, invite):
                    statuses_updated += 1
                continue
                
            # Create patient record if needed
            patient = create_patient_record(db, invite)
            
            if patient:
                patients_created += 1
                
                # Link invite to patient
                if link_invite_to_patient(db, invite, patient):
                    invites_linked += 1
                    
                # Update invite status
                if update_invite_status(db, invite):
                    statuses_updated += 1
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Migration completed successfully:")
        logger.info(f"- Created {patients_created} patient records")
        logger.info(f"- Linked {invites_linked} invites to patients")
        logger.info(f"- Updated {statuses_updated} invite statuses")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
