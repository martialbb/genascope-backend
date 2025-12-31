from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from app.api.auth import require_full_access, User
from app.schemas import (
    AccountCreate, AccountResponse, AccountUpdate, AccountMetricsResponse,
    BillingInfo, BillingUpdate, Invoice
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Mock admin verification - in a real app, this would check admin privileges
async def verify_super_admin(current_user: User = Depends(require_full_access)):
    # This is a simplified check - in a real app, you would check against user roles in the database
    if current_user.username != "admin@genascope.com":
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
    from datetime import datetime
    now = datetime.utcnow()
    return AccountResponse(
        id=f"acc_{account_data.domain.replace('.', '_')}",
        name=account_data.name,
        domain=account_data.domain,
        admin_email=account_data.admin_email,
        subscription_tier=account_data.subscription_tier,
        max_users=account_data.max_users,
        created_at=now,
        updated_at=now,
        is_active=True
    )
