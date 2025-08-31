# Local Development Setup

This guide covers setting up Genascope for local development using Docker Compose.

## Prerequisites

1. **Docker and Docker Compose** installed on your system
2. **Python 3.12+** for backend development
3. **Node.js 18+** for frontend development (if running separately)

## Quick Start with Docker Compose

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

3. **Start all services:**
```bash
docker-compose up -d
```

This will:
- Start PostgreSQL with pgvector extension and run initialization scripts
- **Restore production data** from `03_restore_data.dump` (includes real users, strategies, and chat data)
- Automatically run database migrations (Alembic)  
- Start the Backend API with hot-reload enabled
- Start MailDev for email testing

Services:
- **PostgreSQL with pgvector**: Database on port 5432
- **Backend API**: FastAPI server on port 8080  
- **MailDev**: Email testing interface on port 1080

## Pre-loaded Test Data

The database comes pre-populated with production data including:
- User accounts and clinicians
- Chat strategies (including NCCN Breast Cancer Screening Strategy)
- Knowledge sources and PDF documents
- Patient profiles and appointments
- AI chat sessions and messages

This allows immediate testing of all features without manual data setup.

## Environment Configuration

Key environment variables for local development:

```bash
# Database
DATABASE_URI=postgresql://postgres:postgres@localhost:5432/genascope

# API Configuration
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# Email (using MailDev)
SMTP_SERVER=localhost
SMTP_PORT=1025
SMTP_USERNAME=""
SMTP_PASSWORD=""
EMAIL_ENABLED=true

# AI/Chat Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
ENABLE_MOCK_CALCULATORS=true

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## Database Setup

1. **Run migrations:**
```bash
# From the backend directory
python -m alembic upgrade head
```

2. **Create test data (optional):**
```bash
python scripts/create_test_users.py
python scripts/setup_dev_users.py
```

## Development Workflow

1. **Backend development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

2. **Frontend development:**
```bash
# In your frontend repository
npm install
npm run dev
```

## Testing

1. **Run backend tests:**
```bash
python -m pytest
```

2. **Test API endpoints:**
```bash
curl http://localhost:8080/health
```

3. **Test email functionality:**
Visit http://localhost:1080 to see MailDev interface

## Services Overview

### PostgreSQL Database
- **Host:** localhost:5432
- **Database:** genascope
- **User:** postgres
- **Password:** postgres
- **Extensions:** pgvector enabled for AI/ML capabilities

### Backend API
- **URL:** http://localhost:8080
- **Documentation:** http://localhost:8080/docs
- **Health Check:** http://localhost:8080/health

### MailDev (Email Testing)
- **Web Interface:** http://localhost:1080
- **SMTP:** localhost:1025

## Production Considerations

For production deployment, consider:
- Using managed PostgreSQL with pgvector support
- Proper secret management
- SSL/TLS configuration
- Monitoring and logging
- Backup strategies
- Load balancing and scaling

## Troubleshooting

1. **Database connection issues:**
   - Ensure PostgreSQL is running
   - Check DATABASE_URI format
   - Verify database exists

2. **pgvector extension issues:**
   - Use pgvector/pgvector Docker image
   - Or install pgvector manually on PostgreSQL

3. **Email not working:**
   - Check MailDev is running on port 1025
   - Verify SMTP configuration

## Security Notes

- Change default passwords in production
- Use environment variables for secrets
- Enable proper authentication and authorization
- Regular security updates
