"""
User repository handling database operations for User entities.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import or_

from app.repositories.base import BaseRepository
from app.models.users import User
from app.schemas.users import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User entity database operations"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        account_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """
        Get list of users with filtering options

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by user role
            account_id: Filter by account ID
            search: Search term for name or email
        """
        query = self.db.query(self.model)

        # Apply filters
        if role:
            query = query.filter(self.model.role == role)

        if account_id:
            query = query.filter(self.model.account_id == account_id)

        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.email.ilike(search_term)
                )
            )

        return query.offset(skip).limit(limit).all()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.get_by_attribute("email", email)

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user with timestamps"""
        if "created_at" not in user_data:
            user_data["created_at"] = datetime.utcnow()

        # Set updated_at to the same value as created_at
        user_data["updated_at"] = user_data["created_at"]

        return self.create(user_data)

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update user with timestamp"""
        user_data["updated_at"] = datetime.utcnow()
        return self.update(user_id, user_data)
