# Genascope Backend Documentation

## Overview

The Genascope backend is a FastAPI-based application that provides RESTful API endpoints to support the Genascope frontend. It handles authentication, patient data management, chat sessions, eligibility analysis, account management, lab integrations, and secure file storage via AWS S3. The backend implements least-privilege security patterns using IAM roles and temporary credentials for all AWS service access.

## Recent Improvements (December 2024)

### Security & Infrastructure Enhancements
- **AWS S3 Integration**: Implemented secure file storage with IAM role-based access
- **IAM Role Assumption**: Backend uses STS to assume IAM roles for temporary AWS credentials
- **TLS Enforcement**: All S3 communications encrypted in transit with bucket policy enforcement
- **Least Privilege Access**: Granular IAM policies for S3, CloudWatch, SES, and Secrets Manager
- **Regional STS Endpoint**: Configured regional STS endpoint for improved reliability
- **Environment Standardization**: Consolidated environment variable management

### Previous Improvements (June 2025)

### User Management Enhancements
- **Account ID Resolution**: Fixed account_id mismatch issues that caused 403 Forbidden errors during user operations
- **Cascade Deletion**: Implemented proper foreign key cascade handling for user deletion operations
- **User-Patient Relationship**: Enhanced relationship management between users and patient profiles

### Invite System Fixes
- **Null Handling**: Resolved "User not found" errors for invites with null clinician_id values
- **Schema Validation**: Improved API request/response validation for edge cases
- **Error Recovery**: Enhanced error handling and fallback mechanisms

### Authentication & Authorization
- **JWT Token Validation**: Strengthened token validation and user role management
- **Session Management**: Improved session handling and token refresh mechanisms
- **Role-Based Access**: Enhanced role-based routing and permission checking

## Project Structure

The project follows a unified full-stack architecture within the genascope-frontend repository:

```
genascope-frontend/
├── backend/                 # Backend FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Main FastAPI application entry point
│   │   ├── api/                 # API modules
│   │   │   ├── __init__.py      # Router registration
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   ├── eligibility.py   # Eligibility analysis endpoints
│   │   │   ├── admin.py         # Admin endpoints
│   │   │   ├── account.py       # Account management endpoints
│   │   │   ├── appointments.py  # Appointment scheduling endpoints
│   │   │   ├── invites.py       # Patient invite endpoints (fixed June 2025)
│   │   │   ├── users.py         # User management endpoints (enhanced)
│   │   │   └── labs.py          # Lab integration endpoints
│   │   ├── schemas/             # Pydantic models (DTOs)
│   │   │   ├── __init__.py      # Schema exports
│   │   │   ├── chat.py          # Chat-related schemas
│   │   │   ├── users.py         # User-related schemas (updated validation)
│   │   │   ├── appointments.py  # Appointment-related schemas
│   │   │   ├── labs.py          # Lab test-related schemas
│   │   │   ├── common.py        # Common utility schemas
│   │   │   └── README.md        # Schema documentation
│   │   ├── models/              # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User models with cascade deletion
│   │   │   ├── patient.py       # Patient models with enhanced relationships
│   │   │   └── appointment.py   # Appointment-related models
│   │   ├── services/            # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py  # User management with improved error handling
│   │   │   ├── invite_service.py # Invite service with null handling fixes
│   │   │   └── README.md        # Service documentation
│   │   ├── repositories/        # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py # Enhanced user CRUD operations
│   │   │   └── README.md        # Repository documentation
│   │   ├── db/                  # Database connection
│   │   │   └── database.py      # Database connection and session management
│   │   ├── tests/               # Test modules
│   │   │   ├── __init__.py
│   │   │   ├── api/             # API tests
│   │   │   ├── integration/     # Integration tests
│   │   │   ├── unit/            # Unit tests
│   │   │   └── README.md        # Testing documentation
│   │   └── utils/               # Utility functions
│   ├── .env                     # Environment variables
│   ├── .env.example             # Example environment variables
│   ├── requirements.txt         # Python dependencies
│   ├── BACKEND_DOCUMENTATION.md # This documentation
│   └── README.md                # Backend-specific README
├── src/                     # Frontend Astro/React application
├── docker-compose.yml       # Production Docker setup
├── docker-compose.dev.yml   # Development Docker setup with MailDev
└── README.md                # Main project documentation
```

## Architecture

The Genascope backend follows a layered architecture pattern to separate concerns and maintain a modular, maintainable codebase.

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

## Repository Pattern for User Management

All user-related operations (creation, authentication, updates, queries) are handled through the repository layer, specifically the `UserRepository` and related repositories. The service layer (e.g., `UserService`) does not make direct database calls; instead, it delegates all data access to the repository classes. This ensures a clean separation of concerns, improves testability, and centralizes data access logic.

**Example:**
- `UserService` uses `UserRepository` for user CRUD and authentication.
- No direct SQLAlchemy queries are made in the service layer for users.

This pattern is followed for accounts and patient profiles as well, using `AccountRepository` and `PatientProfileRepository`.

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

### User Management

All user management endpoints (such as user creation, authentication, and updates) utilize the repository layer for database access. The API controllers call the service layer, which in turn uses the `UserRepository` for all user data operations. This ensures consistency and maintainability across the codebase.

#### POST `/api/account/create_user`
Creates a new user within an account (requires admin role). The user is created using the repository pattern via the service layer.

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

> **Note:** All user CRUD and authentication operations are routed through the `UserRepository` and not direct database calls.

### File Upload & Storage

#### POST `/api/upload`

Uploads a file to S3 with secure authentication and IAM role-based access.

**Authentication Required**: JWT Bearer token

