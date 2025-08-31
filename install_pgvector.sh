#!/bin/bash
set -e

echo "Starting pgvector installation..."

# Update package lists
apt-get update

# Install required packages
echo "Installing build dependencies..."
apt-get install -y git build-essential postgresql-server-dev-17

# Clone pgvector
echo "Cloning pgvector repository..."
cd /tmp
git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector

# Build pgvector
echo "Building pgvector..."
make clean
make
make install

# Connect to PostgreSQL and create the extension
echo "Creating pgvector extension in database..."
su - postgres -c "psql -d postgres -c 'CREATE EXTENSION IF NOT EXISTS vector;'"

echo "pgvector installation completed successfully!"

# Verify installation
su - postgres -c "psql -d postgres -c \"SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';\""

echo "Installation verification completed."
