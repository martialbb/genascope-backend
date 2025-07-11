"""
Account repository handling database operations for Account entities.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories.base import BaseRepository
from app.models.accounts import Account
from app.schemas.accounts import AccountCreate, AccountUpdate

class AccountRepository(BaseRepository[Account, AccountCreate, AccountUpdate]):
    """Repository for Account entity database operations"""

    def __init__(self, db: Session):
        super().__init__(db, Account)

    def get_accounts(self, skip: int = 0, limit: int = 100, name: Optional[str] = None) -> List[Account]:
        """Get list of accounts with optional filtering by name"""
        filters = {}
        if name:
            filters["name"] = {"like": name}
        return self.get_all(skip=skip, limit=limit, **filters)

    def create_account(self, account_data: Dict[str, Any]) -> Account:
        """Create a new account with timestamp"""
        if "created_at" not in account_data:
            account_data["created_at"] = datetime.utcnow()
        if "updated_at" not in account_data:
            account_data["updated_at"] = datetime.utcnow()
        return self.create(account_data)

    def update_account(self, account_id: str, account_data: Dict[str, Any]) -> Optional[Account]:
        """Update account with timestamp"""
        account_data["updated_at"] = datetime.utcnow()
        return self.update(account_id, account_data)
