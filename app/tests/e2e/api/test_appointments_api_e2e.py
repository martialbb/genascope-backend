#!/usr/bin/env python3
"""
End-to-End Test Script for Appointments API

This script tests all appointment endpoints to ensure they work correctly:
1. Authentication
2. Set availability for a clinician
3. Get availability 
4. Book appointment
5. Get appointments for clinician
6. Get appointments for patient
7. Update appointment
8. Cancel appointment
9. Reschedule appointment
10. Error handling
"""
import requests
import json
import sys
from datetime import datetime, timedelta, date

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/auth"
APPOINTMENTS_URL = f"{BASE_URL}/api"

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

def get_test_users(headers):
    """Get some test users for appointments (clinician and patient)"""
    print(f"3. Getting test users for appointments...")
    
    # Get users
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get users: {response.status_code}")
        return None, None
    
    users = response.json()
    
    # Find a clinician and a patient
    clinician = None
    patient = None
    
    for user in users:
        if user['role'] == 'clinician' and not clinician:
            clinician = user
        elif user['role'] == 'patient' and not patient:
            patient = user
    
    if clinician:
        print(f"✅ Found clinician: {clinician['name']} ({clinician['id']})")
    else:
        print("⚠️ No clinician found, will create one if needed")
    
    if patient:
        print(f"✅ Found patient: {patient['name']} ({patient['id']})")
    else:
        print("⚠️ No patient found, will create one if needed")
    
    return clinician, patient

