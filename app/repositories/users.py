from typing import List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import User, Account, PatientProfile, UserRole
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository):
    """
    Repository for User entity operations
    """
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, id: str) -> Optional[User]:
        """Get a user by ID"""
        return self.db.query(User).filter(User.id == id).first()
    
    def get_users_by_account(self, account_id: str) -> List[User]:
        """Get all users for a specific account"""
        return self.db.query(User).filter(User.account_id == account_id).all()
    
    def get_users_by_role(self, roles: List[UserRole]) -> List[User]:
        """Get all users with specific roles"""
        if not roles:
            return []
        return self.db.query(User).filter(User.role.in_(roles)).all()
    
    def get_users_by_role_and_account(self, roles: List[UserRole], account_id: str) -> List[User]:
        """Get all users with specific roles in a specific account"""
        if not roles:
            return []
        return self.db.query(User).filter(
            User.role.in_(roles),
            User.account_id == account_id
        ).all()
    
    def get_patients_by_clinician(self, clinician_id: str) -> List[User]:
        """Get all patients assigned to a specific clinician"""
        return self.db.query(User).filter(
            and_(User.clinician_id == clinician_id, User.role == UserRole.PATIENT)
        ).all()
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update an existing user"""
        user = self.get_by_id(user_id)
        if not user:
            print(f"DEBUG Repo: User with id {user_id} not found")
            return None
            
        # Debug info before update
        print(f"DEBUG Repo: Before update, user {user_id} has role: {user.role}, name: {user.name}")
        print(f"DEBUG Repo: Update data received: {user_data}")
        
        # Create a copy of the data to avoid modifying the original
        update_data = dict(user_data)
        
        # Ensure role is properly handled
        if "role" in update_data and update_data["role"] is not None:
            from app.models.user import UserRole
            try:
                if isinstance(update_data["role"], str):
                    update_data["role"] = UserRole(update_data["role"])
                    print(f"DEBUG Repo: Converted role string to enum value {update_data['role']}")
            except ValueError as e:
                print(f"DEBUG Repo: Error converting role: {e}")
            
        # Use our safe attribute setter with the potentially modified data
        self._safe_set_attributes(user, update_data)
        
        # Debug info after update
        print(f"DEBUG Repo: After update, user {user_id} has role: {user.role}, name: {user.name}")

        try:
            self.db.commit()
            self.db.refresh(user)
            print(f"DEBUG Repo: Successfully committed changes to user {user_id}")
            return user
        except Exception as e:
            self.db.rollback()
            print(f"ERROR Repo: Failed to update user {user_id}: {str(e)}")
            raise

    def delete_user(self, user_id: str) -> bool:
        """Delete a user and related data"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        try:
            # Delete related patient profile if exists
            patient_profile = self.db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
            if patient_profile:
                self.db.delete(patient_profile)
            
            # Delete the user
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise

    def get_users(
        self,
        role: Optional[str] = None,
        account_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get a list of users with optional filters and pagination."""
        query = self.db.query(User)

        if role:
            query = query.filter(User.role == role)

        if account_id:
            query = query.filter(User.account_id == account_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        return query.offset(skip).limit(limit).all()

    # _safe_set_attributes moved to BaseRepository

class AccountRepository(BaseRepository):
    """
    Repository for Account entity operations
    """
    def __init__(self, db: Session):
        super().__init__(db, Account)
    
    def get_by_domain(self, domain: str) -> Optional[Account]:
        """Get an account by domain"""
        return self.db.query(Account).filter(Account.domain == domain).first()
    
    def get_by_id(self, id: str) -> Optional[Account]:
        """Get an account by ID"""
        return self.db.query(Account).filter(Account.id == id).first()
    
    def create_account(self, account_data: Dict[str, Any]) -> Account:
        """Create a new account"""
        account = Account(**account_data)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def update_account(self, account_id: str, account_data: Dict[str, Any]) -> Optional[Account]:
        """Update an existing account"""
        account = self.get_by_id(account_id)
        if not account:
            return None
            
        # Use our safe attribute setter
        self._safe_set_attributes(account, account_data)
            
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an account"""
        account = self.get_by_id(account_id)
        if not account:
            return False
            
        self.db.delete(account)
        self.db.commit()
        return True

class PatientProfileRepository(BaseRepository):
    """
    Repository for PatientProfile entity operations
    """
    def __init__(self, db: Session):
        super().__init__(db, PatientProfile)
    
    def get_by_user_id(self, user_id: str) -> Optional[PatientProfile]:
        """Get a patient profile by user ID"""
        return self.db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    
    def create_profile(self, profile_data: Dict[str, Any]) -> PatientProfile:
        """Create a new patient profile"""
        profile = PatientProfile(**profile_data)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def update_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> Optional[PatientProfile]:
        """Update an existing patient profile"""
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
            
        # Use our safe attribute setter
        self._safe_set_attributes(profile, profile_data)
            
        self.db.commit()
        self.db.refresh(profile)
        return profile
