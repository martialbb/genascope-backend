from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.schemas.users import UserCreate, UserResponse
from app.services.users import UserService

router = APIRouter(prefix="/api/account", tags=["account"])

@router.post("/create_user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user within an account (requires admin role).
    This is a legacy endpoint - the main user creation endpoint is now at /api/users
    """
    # Verify permissions
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data.model_dump())
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )