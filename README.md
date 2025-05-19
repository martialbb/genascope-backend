# Genascope Backend

This is the backend repository for the Genascope application, built with FastAPI and Python.

## 🔄 Related Repositories

This project is part of a multi-repository architecture:
- Backend (this repo): API server for the Genascope application
- Frontend: [cancer-genix-frontend](https://github.com/martialbb/cancer-genix-frontend) - Astro/React UI

## 🚀 Project Setup

```sh
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                 | Action                                           |
| :---------------------- | :----------------------------------------------- |
| `uvicorn app.main:app --reload` | Start development server at `localhost:8000` |
| `./run_tests.sh`        | Run comprehensive test suite                      |
| `pytest`                | Run tests                                        |
| `alembic upgrade head`  | Run database migrations                          |
| `alembic revision --autogenerate -m "message"` | Generate database migration |

## 📚 API Documentation

Once the server is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## 🏗️ Architecture

The application follows a layered architecture pattern:

1. **Models** (`/app/models/`): SQLAlchemy database models
2. **Repositories** (`/app/repositories/`): Data access layer for database operations
3. **Services** (`/app/services/`): Business logic layer
4. **APIs** (`/app/api/`): REST API endpoints using FastAPI
5. **Schemas** (`/app/schemas/`): Pydantic models for request/response validation

## ✨ Features

The backend implements the following key features:

- **Authentication**: JWT token-based authentication system
- **User Management**: Complete CRUD operations for different user roles
- **Chat System**: Interactive chat with branching logic and persistence
- **Patient Eligibility Analysis**: Risk assessment based on chat answers
- **Patient Invites**: System for clinicians to invite patients
- **Lab Integration**: Orders and results management with external labs
- **Appointments**: Scheduling system for patient appointments

## 🔌 Frontend Connection

This backend is designed to work with the [cancer-genix-frontend](https://github.com/martialbb/cancer-genix-frontend) repository.

Make sure to configure CORS in `app/main.py` to allow requests from your frontend application.

## 🧪 Testing

Run the comprehensive test suite:

```sh
./run_tests.sh
```

This will run:
- Unit tests for individual components
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Code quality checks with flake8
- Type checking with mypy (if available)
- Coverage report generation

### Test Structure

The tests are organized as follows:

```
app/tests/
├── unit/               # Unit tests for individual components
│   ├── api/            # API route handler tests
│   └── services/       # Service layer tests
│       ├── test_chat_service.py
│       ├── test_invite_service.py
│       └── test_labs_service.py
├── integration/        # Integration tests for API endpoints
│   └── api/
│       ├── test_appointments.py
│       ├── test_chat.py
│       ├── test_invites.py
│       └── test_labs.py
└── e2e/                # End-to-end tests for complete workflows
    └── test_patient_eligibility_flow.py
```

### Writing Tests

Each test type follows a specific pattern:

1. **Unit Tests**: Focus on testing individual components in isolation with mocked dependencies
2. **Integration Tests**: Test API endpoints with the actual FastAPI application
3. **E2E Tests**: Test complete user journeys across multiple endpoints
