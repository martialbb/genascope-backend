# Service Layer Architecture

This folder contains the service layer for the Genascope backend application. The service layer sits between the API controllers and the data access layer (repositories).

## Architecture Overview

The architecture follows a layered approach:

```
┌──────────────────┐
│  API Controllers │  Handles HTTP requests/responses
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     Services     │  Implements business logic
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Repositories   │  Manages data access
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Database      │  Persistent storage
└──────────────────┘
```

## Service Layer Responsibilities

The service layer is responsible for:

1. **Business Logic**: Implementing the application's business rules
2. **Transaction Management**: Coordinating database transactions
3. **Input Validation**: Validating domain-specific rules
4. **Orchestration**: Coordinating between different repositories and external services

## Services

- **AppointmentService**: Handles appointment scheduling, availability management
- **UserService**: Manages user data and operations
- **LabService**: Interfaces with external lab systems for test ordering and results

## Base Classes

- **BaseService**: Generic service with common functionality like error handling
- **BaseRepository**: Generic repository with common CRUD operations

## Usage Example

```python
# In an API endpoint
@router.get("/availability")
async def get_availability(
    clinician_id: str, 
    date_str: str,
    db: Session = Depends(get_db)
):
    # Create service
    appointment_service = AppointmentService(db)
    
    # Call service method
    clinician_name, time_slots = appointment_service.get_availability(
        clinician_id, 
        datetime.strptime(date_str, "%Y-%m-%d").date()
    )
    
    # Return response
    return AvailabilityResponse(
        date=date_str,
        clinician_id=clinician_id,
        clinician_name=clinician_name,
        time_slots=time_slots
    )
```
