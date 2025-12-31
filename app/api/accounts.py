from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.api.auth import require_full_access, User
from app.schemas.accounts import AccountCreate, AccountResponse, AccountUpdate
from app.services.accounts import AccountService

# Change the router prefix to a simpler path
router = APIRouter(prefix="/api/accounts", tags=["accounts"])

# Verify super admin privileges for account management
async def verify_super_admin(current_user: User = Depends(require_full_access)):
    """Dependency to verify user has super admin privileges"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can perform this action"
        )
    return current_user

# Verify admin or super admin privileges
async def verify_admin_or_super_admin(current_user: User = Depends(require_full_access)):
    """Dependency to verify user has admin or super admin privileges"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )
    return current_user


@router.get("/", response_model=List[AccountResponse], summary="List Accounts")
async def get_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter accounts by name (case-insensitive)"),
    current_user: User = Depends(verify_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of accounts based on user permissions.

    - **Permissions**: Requires admin or super_admin role
    - **Pagination**: Use skip and limit parameters
    - **Filtering**: Filter by name (optional)

    **Access Control:**
    - Super admins can see all accounts
    - Regular admins can only see their own account

    Returns a list of accounts the current user has access to.
    """
    print(f"Debug: get_accounts called by user {current_user.id} with role {current_user.role}")

    try:
        # Use AccountService following the proper service layer pattern
        account_service = AccountService(db)
        
        # Apply role-based access control
        if current_user.role == "super_admin":
            # Super admins can see all accounts
            accounts = account_service.get_accounts(skip=skip, limit=limit, name=name)
            print(f"Debug: Super admin - retrieved all accounts")
        elif current_user.role == "admin":
            # Regular admins can only see their own account
            if not hasattr(current_user, 'account_id') or not current_user.account_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin user must be associated with an account"
                )
            
            # Get only the admin's own account
            user_account = account_service.get_account(current_user.account_id)
            if not user_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin's account not found"
                )
            
            # Apply name filtering if provided
            if name and name.lower() not in user_account.name.lower():
                accounts = []  # Filter out if name doesn't match
            else:
                accounts = [user_account]
            
            print(f"Debug: Regular admin - retrieved own account only: {user_account.name}")
        else:
            # This shouldn't happen due to the dependency, but just in case
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access accounts"
            )
        
        # Convert to response format
        result = []
        for account in accounts:
            result.append({
                "id": str(account.id),
                "name": account.name,
                "domain": getattr(account, 'domain', None),  # Include domain field
                "status": getattr(account, 'status', 'active'),  # Handle missing status field gracefully
                "created_at": account.created_at.isoformat() if hasattr(account, 'created_at') and account.created_at else None,
                "updated_at": account.updated_at.isoformat() if hasattr(account, 'updated_at') and account.updated_at else None
            })
        
        print(f"Debug: Successfully retrieved {len(result)} accounts")
        return result
        
    except Exception as e:
        print(f"Debug: Error in get_accounts: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve accounts: {str(e)}"
        )

@router.get("/{account_id}", response_model=AccountResponse, summary="Get Account")
async def get_account(
    account_id: str = Path(..., description="The ID of the account to retrieve"),
    current_user: User = Depends(verify_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific account by ID.

    - **Permissions**: Requires admin or super_admin role
    - **Path Parameter**: account_id - The unique identifier of the account

    Returns details for the specified account if the user has permission to view it.
    """
    print(f"Debug: get_account called for account_id {account_id} by user {current_user.id}")
    
    try:
        # Use AccountService following the proper service layer pattern
        account_service = AccountService(db)
        account = account_service.get_account(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Convert to response format
        result = {
            "id": str(account.id),
            "name": account.name,
            "domain": getattr(account, 'domain', None),  # Include domain field
            "status": getattr(account, 'status', 'active'),  # Handle missing status field gracefully
            "created_at": account.created_at.isoformat() if hasattr(account, 'created_at') and account.created_at else None,
            "updated_at": account.updated_at.isoformat() if hasattr(account, 'updated_at') and account.updated_at else None
        }
        
        print(f"Debug: Successfully retrieved account {account_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Debug: Error in get_account: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve account: {str(e)}"
        )

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED, summary="Create Account")
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(verify_super_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new organization account with an administrator user.

    - **Permissions**: Requires super_admin role
    - **Request Body**: Account details including admin user information

    Creates a new account and its first administrator user in one operation.
    The newly created admin will have access to manage the account and its users.

    Example:
    ```json
    {
      "name": "Medical Center Inc",
      "domain": "medcenter.org",
      "admin_email": "admin@medcenter.org",
      "admin_name": "Admin User",
      "admin_password": "SecurePassword123!",
      "admin_confirm_password": "SecurePassword123!"
    }
    ```

    Returns the created account details.
    """
    account_service = AccountService(db)
    try:
        account = account_service.create_account(account_data)
        
        # Convert to response format
        result = {
            "id": str(account.id),
            "name": account.name,
            "domain": getattr(account, 'domain', None),  # Include domain field
            "status": getattr(account, 'status', 'active'),  # Handle missing status field gracefully
            "created_at": account.created_at.isoformat() if hasattr(account, 'created_at') and account.created_at else None,
            "updated_at": account.updated_at.isoformat() if hasattr(account, 'updated_at') and account.updated_at else None
        }
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create account: {str(e)}"
        )

@router.put("/{account_id}", response_model=AccountResponse, summary="Update Account")
async def update_account(
    account_id: str = Path(..., description="The ID of the account to update"),
    account_data: AccountUpdate = ...,
    current_user: User = Depends(verify_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """
    Update an existing account's details.

    - **Permissions**: Requires admin or super_admin role
    - **Path Parameter**: account_id - The unique identifier of the account
    - **Request Body**: Account details to update

    Regular admins can only update their own account's details,
    while super admins can update any account.

    Example:
    ```json
    {
      "name": "Updated Medical Center Name",
      "domain": "updated-domain.org",
      "is_active": true
    }
    ```

    Returns the updated account information.
    """
    account_service = AccountService(db)
    try:
        updated_account = account_service.update_account(account_id, account_data)
        if not updated_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Convert to response format
        result = {
            "id": str(updated_account.id),
            "name": updated_account.name,
            "domain": getattr(updated_account, 'domain', None),  # Include domain field
            "status": getattr(updated_account, 'status', 'active'),  # Handle missing status field gracefully
            "created_at": updated_account.created_at.isoformat() if hasattr(updated_account, 'created_at') and updated_account.created_at else None,
            "updated_at": updated_account.updated_at.isoformat() if hasattr(updated_account, 'updated_at') and updated_account.updated_at else None
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update account: {str(e)}"
        )

@router.delete("/{account_id}", status_code=status.HTTP_200_OK, summary="Delete Account")
async def delete_account(
    account_id: str = Path(..., description="The ID of the account to delete"),
    current_user: User = Depends(verify_super_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an organization account and all its associated users.

    - **Permissions**: Requires super_admin role
    - **Path Parameter**: account_id - The unique identifier of the account

    This is a destructive operation that will remove the account and all users
    associated with it. This operation cannot be undone.

    Returns a success message when the account is successfully deleted.
    """
    account_service = AccountService(db)
    success = account_service.delete_account(account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return {"message": "Account successfully deleted", "status_code": 200}
