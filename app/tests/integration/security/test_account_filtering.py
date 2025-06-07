#!/usr/bin/env python3
"""
Test script for account-based patient filtering
"""
import requests
import json
import sys

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

def get_current_user(token):
    """Get current user info"""
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"👤 Current user: {user_data.get('name')} ({user_data.get('role')}) - Account: {user_data.get('account_id', 'None')}")
        return user_data
    else:
        print(f"❌ Failed to get user info: {response.status_code}")
        return None

def list_patients(token, account_name=None):
    """List patients with optional account filtering"""
    print(f"\n📋 Listing patients" + (f" for account '{account_name}'" if account_name else ""))
    
    params = {}
    if account_name:
        params["account_name"] = account_name
    
    response = requests.get(
        f"{BASE_URL}/api/patients",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )
    
    if response.status_code == 200:
        patients = response.json()
        print(f"✅ Found {len(patients)} patients:")
        for patient in patients:
            print(f"  - {patient.get('first_name')} {patient.get('last_name')} (Account: {patient.get('account_id', 'None')})")
        return patients
    else:
        print(f"❌ Failed to list patients: {response.status_code} - {response.text}")
        return []

def list_accounts(token):
    """List all accounts"""
    print(f"\n🏥 Listing accounts...")
    
    response = requests.get(
        f"{BASE_URL}/api/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Found {len(accounts)} accounts:")
        for account in accounts:
            print(f"  - {account.get('name')} (ID: {account.get('id')})")
        return accounts
    else:
        print(f"❌ Failed to list accounts: {response.status_code} - {response.text}")
        return []

def test_accounts_endpoint(token):
    """Test the accounts endpoint"""
    print("📋 Testing accounts endpoint")
    
    response = requests.get(
        f"{BASE_URL}/api/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Retrieved {len(accounts)} accounts:")
        for account in accounts[:3]:  # Show first 3
            print(f"  - {account.get('name', 'Unknown')} (ID: {account.get('id', 'Unknown')[:8]}..., Status: {account.get('status', 'Unknown')})")
        if len(accounts) > 3:
            print(f"  ... and {len(accounts) - 3} more accounts")
        return accounts
    else:
        print(f"❌ Failed to get accounts: {response.status_code} - {response.text}")
        return []

def test_account_name_filtering(token):
    """Test account name filtering"""
    print("🔍 Testing account name filtering")
    
    # Test filtering by "Hospital"
    response = requests.get(
        f"{BASE_URL}/api/accounts",
        params={"name": "Hospital"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        hospitals = response.json()
        print(f"✅ Found {len(hospitals)} accounts with 'Hospital' in name:")
        for account in hospitals:
            print(f"  - {account.get('name', 'Unknown')}")
    else:
        print(f"❌ Failed to filter accounts: {response.status_code} - {response.text}")
    
    # Test filtering by "Clinic"
    response = requests.get(
        f"{BASE_URL}/api/accounts",
        params={"name": "Clinic"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        clinics = response.json()
        print(f"✅ Found {len(clinics)} accounts with 'Clinic' in name:")
        for account in clinics:
            print(f"  - {account.get('name', 'Unknown')}")
    else:
        print(f"❌ Failed to filter accounts: {response.status_code} - {response.text}")

def main():
    print("🧪 Testing Account-Based Patient Filtering\n")
    
    # Test cases
    test_users = [
        ("admin@test.com", "admin123", "Regular Admin"),
        ("superadmin@genascope.com", "admin123", "Super Admin"),
        ("clinician@test.com", "admin123", "Clinician")
    ]
    
    for email, password, user_type in test_users:
        print(f"\n{'='*60}")
        print(f"Testing as {user_type} ({email})")
        print(f"{'='*60}")
        
        # Authenticate
        token = authenticate(email, password)
        if not token:
            continue
        
        # Get user info
        user_info = get_current_user(token)
        if not user_info:
            continue
        
        # List accounts (for super admin)
        if user_info.get('role') == 'super_admin':
            accounts = list_accounts(token)
            
            # Test the accounts endpoint more thoroughly
            test_accounts_endpoint(token)
            
            # Test account name filtering
            test_account_name_filtering(token)
        
        # List all patients
        all_patients = list_patients(token)
        
        # For super admin, test account filtering
        if user_info.get('role') == 'super_admin':
            print(f"\n🔍 Testing account name filtering...")
            # Test with some known account names from our patient data
            list_patients(token, account_name="Test Hospital")
            list_patients(token, account_name="Medical Center")
            list_patients(token, account_name="Genascope Research")
            # Test with partial name match
            list_patients(token, account_name="test")
        
        print(f"\n✅ Test completed for {user_type}")

if __name__ == "__main__":
    main()
