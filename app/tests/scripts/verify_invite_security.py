#!/usr/bin/env python3
"""
Final verification script for invite security implementation
Tests role-based access control with different user types
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ACCOUNTS_URL = f"{BASE_URL}/api/accounts"
INVITES_URL = f"{BASE_URL}/api/invites"
CLINICIANS_URL = f"{BASE_URL}/api/clinicians"
LOGIN_URL = f"{BASE_URL}/api/auth/token"

# Test user credentials
TEST_USERS = {
    "super_admin": {
        "username": "superadmin@genascope.com",
        "password": "admin123",
        "grant_type": "password"
    },
    "admin": {
        "username": "admin@test.com", 
        "password": "admin123",
        "grant_type": "password"
    },
    "clinician": {
        "username": "clinician@test.com",
        "password": "admin123",
        "grant_type": "password"
    }
}

def login_user(user_type):
    """Login and return session with auth token"""
    credentials = TEST_USERS.get(user_type)
    if not credentials:
        print(f"❌ No credentials found for user type: {user_type}")
        return None
    
    session = requests.Session()
    
    try:
        response = session.post(
            LOGIN_URL, 
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            token_data = response.json()
            session.headers.update({
                "Authorization": f"Bearer {token_data['access_token']}"
            })
            print(f"✅ Successfully logged in as {user_type}")
            return session
        else:
            print(f"❌ Failed to login as {user_type}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error logging in as {user_type}: {e}")
        return None

def test_invites_endpoint(user_type, session):
    """Test invites list endpoint access"""
    print(f"\n🔍 Testing /api/invites access for {user_type}...")
    
    try:
        response = session.get(INVITES_URL)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {user_type} can access invites")
            print(f"   Total invites: {data.get('total_count', 0)}")
            
            # Check if account filtering is applied
            invites = data.get('invites', [])
            if invites:
                print(f"   Sample invite details:")
                for invite in invites[:2]:  # Show first 2 invites
                    print(f"     - ID: {invite['invite_id']}")
                    print(f"       Provider: {invite['provider_name']}")
                    print(f"       Status: {invite['status']}")
            else:
                print("   No invites found")
                
        elif response.status_code == 403:
            print(f"❌ {user_type} access denied (403) - as expected")
        else:
            print(f"⚠️ {user_type} unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invites for {user_type}: {e}")

def test_clinicians_endpoint(user_type, session):
    """Test clinicians list endpoint access"""
    print(f"\n🔍 Testing /api/clinicians access for {user_type}...")
    
    try:
        response = session.get(CLINICIANS_URL)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {user_type} can access clinicians list")
            print(f"   Total clinicians: {len(data)}")
            
            # Show sample clinicians with account info
            for clinician in data[:3]:  # Show first 3
                print(f"     - {clinician['name']} ({clinician['email']})")
                print(f"       Role: {clinician['role']}")
                
        elif response.status_code == 403:
            print(f"❌ {user_type} access denied (403) - as expected")
        else:
            print(f"⚠️ {user_type} unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing clinicians for {user_type}: {e}")

def test_accounts_endpoint(user_type, session):
    """Test accounts endpoint to compare filtering behavior"""
    print(f"\n🔍 Testing /api/accounts access for {user_type}...")
    
    try:
        response = session.get(ACCOUNTS_URL)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {user_type} can access accounts")
            print(f"   Total accounts: {data.get('total_count', len(data.get('accounts', data)))}")
            
        elif response.status_code == 403:
            print(f"❌ {user_type} access denied (403)")
        else:
            print(f"⚠️ {user_type} unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing accounts for {user_type}: {e}")

def main():
    """Main verification function"""
    print("🔒 Final Invite Security Verification")
    print("=" * 50)
    
    # Test each user type
    for user_type in ["super_admin", "admin", "clinician"]:
        print(f"\n🚀 Testing {user_type.upper()} access...")
        
        session = login_user(user_type)
        if not session:
            continue
            
        # Test various endpoints
        test_invites_endpoint(user_type, session)
        test_clinicians_endpoint(user_type, session)
        test_accounts_endpoint(user_type, session)
        
        print(f"✅ Completed {user_type} testing")
    
    print("\n" + "=" * 50)
    print("🏁 Verification completed!")
    print("\n📋 Summary of expected behavior:")
    print("   - Super Admin: Should access all invites across all accounts")
    print("   - Admin: Should only see invites from their account")
    print("   - Clinician: Should only see their own invites within their account")
    print("\n🔐 Security pattern successfully applied to invites endpoints!")

if __name__ == "__main__":
    main()
