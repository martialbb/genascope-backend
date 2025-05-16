# CancerGenix Backend Documentation

## Overview

The CancerGenix backend is a FastAPI-based application that provides RESTful API endpoints to support the CancerGenix frontend. It handles authentication, patient data management, chat sessions, eligibility analysis, account management, and lab integrations.

## Project Structure

The project follows a typical FastAPI project structure:

```
cancer-genix-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI application entry point
│   ├── api/                 # API modules
│   │   ├── __init__.py      # Router registration
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── chat.py          # Chat endpoints
│   │   ├── eligibility.py   # Eligibility analysis endpoints
│   │   ├── admin.py         # Admin endpoints
│   │   ├── account.py       # Account management endpoints
│   │   ├── appointments.py  # Appointment scheduling endpoints
│   │   ├── invites.py       # Patient invite endpoints
│   │   └── labs.py          # Lab integration endpoints
│   ├── schemas/             # Pydantic models (DTOs)
│   │   ├── __init__.py      # Schema exports
│   │   ├── chat.py          # Chat-related schemas
│   │   ├── users.py         # User-related schemas
│   │   ├── appointments.py  # Appointment-related schemas
│   │   ├── labs.py          # Lab test-related schemas
│   │   ├── common.py        # Common utility schemas
│   │   └── README.md        # Schema documentation
│   ├── models/              # Database models
│   │   ├── __init__.py
│   │   └── appointment.py   # Appointment-related models
│   ├── db/                  # Database connection
│   │   └── database.py      # Database connection and session management
│   ├── tests/               # Test modules
│   │   ├── __init__.py
│   │   ├── api/             # API tests
│   │   │   ├── __init__.py
│   │   │   ├── test_appointments.py           # Unit tests for appointments
│   │   │   ├── test_appointments_integration.py # Integration tests
│   │   │   └── test_appointments_e2e.py       # End-to-end tests
│   │   ├── mock_models.py   # Mock models for testing
│   │   └── test_utils.py    # Test utilities
│   └── utils/               # Utility functions
├── .env                     # Environment variables
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── pytest.ini               # Test configuration
├── Dockerfile               # Docker configuration
└── README.md                # Basic documentation
```

## Architecture

The CancerGenix backend follows a layered architecture pattern to separate concerns and maintain a modular, maintainable codebase.

### Layers

1. **API Layer (Controllers)** - Located in `app/api/`
   - Handles HTTP requests and responses
   - Validates input data using Pydantic models
   - Routes requests to appropriate services

2. **Service Layer** - Located in `app/services/`
   - Contains business logic
   - Orchestrates operations between repositories
   - Handles transactions
   - Implements domain-specific validation rules

3. **Repository Layer** - Located in `app/repositories/`
   - Abstracts data access operations
   - Provides methods for CRUD operations on database entities
   - Hides SQL/ORM complexity from services

4. **Model Layer** - Located in `app/models/`
   - Defines database models using SQLAlchemy ORM
   - Represents database structure and relationships

5. **Schema Layer (DTOs)** - Located in `app/schemas/`
   - Defines Pydantic models for request/response validation
   - Handles data serialization/deserialization
   - Provides clear contracts between API and service layers
   - Documents API input/output expectations with validation rules
   - Creates a separation between API models and database models

### Data Flow

```
Client Request → API Controller → Service → Repository → Database
                       ↑              ↑           ↑
                       ↓              ↓           ↓
Response    ←    Schemas    ←    Domain Logic ← Database Models
```

### Dependency Injection

The application uses FastAPI's dependency injection system to provide services with the resources they need:

```python
@router.get("/availability")
async def get_availability(
    clinician_id: str, 
    date_str: str = Query(..., alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    appointment_service = AppointmentService(db)
    # Use service to handle business logic
```

### Data Transfer Objects (DTOs)

The application uses Data Transfer Objects (DTOs) implemented with Pydantic models to:

1. **Validate Input Data**: Automatically validate and parse input data according to defined schemas
2. **Document API Contracts**: Provide clear input/output contracts for API endpoints
3. **Enable API Documentation**: Generate OpenAPI documentation automatically
4. **Separate API from Database Models**: Decouple external-facing data structures from internal models

#### DTO Types

For each domain entity, the application typically defines multiple DTO types:

1. **Base**: Common fields shared between request and response schemas
2. **Create**: Used for entity creation requests (POST endpoints)
3. **Update**: Used for entity updates (PUT/PATCH endpoints)
4. **Response**: Used for API responses, often with additional fields

#### Example DTO Usage

