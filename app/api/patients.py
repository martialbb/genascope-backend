"""
API endpoints for managing patient data and operations.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import csv
from io import StringIO

from app.db.database import get_db
from app.api.auth import require_full_access, User
from app.services.patients import PatientService
from app.services.invites import InviteService
from app.models.user import UserRole
from app.schemas.patients import (
    PatientCreate, PatientResponse, PatientUpdate, PatientBulkImport, 
    PatientImportResponse, PatientCSVImportResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    request: Request,
    clinician_id: Optional[str] = None,
    account_id: Optional[str] = None,
    account_name: Optional[str] = None,
    query: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get patients based on filters with account-based access control.
    
    - Non-superusers can only see patients from their account
    - Superusers can see patients from all accounts and filter by account_id or account_name
    - Clinicians are restricted to their assigned patients
    """
    # Only clinicians, admins and super admins can view patients
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view patients"
        )
    
    patient_service = PatientService(db)
    
    # Account-based access control
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can access all accounts and filter by account_id or account_name if provided
        # If account_id or account_name is provided, use it; otherwise show all patients
        pass  # account_id and account_name can be None or specific values
    else:
        # Non-super admins can only access patients from their own account
        if not current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not associated with any organization"
            )
        
        # Override account_id parameter with user's account for non-super admins
        account_id = current_user.account_id
        # Clear account_name filter for non-super admins as they can't filter by other accounts
        account_name = None
    
    # If clinician_id is not provided but user is a clinician, use their ID
    if not clinician_id and current_user.role == UserRole.CLINICIAN:
        clinician_id = current_user.id
    
    search_params = {
        "account_id": account_id,
        "account_name": account_name,
        "clinician_id": clinician_id,
        "query": query,
        "status": status,
        "offset": offset,
        "limit": limit
    }
    
    patients_with_status = patient_service.search_patients_with_invite_status(search_params)
    
    # Convert to response model
    patient_responses = [PatientResponse(**patient) for patient in patients_with_status]
    
    return patient_responses


@router.post("/", response_model=PatientResponse)
async def create_patient(
    request: Request,
    patient_data: PatientCreate,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Create a new patient record
    """
    # Only clinicians, admins and super admins can create patients
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create patients"
        )
    
    patient_service = PatientService(db)
    
    # Use the current user's account if not specified
    if not hasattr(patient_data, "account_id") or not patient_data.account_id:
        # Assign the patient to the current user's account
        patient_data_dict = patient_data.model_dump()
        if current_user.account_id:
            patient_data_dict["account_id"] = current_user.account_id
    else:
        patient_data_dict = patient_data.model_dump()
    
    try:
        patient = patient_service.create_patient(patient_data_dict)
        
        # Get patient with invite status
        patient_with_status = patient_service.get_patient_with_invite_status(patient.id)
        
        return PatientResponse(**patient_with_status)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(e)}"
        )


@router.post("/bulk", response_model=PatientImportResponse)
async def bulk_create_patients(
    request: Request,
    bulk_data: PatientBulkImport,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Create multiple patients at once
    """
    # Only admins and super admins can bulk create patients
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to bulk create patients"
        )
    
    patient_service = PatientService(db)
    
    # Process each patient in the bulk import
    patients_data = []
    for patient in bulk_data.patients:
        patient_dict = patient.model_dump()
        
        # If no clinician assigned for this patient, use the default
        if not patient_dict.get("clinician_id") and bulk_data.clinician_id:
            patient_dict["clinician_id"] = bulk_data.clinician_id
        
        # Use the current user's account if available
        if current_user.account_id:
            patient_dict["account_id"] = current_user.account_id
        
        patients_data.append(patient_dict)
    
    # Create patients in bulk
    successful, failed = patient_service.bulk_create_patients(patients_data)
    
    # Get patients with invite status
    successful_with_status = []
    for patient in successful:
        patient_with_status = patient_service.get_patient_with_invite_status(patient.id)
        successful_with_status.append(patient_with_status)
    
    # Convert to response format
    response = PatientImportResponse(
        successful=[PatientResponse(**patient) for patient in successful_with_status],
        failed=failed,
        total_imported=len(successful),
        total_failed=len(failed)
    )
    
    return response


