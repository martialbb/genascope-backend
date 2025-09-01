# GenAScope Backend Deployment Guide

## Overview
This deployment guide covers the optimized Docker build strategy that resolves previous timeout issues and provides flexible deployment options for both AMD64 and ARM64 architectures.

## Build Strategy (Post-Optimization)

### 🚀 **Automatic AMD64 Builds**
- **Trigger**: Every push to any branch
- **Build Time**: ~15-20 minutes
- **Platforms**: AMD64 only
- **Usage**: Development, most production deployments
- **Image Tag**: `ghcr.io/martialbb/genascope-backend:latest`

### 📱 **Manual ARM64 Builds**
- **Trigger**: Manual workflow dispatch
- **Build Time**: ~45-60 minutes
- **Platforms**: ARM64 only
- **Usage**: Orange Pi, ARM-based devices
- **Image Tag**: `ghcr.io/martialbb/genascope-backend:arm64-latest`

## Deployment Options

### Option 1: AMD64 Deployment (Recommended)

#### For Cloud Servers (AWS, DigitalOcean, etc.)
```bash
# Pull the latest AMD64 image
docker pull ghcr.io/martialbb/genascope-backend:latest

# Start production environment
docker-compose -f docker-compose.prod.yml up -d
```

#### For Local Development
```bash
# Regular development workflow
git push  # Triggers automatic AMD64 build
# Wait ~15 minutes for build completion
docker pull ghcr.io/martialbb/genascope-backend:latest
docker-compose up -d
```

### Option 2: ARM64 Deployment (Orange Pi, etc.)

