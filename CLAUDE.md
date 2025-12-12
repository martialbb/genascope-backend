# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Genascope Backend is a FastAPI-based medical application for genetic testing assessment and patient management. The application uses AI-powered chat to determine patient eligibility for genetic testing based on NCCN (National Comprehensive Cancer Network) guidelines.

**Key Technologies:**
- FastAPI for REST API
- PostgreSQL with pgvector extension for vector embeddings
- SQLAlchemy ORM with Alembic migrations
- OpenAI integration for AI chat
- RAG (Retrieval Augmented Generation) for knowledge-based assessments
- AWS S3 for file storage (IAM role-based access)
- JWT authentication

## Essential Commands

### Development Setup

```bash
# Start all services (PostgreSQL, Backend, MailDev)
docker-compose up -d

# Start backend only in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Install dependencies
pip install -r requirements.txt
```

### Database Management

```bash
# Run all migrations
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "description of changes"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Access PostgreSQL directly
psql postgresql://postgres:postgres@localhost:5432/genascope
```

### Testing

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # End-to-end tests only

# Run tests with coverage
pytest --cov=app tests/

# Run specific test file
pytest app/tests/api/test_auth.py

# Run with verbose output
pytest -v
```

### Docker Commands

```bash
# View backend logs
docker-compose logs -f backend

# Rebuild after dependency changes
docker-compose up --build

# Reset everything (removes volumes)
docker-compose down -v

# Access backend container
docker exec -it genascope_backend bash
```

## Architecture

### Layered Architecture Pattern

The codebase follows a strict layered architecture:

```
API Layer (app/api/)
    ↓ uses Pydantic schemas
Service Layer (app/services/)
    ↓ orchestrates business logic
Repository Layer (app/repositories/)
    ↓ abstracts data access
Database Models (app/models/)
    ↓ SQLAlchemy ORM
PostgreSQL Database
```

**CRITICAL:** Always follow this pattern:
- API controllers ONLY call service layer
- Service layer ONLY calls repository layer
- NO direct database queries in service/API layers
- Repository layer handles ALL database operations

### Data Transfer Objects (DTOs)

Located in `app/schemas/`, DTOs define API contracts:
- **Base**: Common fields shared between request/response
- **Create**: Used for POST endpoints (entity creation)
- **Update**: Used for PUT/PATCH endpoints (entity updates)
- **Response**: Used for API responses (includes computed fields)

### Key Services

**AI Chat Engine** (`app/services/ai_chat_engine.py`)
- RAG-based NCCN criteria assessment
- Proactive questioning based on chat strategies
- Real-time analysis of patient responses against NCCN guidelines
- Circuit breaker pattern for OpenAI API resilience

**RAG Service** (`app/services/rag_service.py`)
- Knowledge source retrieval using pgvector
- Semantic search for relevant NCCN guidelines
- Context injection for AI responses

**Storage Service** (`app/services/storage.py`)
- AWS S3 integration with IAM role assumption
- Temporary credentials via AWS STS
- TLS-enforced uploads with AES-256 encryption

### Authentication & Authorization

JWT-based authentication with role hierarchy:
- `super_admin`: Manages organizational accounts
- `admin`: Manages users within organization
- `clinician`/`physician`: Patient data access, test ordering
- `user`: Limited access

**Access Pattern:**
```python
from app.core.security import get_current_active_user

@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_active_user)):
    # User is authenticated, check roles as needed
```

## Critical Patterns & Rules

### Database Migrations

1. **Always autogenerate migrations** after model changes:
   ```bash
   alembic revision --autogenerate -m "descriptive message"
   ```

2. **Review generated migration** before applying - Alembic sometimes misses foreign keys or indexes

3. **Never edit applied migrations** - create a new migration to fix issues

4. **Handle data migrations separately** - add custom `upgrade()` logic for data transformations

### AI Service Configuration

**Environment-Specific Behavior:**
- **Development**: Mock mode allowed if `OPENAI_API_KEY` not set
- **Production**: Fail-fast on startup if OpenAI not configured
- **Never use mock mode in production** - application will refuse to start

```python
# Configuration checks in app/main.py startup_event()
if ai_chat_settings.is_production() and not ai_chat_settings.is_openai_configured:
    raise RuntimeError("OpenAI required in production")
