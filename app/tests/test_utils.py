"""
Utility module for creating test databases and mocks.
"""
from unittest.mock import MagicMock
from datetime import datetime

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
        self.id = kwargs.get('id', 'mock-appointment-id')
        self.clinician_id = kwargs.get('clinician_id', 'mock-clinician-id')
        self.clinician_name = kwargs.get('clinician_name', 'Dr. Test Clinician')
        self.patient_id = kwargs.get('patient_id', 'mock-patient-id')
        self.patient_name = kwargs.get('patient_name', 'Test Patient')
        self.date = kwargs.get('date', datetime.now().date())
        self.time = kwargs.get('time', datetime.now().time())
        self.appointment_type = kwargs.get('appointment_type', 'virtual')
        self.status = kwargs.get('status', 'scheduled')
        self.notes = kwargs.get('notes', 'Mock appointment notes')
        self.confirmation_code = kwargs.get('confirmation_code', 'TEST123')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        
        # Add any additional attributes 
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
            
class MockAvailability:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
