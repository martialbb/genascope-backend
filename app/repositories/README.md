# Repository Layer Architecture

This folder contains the repository layer for the Genascope backend application. The repository layer is responsible for data access and abstraction of the database operations.

## Repository Layer Responsibilities

The repository layer is responsible for:

1. **Data Access**: Providing methods to read and write data to the database
2. **Query Abstraction**: Hiding SQL/ORM query complexity
3. **Entity Mapping**: Converting between database models and domain objects
4. **Caching**: (When implemented) Providing data caching strategies

## Repositories

- **AppointmentRepository**: Handles appointment-related database operations
- **Base Repository**: Generic repository with common CRUD operations

## Usage Example

```python
# In a service
class AppointmentService:
    def __init__(self, db: Session):
        self.repository = AppointmentRepository(db)
    
    def get_clinician_appointments(self, clinician_id, start_date, end_date):
        # Use repository to access data
        appointments = self.repository.get_clinician_appointments(
            clinician_id, start_date, end_date
        )
        
        # Process data and return
        return format_appointments(appointments)
```

## Repository Pattern Benefits

1. **Testability**: Makes it easier to mock database access in tests
2. **Maintainability**: Changes to data access don't affect business logic
3. **Separation of Concerns**: Business logic remains separate from data access
4. **Consistency**: Common data access patterns are standardized
