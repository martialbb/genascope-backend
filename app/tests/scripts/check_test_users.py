#!/usr/bin/env python3
"""
Check if test users exist in the database
"""

import requests
import json

BASE_URL = "http://localhost:8000"
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

def test_authentication():
    """Test authentication with different users"""
    print("🔐 Testing User Authentication")
    print("=" * 40)
    
    for user_type, credentials in TEST_USERS.items():
        print(f"\n🚀 Testing {user_type}...")
        print(f"   Email: {credentials['username']}")
        
        try:
            response = requests.post(
                LOGIN_URL,
                data=credentials,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Authentication successful")
                print(f"   Token type: {data.get('token_type')}")
                print(f"   Access token: {data.get('access_token')[:50]}...")
                
                # Test /me endpoint with token
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
                
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"   User info: {user_info['name']} ({user_info['role']})")
                    if user_info.get('account_id'):
                        print(f"   Account ID: {user_info['account_id']}")
                    else:
                        print(f"   ⚠️  No account_id found")
                else:
                    print(f"   ❌ Failed to get user info: {me_response.status_code}")
                    
            elif response.status_code == 422:
                print(f"   ❌ Validation error (422)")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error text: {response.text}")
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed - invalid credentials")
            else:
                print(f"   ❌ Unexpected error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 40)
    print("🏁 Authentication test completed!")

if __name__ == "__main__":
    test_authentication()
