#!/usr/bin/env python3
"""
Quick test to verify the invite URL generation is working correctly
"""
import sys
sys.path.append('/app')

from app.core.config import settings

def test_invite_url():
    print(f"🔍 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Frontend URL: {settings.FRONTEND_URL}")
    
    # Simulate invite URL generation
    mock_token = "test-token-123"
    invite_url = f"{settings.FRONTEND_URL}/invite/{mock_token}"
    print(f"📧 Generated invite URL: {invite_url}")
    
    if "https://chat-dev.genascope.com" in invite_url:
        print("✅ SUCCESS: Invite URL uses the correct domain!")
        return True
    else:
        print("❌ FAILURE: Invite URL still uses localhost")
        return False

if __name__ == "__main__":
    test_invite_url()
