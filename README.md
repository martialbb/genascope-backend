# Genascope Backend

This is the backend repository for the Genascope application, built with FastAPI and Python. The backend provides secure API endpoints with AWS S3 integration for file storage using IAM role-based access and least-privilege security patterns.

## 🔄 Related Repositories

This project is part of a multi-repository architecture:
- Backend (this repo): API server for the Genascope application with AWS integration
- Frontend: [genascope-frontend](https://github.com/martialbb/genascope-frontend) - Astro/React UI

## 🛡️ Security Features

- **AWS S3 Integration**: Secure file storage with IAM role-based access
- **Temporary Credentials**: Uses AWS STS for short-lived credentials (no long-term keys)
- **TLS Enforcement**: All S3 communications encrypted in transit
- **Least Privilege**: Granular IAM policies for minimum required permissions
- **Role Assumption**: Backend assumes IAM roles for AWS service access

## 🚀 Project Setup

### Prerequisites

1. **AWS Infrastructure**: Provision AWS resources using Infrastructure as Code:
```sh
# Navigate to infrastructure directory
cd ../iac/environments/dev

# Initialize and apply Terraform/OpenTofu
tofu init
tofu plan
tofu apply
```

2. **Environment Configuration**: Create `.env.local` with AWS and database settings:
```sh
# Copy example environment file
cp .env.example .env.local

# Update with your AWS credentials and S3 bucket name from infrastructure outputs
```

### Development Setup

#### Option 1: Docker (Recommended)

```sh
# Quick start with Docker
./build.sh dev

# Development with hot-reload
docker-compose up --build

# Access API at http://localhost:8080
```

#### Option 2: Local Python Environment

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

# Test AWS integration
python scripts/test_s3_access.py
```

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                 | Action                                           |
| :---------------------- | :----------------------------------------------- |
| `./build.sh dev`        | Build optimized Docker image for development     |
| `./build.sh prod`       | Build optimized Docker image for production      |
| `docker-compose up`     | Start development environment with hot-reload   |
| `uvicorn app.main:app --reload` | Start development server at `localhost:8000` |
| `pytest tests/`          | Run comprehensive test suite                      |
| `pytest`                | Run tests                                        |
| `alembic upgrade head`  | Run database migrations                          |
| `alembic revision --autogenerate -m "message"` | Generate database migration |

## 🐳 Docker Development

### Quick Start
```sh
# Build and run with Docker (recommended)
./build.sh dev
docker run -p 8080:8080 genascope-backend:dev

# Or use docker-compose for development
docker-compose up --build
```

### Docker Features
- **Multi-stage builds** for optimized image size (1.6GB vs 1.86GB)
- **Hot-reload support** in development mode
- **Security hardening** with non-root user
- **Health checks** for container orchestration
- **Virtual environment isolation** for better dependency management

### Build Scripts
- `./build.sh dev` - Development build with debugging
- `./build.sh prod` - Production build optimized for size
- `./build.sh --no-cache` - Force rebuild without cache

See [DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md) for detailed optimization information.

## 📚 API Documentation

Once the server is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## 📖 Additional Documentation

- [Docker Optimization Guide](DOCKER_OPTIMIZATION.md) - Detailed Docker build improvements
- [Development Setup](DEVELOPMENT_SETUP.md) - Complete development environment setup
- [Deployment Guide](DEPLOYMENT.md) - Production deployment instructions
- [Changelog](CHANGELOG.md) - Recent changes and improvements

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

### Testing AWS Integration
```sh
# Test S3 access and role assumption
python scripts/test_s3_access.py

# Test file upload with authentication
python scripts/upload_test_file.py

# Test via API endpoint
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer <jwt-token>" \
  -F "file=@test-file.txt"
```

## 🔌 Frontend Connection

This backend is designed to work with the [genascope-frontend](https://github.com/martialbb/genascope-frontend) repository.

The backend provides secure API endpoints for:
- User authentication and management
- File upload to S3 with role-based access
- Chat interactions and eligibility analysis
- Patient invite management
- Lab test ordering and results

Make sure to configure CORS in `app/main.py` to allow requests from your frontend application.

## 🧪 Testing

Run the comprehensive test suite:

```sh
pytest tests/
```

This will run:
- Unit tests for individual components
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Code quality checks with flake8
- Type checking with mypy (if available)
- Coverage report generation
