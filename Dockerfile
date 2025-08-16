FROM python:3.11-slim

WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy all requirements files
COPY requirements.txt requirements.ai-chat.txt requirements.postgresql.txt ./

# Install all Python dependencies with verbose output
RUN pip install --no-cache-dir --verbose -r requirements.txt \
    && pip install --no-cache-dir --verbose -r requirements.postgresql.txt \
    && pip install --no-cache-dir --verbose -r requirements.ai-chat.txt

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port 8080 for fly.io
EXPOSE 8080

# Set the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]

# Default command for fly.io (can be overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

