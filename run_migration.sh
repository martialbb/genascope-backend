#!/bin/bash
# Script to run database migration to add missing columns

# Check if we're in a Docker environment
if [ -f /.dockerenv ]; then
    echo "Running migration in Docker environment..."
    python /app/app/db/migrations/add_missing_columns.py
else
    echo "Running migration in local environment..."
    # Set the Python path based on the script location
    export PYTHONPATH=/Users/martial-m1/genascope-frontend/backend
    python /Users/martial-m1/genascope-frontend/backend/app/db/migrations/add_missing_columns.py
fi
