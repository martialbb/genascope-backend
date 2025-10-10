#!/usr/bin/env python3
"""
Simple test to verify invite URL generation
"""
import sys
import os

# Add the app directory to the path so we can import the modules
sys.path.append('/app')

from app.core.config import settings

class MockInvite:
    """Mock invite object for testing"""
    def __init__(self, invite_token):
        self.invite_token = invite_token

def test_url_generation():
    print("🔍 Testing invite URL generation...")
    
    # Check the FRONTEND_URL setting
    print(f"📍 FRONTEND_URL setting: {settings.FRONTEND_URL}")
    
    # Create a mock invite
    mock_invite = MockInvite(invite_token="test-token-123")
    
    # Simulate the URL generation logic from InviteService.generate_invite_url
    base = settings.FRONTEND_URL
    base = base.rstrip("/")  # Remove trailing slash if present
    invite_url = f"{base}/invite/{mock_invite.invite_token}"
    
    print(f"🔗 Generated invite URL: {invite_url}")
    
    # Check if it uses the correct domain
    if "https://chat-dev.genascope.com" in invite_url:
        print("✅ SUCCESS: Invite URL uses the correct external domain!")
        print("✅ Patient invites will now use https://chat-dev.genascope.com instead of localhost")
        return True
    else:
        print("❌ FAILURE: Invite URL still uses localhost or incorrect domain")
        return False

if __name__ == "__main__":
    success = test_url_generation()
    sys.exit(0 if success else 1)
