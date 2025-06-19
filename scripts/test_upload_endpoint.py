#!/usr/bin/env python3
"""
Test script for the knowledge source file upload endpoint.
This script tests the S3 integration with the backend API.
"""

import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/v1/chat-configuration/knowledge-sources/upload"
AUTH_ENDPOINT = f"{BASE_URL}/api/auth/token"

def test_backend_connection():
    """Test if the backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not accessible: {e}")
        return False

def get_auth_token():
    """Get authentication token for API access."""
    # This would typically require valid credentials
    # For now, we'll just test the connection
    print("ℹ️  Authentication token would be needed for actual testing")
    return None

def create_test_file():
    """Create a test file for upload."""
    test_file_path = "/tmp/test_knowledge_source.txt"
    test_content = """
# Test Knowledge Source Document

This is a test document for the Genascope knowledge source upload system.

## Cancer Screening Guidelines

1. Regular screening is important for early detection
2. Different types of screening for different cancers
3. Age-appropriate screening recommendations

This document tests the S3 upload functionality through the backend API.
"""
    
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    print(f"✅ Created test file: {test_file_path}")
    return test_file_path

def test_upload_endpoint(test_file_path, auth_token=None):
    """Test the file upload endpoint."""
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return False
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    files = {
        'file': ('test_knowledge_source.txt', open(test_file_path, 'rb'), 'text/plain')
    }
    
    data = {
        'name': 'Test Knowledge Source',
        'description': 'A test document for S3 upload functionality',
        'tags': '["test", "cancer-screening", "guidelines"]',
        'access_level': 'private'
    }
    
    try:
        print("🚀 Testing file upload endpoint...")
        response = requests.post(UPLOAD_ENDPOINT, files=files, data=data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Knowledge Source ID: {result.get('id')}")
            print(f"Title: {result.get('title')}")
            print(f"Status: {result.get('status')}")
            print(f"Storage Path: {result.get('storage_path')}")
            return True
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    finally:
        files['file'][1].close()

def check_s3_bucket():
    """Check if the S3 bucket exists and is accessible."""
    try:
        import boto3
        s3_client = boto3.client('s3', region_name='us-west-2')
        
        bucket_name = 'genascope-dev-knowledge-sources'
        response = s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' is accessible")
        
        # List objects to verify we can read
        objects = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        object_count = objects.get('KeyCount', 0)
        print(f"ℹ️  Bucket contains {object_count} objects")
        
        return True
    except Exception as e:
        print(f"❌ S3 bucket check failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Genascope Knowledge Source Upload Endpoint")
    print("=" * 60)
    
    # Check S3 bucket accessibility
    print("\n1. Checking S3 bucket accessibility...")
    s3_ok = check_s3_bucket()
    
    # Check backend connectivity
    print("\n2. Checking backend connectivity...")
    backend_ok = test_backend_connection()
    
    if not backend_ok:
        print("\n❌ Cannot proceed with upload test - backend is not running")
        print("\nTo start the backend:")
        print("1. Navigate to the backend directory")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Set up environment variables in .env.local")
        print("4. Run: uvicorn app.main:app --reload")
        return
    
    # Create test file
    print("\n3. Creating test file...")
    test_file = create_test_file()
    
    # Get auth token (if possible)
    print("\n4. Getting authentication token...")
    auth_token = get_auth_token()
    
    # Test upload
    print("\n5. Testing file upload...")
    upload_ok = test_upload_endpoint(test_file, auth_token)
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"🧹 Cleaned up test file: {test_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"S3 Bucket Access: {'✅' if s3_ok else '❌'}")
    print(f"Backend Connection: {'✅' if backend_ok else '❌'}")
    print(f"File Upload: {'✅' if upload_ok else '❌'}")
    
    if s3_ok and backend_ok and upload_ok:
        print("\n🎉 All tests passed! The upload endpoint is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()
