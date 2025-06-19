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
- **StorageService**: Manages secure file storage to AWS S3 with IAM role-based access

### StorageService

The `StorageService` provides secure file storage capabilities:

**Features**:
- IAM role assumption for AWS access (no long-term credentials)
- TLS encryption for all S3 communications
- Automatic credential refresh for temporary tokens
- Regional STS endpoint configuration for reliability

**Usage**:
```python
# In an API endpoint
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    file_content = await file.read()
    file_key = f"uploads/{current_user.id}/{file.filename}"
    
    s3_url = await storage_service.upload_file(file_content, file_key)
    
    return {"s3_url": s3_url, "file_key": file_key}
```

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