```python
# API endpoint definition using DTOs
@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    appointment_service = AppointmentService(db)
    return appointment_service.create_appointment(appointment)

# Service using DTOs
def create_appointment(self, appointment_data: AppointmentCreate) -> AppointmentResponse:
    # Convert DTO to database model
    appointment = Appointment(
        id=str(uuid.uuid4()),
        clinician_id=appointment_data.clinician_id,
        date=datetime.fromisoformat(appointment_data.date),
        # Convert and validate other fields...
    )
    
    # Save through repository layer
    created_appointment = self.repository.create_appointment(appointment)
    
    # Convert database model back to response DTO
    return AppointmentResponse.from_orm(created_appointment)
```

## API Endpoints

### Authentication

#### POST `/api/auth/token`

Authenticates a user and returns an access token.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJ...",
  "token_type": "bearer"
}
```

### Chat Management

#### POST `/api/start_chat`

Starts a new chat session or resumes an existing one.

**Request Body:**
```json
{
  "sessionId": "session-uuid"
}
```

**Response:**
```json
{
  "question": {
    "id": 1,
    "text": "Do you have a family history of breast cancer?"
  },
  "nextQuestion": null
}
```

#### POST `/api/submit_answer`

Submits an answer to a question and gets the next question.

**Request Body:**
```json
{
  "sessionId": "session-uuid",
  "questionId": 1,
  "answer": "Yes"
}
```

**Response:**
```json
{
  "question": {
    "id": 1,
    "text": "Do you have a family history of breast cancer?"
  },
  "nextQuestion": {
    "id": 2,
    "text": "At what age was your relative diagnosed?"
  }
}
```

### Eligibility Analysis

#### POST `/api/eligibility/analyze`

Analyzes chat responses to determine eligibility for genetic testing.

**Request Body:**
```json
{
  "sessionId": "session-uuid"
}
```

**Response:**
```json
{
  "is_eligible": true,
  "nccn_eligible": true,
  "tyrer_cuzick_score": 23.5,
  "tyrer_cuzick_threshold": 20.0
}
```

### Account Management

#### POST `/api/admin/create_account`

Creates a new organizational account (requires super_admin role).

**Request Body:**
```json
{
  "name": "Hospital Name",
  "domain": "hospital.org",
  "admin_email": "admin@hospital.org",
  "admin_name": "Admin Name",
  "admin_password": "securepassword"
}
```

**Response:**
```json
{
  "id": "acc001",
  "name": "Hospital Name",
  "domain": "hospital.org",
  "created_at": "2025-05-12T12:00:00Z"
}
```

#### POST `/api/account/create_user`

Creates a new user within an account (requires admin role).

**Request Body:**
```json
{
  "email": "user@hospital.org",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "physician",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "id": "usr001",
  "email": "user@hospital.org",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "physician",
  "created_at": "2025-05-12T12:00:00Z"
}
```

### Patient Management

#### POST `/api/generate_invite`

Generates a unique invite URL for a patient.

**Request Body:**
```json
{
  "email": "patient@example.com",
  "first_name": "John",
  "last_name": "Smith",
  "phone": "+1234567890",
  "provider_id": "usr001"
}
```

**Response:**
```json
{
  "invite_id": "inv-uuid",
  "invite_url": "http://localhost:4321/invite/inv-uuid"
}
```

#### GET `/api/patients`

Gets a list of patients (requires clinician, physician, or admin role).

**Response:**
```json
[
  {
    "id": "pat001",
    "name": "John Smith",
    "status": "Chat Completed",
    "lastActivity": "2025-05-11"
  }
]
```

### Lab Integration

#### POST `/api/labs/order_test`

Orders a genetic test for a patient.

**Request Body:**
```json
{
  "patient_id": "pat001",
  "test_type": "BRCA",
  "provider_id": "usr001",
  "shipping_address": {
    "line1": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "12345"
  }
}
```

**Response:**
```json
{
  "order_id": "ord001",
  "status": "ordered",
  "created_at": "2025-05-12T12:00:00Z"
}
```

#### GET `/api/labs/results/{order_id}`

Gets the results for a lab test.

**Response:**
```json
{
  "order_id": "ord001",
  "status": "completed",
  "results": {
    "brca1": "negative",
    "brca2": "variant of uncertain significance",
    "report_url": "https://example.com/reports/ord001"
  }
}
```

### Appointment Management

#### GET `/api/availability`

Gets available time slots for a clinician on a specific date.

**Query Parameters:**
- `clinician_id`: ID of the clinician
- `date`: Specific date in YYYY-MM-DD format

**Response:**
```json
{
  "date": "2025-05-15",
  "clinician_id": "clinician-123",
  "clinician_name": "Dr. Jane Smith",
  "time_slots": [
    {
      "time": "09:00",
      "available": true
    },
    {
      "time": "09:30",
      "available": false
    }
  ]
}
```

#### POST `/api/availability/set`

Sets availability for a clinician, supporting both single-day and recurring schedules.

**Query Parameters:**
- `clinician_id`: ID of the clinician

**Request Body:**
```json
{
  "date": "2025-05-15",
  "time_slots": ["09:00", "09:30", "10:00"],
  "recurring": false
}
```

**Request Body (Recurring):**
```json
{
  "date": "2025-05-15",
  "time_slots": ["09:00", "09:30", "10:00"],
  "recurring": true,
  "recurring_days": [1, 3, 5],
  "recurring_until": "2025-06-15"
}
```

**Response:**
```json
{
  "message": "Availability set successfully",
  "date": "2025-05-15",
  "time_slots": ["09:00", "09:30", "10:00"]
}
```

#### POST `/api/book_appointment`

Books an appointment for a patient with a clinician.

**Request Body:**
```json
{
  "clinician_id": "clinician-123",
  "date": "2025-05-15",
  "time": "09:00",
  "patient_id": "patient-456",
  "appointment_type": "virtual",
  "notes": "Initial consultation"
}
```

**Response:**
```json
{
  "appointment_id": "appt-789",
  "clinician_id": "clinician-123",
  "clinician_name": "Dr. Jane Smith",
  "patient_id": "patient-456",
  "patient_name": "John Doe",
  "date_time": "2025-05-15T09:00:00Z",
  "appointment_type": "virtual",
  "status": "scheduled",
  "confirmation_code": "ABC123"
}
```

#### GET `/api/appointments/clinician/{clinician_id}`

Gets all appointments for a clinician within a date range.

**Query Parameters:**
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format

**Response:**
```json
{
  "clinician_id": "clinician-123",
  "appointments": [
    {
      "appointment_id": "appt-789",
      "patient_id": "patient-456",
      "patient_name": "John Doe",
      "date_time": "2025-05-15T09:00:00Z",
      "appointment_type": "virtual",
      "status": "scheduled"
    }
  ]
}
```

#### GET `/api/appointments/patient/{patient_id}`

Gets all appointments for a patient.

**Response:**
```json
{
  "patient_id": "patient-456",
  "appointments": [
    {
      "appointment_id": "appt-789",
      "clinician_id": "clinician-123",
      "clinician_name": "Dr. Jane Smith",
      "date_time": "2025-05-15T09:00:00Z",
      "appointment_type": "virtual",
      "status": "scheduled"
    }
  ]
}
```

#### PUT `/api/appointments/{appointment_id}`

Updates the status of an appointment.

**Query Parameters:**
- `status`: New status (scheduled, completed, canceled, rescheduled)

**Response:**
```json
{
  "appointment_id": "appt-789",
  "status": "canceled",
  "updated_at": "2025-05-12T15:30:45Z"
}
```

## Authentication and Authorization

The backend uses JWT-based authentication. The `get_current_active_user` dependency is used to protect endpoints that require authentication.

```python
@router.post("/protected_endpoint")
async def protected_endpoint(current_user: User = Depends(get_current_active_user)):
    # This endpoint is only accessible to authenticated users
    return {"message": "You are authenticated"}
