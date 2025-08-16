#!/bin/bash
set -e

echo "🚀 Starting GenAScope Backend..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database connection..."
    
    # Extract database host and port from DATABASE_URL if available
    if [ -n "$DATABASE_URL" ]; then
        # Parse DATABASE_URL to get host and port
        DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*://[^@]*@\([^:/]*\).*|\1|p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's|.*://[^@]*@[^:]*:\([0-9]*\)/.*|\1|p')
        
        # Default to standard PostgreSQL port if not found
        if [ -z "$DB_PORT" ]; then
            DB_PORT=5432
        fi
        
        echo "📡 Checking database connectivity to $DB_HOST:$DB_PORT..."
        
        # Wait for database to be ready
        until nc -z "$DB_HOST" "$DB_PORT"; do 
            echo "⌛ Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."; 
            sleep 2; 
        done;
        
        echo "✅ Database is ready!"
    else
        echo "⚠️  No DATABASE_URL found, skipping database wait"
    fi
}

# Function to run database migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    export PYTHONPATH=/app
    
    if alembic upgrade head; then
        echo "✅ Database migrations completed successfully!"
    else
        echo "⚠️  Warning: Migration had issues but continuing..."
        echo "📝 This might be normal if tables already exist"
    fi
}

# Function to create test users
setup_test_users() {
    echo "👥 Setting up test users..."
    
    if python scripts/create_test_users.py; then
        echo "✅ Test users created successfully!"
        echo ""
        if [ "$ENVIRONMENT" = "production" ]; then
            echo "🎯 PRODUCTION LOGIN CREDENTIALS:"
            echo "   👨‍💼 Admin: admin@test.com / test123"
        else
            echo "🎯 DEVELOPMENT LOGIN CREDENTIALS:"
            echo "   👨‍💼 Admin: admin@testhospital.com / Admin123!"
            echo "   👨‍💼 Simple Admin: admin@test.com / test123"
            echo "   👩‍⚕️ Clinician: clinician@testhospital.com / Clinician123!"
            echo "   👤 Patient: patient1@example.com / Patient123!"
        fi
        echo ""
    else
        echo "📝 Note: Test users may already exist or creation failed"
        echo "    This is normal if the database was previously initialized"
    fi
}

# Function to start the application
start_app() {
    echo "🌟 Starting GenAScope Backend application..."
    echo "🔗 Application will be available on port ${PORT:-8080}"
    echo ""
    
    # Execute the main command passed to the container
    exec "$@"
}

# Main execution flow
main() {
    echo "🔧 Environment: ${ENVIRONMENT:-development}"
    echo "🐍 Python version: $(python --version)"
    echo "📦 Working directory: $(pwd)"
    echo ""
    
    # Only wait for database and run migrations if DATABASE_URL is set
    if [ -n "$DATABASE_URL" ]; then
        wait_for_db
        run_migrations
        setup_test_users
    else
        echo "⚠️  No DATABASE_URL configured - skipping database setup"
    fi
    
    start_app "$@"
}

# Run main function with all arguments
main "$@"
