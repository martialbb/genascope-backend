#!/usr/bin/env python3
"""
Test script for individual account endpoint fix
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def authenticate(email, password):
    """Authenticate and get access token"""
    print(f"🔐 Authenticating as {email}...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/token",
        data={
            "username": email,
            "password": password,
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Authentication successful")
        return token_data["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def test_individual_account_endpoint(token):
    """Test the individual account endpoint"""
    print("\n🧪 Testing Individual Account Endpoint")
    print("=" * 60)
    
    # First get list of accounts to get an account ID
    response = requests.get(
        f"{BASE_URL}/api/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get accounts list: {response.status_code}")
        return False
    
    accounts = response.json()
    if not accounts:
        print("❌ No accounts found")
        return False
    
    account_id = accounts[0]['id']
    account_name = accounts[0]['name']
    print(f"📋 Testing with account: {account_name} (ID: {account_id})")
    
    # Test individual account endpoint
    response = requests.get(
        f"{BASE_URL}/api/accounts/{account_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        account = response.json()
        print(f"✅ Successfully retrieved individual account:")
        print(f"  - Name: {account.get('name')}")
        print(f"  - ID: {account.get('id')}")
        print(f"  - Status: {account.get('status')}")
        print(f"  - Created: {account.get('created_at')}")
        print(f"  - Updated: {account.get('updated_at')}")
        
        # Verify the response structure
        required_fields = ['id', 'name', 'status', 'created_at']
        for field in required_fields:
            if field not in account:
                print(f"  ❌ Missing required field: {field}")
                return False
            else:
                print(f"  ✅ {field}: Present")
        
        print(f"\n✅ Individual account endpoint is working correctly!")
        return True
    else:
        print(f"❌ Failed to get individual account: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    print("🧪 Testing Individual Account Endpoint Fix\n")
    
    # Authenticate as super admin
    token = authenticate("superadmin@genascope.com", "admin123")
    if not token:
        print("❌ Failed to authenticate")
        return
    
    # Test individual account endpoint
    success = test_individual_account_endpoint(token)
    
    if success:
        print("\n🎉 All tests passed! Individual account endpoint is working.")
    else:
        print("\n❌ Tests failed. Check the logs for details.")

if __name__ == "__main__":
    main()
