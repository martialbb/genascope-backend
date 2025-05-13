"""
Utility module for creating test databases and mocks.
"""
from unittest.mock import MagicMock

class MockDBSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self._query_results = {}
    
    def commit(self):
        self.committed = True
    
    def rollback(self):
        self.rolled_back = True
    
    def close(self):
        self.closed = True
    
    def query(self, model):
        return MockQuery(self._query_results.get(model.__name__, []))
    
    def add(self, instance):
        # For testing, store the instance somewhere
        model_name = instance.__class__.__name__
        if model_name not in self._query_results:
            self._query_results[model_name] = []
        self._query_results[model_name].append(instance)
        
    def set_query_result(self, model_name, results):
        """Set predefined results for a specific model query"""
        self._query_results[model_name] = results

class MockQuery:
    def __init__(self, results=None):
        self.results = results or []
        self.filters = []
    
    def filter(self, *args, **kwargs):
        # In a real mock, you'd implement filtering logic
        # For now, we just return the same query
        return self
        
    def filter_by(self, **kwargs):
        # In a real mock, you'd implement filtering logic
        # For now, we just return the same query
        return self
        
    def first(self):
        return self.results[0] if self.results else None
    
    def all(self):
        return self.results
        
    def offset(self, n):
        return self
        
    def limit(self, n):
        return self

def get_mock_db():
    """Mock dependency for database sessions"""
    db = MockDBSession()
    try:
        yield db
    finally:
        db.close()

# Model mocks
class MockAppointment:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
class MockAvailability:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
