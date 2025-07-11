#!/usr/bin/env python3
"""
End-to-End Test Script for Users API

This script tests all user endpoints to ensure they work correctly:
1. Authentication
2. List users (with filtering and pagination)
3. Create user
4. Get user by ID
5. Update user
6. Delete user
7. Error handling
8. Permission checks
"""
import requests
import json
import sys
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/auth"
USERS_URL = f"{BASE_URL}/api/users"

# Test credentials (super admin)
USERNAME = "superadmin@genascope.com"
PASSWORD = "SuperAdmin123!"

def authenticate():
    """Authenticate and get access token"""
    print(f"1. Authenticating with {USERNAME}...")
    
    auth_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    }
    
    response = requests.post(f"{AUTH_URL}/token", data=auth_data)
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print("✅ Authentication successful")
    
    return access_token

def get_current_user(headers):
    """Get current user information"""
    print(f"2. Checking current user role...")
    
    response = requests.get(f"{AUTH_URL}/me", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get current user: {response.status_code}")
        sys.exit(1)
    
    user_data = response.json()
    print(f"✅ Current user: {user_data['email']}")
    print(f"   Role: {user_data['role']}")
    print(f"   ID: {user_data['id']}")
    
    return user_data

def test_list_users(headers):
    """Test listing users with various filters"""
    print(f"3. Testing get all users...")
    
    response = requests.get(USERS_URL, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        users = response.json()
        print(f"   Response: {json.dumps(users, indent=2)}")
        print(f"✅ Retrieved {len(users)} users")
        return users
    else:
        print(f"❌ Failed to get users: {response.text}")
        return []

def test_list_users_with_filters(headers):
    """Test listing users with filters and pagination"""
    print(f"4. Testing get users with filters...")
    
    # Test pagination
    params = {"skip": 0, "limit": 5}
    response = requests.get(USERS_URL, headers=headers, params=params)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Pagination works: {len(users)} users (limit 5)")
        
        # Test role filter if we have users
        if users:
            params = {"role": "super_admin"}
            response = requests.get(USERS_URL, headers=headers, params=params)
            if response.status_code == 200:
                filtered_users = response.json()
                print(f"✅ Role filtering works: {len(filtered_users)} super_admin users")
        
        return users
    else:
        print(f"❌ Failed to get filtered users: {response.text}")
        return []

def test_create_user(headers):
    """Test creating a new user"""
    print(f"5. Testing create new user...")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    user_data = {
        "email": f"testuser{timestamp}@example.com",
        "name": f"Test User {timestamp}",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "role": "clinician",
        "is_active": True
    }
    
    response = requests.post(USERS_URL, headers=headers, json=user_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        user = response.json()
        print(f"   Response: {json.dumps(user, indent=2)}")
        print(f"✅ User created successfully: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user['name']}")
        print(f"   Role: {user['role']}")
        return user
    else:
        print(f"❌ Failed to create user: {response.text}")
        return None

def test_get_user_by_id(headers, user_id):
    """Test getting a user by ID"""
    print(f"6. Testing get user by ID...")
    
    response = requests.get(f"{USERS_URL}/{user_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        user = response.json()
        print(f"   Response: {json.dumps(user, indent=2)}")
        print(f"✅ Retrieved user: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user['name']}")
        return user
    else:
        print(f"❌ Failed to get user: {response.text}")
        return None

def test_update_user(headers, user_id):
    """Test updating a user"""
    print(f"7. Testing update user...")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    update_data = {
        "name": f"Updated Test User {timestamp}",
        "is_active": True
    }
    
    response = requests.put(f"{USERS_URL}/{user_id}", headers=headers, json=update_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        user = response.json()
        print(f"   Response: {json.dumps(user, indent=2)}")
        print(f"✅ User updated successfully")
        print(f"   New name: {user['name']}")
        return user
    else:
        print(f"❌ Failed to update user: {response.text}")
        return None

def test_error_handling(headers):
    """Test error handling for invalid requests"""
    print(f"8. Testing error handling...")
    
    # Test creating user with invalid data
    invalid_user_data = {
        "email": "invalid-email",  # Invalid email format
        "name": "",  # Empty name
        "password": "123",  # Weak password
        "role": "invalid_role"  # Invalid role
    }
    
    response = requests.post(USERS_URL, headers=headers, json=invalid_user_data)
    if response.status_code in [400, 422]:
        print("✅ 422/400 error for invalid user data")
    else:
        print(f"❌ Expected 422/400 error, got {response.status_code}")

def test_delete_user(headers, user_id):
    """Test deleting a user"""
    print(f"9. Testing delete user...")
    
    response = requests.delete(f"{USERS_URL}/{user_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        print(f"✅ User deleted successfully")
        return True
    else:
        print(f"❌ Delete user failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_authentication_requirements():
    """Test that endpoints require authentication"""
    print(f"10. Testing authentication requirements...")
    
    # Test without authentication
    response = requests.get(USERS_URL)
    if response.status_code == 401:
        print("✅ 401 error when no authentication provided")
    else:
        print(f"❌ Expected 401 error, got {response.status_code}")
    
    # Test with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(USERS_URL, headers=invalid_headers)
    if response.status_code == 401:
        print("✅ 401 error for invalid token")
    else:
        print(f"❌ Expected 401 error, got {response.status_code}")

def main():
    print("🧪 Testing User API Endpoints")
    print("=" * 50)
    
    # Step 1: Authenticate
    access_token = authenticate()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Get current user info
    current_user = get_current_user(headers)
    
    # Step 3: Test list users
    users = test_list_users(headers)
    
    # Step 4: Test list users with filters
    filtered_users = test_list_users_with_filters(headers)
    
    # Step 5: Test create user
    created_user = test_create_user(headers)
    
    if created_user:
        user_id = created_user["id"]
        
        # Step 6: Test get user by ID
        retrieved_user = test_get_user_by_id(headers, user_id)
        
        # Step 7: Test update user
        updated_user = test_update_user(headers, user_id)
        
        # Step 8: Test error handling
        test_error_handling(headers)
        
        # Step 9: Test delete user
        deleted = test_delete_user(headers, user_id)
        
        # Step 10: Test authentication requirements
        test_authentication_requirements()
        
        print("\n" + "=" * 50)
        print("🎉 Users API testing completed!")
        
        # Cleanup: try to delete the created user if it wasn't deleted successfully
        if not deleted:
            print(f"11. Cleaning up created user...")
            cleanup_response = requests.delete(f"{USERS_URL}/{user_id}", headers=headers)
            if cleanup_response.status_code == 200:
                print("✅ Cleanup successful")
            else:
                print(f"⚠️ Cleanup failed: {cleanup_response.status_code}")
    else:
        print("❌ Could not test remaining endpoints due to user creation failure")
        sys.exit(1)

if __name__ == "__main__":
    main()