```

Role-based authorization is implemented, with the following roles:

- **super_admin**: Can manage organizational accounts
- **admin**: Can manage users within their organization
- **clinician/physician**: Can access patient data, send invites, order tests
- **user**: Regular user with limited access

## Data Models

### User

The User model represents an authenticated user in the system.

### Patient

The Patient model contains patient information and their assessment status.

### Invite

The Invite model stores information about invitations sent to patients.

### LabOrder

The LabOrder model represents genetic test orders.

### Appointment

The Appointment model contains information about scheduled appointments between patients and clinicians.

### Availability

The Availability model stores clinician availability information for specific dates and times.

### RecurringAvailability

The RecurringAvailability model tracks recurring availability patterns for clinicians.

## Database Models

The backend uses SQLAlchemy ORM to interact with the database. Below are the main database models:

### User

The User model represents clinicians, patients, and administrators in the system.

### Appointment

The Appointment model contains information about scheduled appointments between patients and clinicians:

```python
class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(String(36), primary_key=True)  # UUID
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    clinician_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    appointment_type = Column(Enum("virtual", "in-person", name="appointment_type"), nullable=False)
    status = Column(Enum("scheduled", "completed", "canceled", "rescheduled", 
                        name="appointment_status"), nullable=False)
    notes = Column(Text, nullable=True)
    confirmation_code = Column(String(10), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, 
                       server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
```

### Availability

The Availability model stores clinician availability information for specific dates and times:

```python
class Availability(Base):
    __tablename__ = "clinician_availability"
    
    id = Column(String(36), primary_key=True)  # UUID
    clinician_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, 
                       server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
```

### RecurringAvailability

The RecurringAvailability model tracks recurring availability patterns for clinicians:

```python
class RecurringAvailability(Base):
    __tablename__ = "clinician_recurring_availability"
    
    id = Column(String(36), primary_key=True)  # UUID
    clinician_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_of_week = Column(String(50), nullable=False)  # JSON string of day numbers (0=Mon, 6=Sun)
    time_slots = Column(String(255), nullable=False)  # JSON string of time slots
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, nullable=False, 
                       server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
```

## Environment Setup

### Environment Variables

Create a `.env` file based on the `.env.example` template:

```
DATABASE_URL=mysql+pymysql://user:password@db:3306/cancergenix
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### Running Locally

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `uvicorn app.main:app --reload`

### Docker Setup

For Docker-based development:

1. Build the image: `docker build -t cancer-genix-backend .`
2. Start containers: `docker-compose up`

## Development Guidelines

1. Use Pydantic models for request/response validation
2. Follow REST principles when designing endpoints
3. Implement proper error handling with appropriate HTTP status codes
4. Document all endpoints with docstrings
5. Write unit tests for all endpoints

## Integration with Frontend

The backend is designed to work seamlessly with the CancerGenix frontend. The API endpoints match the frontend's expected request and response formats.

## Testing Framework

The CancerGenix backend uses pytest for testing. Tests are organized into three categories:

### Test Categories

1. **Unit Tests** - Tests individual functions and API endpoints in isolation with mocked dependencies
2. **Integration Tests** - Tests API endpoints with database integration using mock database sessions
3. **End-to-End Tests** - Tests complete workflows across multiple API endpoints with authentication

### Running Tests

Run all tests:
```bash
python -m pytest
```

Run tests by category using markers:
```bash
# Unit tests only
python -m pytest -m "not integration and not e2e"

# Integration tests
python -m pytest -m integration

# End-to-End tests
python -m pytest -m e2e
```

Run specific test file:
```bash
python -m pytest app/tests/api/test_appointments.py
```

Run a specific test function:
```bash
python -m pytest app/tests/api/test_appointments.py::TestAppointmentsAPI::test_book_appointment
```

### Test Configuration

The `pytest.ini` file contains custom test markers and configuration:

```ini
[pytest]
markers =
    unit: marks a test as a unit test (default if no marker)
    integration: marks a test as an integration test
    e2e: marks a test as an end-to-end test
testpaths = app/tests
```

### Mock Database Implementation

For testing, the application uses a mock database implementation that simulates database operations:

```python
class MockDBSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self._query_results = {}
        self._added_objects = []
    
    def commit(self):
        self.committed = True
    
    def rollback(self):
        self.rolled_back = True
    
    def close(self):
        self.closed = True
    
    def add(self, obj):
        self._added_objects.append(obj)
    
    def query(self, model_cls):
        return MockQuery(self, model_cls)
    
    def set_query_result(self, model_cls, results):
        self._query_results[model_cls.__name__] = results
```

### Test Example: Appointment Booking Integration Test

```python
@pytest.mark.integration
class TestAppointmentsAPIIntegration:
    @patch('app.api.appointments.get_db')
    def test_book_appointment_integration(self, mock_get_db, mock_db):
        # Configure the mock to yield our mock_db when called
        mock_get_db.return_value.__iter__.return_value = iter([mock_db])
        
        # Set up test data
        today = date.today().isoformat()
        appointment_data = {
            "clinician_id": "clinician-123",
            "date": today,
            "time": "10:00",
            "patient_id": "patient-123",
            "appointment_type": "virtual",
            "notes": "Test appointment"
        }
        
        # Make request
        response = client.post("/api/book_appointment", json=appointment_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "appointment_id" in data
        assert data["status"] == "scheduled"
        
        # Verify database operations were committed
        assert mock_db.committed
```

### End-to-End Test Example

```python
@pytest.mark.e2e
class TestAppointmentsE2E:
    def test_appointment_scheduling_workflow(self):
        # 1. Get authorization token for clinician
        clinician_token = get_auth_token(role="clinician")
        clinician_headers = auth_headers(clinician_token)
        
        # 2. Clinician sets availability
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        availability_data = {
            "date": tomorrow,
            "time_slots": ["09:00", "09:30", "10:00", "10:30"],
            "recurring": False
        }
        
        set_avail_response = client.post(
            "/api/availability/set?clinician_id=clinician_123",
            headers=clinician_headers,
            json=availability_data
        )
        
        assert set_avail_response.status_code == 200
        
        # 3-9. Continue with booking, viewing and canceling appointments
        # (Full workflow test)
```

### Test Coverage Summary

The current test suite provides comprehensive coverage of the appointments API with:
- Unit tests: 10 passing tests
- Integration tests: 5 passing tests
- End-to-End tests: 3 passing tests

Each test type ensures the API functions correctly at different levels of abstraction, from individual endpoint behavior to complete user workflows.