**Request Format**: Multipart form data
```
Content-Type: multipart/form-data

file: [binary file data]
```

**Example with curl**:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer <jwt-token>" \
  -F "file=@document.pdf"
```

**Response**:
```json
{
  "message": "File uploaded successfully",
  "s3_url": "s3://genascope-dev-knowledge-sources/uploads/user-123/document.pdf",
  "file_key": "uploads/user-123/document.pdf"
}
```

**Security Features**:
- Uses temporary AWS credentials via IAM role assumption
- All uploads encrypted in transit (TLS) and at rest (AES-256)
- Files organized by user ID for access control
- Comprehensive error handling and logging

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: S3 upload failure or AWS access issues

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

## Storage & File Management

### AWS S3 Integration

The backend implements secure file storage using AWS S3 with the following security features:

#### IAM Role-Based Access
- **Service Role**: Backend assumes `genascope-dev-backend-role` IAM role for AWS access
- **Temporary Credentials**: Uses AWS STS to obtain short-lived credentials instead of long-term access keys
- **Regional STS**: Configured to use regional STS endpoint (`sts.us-west-2.amazonaws.com`) for reliability
- **Credential Refresh**: Automatically refreshes temporary credentials before expiration

#### Security Policies
- **Least Privilege**: IAM policies grant minimum required permissions for each AWS service
- **TLS Enforcement**: S3 bucket policy denies all non-HTTPS requests
- **Access Control**: Role-based access ensures only authenticated backend services can access S3
- **Audit Trail**: All operations logged to CloudWatch for compliance and monitoring

#### Storage Service Implementation

**Location**: `app/services/storage.py`

```python
class StorageService:
    def __init__(self):
        self.s3_client = self._create_s3_client()
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def _create_s3_client(self):
        """Create S3 client with role assumption for security"""
        if settings.BACKEND_ROLE_NAME:
            # Use IAM role assumption for production
            return self._assume_role_and_create_client()
        else:
            # Fallback to access keys for development
            return boto3.client('s3', region_name=settings.AWS_DEFAULT_REGION)
    
    async def upload_file(self, file_content: bytes, file_name: str) -> str:
        """Upload file to S3 with TLS encryption"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_content,
                ServerSideEncryption='AES256'
            )
            return f"s3://{self.bucket_name}/{file_name}"
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
```

#### File Upload Endpoint

**Location**: `app/api/upload.py`

```python
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Upload file to S3 with authentication and role-based access"""
    try:
        file_content = await file.read()
        file_key = f"uploads/{current_user.id}/{file.filename}"
        
        s3_url = await storage_service.upload_file(file_content, file_key)
        
        return {
            "message": "File uploaded successfully",
            "s3_url": s3_url,
            "file_key": file_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

#### Environment Configuration

**Required Environment Variables**:
```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-west-2
AWS_ACCESS_KEY_ID=<initial-credentials>  # For role assumption
AWS_SECRET_ACCESS_KEY=<initial-credentials>  # For role assumption

# S3 Configuration
S3_BUCKET_NAME=genascope-dev-knowledge-sources

# IAM Role Configuration
BACKEND_ROLE_NAME=genascope-dev-backend-role
```

### Environment Setup

### Environment Variables

Create a `.env.local` file based on the `.env.example` template with the following configuration:

#### Database Configuration
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/genascope_db
# Alternative for MySQL: mysql+pymysql://user:password@db:3306/genascope
```

#### Authentication Configuration
```bash
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

#### AWS Configuration (Required for S3 File Storage)
```bash
# AWS Region
AWS_DEFAULT_REGION=us-west-2

# Initial AWS Credentials (for role assumption)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# S3 Bucket Configuration
S3_BUCKET_NAME=genascope-dev-knowledge-sources

# IAM Role for Backend Service
BACKEND_ROLE_NAME=genascope-dev-backend-role
```

#### Email Configuration (Optional)
```bash
# SMTP Configuration for email services
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@genascope.local
```

### AWS Infrastructure Prerequisites

Before running the backend, ensure AWS infrastructure is provisioned:

```bash
# Navigate to infrastructure directory
cd ../iac/environments/dev

# Initialize Terraform/OpenTofu
tofu init

# Plan and apply infrastructure
tofu plan
tofu apply

# Get outputs (S3 bucket name, IAM role ARN)
tofu output
```

### Running Locally

#### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Verify AWS Integration
```bash
# Test S3 access and role assumption
python scripts/test_s3_access.py

# Test file upload functionality
python scripts/upload_test_file.py
```

### Docker Setup

For Docker-based development with full AWS integration:

```bash
# Start development environment with PostgreSQL
docker-compose -f ../docker-compose.postgresql.dev.yml up --build

# View backend logs
docker-compose -f ../docker-compose.postgresql.dev.yml logs -f backend

# Test inside container
docker exec -it genascope-frontend-backend-1 python scripts/test_s3_access.py
```

#### Testing File Upload

**Test Scripts Location**: `backend/scripts/`

```bash
# Test S3 access and role assumption
python scripts/test_s3_access.py

# Test file upload with authentication
python scripts/upload_test_file.py

# Test upload via API endpoint
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer <jwt-token>" \
  -F "file=@test-file.txt"
```

### File Storage Security Features

1. **Encryption in Transit**: All S3 communications use TLS 1.2+
2. **Encryption at Rest**: Files encrypted with AES-256 server-side encryption
3. **Access Control**: IAM policies restrict access to authorized roles only
4. **Audit Logging**: All file operations logged to CloudWatch
5. **Temporary Credentials**: No long-term AWS credentials stored in production
6. **Regional Isolation**: Resources isolated to specific AWS regions
