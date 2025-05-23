from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from app.api.auth import get_current_active_user, User
from app.schemas import (
    UserCreate, UserResponse, UserUpdate, UserPasswordChange,
    UserRole, PatientProfile, ClinicianProfile
)

router = APIRouter(prefix="/api/account", tags=["account"])
    
# Mock account admin verification - in a real app, this would check admin privileges
async def verify_account_admin(current_user: User = Depends(get_current_active_user)):
    # This is a simplified check - in a real app, you would check against user roles in the database
    if current_user.username != "admin@genascope.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only account administrators can perform this action"
        )
    return current_user

@router.post("/create_user", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(verify_account_admin)
):
    """
    Create a new user within an account.
    Only account administrators can create users.
    """
    # For now, echo back all required fields from UserCreate
    return UserResponse(
        id=f"usr_{user_data.email.split('@')[0]}",
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        is_active=True
    )
