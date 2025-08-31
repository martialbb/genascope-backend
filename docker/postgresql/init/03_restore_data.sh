#!/bin/bash
set -e

# Restore data from production dump
echo "Restoring production data from dump file..."

# Wait for PostgreSQL to be ready
until pg_isready -U postgres; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Check if data already exists (to avoid duplicate imports)
TABLE_COUNT=$(psql -U postgres -d genascope -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name NOT IN ('alembic_version');")

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo "No existing tables found, restoring schema and data from dump..."
    
    # Restore the dump file (includes both schema and data)
    pg_restore -U postgres -d genascope --verbose --no-owner --no-privileges /docker-entrypoint-initdb.d/03_restore_data.dump
    
    echo "✅ Production schema and data restored successfully!"
else
    echo "ℹ️ Tables already exist. Checking for data..."
    
    # Check if we have actual data in key tables
    STRATEGY_COUNT=$(psql -U postgres -d genascope -t -c "SELECT COUNT(*) FROM chat_strategies;" 2>/dev/null || echo "0")
    
    if [ "$STRATEGY_COUNT" -eq 0 ]; then
        echo "Tables exist but no data found, restoring data only..."
        
        # Restore only the data, skip schema creation
        pg_restore -U postgres -d genascope --verbose --no-owner --no-privileges --data-only /docker-entrypoint-initdb.d/03_restore_data.dump
        
        echo "✅ Production data restored successfully!"
    else
        echo "ℹ️ Data already exists ($STRATEGY_COUNT strategies found), skipping dump restore."
    fi
fi

echo "✅ Data initialization completed."