#### Method A: Manual ARM64 Build
1. **Trigger ARM64 Build**:
   - Go to [GitHub Actions](https://github.com/martialbb/genascope-backend/actions)
   - Select "Build ARM64 Docker Image"
   - Click "Run workflow"
   - Wait ~45-60 minutes for completion

2. **Deploy ARM64 Image**:
```bash
# Pull the ARM64-specific image
docker pull ghcr.io/martialbb/genascope-backend:arm64-latest

# Update docker-compose to use ARM64 tag
sed -i 's|ghcr.io/martialbb/genascope-backend:latest|ghcr.io/martialbb/genascope-backend:arm64-latest|g' docker-compose.prod.yml

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

#### Method B: Local ARM64 Build (Development)
```bash
# Build locally with lightweight dependencies
docker build -f Dockerfile.arm64 -t genascope-backend:arm64-dev .

# Update docker-compose for local image
sed -i 's|ghcr.io/martialbb/genascope-backend.*|genascope-backend:arm64-dev|g' docker-compose.yml

# Start services
docker-compose up -d
```

#### Method C: AMD64 with Emulation
```bash
# Use AMD64 image on ARM64 (with performance cost)
docker pull ghcr.io/martialbb/genascope-backend:latest
docker-compose -f docker-compose.prod.yml up -d
# Note: This will use emulation and may be slower
```

## Local Development Setup

### Prerequisites

1. **Docker and Docker Compose** installed on your system
2. **Python 3.12+** for backend development
3. **Node.js 18+** for frontend development (if running separately)

### Quick Start with Docker Compose

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

### Pre-loaded Test Data

The database comes pre-populated with production data including:
- User accounts and clinicians
- Chat strategies (including NCCN Breast Cancer Screening Strategy)
- Knowledge sources and PDF documents
- Patient profiles and appointments
- AI chat sessions and messages

This allows immediate testing of all features without manual data setup.

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/genascope
POSTGRES_USER=genascope
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=genascope

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services (if used)
OPENAI_API_KEY=your-openai-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### Local Development Configuration

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

### Docker Compose Files

#### Production (`docker-compose.prod.yml`)
```yaml
version: '3.8'
services:
  web:
    image: ghcr.io/martialbb/genascope-backend:latest  # or :arm64-latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://genascope:${POSTGRES_PASSWORD}@db:5432/genascope
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=genascope
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=genascope
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## Performance Considerations

### AMD64 vs ARM64 Performance

| Metric | AMD64 | ARM64 (Native) | ARM64 (Emulated) |
|--------|-------|----------------|------------------|
| Build Time | 15-20 min | 45-60 min | N/A |
| Runtime Performance | 100% | 95-100% | 60-80% |
| Memory Usage | Baseline | Similar | +20-30% |
| Recommended Use | Cloud, Dev | Orange Pi, Native ARM | Last resort |

### Deployment Size Comparison

| Component | AMD64 | ARM64 |
|-----------|-------|-------|
| Base Image | ~800MB | ~850MB |
| With Dependencies | ~1.2GB | ~1.1GB |
| Runtime Memory | ~200MB | ~220MB |

## Troubleshooting

### Common Issues

#### 1. Build Timeouts (Previous Issue - Now Resolved)
```bash
# Before optimization: 1h57min+ builds with failures
# After optimization: 15-20min AMD64, 45-60min ARM64
```

#### 2. ARM64 Image Not Available
```bash
# Check if ARM64 build was triggered
gh api repos/martialbb/genascope-backend/actions/workflows/build-arm64.yml/runs

# Trigger manual ARM64 build
# GitHub UI: Actions → "Build ARM64 Docker Image" → "Run workflow"
```

#### 3. Wrong Architecture Image
```bash
# Check image architecture
docker image inspect ghcr.io/martialbb/genascope-backend:latest | grep Architecture

# Force pull specific architecture
docker pull --platform linux/amd64 ghcr.io/martialbb/genascope-backend:latest
docker pull --platform linux/arm64 ghcr.io/martialbb/genascope-backend:arm64-latest
```

#### 4. Performance Issues on ARM64
```bash
# Option 1: Use native ARM64 build
docker pull ghcr.io/martialbb/genascope-backend:arm64-latest

# Option 2: Local build with lightweight deps
docker build -f Dockerfile.arm64 -t genascope-local .

# Option 3: Check if running emulated
docker info | grep Architecture
```

#### 5. Database Issues
   - Database connection issues: Ensure PostgreSQL is running, check DATABASE_URI format, verify database exists
   - pgvector extension issues: Use pgvector/pgvector Docker image or install pgvector manually on PostgreSQL

#### 6. Email Issues
   - Email not working: Check MailDev is running on port 1025, verify SMTP configuration
   - Test email functionality: Visit http://localhost:1080 to see MailDev interface

## Monitoring and Health Checks

### Application Health
```bash
# Check application status
curl http://localhost:8000/health

# View application logs
docker-compose logs -f web

# Monitor resource usage
docker stats
```

### Database Health
```bash
# Check database connection
docker-compose exec db psql -U genascope -d genascope -c "SELECT version();"

# View database logs
docker-compose logs -f db
```

### Services Overview

#### PostgreSQL Database
- **Host:** localhost:5432
- **Database:** genascope
- **User:** postgres
- **Password:** postgres
- **Extensions:** pgvector enabled for AI/ML capabilities

#### Backend API
- **URL:** http://localhost:8080
- **Documentation:** http://localhost:8080/docs
- **Health Check:** http://localhost:8080/health

#### MailDev (Email Testing)
- **Web Interface:** http://localhost:1080
- **SMTP:** localhost:1025

## Maintenance

### Regular Updates
```bash
# Pull latest image
docker pull ghcr.io/martialbb/genascope-backend:latest

# Restart services with new image
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Database Migrations
```bash
# Run pending migrations
docker-compose exec web alembic upgrade head

# Check migration status
docker-compose exec web alembic current
```

### Development Workflow

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

### Testing

1. **Run backend tests:**
```bash
python -m pytest
```

2. **Test API endpoints:**
```bash
curl http://localhost:8080/health
```

### Cleanup
```bash
# Remove unused images
docker image prune -f

# Remove unused volumes (CAUTION: This removes data)
docker volume prune -f
```

## Production Considerations

For production deployment, consider:
- Using managed PostgreSQL with pgvector support
- Proper secret management
- SSL/TLS configuration
- Monitoring and logging
- Backup strategies
- Load balancing and scaling

## Security Notes

- Change default passwords in production
- Use environment variables for secrets
- Enable proper authentication and authorization
- Regular security updates

## Architecture Decision Summary

The current deployment strategy prioritizes:
1. **Fast development iteration** (15-20 min AMD64 builds)
2. **Reliable CI/CD** (no more timeout failures)
3. **Flexible deployment** (AMD64 automatic, ARM64 on-demand)
4. **Production stability** (proven AMD64 performance)

This approach resolves the previous 1h57min build timeout issues while maintaining support for all target platforms.
