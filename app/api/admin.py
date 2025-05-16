from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from app.api.auth import get_current_active_user, User
from app.schemas import (
    AccountCreate, AccountResponse, AccountUpdate, AccountMetricsResponse,
    BillingInfo, BillingUpdate, Invoice
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Mock admin verification - in a real app, this would check admin privileges
async def verify_super_admin(current_user: User = Depends(get_current_active_user)):
    # This is a simplified check - in a real app, you would check against user roles in the database
    if current_user.username != "admin@cancergenix.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can perform this action"
        )
    return current_user

@router.post("/create_account", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(verify_super_admin)
):
    """
    Create a new account (organization) with an admin user.
    Only super administrators can create accounts.
    """
    # Generate a unique account ID
    account_id = f"acc_{account_data.domain.replace('.', '_')}"
    
    # In a real implementation, this would:
    # 1. Create an account record in the database
    # 2. Create an admin user for the account
    # 3. Send email invitation to the admin
    
    # Return the created account
    return AccountResponse(
        id=account_id,
        name=account_data.name,
        domain=account_data.domain,
        admin_email=account_data.admin_email,
        subscription_tier=account_data.subscription_tier,
        max_users=account_data.max_users
    )
