#!/usr/bin/env python3
"""
Simple test script to verify authentication works.
"""
import requests

BASE_URL = "http://localhost:8000"
AUTH_API = f"{BASE_URL}/api/auth"

def test_auth():
    """Test authentication."""
    auth_data = {
        "username": "admin@test.com",
        "password": "test123"
    }
    
    print("Testing authentication...")
    response = requests.post(f"{AUTH_API}/token", data=auth_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Authentication successful!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Authentication failed")
        return None

if __name__ == "__main__":
    test_auth()
