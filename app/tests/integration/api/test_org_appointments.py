#!/usr/bin/env python3
"""
Test script for the organization appointments endpoint
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/Users/martial-m1/genascope-backend')

def test_import():
    """Test that all imports work correctly"""
    try:
        from app.api.appointments import router
        from app.schemas.appointments import OrganizationAppointmentListResponse
        from app.services.appointments import AppointmentService
        from app.repositories.appointments import AppointmentRepository
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_schema_structure():
    """Test the schema structure"""
    try:
        from app.schemas.appointments import OrganizationAppointmentResponse, OrganizationAppointmentListResponse
        
        # Test basic schema creation
        response_fields = OrganizationAppointmentResponse.model_fields
        list_response_fields = OrganizationAppointmentListResponse.model_fields
        
        print("✅ Schema structure valid!")
        print(f"   OrganizationAppointmentResponse fields: {list(response_fields.keys())}")
        print(f"   OrganizationAppointmentListResponse fields: {list(list_response_fields.keys())}")
        return True
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Organization Appointments Endpoint Implementation")
    print("=" * 60)
    
    success = True
    
    print("1. Testing imports...")
    success &= test_import()
    
    print("\n2. Testing schema structure...")
    success &= test_schema_structure()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! The implementation looks good.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
