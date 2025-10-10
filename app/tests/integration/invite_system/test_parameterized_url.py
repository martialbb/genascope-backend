#!/usr/bin/env python3
"""
Test script to verify parameterized frontend URL generation
"""
import sys
import os

# Add the app directory to the path so we can import the modules
sys.path.append('/app')

from app.core.config import settings

def test_parameterized_url():
    print("🔍 Testing parameterized frontend URL generation...")
    
    # Check the ENVIRONMENT setting
    print(f"📍 ENVIRONMENT setting: {settings.ENVIRONMENT}")
    
    # Get the frontend URL (this should be computed dynamically)
    frontend_url = settings.FRONTEND_URL
    print(f"🔗 Generated frontend URL: {frontend_url}")
    
    # Verify it matches the expected pattern for development
    expected_url = "https://chat-dev.genascope.com"
    if frontend_url == expected_url:
        print("✅ SUCCESS: Frontend URL correctly computed for development environment!")
        
        # Test URL generation logic for other environments
        print("\n🧪 Testing other environments:")
        
        # Test staging
        original_env = settings.ENVIRONMENT
        settings.ENVIRONMENT = "staging"
        staging_url = settings.FRONTEND_URL
        print(f"🔗 Staging URL: {staging_url}")
        
        # Test production
        settings.ENVIRONMENT = "production"
        prod_url = settings.FRONTEND_URL
        print(f"🔗 Production URL: {prod_url}")
        
        # Test prod alias
        settings.ENVIRONMENT = "prod"
        prod_alias_url = settings.FRONTEND_URL
        print(f"🔗 Prod (alias) URL: {prod_alias_url}")
        
        # Restore original environment
        settings.ENVIRONMENT = original_env
        
        # Check if all URLs are correct
        if (staging_url == "https://chat-staging.genascope.com" and 
            prod_url == "https://chat.genascope.com" and
            prod_alias_url == "https://chat.genascope.com"):
            print("✅ SUCCESS: All environment URL mappings work correctly!")
            return True
        else:
            print("❌ FAILURE: Some environment URL mappings are incorrect")
            return False
    else:
        print(f"❌ FAILURE: Expected {expected_url}, got {frontend_url}")
        return False

if __name__ == "__main__":
    success = test_parameterized_url()
    sys.exit(0 if success else 1)
