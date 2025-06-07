#!/usr/bin/env python
"""
Data migration script to transition from invite-first to patient-first approach.

This script:
1. Finds all existing invites without linked patients
2. Creates patient records for each invite
3. Links the invites to the new patient records

Usage:
    python migrate_invites_to_patients.py
"""
import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.invite import PatientInvite
from app.models.patient import Patient, PatientStatus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main migration function"""
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    logger.info("Connecting to database...")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find all invites without linked patients
        logger.info("Finding invites without linked patients...")
        orphaned_invites = session.query(PatientInvite).filter(
            PatientInvite.patient_id.is_(None)
        ).all()
        
        logger.info(f"Found {len(orphaned_invites)} invites to migrate")
        
        # Process each invite
        for invite in orphaned_invites:
            # Create new patient record
            logger.info(f"Creating patient for invite {invite.id} ({invite.email})")
            
            patient = Patient(
                id=str(uuid.uuid4()),
                email=invite.email,
                first_name=invite.first_name,
                last_name=invite.last_name,
                phone=invite.phone,
                status=PatientStatus.PENDING.value if invite.status == "pending" else PatientStatus.ACTIVE.value,
                clinician_id=invite.clinician_id,
                created_at=invite.created_at,
                updated_at=invite.updated_at
            )
            
            # Add patient to session
            session.add(patient)
            session.flush()  # Make sure patient has ID before linking
            
            # Link invite to new patient
            logger.info(f"Linking invite {invite.id} to patient {patient.id}")
            invite.patient_id = patient.id
            
            # If invite is accepted and has a user, link patient to user too
            if invite.status == "accepted" and invite.user_id:
                logger.info(f"Linking patient {patient.id} to user {invite.user_id}")
                patient.user_id = invite.user_id
        
        # Commit all changes at once
        logger.info("Committing changes to database...")
        session.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
