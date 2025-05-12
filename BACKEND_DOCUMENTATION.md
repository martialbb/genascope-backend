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
│   │   ├── invites.py       # Patient invite endpoints
│   │   └── labs.py          # Lab integration endpoints
│   ├── schemas/             # Pydantic models
│   │   ├── __init__.py
│   │   └── chat.py          # Chat-related schemas
│   ├── models/              # Database models
│   ├── db/                  # Database connection
│   └── utils/               # Utility functions
├── .env                     # Environment variables
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
└── README.md                # Basic documentation
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
