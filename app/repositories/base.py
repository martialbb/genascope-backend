from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

# Define a generic type for the ORM model
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)

class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations
    """
    def __init__(self, db: Session, model_class: Type[ModelType]):
        self.db = db
        self.model_class = model_class
    
    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a record by id
        """
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self) -> List[ModelType]:
        """
        Get all records
        """
        return self.db.query(self.model_class).all()
    
    def create(self, obj_in: ModelType) -> ModelType:
        """
        Create a new record
        """
        self.db.add(obj_in)
        self.db.commit()
        self.db.refresh(obj_in)
        return obj_in
    
    def update(self, obj: ModelType) -> ModelType:
        """
        Update a record
        """
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, id: Any) -> Optional[ModelType]:
        """
        Delete a record by id
        """
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
