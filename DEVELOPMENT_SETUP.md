# 🚀 Genascope Development Setup Guide

This guide will help new developers get the entire Genascope application running with **zero manual configuration**.

## ✅ Prerequisites

- Docker Desktop installed and running
- Git

## 🏃‍♂️ Quick Start (One Command Setup)

1. **Clone both repositories:**
```bash
# Clone the frontend (this contains the docker-compose file)
git clone https://github.com/martialbb/genascope-frontend.git
cd genascope-frontend

# Clone the backend as a sibling directory
cd ..
git clone https://github.com/martialbb/genascope-backend.git
cd genascope-frontend
```

2. **Start everything with one command:**
```bash
docker compose -f docker-compose.postgresql.dev.yml up --build
```

That's it! 🎉 The system will automatically:
- ✅ Start PostgreSQL database with pgvector support
- ✅ Run all database migrations automatically
- ✅ Create test users for immediate login (including admin@test.com/test123)
- ✅ Start the FastAPI backend on http://localhost:8000
- ✅ Start the frontend on http://localhost:4321
- ✅ Start supporting services (MinIO, MailDev)

## 🌐 Access Points

Once everything is running, you can access:

- **Frontend**: http://localhost:4321
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (genascope/genascope/genascope)
- **Email Testing**: http://localhost:8025 (MailDev)
- **File Storage**: http://localhost:9001 (MinIO Console - minioadmin/minioadmin123)

## 👤 Test User Credentials

The system automatically creates test users for development. You can login immediately with:

### Quick Login (for immediate testing):
- **Email:** `admin@test.com`
- **Password:** `test123`
- **Role:** Admin

### Full Test User Set:
- **Super Admin:** `superadmin@genascope.com` / `SuperAdmin123!`
- **Admin:** `admin@testhospital.com` / `Admin123!`
- **Clinician:** `clinician@testhospital.com` / `Clinician123!`
- **Clinician 2:** `clinician2@testhospital.com` / `Clinician123!`
- **Lab Tech:** `labtech@testhospital.com` / `LabTech123!`
- **Patient 1:** `patient1@example.com` / `Patient123!`
- **Patient 2:** `patient2@example.com` / `Patient123!`

The `admin@test.com` user is created specifically for quick testing and development scenarios.

## 🔧 Development Workflow

### Backend Development
```bash
# View backend logs
docker compose -f docker-compose.postgresql.dev.yml logs -f backend

# Access backend container for debugging
docker compose -f docker-compose.postgresql.dev.yml exec backend bash

# Run tests in backend container
docker compose -f docker-compose.postgresql.dev.yml exec backend pytest

# Check migration status
docker compose -f docker-compose.postgresql.dev.yml exec backend alembic current
```

### Frontend Development
```bash
# View frontend logs
docker compose -f docker-compose.postgresql.dev.yml logs -f frontend

# Access frontend container
docker compose -f docker-compose.postgresql.dev.yml exec frontend bash
```

### Database Operations
```bash
# Connect to PostgreSQL
docker compose -f docker-compose.postgresql.dev.yml exec db psql -U genascope -d genascope

# View database logs
docker compose -f docker-compose.postgresql.dev.yml logs -f db
```

## 🔄 Managing Services

```bash
# Stop all services
docker compose -f docker-compose.postgresql.dev.yml down

# Rebuild and restart everything
docker compose -f docker-compose.postgresql.dev.yml up --build

# Start only specific services
docker compose -f docker-compose.postgresql.dev.yml up backend db

# View all running containers
docker compose -f docker-compose.postgresql.dev.yml ps
```

## 🗄️ Database Migrations

**Automatic Migration**: Migrations run automatically when you start the backend! No manual steps needed.

**Automatic Test Users**: Test users (including admin@test.com/test123) are created automatically after migrations complete.

If you need to run migrations manually:
```bash
# Check current migration status
docker compose -f docker-compose.postgresql.dev.yml exec backend alembic current

# Run migrations manually (usually not needed)
docker compose -f docker-compose.postgresql.dev.yml exec backend alembic upgrade head

# Create test users manually (usually not needed)
docker compose -f docker-compose.postgresql.dev.yml exec backend python scripts/setup_dev_users.py

# Create new migration (for developers adding new features)
docker compose -f docker-compose.postgresql.dev.yml exec backend alembic revision --autogenerate -m "description"
```

### For Frontend Developers: Integrating Test User Creation

To enable automatic test user creation in your docker-compose.postgresql.dev.yml, update the backend service command:

```yaml
backend:
  # ... other configuration ...
  command: >
    sh -c "
      echo 'Waiting for PostgreSQL to be ready...'
      while ! nc -z db 5432; do
        echo 'PostgreSQL is not ready - sleeping...'
        sleep 2
      done
      echo 'PostgreSQL is ready! Running migrations...'
      alembic upgrade head
      if [ $$? -eq 0 ]; then
        echo 'Migrations completed successfully!'
        echo 'Creating test users for development...'
        python scripts/setup_dev_users.py
        if [ $$? -eq 0 ]; then
          echo 'Test users created successfully! Login with admin@test.com/test123'
        else
          echo 'Warning: Test user creation failed, but continuing with app startup'
        fi
      else
        echo 'Migration failed! Please check the logs.'
        exit 1
      fi
      echo 'Starting FastAPI application...'
      python run.py
    "
```

## 🧹 Cleanup

```bash
# Stop and remove all containers, networks
docker compose -f docker-compose.postgresql.dev.yml down

# Remove all containers and volumes (fresh start)
docker compose -f docker-compose.postgresql.dev.yml down -v

# Remove all unused Docker resources
docker system prune -a
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Make sure ports 4321, 8000, 5432, 8025, 9000, 9001 are available
2. **Docker not running**: Ensure Docker Desktop is started
3. **Permission issues**: On Linux, you might need to use `sudo` or add your user to the docker group

### Reset Everything
If something goes wrong, you can always reset:
```bash
docker compose -f docker-compose.postgresql.dev.yml down -v
docker system prune -a
docker compose -f docker-compose.postgresql.dev.yml up --build
```

## 🎯 Key Features

- **Zero Configuration**: No manual environment setup needed
- **Automatic Migrations**: Database schema stays in sync automatically
- **Hot Reloading**: Both frontend and backend reload on code changes
- **Isolated Environment**: Everything runs in containers
- **Complete Stack**: Database, backend, frontend, and supporting services
- **Development Tools**: Email testing, file storage, API documentation

## 📁 Project Structure

```
genascope-frontend/
├── docker-compose.postgresql.dev.yml  # Main development configuration
├── DEVELOPMENT_SETUP.md               # This guide
└── src/                              # Frontend source code

genascope-backend/                    # Should be in sibling directory
├── app/                             # FastAPI application
├── alembic/                         # Database migrations
├── requirements.txt                 # Python dependencies (includes pgvector)
└── Dockerfile                       # Backend container definition
```

## 🤝 Contributing

1. Make your changes to the code
2. The containers will automatically reload
3. Test your changes
4. Commit and push your changes
5. Migrations will run automatically for other developers

Happy coding! 🚀
