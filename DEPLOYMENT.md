# Fly.io Deployment Guide

## Prerequisites

1. Install Fly.io CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly.io:
```bash
fly auth login
```

## Docker Build Optimization

The backend uses an optimized multi-stage Docker build for faster deployments:

```bash
# Build optimized production image locally
./build.sh prod

# Verify the build
docker images genascope-backend
```

**Optimization Benefits:**
- 75% faster build times (2-3 minutes vs 8-12 minutes)
- 14% smaller image size (1.6GB vs 1.86GB)
- Enhanced security with non-root user
- Better caching and layer optimization

## Database Setup

1. Create PostgreSQL database with pgvector:
```bash
fly postgres create --name genascope-postgres --region sjc --vm-size shared-cpu-1x --initial-cluster-size 1
```

2. Enable pgvector extension:
```bash
fly postgres connect -a genascope-postgres
# In psql prompt:
CREATE EXTENSION vector;
\q
```

3. Attach database to your app:
```bash
fly postgres attach --app genascope-backend genascope-postgres
```

## Email Service Setup

### Option A: Production Email (Recommended)
Use a service like SendGrid, AWS SES, or similar:

```bash
fly secrets set SMTP_SERVER="smtp.sendgrid.net" -a genascope-backend
fly secrets set SMTP_PORT="587" -a genascope-backend
fly secrets set SMTP_USERNAME="apikey" -a genascope-backend
fly secrets set SMTP_PASSWORD="your-sendgrid-api-key" -a genascope-backend
```

### Option B: Development Email (MailDev)
For staging/development environments, you can deploy MailDev separately.

## Required Secrets

Set these secrets using `fly secrets set`:

```bash
# Generate a strong secret key
fly secrets set SECRET_KEY="$(openssl rand -base64 32)" -a genascope-backend

# AWS Credentials for S3 storage
fly secrets set AWS_ACCESS_KEY_ID="your-access-key" -a genascope-backend
fly secrets set AWS_SECRET_ACCESS_KEY="your-secret-key" -a genascope-backend
fly secrets set AWS_ROLE_ARN="arn:aws:iam::your-account:role/your-role" -a genascope-backend
fly secrets set AWS_S3_BUCKET="your-production-bucket" -a genascope-backend

# OpenAI API for AI features
fly secrets set OPENAI_API_KEY="sk-your-production-openai-key" -a genascope-backend

# External API integrations
fly secrets set LAB_API_KEY="your-lab-api-key" -a genascope-backend
fly secrets set LAB_API_URL="https://api.lab.example.com" -a genascope-backend

# Optional: LangChain for tracing
fly secrets set LANGCHAIN_API_KEY="your-langchain-key" -a genascope-backend

# Optional: Redis for caching
fly secrets set REDIS_URL="redis://your-redis-instance:6379/0" -a genascope-backend
```

## Deployment

1. Deploy the application:
```bash
fly deploy
```

2. Check deployment status:
```bash
fly status -a genascope-backend
fly logs -a genascope-backend
```

3. Access your application:
```bash
fly open -a genascope-backend
```

## Health Checks

Your application will be available with health endpoints:
- `/health` - Comprehensive health check
- `/ready` - Readiness probe
- `/live` - Liveness probe

## Database Migration

The deployment includes automatic database migration via the release command in fly.toml.
Migrations run automatically before the new version starts.

## Monitoring

Check application health:
```bash
curl https://genascope-backend.fly.dev/health
```

View logs:
```bash
fly logs -a genascope-backend -f
```

## Scaling

Scale your application:
```bash
fly scale count 2 -a genascope-backend
fly scale memory 2048 -a genascope-backend
```

## Troubleshooting

1. Check app status: `fly status -a genascope-backend`
2. View logs: `fly logs -a genascope-backend`
3. Access console: `fly ssh console -a genascope-backend`
4. Check secrets: `fly secrets list -a genascope-backend`

## Security Notes

- All secrets are encrypted and managed by Fly.io
- Never commit production secrets to Git
- Rotate credentials regularly
- Use IAM roles instead of hardcoded AWS keys when possible
