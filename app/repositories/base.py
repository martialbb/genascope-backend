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
        
    def _safe_set_attributes(self, entity: Any, data: Dict[str, Any]) -> None:
        """
        Safely set attributes on an entity from a dictionary.
        
        Args:
            entity: The entity to update (e.g., User, Account, PatientProfile)
            data: Dictionary containing the attributes to update
            
        Returns:
            None
        """
        # Print entity's initial state for key fields
        print(f"Debug: Initial entity state - ID: {getattr(entity, 'id', 'unknown')}")
        if hasattr(entity, 'name'):
            print(f"Debug: Initial name: {entity.name}")
        if hasattr(entity, 'role'):
            print(f"Debug: Initial role: {entity.role} (type: {type(entity.role)})")
        
        # Get all entity columns and their types for validation
        column_types = {}
        try:
            from sqlalchemy import inspect
            if hasattr(inspect(entity), 'mapper'):
                mapper = inspect(entity).mapper
                if hasattr(mapper, 'columns'):
                    for column_name, column in mapper.columns.items():
                        if hasattr(column, 'type'):
                            column_types[column_name] = column.type
                            print(f"Debug: Column {column_name} has type {column.type}")
        except Exception as e:
            print(f"Debug: Error inspecting entity columns: {e}")
        
        for key, value in data.items():
            if hasattr(entity, key):
                # Skip None values to prevent overwriting with None
                if value is None:
                    print(f"Debug: Skipping None value for attribute '{key}'")
                    continue
                    
                # Store original value for logging
                original_value = getattr(entity, key)
                
                # Special handling for enum attributes (like role)
                if key in column_types and hasattr(column_types[key], 'enum_class'):
                    enum_class = column_types[key].enum_class
                    print(f"Debug: Handling enum attribute '{key}' with enum class {enum_class}")
                    
                    try:
                        if isinstance(value, str) and not isinstance(value, enum_class):
                            # Convert string to enum value
                            enum_value = enum_class(value)
                            print(f"Debug: Converted string '{value}' to enum value {enum_value}")
                            setattr(entity, key, enum_value)
                        elif isinstance(value, enum_class):
                            # Already the right type
                            print(f"Debug: Value '{value}' is already correct enum type")
                            setattr(entity, key, value)
                        else:
                            # Try to convert other types
                            print(f"Debug: Attempting to convert {type(value)} to enum")
                            enum_value = enum_class(str(value))
                            setattr(entity, key, enum_value)
                    except Exception as e:
                        print(f"Debug: Error handling enum conversion for '{key}': {e}")
                        print(f"Debug: Falling back to direct assignment for '{key}'")
                        # Fall back to direct assignment
                        setattr(entity, key, value)
                else:
                    # Default attribute setting for non-enum types
                    setattr(entity, key, value)
                    
                print(f"Debug: Changed attribute '{key}' from '{original_value}' to '{getattr(entity, key)}' on {entity.__class__.__name__}")
            else:
                # Log or handle unknown attributes appropriately
                # This prevents silent failures when attribute names are mismatched
                print(f"Warning: Attribute '{key}' does not exist on {entity.__class__.__name__}")
        
        # Print final state for validation
        if hasattr(entity, 'name'):
            print(f"Debug: Final name: {entity.name}")
        if hasattr(entity, 'role'):
            print(f"Debug: Final role: {entity.role} (type: {type(entity.role)})")
        
        # Print entity's final state for key fields to confirm the update
        if hasattr(entity, 'name'):
            print(f"Debug: Final name: {entity.name}")
        if hasattr(entity, 'role'):
            print(f"Debug: Final role: {entity.role} (type: {type(entity.role)})")
