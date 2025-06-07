#!/usr/bin/env python
"""
Migration script to link existing chat sessions to patient records.

This script runs after the basic invite-to-patient migration and connects any
existing chat sessions to the newly created patient records based on user relationships.

Usage:
    python link_chats_to_patients.py
"""
import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import the required models, with fallback for ChatSession if not yet imported
try:
    from app.models.chat import ChatSession
    from app.models.patient import Patient
    from app.models.user import User
    
    CHAT_SESSION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import ChatSession model: {e}")
    logger.warning("Skipping chat session linkage. You may need to update the import paths.")
    CHAT_SESSION_AVAILABLE = False

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
    
    if not CHAT_SESSION_AVAILABLE:
        logger.warning("ChatSession model not available. Migration script will exit.")
        sys.exit(0)
    
    try:
        # Get all patients with associated users
        logger.info("Finding patients with associated users...")
        patients_with_users = session.query(Patient).filter(Patient.user_id.isnot(None)).all()
        
        logger.info(f"Found {len(patients_with_users)} patients with user accounts")
        
        # For each patient with a user, find their chat sessions and link them
        updated_count = 0
        
        for patient in patients_with_users:
            # Get chat sessions for this user
            chat_sessions = session.query(ChatSession).filter(
                ChatSession.patient_id == patient.user_id
            ).all()
            
            if chat_sessions:
                logger.info(f"Found {len(chat_sessions)} chat sessions for patient {patient.id} (user {patient.user_id})")
                
                # Update the patient_id field on each chat session to point to the patient record
                # Note: This assumes there's a way to link chat sessions to patients directly
                # If the ChatSession model doesn't have a direct link, this would need to be adapted
                for chat in chat_sessions:
                    try:
                        # Assuming there's a field to store the reference to the patient model
                        # This might need to be adapted based on your actual model structure
                        chat.patient_record_id = patient.id
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"Failed to update chat session {chat.id}: {str(e)}")
        
        # Commit all changes at once
        if updated_count > 0:
            logger.info(f"Committing changes for {updated_count} chat sessions...")
            session.commit()
            logger.info("Chat session linkage completed successfully")
        else:
            logger.info("No chat sessions needed to be updated")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
