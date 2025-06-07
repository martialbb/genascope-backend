#!/usr/bin/env python3
"""
Debug the clinician 500 error for invites endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/token"
INVITES_URL = f"{BASE_URL}/api/invites"

def test_clinician_invites():
    """Test the specific clinician invites issue"""
    print("🔍 Testing Clinician Invites 500 Error")
    print("=" * 40)
    
    # Login as clinician
    print("🔐 Logging in as clinician...")
    login_response = requests.post(
        LOGIN_URL,
        data={
            "username": "clinician@test.com",
            "password": "admin123",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Failed to login: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token_data = login_response.json()
    token = token_data["access_token"]
    print(f"✅ Login successful")
    
    # Test /me endpoint to get user info
    print("\n🔍 Testing /me endpoint...")
    me_response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"✅ User info retrieved:")
        print(f"   ID: {user_info['id']}")
        print(f"   Name: {user_info['name']}")
        print(f"   Role: {user_info['role']}")
        print(f"   Account ID: {user_info.get('account_id', 'None')}")
    else:
        print(f"❌ Failed to get user info: {me_response.status_code}")
        return
    
    # Test invites endpoint with detailed error handling
    print("\n🔍 Testing /api/invites endpoint...")
    try:
        invites_response = requests.get(
            INVITES_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {invites_response.status_code}")
        print(f"Response Headers: {dict(invites_response.headers)}")
        
        if invites_response.status_code == 200:
            data = invites_response.json()
            print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error Response: {invites_response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test with query parameters to see if that helps
    print("\n🔍 Testing /api/invites with query parameters...")
    try:
        invites_response = requests.get(
            f"{INVITES_URL}?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"Status Code: {invites_response.status_code}")
        if invites_response.status_code == 200:
            data = invites_response.json()
            print(f"✅ Success with query params!")
        else:
            print(f"❌ Error with query params: {invites_response.text}")
            
    except Exception as e:
        print(f"❌ Error with query params: {e}")

if __name__ == "__main__":
    test_clinician_invites()
