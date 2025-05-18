# Repository fixtures for test database operations
"""
Fixtures for repository tests.

This module provides fixtures for testing repository classes,
which typically interact with the database.
"""
import pytest
from unittest.mock import MagicMock
from typing import Dict, List, Any, Generator, Optional
import uuid
from datetime import datetime

# Import the safe_import utility
from ..utils import safe_import


@pytest.fixture
def mock_db_session():
    """
    Create a mock database session for unit tests.
    
    This fixture creates a MagicMock that simulates a SQLAlchemy session
    without requiring an actual database connection. This is useful for
    unit testing repositories in isolation.
    
    Returns:
        MagicMock: Configured to simulate a database session
    """
    session = MagicMock()
    
    # Configure common session methods
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.order_by.return_value = session
    session.offset.return_value = session
    session.limit.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    
    # For transaction management
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    
    return session


@pytest.fixture
def in_memory_db():
    """
    Create an in-memory SQLite database for integration tests.
    
    This fixture creates a real SQLAlchemy session with an in-memory SQLite database.
    It's useful for integration tests that need to test actual database operations.
    
    Returns:
        Session: A SQLAlchemy session
    """
    try:
        # Import database module
        from app.db.database import Base, engine, get_db
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, Session
        import sqlalchemy.pool as pool
        
        # Create in-memory database
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool
        )
        
        # Create all tables
        Base.metadata.create_all(bind=test_engine)
        
        # Create session
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=test_engine
        )
        db = TestingSessionLocal()
        
        yield db
        
        # Clean up
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        
    except ImportError as e:
        pytest.skip(f"Unable to create in-memory database: {e}")
        yield MagicMock()


class InMemoryRepository:
    """
    Base class for creating in-memory repositories for testing.
    
    This class can be extended to create specific repository implementations
    that store data in memory rather than in a database.
    """
    
    def __init__(self, model_class=None):
        """Initialize with empty storage and optional model class."""
        self.model_class = model_class
        self.items: Dict[str, Any] = {}
        self.next_id = 1
    
    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new item."""
        # Generate ID if not provided
        if "id" not in data:
            if isinstance(self.next_id, int):
                data["id"] = str(self.next_id)
                self.next_id += 1
            else:
                data["id"] = str(uuid.uuid4())
        
        # Set timestamps
        if "created_at" not in data:
            data["created_at"] = datetime.now()
        if "updated_at" not in data:
            data["updated_at"] = datetime.now()
        
        # Store the item
        if self.model_class:
            item = self.model_class(**data)
        else:
            # Create a dynamic object
            class Item(object):
                pass
            
            item = Item()
            for key, value in data.items():
                setattr(item, key, value)
        
        self.items[data["id"]] = item
        return item
    
    def get_by_id(self, id: str) -> Optional[Any]:
        """Get an item by ID."""
        return self.items.get(id)
    
    def get_all(self) -> List[Any]:
        """Get all items."""
        return list(self.items.values())
    
    def update(self, id: str, data: Dict[str, Any]) -> Optional[Any]:
        """Update an item."""
        if id not in self.items:
            return None
        
        # Update timestamps
        data["updated_at"] = datetime.now()
        
        # Update the item
        item = self.items[id]
        for key, value in data.items():
            setattr(item, key, value)
        
        return item
    
    def delete(self, id: str) -> bool:
        """Delete an item."""
        if id in self.items:
            del self.items[id]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all items."""
        self.items = {}