```

### Repository Pattern

**All database operations must go through repositories:**

```python
# ✅ CORRECT
class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def get_user(self, user_id: str):
        return self.user_repo.get_by_id(user_id)

# ❌ WRONG - No direct DB queries in service layer
class UserService:
    def get_user(self, db: Session, user_id: str):
        return db.query(User).filter(User.id == user_id).first()
```

### Error Handling

Follow these patterns:
- **API Layer**: Return proper HTTP status codes (400, 401, 403, 404, 500)
- **Service Layer**: Raise `HTTPException` with detailed messages
- **Repository Layer**: Return `None` for not found, raise exceptions for DB errors

### File Storage Security

**S3 uploads must use IAM roles:**
```python
# ✅ CORRECT - Uses role assumption
storage_service = StorageService()  # Internally assumes IAM role
await storage_service.upload_file(content, filename)

# ❌ WRONG - Never use hardcoded credentials
s3_client = boto3.client('s3',
    aws_access_key_id='AKIA...',
    aws_secret_access_key='...')
```

## Testing Conventions

### Test Organization

- `app/tests/unit/` - Unit tests for isolated components
- `app/tests/integration/` - Tests requiring database/external services
- `app/tests/e2e/` - End-to-end API workflow tests

### Test Fixtures

Reusable fixtures in `app/tests/conftest.py` and `app/tests/fixtures/`:
- `db_session`: Database session for tests
- `test_user`: Pre-created test user
- `auth_headers`: JWT authentication headers

### Writing Tests

```python
import pytest
from app.tests.conftest import db_session, test_user

@pytest.mark.unit
def test_user_creation():
    # Unit test - no external dependencies
    pass

@pytest.mark.integration
def test_user_api(client, db_session):
    # Integration test - uses database
    pass

@pytest.mark.e2e
def test_full_workflow(client, auth_headers):
    # End-to-end test - complete user flow
    pass
```

## Common Pitfalls

1. **Missing account_id filtering**: Always filter by `account_id` to ensure data isolation
2. **Forgetting migrations**: Run `alembic upgrade head` after pulling changes
3. **Not handling null clinician_id**: Invite system allows null clinician_id for self-registration
4. **Skipping circuit breaker**: AI services must use circuit breaker for resilience
5. **Direct DB queries**: Always use repository layer, never query database directly from services
6. **Mock mode in production**: Application will fail to start - this is intentional

## Development Workflow

### Adding a New Feature

1. **Create database models** in `app/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "add feature"`
3. **Create repository** in `app/repositories/` for data access
4. **Implement service** in `app/services/` with business logic
5. **Define schemas** in `app/schemas/` for request/response
6. **Create API endpoints** in `app/api/`
7. **Write tests** in `app/tests/` (unit, integration, e2e)
8. **Update API router** in `app/api/__init__.py`

### Debugging

```bash
# View application logs
docker-compose logs -f backend

# Access Python REPL in container
docker exec -it genascope_backend python

# Check migration status
docker exec -it genascope_backend alembic current

# Test database connection
docker exec -it genascope_postgres psql -U postgres -d genascope -c "SELECT version();"
```

## Key Files

- `app/main.py` - FastAPI application entry point with startup validation
- `app/api/__init__.py` - API router registration
- `app/core/security.py` - Authentication and JWT handling
- `app/db/database.py` - Database connection and session management
- `app/services/ai_chat_engine.py` - RAG-based NCCN criteria assessment
- `docker-compose.yml` - Development environment setup
- `alembic.ini` - Database migration configuration

## Environment Variables

Required for development:
```bash
DATABASE_URI=postgresql://postgres:postgres@localhost:5432/genascope
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...  # Optional in dev, required in production
ENVIRONMENT=development  # or production, staging
```

AWS/S3 configuration:
```bash
AWS_DEFAULT_REGION=us-west-2
S3_BUCKET_NAME=genascope-dev-knowledge-sources
BACKEND_ROLE_NAME=genascope-dev-backend-role
```

## Related Documentation

- `README.md` - Setup and deployment guide
- `DEVELOPMENT_SETUP.md` - Detailed local development setup
- `docs/BACKEND_DOCUMENTATION.md` - Comprehensive API documentation
- `docs/AI_SERVICE_BEST_PRACTICES.md` - AI service configuration patterns
- `NCCN_RAG_IMPLEMENTATION.md` - RAG system implementation details
