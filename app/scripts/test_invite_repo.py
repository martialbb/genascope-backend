#!/usr/bin/env python
"""
Simple test to check if the InviteRepository.get_by_patient_id method exists and works.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing InviteRepository.get_by_patient_id method...")

try:
    from repositories.invites import InviteRepository
    print("✓ Successfully imported InviteRepository")
    
    # Check if the method exists
    if hasattr(InviteRepository, 'get_by_patient_id'):
        print("✓ get_by_patient_id method exists")
        
        # Get method details
        import inspect
        method = getattr(InviteRepository, 'get_by_patient_id')
        signature = inspect.signature(method)
        print(f"✓ Method signature: {signature}")
        
        # Try to get source code
        try:
            source = inspect.getsource(method)
            print("✓ Method source code:")
            print(source)
        except Exception as e:
            print(f"Could not get source: {e}")
            
    else:
        print("✗ get_by_patient_id method does not exist")
        print("Available methods:")
        methods = [m for m in dir(InviteRepository) if not m.startswith('_')]
        for method in methods:
            print(f"  - {method}")
            
except ImportError as e:
    print(f"✗ Failed to import InviteRepository: {e}")
    print("Available files in repositories/:")
    try:
        import os
        files = os.listdir('repositories')
        for f in files:
            print(f"  - {f}")
    except:
        print("  Could not list files")

print("\nTesting PatientService...")

try:
    from services.patients import PatientService
    print("✓ Successfully imported PatientService")
    
    # Check if the method exists
    if hasattr(PatientService, 'update_patient'):
        print("✓ update_patient method exists")
        
        # Get method details
        import inspect
        method = getattr(PatientService, 'update_patient')
        signature = inspect.signature(method)
        print(f"✓ Method signature: {signature}")
        
    else:
        print("✗ update_patient method does not exist")
        
except ImportError as e:
    print(f"✗ Failed to import PatientService: {e}")

print("\nDone!")
