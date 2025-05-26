"""
User Management API

All user CRUD, authentication, and update operations are performed via the repository layer (`UserRepository`) through the service layer (`UserService`).
This ensures a clean separation of concerns, maintainability, and testability. No direct database calls are made in the API or service layer for user operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, Path, Body
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.auth import get_current_active_user, User
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services.users import UserService

router = APIRouter(prefix="/api/users", tags=["users"])

# Verify admin or super admin privileges for user management
async def verify_user_management_permissions(current_user: User = Depends(get_current_active_user)):
    """Dependency to verify user has permissions to manage users"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage users"
        )
    return current_user

@router.get("/", response_model=List[UserResponse], summary="List Users")
async def get_users(
    role: Optional[str] = Query(None, description="Filter users by role (e.g., admin, clinician, patient)"),
    account_id: Optional[str] = Query(None, description="Filter users by account ID"),
    search: Optional[str] = Query(None, description="Search users by name or email"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(verify_user_management_permissions),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of users with filtering, searching and pagination options.

    - **Permissions**: Requires admin or super_admin role
    - **Filtering**: Filter by role, account_id
    - **Search**: Search by name or email (case-insensitive)
    - **Pagination**: Use skip and limit parameters

    Regular admins can only see users in their own account.
    Super admins can see all users across accounts.

    Returns a list of users matching the specified criteria.
    """
    user_service = UserService(db)

    # Regular admins can only see users in their own account
    if current_user.role == "admin" and (not account_id or account_id != current_user.account_id):
        account_id = current_user.account_id

    return user_service.get_users(
        role=role,
        account_id=account_id,
        search=search,
        skip=skip,
        limit=limit
    )

@router.get("/{user_id}", response_model=UserResponse, summary="Get User")
async def get_user(
    user_id: str = Path(..., description="The ID of the user to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific user by ID.

    - **Permissions**:
      - Users can view their own profile
      - Admins can view users in their account
      - Super admins can view any user
    - **Path Parameter**: user_id - The unique identifier of the user

    Returns the specified user's details if the current user has permissions to view them.
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions: users can see their own profile, admins can see users in their account
    if (current_user.id != user_id and
        current_user.role != "super_admin" and
        (current_user.role != "admin" or current_user.account_id != user.account_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User")
async def create_user(
    user_data: UserCreate = Body(...,
        examples={
            "regular_user": {
                "summary": "Create a regular user",
                "value": {
                    "email": "user@example.com",
                    "name": "New User",
                    "role": "clinician",
                    "account_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "is_active": True,
                    "password": "StrongPassword123!",
                    "confirm_password": "StrongPassword123!"
                }
            },
            "admin_user": {
                "summary": "Create an admin user (super_admin only)",
                "value": {
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "account_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "is_active": True,
                    "password": "AdminStrongPassword123!",
                    "confirm_password": "AdminStrongPassword123!"
                }
            }
        }
    ),
    current_user: User = Depends(verify_user_management_permissions),
    db: Session = Depends(get_db)
):
    """
    Create a new user.

    - **Permissions**:
      - Admins can create regular users in their own account
      - Super admins can create any user in any account
    - **Request Body**: User details including password
    - **Account Restrictions**: Regular admins can only create users in their own account
    - **Role Restrictions**: Only super admins can create users with admin or super_admin roles

    Returns the created user details (without password).
    """
    # Regular admins can only create users in their own account
    if current_user.role == "admin":
        if not user_data.account_id:
            user_data.account_id = current_user.account_id
        elif user_data.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create users in your own account"
            )

    # Only super_admin can create users with admin or super_admin roles
    if user_data.role in ["admin", "super_admin"] and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can create admin or super_admin users"
        )

    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data)
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

@router.put("/{user_id}", response_model=UserResponse, summary="Update User")
async def update_user(
    user_id: str = Path(..., description="The ID of the user to update"),
    user_data: UserUpdate = Body(...,
        examples={
            "basic_update": {
                "summary": "Update basic user information",
                "value": {
                    "name": "Updated Name",
                    "email": "updated@example.com"
                }
            },
            "status_update": {
                "summary": "Activate or deactivate a user",
                "value": {
                    "is_active": False
                }
            },
            "admin_update": {
                "summary": "Update role (admin only)",
                "value": {
                    "role": "clinician",
                    "is_active": True
                }
            }
        }
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a user's information.

    - **Permissions**:
      - Users can update their own basic information (name, email)
      - Admins can update users in their account
      - Super admins can update any user
    - **Path Parameter**: user_id - The unique identifier of the user to update
    - **Request Body**: User details to update
    - **Role Restrictions**: Only super admins can assign admin or super_admin roles

    Returns the updated user information.
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    is_admin_or_super = current_user.role in ["admin", "super_admin"]
    is_self_update = current_user.id == user_id
    is_same_account = getattr(current_user, "account_id", None) == getattr(user, "account_id", None)

    if not is_self_update and (not is_admin_or_super or (current_user.role == "admin" and not is_same_account)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # For self-updates, only allow updating certain fields
    if is_self_update and not is_admin_or_super:
        allowed_fields = {"name", "email"}
        for field in user_data.model_dump(exclude_unset=True):
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to update the {field} field"
                )

    # Only super_admin can change roles to admin or super_admin
    print(f"DEBUG: user_data type: {type(user_data)}")
    print(f"DEBUG: user_data fields: {dir(user_data)}")
    print(f"DEBUG: user_data dict: {user_data.model_dump(exclude_unset=True)}")
    
    # Check if role is included in the update data
    user_data_dict = user_data.model_dump(exclude_unset=True)
    if 'role' in user_data_dict and user_data_dict['role'] is not None:
        role_value = user_data_dict['role']
        print(f"DEBUG: role value from dict: {role_value}")
        
        # Only super_admin can assign admin or super_admin roles
        if role_value in ["admin", "super_admin"] and current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can assign admin or super_admin roles"
            )

    try:
        # First, get the current user state for detailed logging
        current_user_state = user_service.get_user_by_id(user_id)
        print(f"DEBUG API: Current user state before update: role={current_user_state.role}, name={current_user_state.name}")
        
        # Attempt the update
        updated_user = user_service.update_user(user_id, user_data)
        
        # Log the result
        print(f"DEBUG API: Updated user result: role={updated_user.role}, name={updated_user.name}")
        
        # Verify update was successful by reloading the user
        reloaded_user = user_service.get_user_by_id(user_id)
        print(f"DEBUG API: Reloaded user state: role={reloaded_user.role}, name={reloaded_user.name}")
        
        # Return the reloaded user to ensure we're sending the most accurate state
        return reloaded_user
    except ValueError as e:
        print(f"DEBUG API: Value error during update: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        print(f"DEBUG API: Exception during update: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_200_OK, summary="Delete User")
async def delete_user(
    user_id: str = Path(..., description="The ID of the user to delete"),
    current_user: User = Depends(verify_user_management_permissions),
    db: Session = Depends(get_db)
):
    """
    Delete a user.

    - **Permissions**:
      - Admins can delete users in their account
      - Super admins can delete any user
    - **Path Parameter**: user_id - The unique identifier of the user to delete
    - **Restrictions**:
      - Users cannot delete themselves
      - Regular admins can only delete users in their account

    This is a destructive operation that permanently removes the user.
    This operation cannot be undone.

    Returns a success message when the user is successfully deleted.
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Regular admins can only delete users in their account
    if current_user.role == "admin" and getattr(current_user, "account_id", None) != getattr(user, "account_id", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete users in your own account"
        )

    # Prevent users from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    try:
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        return {"message": "User successfully deleted", "status_code": 200}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