@router.post("/import-csv", response_model=PatientCSVImportResponse)
async def import_patients_from_csv(
    request: Request,
    file: UploadFile = File(...),
    clinician_id: Optional[str] = None,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Import patients from a CSV file
    
    CSV format should have headers:
    email,first_name,last_name,phone,external_id,date_of_birth
    
    Example:
    email,first_name,last_name,phone,external_id,date_of_birth
    patient1@example.com,John,Doe,123-456-7890,CLIN001,1980-01-01
    patient2@example.com,Jane,Smith,123-456-7891,CLIN002,1985-05-15
    """
    # Only admins and super admins can import patients from CSV
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to import patients from CSV"
        )
    
    # Check if file is CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    # Read the CSV file
    contents = await file.read()
    
    try:
        # Decode and parse CSV
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_text))
        
        # Process CSV rows
        csv_data = []
        for row in csv_reader:
            # Clean up field names (remove whitespace)
            clean_row = {k.strip(): v for k, v in row.items()}
            csv_data.append(clean_row)
        
        # Check if there's data
        if not csv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or has no valid data"
            )
        
        # Import patients
        patient_service = PatientService(db)
        account_id = current_user.account_id if current_user.account_id else None
        
        if not account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no associated account"
            )
        
        successful, failed = patient_service.import_patients_from_csv(csv_data, account_id, clinician_id)
        
        # Get sample of successful patients with invite status for response
        sample_patients = []
        for patient in successful[:5]:  # Show up to 5 examples
            patient_with_status = patient_service.get_patient_with_invite_status(patient.id)
            sample_patients.append(PatientResponse(**patient_with_status))
        
        # Create response
        response = PatientCSVImportResponse(
            successful_count=len(successful),
            failed_count=len(failed),
            errors=failed,
            sample_patients=sample_patients
        )
        
        return response
    except HTTPException as e:
        raise e
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is not properly encoded (use UTF-8)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import patients: {str(e)}"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    request: Request,
    patient_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Get a specific patient by ID
    """
    # Only clinicians, admins and super admins can view patients
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view patients"
        )
    
    patient_service = PatientService(db)
    
    try:
        patient_with_status = patient_service.get_patient_with_invite_status(patient_id)
        
        if not patient_with_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Check if user has access to this patient's account
        if (current_user.role not in [UserRole.SUPER_ADMIN] and 
            current_user.account_id and 
            str(patient_with_status.get("account_id")) != str(current_user.account_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this patient"
            )
        
        return PatientResponse(**patient_with_status)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient: {str(e)}"
        )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    request: Request,
    patient_id: str,
    patient_data: PatientUpdate,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Update an existing patient record
    """
    # Only clinicians, admins and super admins can update patients
    if current_user.role not in [UserRole.CLINICIAN, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update patients"
        )
    
    patient_service = PatientService(db)
    
    try:
        # First check if patient exists and user has access
        existing_patient = patient_service.get_patient_with_invite_status(patient_id)
        
        if not existing_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Check if user has access to this patient's account
        if (current_user.role not in [UserRole.SUPER_ADMIN] and 
            current_user.account_id and 
            str(existing_patient.get("account_id")) != str(current_user.account_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this patient"
            )
        
        # Update the patient
        update_data = patient_data.model_dump(exclude_unset=True)
        updated_patient = patient_service.update_patient(patient_id, update_data)
        
        if not updated_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Get updated patient with invite status
        patient_with_status = patient_service.get_patient_with_invite_status(updated_patient.id)
        
        return PatientResponse(**patient_with_status)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient: {str(e)}"
        )


@router.delete("/{patient_id}", status_code=status.HTTP_200_OK)
async def delete_patient(
    request: Request,
    patient_id: str,
    current_user: User = Depends(require_full_access),
    db: Session = Depends(get_db)
):
    """
    Delete a patient record
    """
    # Only admins and super admins can delete patients
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete patients"
        )
    
    patient_service = PatientService(db)
    
    try:
        # First check if patient exists and user has access
        existing_patient = patient_service.get_patient_with_invite_status(patient_id)
        
        if not existing_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Check if user has access to this patient's account
        if (current_user.role not in [UserRole.SUPER_ADMIN] and 
            current_user.account_id and 
            str(existing_patient.get("account_id")) != str(current_user.account_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this patient"
            )
        
        # Check if patient has any pending invites or active sessions
        if existing_patient.get("has_pending_invite"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete patient with pending invites. Cancel invites first."
            )
        
        # Delete the patient
        success = patient_service.delete_patient(patient_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete patient"
            )
        
        return SuccessResponse(
            message="Patient deleted successfully",
            data={"patient_id": patient_id}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete patient: {str(e)}"
        )
