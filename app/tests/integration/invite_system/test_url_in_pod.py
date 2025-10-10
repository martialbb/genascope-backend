#!/usr/bin/env python3
"""
Test script to verify invite URL generation
"""
import sys
import os

# Add the app directory to the path so we can import the modules
sys.path.append('/app')

from app.core.config import settings
from app.models.invite import PatientInvite
from app.services.invites import InviteService
from datetime import datetime
import uuid

def test_url_generation():
    print("🔍 Testing invite URL generation...")
    
    # Check the FRONTEND_URL setting
    print(f"📍 FRONTEND_URL setting: {settings.FRONTEND_URL}")
    
    # Create a mock invite object
    mock_invite = PatientInvite(
        id=1,
        invite_token=str(uuid.uuid4()),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow()
    )
    
    # Create an invite service instance
    invite_service = InviteService(db=None)  # We don't need DB for URL generation
    
    # Generate the URL
    invite_url = invite_service.generate_invite_url(mock_invite)
    
    print(f"🔗 Generated invite URL: {invite_url}")
    
    # Check if it uses the correct domain
    if "https://chat-dev.genascope.com" in invite_url:
        print("✅ SUCCESS: Invite URL uses the correct external domain!")
        return True
    else:
        print("❌ FAILURE: Invite URL still uses localhost or incorrect domain")
        return False

if __name__ == "__main__":
    success = test_url_generation()
    sys.exit(0 if success else 1)
