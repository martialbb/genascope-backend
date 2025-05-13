from typing import Generic, TypeVar, Type
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.base import BaseRepository

# Generic type for the repository
RepoType = TypeVar("RepoType", bound=BaseRepository)

class BaseService(Generic[RepoType]):
    """
    Base service class with common functionality
    """
    def __init__(self, db: Session, repository_class: Type[RepoType], model_class=None):
        """
        Initialize the service with a database session and repository class
        """
        if model_class:
            self.repository = repository_class(db, model_class)
        else:
            self.repository = repository_class(db)
        self.db = db  # Keep for transaction management
    
    def handle_exception(self, e: Exception, status_code: int = 500, error_prefix: str = "Operation failed"):
        """
        Handle exceptions consistently across service methods
        """
        self.db.rollback()
        if isinstance(e, HTTPException):
            # Re-raise HTTP exceptions
            raise e
        else:
            # Wrap other exceptions in an HTTP exception
            raise HTTPException(
                status_code=status_code,
                detail=f"{error_prefix}: {str(e)}"
            )
