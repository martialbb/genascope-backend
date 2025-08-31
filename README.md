# Genascope Backend

This is the backend repository for the Genascope application, built with FastAPI and Python. The backend provides secure API endpoints for genetic counseling, AI-powered chat, and patient management with PostgreSQL and pgvector for AI/ML capabilities.

## 🔄 Related Repositories

This project is part of a multi-repository architecture:
- Backend (this repo): API server for the Genascope application
- Frontend: [genascope-frontend](https://github.com/martialbb/genascope-frontend) - Astro/React UI

## 🛡️ Security Features

- **JWT Authentication**: Secure API access with role-based permissions
- **Data Encryption**: All sensitive data encrypted at rest and in transit
- **PII Masking**: Automatic anonymization of sensitive patient data
- **Audit Logging**: Comprehensive logging for security and compliance
- **Environment Isolation**: Separate configurations for development and production

## 🚀 Quick Start

### Prerequisites

1. **Docker and Docker Compose**: For running services locally
2. **Python 3.12+**: For backend development
3. **PostgreSQL with pgvector**: For database and AI capabilities

## 🏗️ CI/CD Pipeline

This project uses GitHub Actions for automated testing, building, and publishing Docker images:

- **Automated Testing**: Runs on every push with PostgreSQL and pgvector
- **Docker Image Building**: Creates multi-architecture images (linux/amd64, linux/arm64)
- **Security Scanning**: Uses Trivy for vulnerability detection
- **GitHub Container Registry**: Publishes images to `ghcr.io/martialbb/genascope-backend`

### Using Published Images

```bash
# Pull the latest image
docker pull ghcr.io/martialbb/genascope-backend:latest

# Or use in production with docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

### Development Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd genascope-backend
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your local settings
```

3. **Start all services with Docker Compose (Recommended):**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL with pgvector extension (port 5432)
- Backend API (port 8080)
- MailDev for email testing (port 1080)
- Automatic restoration of production database dump for testing

#### Alternative: Local Python Environment

```bash
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

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## 🚀 Production Deployment

For production deployment using published Docker images:

1. **Set up environment:**
```bash
cp .env.prod.template .env.prod
# Edit .env.prod with your production values
```

2. **Deploy with Docker Compose:**
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start production services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

3. **Verify deployment:**
```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs backend
```

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                 | Action                                           |
| :---------------------- | :----------------------------------------------- |
| `docker-compose up -d`  | Start all services (PostgreSQL, Backend, MailDev) |
| `docker-compose down`   | Stop all services                               |
| `docker-compose -f docker-compose.prod.yml up -d` | Start production services |
| `uvicorn app.main:app --reload` | Start development server at `localhost:8080` |
| `pytest tests/`         | Run comprehensive test suite                    |
| `alembic upgrade head`  | Run database migrations                         |
| `alembic revision --autogenerate -m "message"` | Generate database migration |

## 🐳 Docker Development

### Quick Start
```bash
# Start all services with Docker Compose (recommended)
docker-compose up -d

# This will automatically:
# - Initialize PostgreSQL with pgvector extension
# - Restore production data (users, strategies, chat sessions)
# - Run database migrations
# - Start the API server with hot-reload
```

### Services & Pre-loaded Data
- **PostgreSQL with pgvector**: Database with AI/ML capabilities on port 5432
- **Backend API**: FastAPI server on port 8080
- **MailDev**: Email testing interface on port 1080
- **Production Data**: Real users, chat strategies, and knowledge sources included

### Useful Docker Commands
```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Stop all services
docker-compose down

# Reset everything (remove volumes)
docker-compose down -v

# Rebuild and restart
docker-compose up --build
```
## 📚 API Documentation

Once the server is running, you can access:
- Interactive API documentation: `http://localhost:8080/docs`
- Alternative API documentation: `http://localhost:8080/redoc`
- Health check endpoint: `http://localhost:8080/health`

## 📖 Additional Documentation

- [Local Development Setup](DEPLOYMENT.md) - Complete local development guide
- [Changelog](CHANGELOG.md) - Recent changes and improvements

## 🏗️ Architecture

The application follows a layered architecture pattern:

1. **Models** (`/app/models/`): SQLAlchemy database models
2. **Repositories** (`/app/repositories/`): Data access layer for database operations
3. **Services** (`/app/services/`): Business logic layer
4. **APIs** (`/app/api/`): REST API endpoints using FastAPI
5. **Schemas** (`/app/schemas/`): Pydantic models for request/response validation

### AI Service Configuration

The application includes AI-powered chat capabilities:

- **Development**: Mock mode available when OpenAI is not configured
- **Production**: Full AI capabilities with OpenAI integration
- **pgvector**: Vector database for embeddings and semantic search
- **Circuit Breaker**: Graceful degradation with user-friendly error messages

#### Environment Variables

```bash
# AI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
PGVECTOR_EXTENSION_ENABLED=true

# Optional AI configuration
FAIL_FAST_ON_STARTUP=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

For detailed information, see [AI Service Best Practices](docs/AI_SERVICE_BEST_PRACTICES.md).

## ✨ Features

The backend implements the following key features:

- **Authentication**: JWT token-based authentication system
- **User Management**: Complete CRUD operations for different user roles
- **File Storage**: Secure S3 integration with IAM role-based access
- **Chat System**: Interactive chat with branching logic and persistence
- **Patient Eligibility Analysis**: Risk assessment based on chat answers
- **Patient Invites**: System for clinicians to invite patients
- **Lab Integration**: Orders and results management with external labs
- **Appointments**: Scheduling system for patient appointments

## 🔐 AWS Integration

### File Upload Security
- **IAM Role Assumption**: Backend assumes `genascope-dev-backend-role` for AWS access
- **Temporary Credentials**: Uses AWS STS for short-lived credentials
- **TLS Encryption**: All S3 communications over HTTPS
- **Regional STS**: Uses regional STS endpoint for improved reliability

```

## 🔌 Frontend Connection

This backend is designed to work with the [genascope-frontend](https://github.com/martialbb/genascope-frontend) repository.

The backend provides secure API endpoints for:
- User authentication and management
- AI-powered chat interactions
- Patient management and eligibility analysis
- Knowledge source management with vector embeddings
- Invite management for patient onboarding
- Lab test ordering and results

CORS is configured in `app/main.py` for local development on ports 3000, 4321, and 5173.

## 🧪 Testing

Run the comprehensive test suite:

```bash
pytest tests/
```

This will run:
- Unit tests for individual components
- Integration tests for API endpoints  
- End-to-end tests for complete workflows
- Database integration tests

### Email Testing

MailDev provides a local email testing interface:
- Web Interface: http://localhost:1080
- SMTP Server: localhost:1025

## 🛠️ Development Tools

### Database Management

```bash
# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "Description"

# Access database directly
psql postgresql://postgres:postgres@localhost:5432/genascope
```

### API Testing

```bash
# Health check
curl http://localhost:8080/health

# Test authentication
curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```
