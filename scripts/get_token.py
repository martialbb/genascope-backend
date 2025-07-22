#!/usr/bin/env python3
"""
Get a fresh authentication token.
"""
import requests

BASE_URL = "http://localhost:8000"

def get_token():
    """Get authentication token."""
    print("🔑 Getting authentication token...")
    
    # Login credentials
    login_data = {
        "username": "admin@test.com",
        "password": "admin123"
    }
    
    # Get token
    response = requests.post(
        f"{BASE_URL}/api/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Token obtained successfully")
        print(f"Token: {token_data['access_token']}")
        return token_data['access_token']
    else:
        print(f"❌ Failed to get token: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    get_token()
