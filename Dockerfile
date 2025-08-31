# ==============================================================================
# Multi-stage Docker build for genascope-backend
# ==============================================================================

# ---- Build stage ----
FROM python:3.11-slim AS builder

# Set build arguments for optimization
ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
ARG PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment for better dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel for faster builds
RUN pip install --upgrade pip wheel setuptools

# Copy only requirements file first (for better caching)
COPY requirements.txt ./

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# ---- Production stage ----
FROM python:3.11-slim AS production

# Set runtime arguments
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only runtime dependencies (much smaller)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user first
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Copy application code with proper ownership
COPY --chown=app:app . .

# Create start script if it doesn't exist
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Wait for database to be ready\n\
if [ -n "$DATABASE_URI" ]; then\n\
    echo "Waiting for database..."\n\
    host=$(echo $DATABASE_URI | sed "s/.*@\\([^:]*\\):.*/\\1/")\n\
    port=$(echo $DATABASE_URI | sed "s/.*:\\([0-9]*\\).*/\\1/")\n\
    \n\
    until nc -z $host $port; do\n\
        echo "Database not ready, waiting..."\n\
        sleep 2\n\
    done\n\
    echo "Database is ready!"\n\
fi\n\
\n\
# Run database migrations\n\
if [ "$RUN_MIGRATIONS" = "true" ]; then\n\
    echo "Running database migrations..."\n\
    alembic upgrade head\n\
fi\n\
\n\
# Start the application\n\
exec "$@"' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown app:app /app/start.sh

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Expose port 8080
EXPOSE 8080

# Default command - start the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

