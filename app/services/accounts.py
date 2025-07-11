from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
from datetime import datetime

from app.models.accounts import Account
from app.models.user import User  # Make sure this is 'user' not 'users'
from app.schemas.accounts import AccountCreate, AccountUpdate
from app.services.users import UserService
from app.repositories.account_repository import AccountRepository
# Remove the security import as we'll handle it differently
# from app.core.security import get_password_hash
import hashlib  # Use hashlib as a temporary password hash solution

class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.account_repository = AccountRepository(db)

    def get_accounts(self, skip: int = 0, limit: int = 100, name: Optional[str] = None) -> List[Account]:
        """Get list of accounts with pagination and optional name filtering"""
        return self.account_repository.get_accounts(skip=skip, limit=limit, name=name)

    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        return self.account_repository.get_by_id(account_id)

    def create_account(self, account_data: AccountCreate) -> Account:
        """Create a new account and its admin user"""
        # Validate passwords match
        if not account_data.validate_passwords_match():
            raise ValueError("Passwords do not match")

        # Create the account using repository
        account_dict = {
            "name": account_data.name,
            "domain": account_data.domain,
            "status": "active"
        }
        db_account = self.account_repository.create_account(account_dict)

        # Create the admin user for this account
        try:
            admin_user = self.user_service.create_user({
                "email": account_data.admin_email,
                "name": account_data.admin_name,
                "password": account_data.admin_password,
                "role": "admin",
                "account_id": db_account.id,
                "is_active": True
            })
        except Exception as e:
            # If admin user creation fails, rollback the account creation
            self.account_repository.delete(db_account.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create admin user: {str(e)}"
            )

        return db_account

    def update_account(self, account_id: str, account_data: AccountUpdate) -> Optional[Account]:
        """Update an existing account"""
        db_account = self.get_account(account_id)
        if not db_account:
            return None

        # Update the account using repository
        update_data = account_data.model_dump(exclude_unset=True)
        return self.account_repository.update_account(account_id, update_data)

    def delete_account(self, account_id: str) -> bool:
        """Delete an account and its associated users"""
        db_account = self.get_account(account_id)
        if not db_account:
            return False

        # Delete the account using repository (cascading delete will handle associated users)
        return self.account_repository.delete(account_id)

