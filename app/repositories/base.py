"""
Base repository interface providing common database operations.
"""
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import uuid4

T = TypeVar('T')  # SQLAlchemy model type
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)

class BaseRepository(Generic[T, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common database operations"""

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all records with optional filtering"""
        query = self.db.query(self.model)

        # Apply filters if provided
        for attr, value in filters.items():
            if value is not None:  # Only filter if value is not None
                # Handle special filter cases (like, startswith, etc.)
                if isinstance(value, dict):
                    if value.get("like"):
                        query = query.filter(getattr(self.model, attr).ilike(f"%{value['like']}%"))
                    elif value.get("in"):
                        query = query.filter(getattr(self.model, attr).in_(value["in"]))
                else:
                    query = query.filter(getattr(self.model, attr) == value)

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, id: str) -> Optional[T]:
        """Get a record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_by_attribute(self, attr: str, value: Any) -> Optional[T]:
        """Get a record by a specific attribute"""
        return self.db.query(self.model).filter(getattr(self.model, attr) == value).first()

    def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> T:
        """Create a new record"""
        # Convert to dict if it's a Pydantic model
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in

        # Generate UUID if not provided
        if "id" not in obj_data or not obj_data["id"]:
            obj_data["id"] = str(uuid4())

        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: str, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> Optional[T]:
        """Update a record"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None

        # Convert to dict if it's a Pydantic model
        update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in

        # Update db_obj attributes
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: str) -> bool:
        """Delete a record by ID"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True
