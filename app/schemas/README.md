# Schema Models / DTOs

This directory contains Pydantic schema models that serve as Data Transfer Objects (DTOs) for the Genascope application.

## Purpose

Schema models serve several important purposes:
1. **Data Validation**: Pydantic automatically validates incoming request data
2. **Type Safety**: Provides strong typing for data structures
3. **API Documentation**: Schemas are used by FastAPI to generate OpenAPI documentation
4. **Separation of Concerns**: Separates data transfer logic from database models

## Schema Organization

The schemas are organized by domain area:

- `users.py`: User account related schemas (patients, clinicians, authentication)
- `appointments.py`: Appointment and availability related schemas
- `labs.py`: Laboratory test orders and results schemas
- `chat.py`: Risk assessment chat functionality schemas
- `common.py`: Common utility schemas used across the application

## Schema Types

For each domain entity, we typically have several schema types:

1. **Base**: Contains common fields used across requests and responses
2. **Create**: Used for create/POST operations (extends Base)
3. **Update**: Used for update/PUT operations (similar fields to Base but made optional)
4. **Response**: Used for API responses (extends Base with additional fields like IDs)

## Best Practices

When working with schemas:

1. **Validation**: Use Pydantic validators for complex field validations
2. **Documentation**: Add docstrings and field descriptions for clear API docs
3. **Inheritance**: Use schema inheritance to reduce code duplication
4. **Enums**: Use Python Enums for fields with a fixed set of choices
5. **Config**: Use the Config class with `orm_mode = True` for easy ORM object conversion

## Example Usage

```python
# API Endpoint example
@router.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user)

# Service layer example
def create_appointment(self, appointment_data: schemas.AppointmentCreate) -> schemas.AppointmentResponse:
    # Convert DTO to database model
    appointment = Appointment(
        id=str(uuid.uuid4()),
        clinician_id=appointment_data.clinician_id,
        patient_id=appointment_data.patient_id,
        date=datetime.fromisoformat(appointment_data.date),
        time=datetime.strptime(appointment_data.time, "%H:%M").time(),
        appointment_type=appointment_data.appointment_type,
        notes=appointment_data.notes
    )
    
    # Save to database
    self.repository.create_appointment(appointment)
    
    # Return response DTO
    return schemas.AppointmentResponse.from_orm(appointment)
```
