from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.services.users import UserService
from app.models.user import UserRole
from app.schemas.users import (
    UserResponse, UserCreate, UserUpdate, PatientResponse, 
    PatientCreate, PatientProfileResponse, PatientProfileUpdate,
    PatientProfileCreate, AccountResponse, AccountCreate, AccountUpdate
)
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/users", tags=["users"])

# User management endpoints

@router.get("", response_model=List[UserResponse])
async def get_users(
    role: Optional[str] = None,
    account_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users with optional filtering
    """
    # Check permissions - Admin or super_admin role required
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user list"
        )
    
    user_service = UserService(db)
    # TODO: Implement filtering, pagination and total count in user service
    # For now, return mock response
    users = user_service.get_users(role=role, account_id=account_id, skip=skip, limit=limit)
    return users

@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user
    """
    # Check permissions - Admin or super_admin role required
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create users"
        )
    
    # Only super_admin can create admin users
    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create admin users"
        )
    
    # Super_admin users can only be created by other super_admins
    if user_data.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create super admin users"
        )
    
    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data.model_dump())
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID
    """
    # Users can view their own profile, admins can view any profile
    if user_id != current_user.id and current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        # Clinicians can view their patients
        user_service = UserService(db)
        patient = user_service.get_user_by_id(user_id)
        
        if not patient or patient.clinician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user details
    """
    # Users can update their own profile, admins can update any profile
    if user_id != current_user.id and current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Only super_admin can change roles
    if user_data.role is not None and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change user roles"
        )
    
    user_service = UserService(db)
    user = user_service.update_user(user_id, user_data.model_dump(exclude_unset=True))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user
    """
    # Only admins can delete users, and users cannot delete themselves
    if current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete users"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user_service = UserService(db)
    
    # Check if target user is an admin - only super_admin can delete admins
    target_user = user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if target_user.role == UserRole.ADMIN and current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete admin users"
        )
    
    if target_user.role == UserRole.SUPER_ADMIN and current_user.id != target_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin users can only delete themselves"
        )
    
    success = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    return SuccessResponse(
        message="User deleted successfully",
        data={"id": user_id}
    )

# Patient-specific endpoints

@router.post("/patients", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new patient with profile
    """
    # Clinicians and admins can create patients
    if current_user.role not in [UserRole.CLINICIAN.value, UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create patients"
        )
    
    # If clinician, automatically assign patient to themselves
    if current_user.role == UserRole.CLINICIAN.value:
        patient_data.clinician_id = current_user.id
    
    user_service = UserService(db)
    profile_data = None
    if patient_data.profile:
        profile_data = patient_data.profile.model_dump()
    
    try:
        patient_response = user_service.create_patient(
            patient_data.model_dump(exclude={"profile"}), 
            profile_data
        )
        return patient_response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(e)}"
        )

@router.get("/patients/{patient_id}/profile", response_model=PatientProfileResponse)
async def get_patient_profile(
    patient_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a patient's profile
    """
    user_service = UserService(db)
    
    # Check authorization - admins and the patient's clinician
    patient = user_service.get_user_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    if (current_user.id != patient_id and  # Not the patient themselves
        current_user.id != patient.clinician_id and  # Not the patient's clinician
        current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]):  # Not an admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient's profile"
        )
    
    profile = user_service.get_patient_profile(patient_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    return profile

@router.put("/patients/{patient_id}/profile", response_model=PatientProfileResponse)
async def update_patient_profile(
    patient_id: str,
    profile_data: PatientProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a patient's profile
    """
    user_service = UserService(db)
    
    # Check authorization - admins and the patient's clinician
    patient = user_service.get_user_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    if (current_user.id != patient_id and  # Not the patient themselves
        current_user.id != patient.clinician_id and  # Not the patient's clinician
        current_user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]):  # Not an admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this patient's profile"
        )
    
    # Get existing profile
    profile = user_service.get_patient_profile(patient_id)
    if not profile:
        # Create profile if it doesn't exist
        profile_data_dict = profile_data.model_dump(exclude_unset=True)
        profile_data_dict["id"] = str(uuid.uuid4())
        profile_data_dict["user_id"] = patient_id
        profile = user_service.profile_repository.create_profile(profile_data_dict)
    else:
        # Update existing profile
        profile = user_service.update_patient_profile(
            profile.id, 
            profile_data.model_dump(exclude_unset=True)
        )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update patient profile"
        )
    
    return profile

# Account management endpoints

@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new account
    """
    # Only super_admin can create accounts
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create accounts"
        )
    
    user_service = UserService(db)
    try:
        account = user_service.create_account(account_data.model_dump())
        return account
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )

@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of accounts
    """
    # Only super_admin can list accounts
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view account list"
        )
    
    # TODO: Implement account listing in user service
    # For now, return empty list
    return []

@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an account
    """
    # Only super_admin can update accounts
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update accounts"
        )
    
    user_service = UserService(db)
    account = user_service.update_account(account_id, account_data.model_dump(exclude_unset=True))
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account