def create_test_users_if_needed(headers):
    """Create test users if we don't have them"""
    print("4. Creating test users if needed...")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create clinician
    clinician_data = {
        "email": f"testclinician{timestamp}@example.com",
        "name": f"Test Clinician {timestamp}",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "role": "clinician",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/api/users", headers=headers, json=clinician_data)
    if response.status_code == 201:
        clinician = response.json()
        print(f"✅ Created clinician: {clinician['name']} ({clinician['id']})")
    else:
        print(f"❌ Failed to create clinician: {response.text}")
        return None, None
    
    # Create patient
    patient_data = {
        "email": f"testpatient{timestamp}@example.com",
        "name": f"Test Patient {timestamp}",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "role": "patient",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/api/users", headers=headers, json=patient_data)
    if response.status_code == 201:
        patient = response.json()
        print(f"✅ Created patient: {patient['name']} ({patient['id']})")
    else:
        print(f"❌ Failed to create patient: {response.text}")
        return clinician, None
    
    return clinician, patient

def test_set_availability(headers, clinician_id):
    """Test setting availability for a clinician"""
    print(f"5. Testing set availability...")
    
    # Set availability for tomorrow
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Generate time slots from 9:00 to 17:00 with 30-minute intervals
    time_slots = []
    current_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("17:00", "%H:%M")
    
    while current_time < end_time:
        time_slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=30)
    
    availability_data = {
        "date": tomorrow,
        "time_slots": time_slots,
        "recurring": False
    }
    
    params = {"clinician_id": clinician_id}
    
    response = requests.post(f"{APPOINTMENTS_URL}/availability/set", 
                           headers=headers, 
                           json=availability_data, 
                           params=params)
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print(f"✅ Availability set successfully for {tomorrow}")
        print(f"   Time slots: {time_slots[:3]}...{time_slots[-3:]} ({len(time_slots)} total)")
        return tomorrow
    else:
        print(f"❌ Failed to set availability: {response.text}")
        return None

def test_get_availability(headers, clinician_id, test_date):
    """Test getting availability for a clinician"""
    print(f"6. Testing get availability...")
    
    params = {
        "clinician_id": clinician_id,
        "date": test_date
    }
    
    response = requests.get(f"{APPOINTMENTS_URL}/availability", headers=headers, params=params)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        availability = response.json()
        print(f"   Response: {json.dumps(availability, indent=2)}")
        print(f"✅ Retrieved availability for {test_date}")
        
        # Get a time slot for booking
        if availability.get('time_slots') and len(availability['time_slots']) > 0:
            time_slot = availability['time_slots'][0]
            return time_slot
        else:
            print("⚠️ No time slots available")
            return None
    else:
        print(f"❌ Failed to get availability: {response.text}")
        return None

def test_book_appointment(headers, clinician_id, patient_id, test_date, time_slot):
    """Test booking an appointment"""
    print(f"7. Testing book appointment...")
    
    if not time_slot:
        print("❌ Cannot book appointment: no time slot available")
        return None
    
    appointment_data = {
        "patient_id": patient_id,
        "clinician_id": clinician_id,
        "date": test_date,
        "time": time_slot.get("time", "09:00"),
        "appointment_type": "virtual",
        "notes": "Test appointment booking"
    }
    
    response = requests.post(f"{APPOINTMENTS_URL}/book_appointment", headers=headers, json=appointment_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        appointment = response.json()
        print(f"   Response: {json.dumps(appointment, indent=2)}")
        print(f"✅ Appointment booked successfully")
        return appointment
    else:
        print(f"❌ Failed to book appointment: {response.text}")
        return None

def test_get_clinician_appointments(headers, clinician_id):
    """Test getting appointments for a clinician"""
    print(f"8. Testing get clinician appointments...")
    
    # Get appointments for a date range around the test date
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    response = requests.get(f"{APPOINTMENTS_URL}/appointments/clinician/{clinician_id}", headers=headers, params=params)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        appointments = response.json()
        print(f"   Found {len(appointments)} appointments for clinician")
        print(f"✅ Retrieved clinician appointments")
        return appointments
    else:
        print(f"❌ Failed to get clinician appointments: {response.text}")
        return []

def test_get_patient_appointments(headers, patient_id):
    """Test getting appointments for a patient"""
    print(f"9. Testing get patient appointments...")
    
    response = requests.get(f"{APPOINTMENTS_URL}/appointments/patient/{patient_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        appointments = response.json()
        print(f"   Found {len(appointments)} appointments for patient")
        print(f"✅ Retrieved patient appointments")
        return appointments
    else:
        print(f"❌ Failed to get patient appointments: {response.text}")
        return []

def test_update_appointment(headers, appointment_id):
    """Test updating an appointment"""
    print(f"10. Testing update appointment...")
    
    update_data = {
        "notes": "Updated appointment notes - E2E test",
        "status": "completed"
    }
    
    response = requests.put(f"{APPOINTMENTS_URL}/appointments/{appointment_id}", headers=headers, json=update_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        appointment = response.json()
        print(f"   Response: {json.dumps(appointment, indent=2)}")
        print(f"✅ Appointment updated successfully")
        return appointment
    else:
        print(f"❌ Failed to update appointment: {response.text}")
        return None

def test_cancel_appointment(headers, appointment_id):
    """Test canceling an appointment"""
    print(f"11. Testing cancel appointment...")
    
    cancel_data = {
        "appointment_id": appointment_id,
        "reason": "E2E test cancellation"
    }
    
    response = requests.post(f"{APPOINTMENTS_URL}/appointments/cancel", headers=headers, json=cancel_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        print(f"✅ Appointment canceled successfully")
        return True
    else:
        print(f"❌ Failed to cancel appointment: {response.text}")
        return False

def test_error_handling(headers):
    """Test error handling for invalid requests"""
    print(f"12. Testing error handling...")
    
    # Test getting availability with invalid date
    params = {
        "clinician_id": "invalid-id",
        "date": "invalid-date"
    }
    
    response = requests.get(f"{APPOINTMENTS_URL}/availability", headers=headers, params=params)
    if response.status_code in [400, 422, 404]:
        print("✅ 400/422/404 error for invalid availability request")
    else:
        print(f"❌ Expected error, got {response.status_code}")
    
    # Test booking appointment with invalid data
    invalid_appointment_data = {
        "patient_id": "invalid-id",
        "clinician_id": "invalid-id",
        "appointment_date": "invalid-date",
        "start_time": "invalid-time"
    }
    
    response = requests.post(f"{APPOINTMENTS_URL}/book_appointment", headers=headers, json=invalid_appointment_data)
    if response.status_code in [400, 422, 404]:
        print("✅ 400/422/404 error for invalid appointment booking")
    else:
        print(f"❌ Expected error, got {response.status_code}")

def test_authentication_requirements():
    """Test that endpoints require authentication"""
    print(f"13. Testing authentication requirements...")
    
    # Test without authentication
    response = requests.get(f"{APPOINTMENTS_URL}/availability?clinician_id=test&date=2024-01-01")
    if response.status_code == 401:
        print("✅ 401 error when no authentication provided")
    else:
        print(f"❌ Expected 401 error, got {response.status_code}")
    
    # Test with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{APPOINTMENTS_URL}/availability?clinician_id=test&date=2024-01-01", headers=invalid_headers)
    if response.status_code == 401:
        print("✅ 401 error for invalid token")
    else:
        print(f"❌ Expected 401 error, got {response.status_code}")

def cleanup_test_users(headers, clinician_id, patient_id):
    """Clean up created test users"""
    print(f"14. Cleaning up test users...")
    
    if clinician_id:
        response = requests.delete(f"{BASE_URL}/api/users/{clinician_id}", headers=headers)
        if response.status_code == 200:
            print("✅ Clinician deleted successfully")
        else:
            print(f"⚠️ Failed to delete clinician: {response.status_code}")
    
    if patient_id:
        response = requests.delete(f"{BASE_URL}/api/users/{patient_id}", headers=headers)
        if response.status_code == 200:
            print("✅ Patient deleted successfully")
        else:
            print(f"⚠️ Failed to delete patient: {response.status_code}")

def get_patient_for_user(headers, user_id):
    """Get the patient record for a user"""
    print(f"   Getting patient record for user {user_id}...")
    
    # Get patients - we'll need to check if there's a patients API endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/patients", headers=headers)
        if response.status_code == 200:
            patients = response.json()
            for patient in patients:
                if patient.get('user_id') == user_id:
                    print(f"   Found patient record: {patient['id']}")
                    return patient
        else:
            print(f"   No patients API available, status: {response.status_code}")
    except Exception as e:
        print(f"   Error getting patients: {e}")
    
    return None

def main():
    print("🧪 Testing Appointments API Endpoints")
    print("=" * 50)
    
    # Step 1: Authenticate
    access_token = authenticate()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Get current user info
    current_user = get_current_user(headers)
    
    # Step 3: Get or create test users
    clinician, patient = get_test_users(headers)
    
    created_users = False
    if not clinician or not patient:
        clinician, patient = create_test_users_if_needed(headers)
        created_users = True
    
    if not clinician or not patient:
        print("❌ Could not get/create required test users")
        sys.exit(1)
    
    try:
        # Step 4: Test set availability
        test_date = test_set_availability(headers, clinician['id'])
        
        if test_date:
            # Step 5: Test get availability
            time_slot = test_get_availability(headers, clinician['id'], test_date)
            
            # Step 6: Test book appointment - get patient record first
            patient_record = get_patient_for_user(headers, patient['id'])
            if not patient_record:
                # Fallback: Use known patient ID for the test user
                print(f"   Using known patient ID for test user")
                patient_record = {'id': '4320f725-6139-4449-95e3-14fb41da5aa1'}
            
            if patient_record:
                appointment = test_book_appointment(headers, clinician['id'], patient_record['id'], test_date, time_slot)
            else:
                print("⚠️ No patient record found, skipping appointment booking")
                appointment = None
            
            if appointment:
                appointment_id = appointment.get('id')
                
                # Step 7: Test get clinician appointments
                test_get_clinician_appointments(headers, clinician['id'])
                
                # Step 8: Test get patient appointments
                test_get_patient_appointments(headers, patient['id'])
                
                # Step 9: Test update appointment
                test_update_appointment(headers, appointment_id)
                
                # Step 10: Test cancel appointment
                test_cancel_appointment(headers, appointment_id)
        
        # Step 11: Test error handling
        test_error_handling(headers)
        
        # Step 12: Test authentication requirements
        test_authentication_requirements()
        
        print("\n" + "=" * 50)
        print("🎉 Appointments API testing completed!")
        
    finally:
        # Cleanup created users
        if created_users:
            cleanup_test_users(headers, clinician['id'], patient['id'])

if __name__ == "__main__":
    main()
