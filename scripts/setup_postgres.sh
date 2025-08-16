#!/bin/bash
# PostgreSQL with pgvector setup script for Fly.io

set -e

echo "🚀 Setting up PostgreSQL with pgvector on Fly.io"

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo "curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! fly auth whoami &> /dev/null; then
    echo "❌ Please login to Fly.io first:"
    echo "fly auth login"
    exit 1
fi

echo "📍 Creating PostgreSQL database..."

# Create PostgreSQL cluster with pgvector support
fly postgres create \
  --name genascope \
  --region sjc \
  --vm-size shared-cpu-1x \
  --initial-cluster-size 1 \
  --volume-size 10

echo "✅ PostgreSQL cluster created!"

echo "🔌 Enabling pgvector extension..."

# Connect to database and enable pgvector
echo "Please run the following commands in the PostgreSQL prompt:"
echo "CREATE EXTENSION IF NOT EXISTS vector;"
echo "\\q"
echo ""
echo "Press Enter to open PostgreSQL connection..."
read -r

fly postgres connect -a genascope

echo "📎 Attaching database to backend app..."

# Attach database to the backend application
fly postgres attach --app genascope-backend genascope

echo "✅ Database attached to genascope-backend!"

echo "🔍 Checking database connection..."
fly secrets list -a genascope-backend | grep DATABASE

echo ""
echo "✅ PostgreSQL with pgvector setup complete!"
echo ""
echo "Next steps:"
echo "1. Your DATABASE_URL is now set as a secret in genascope-backend"
echo "2. The pgvector extension should be enabled"
echo "3. Run 'fly deploy -a genascope-backend' to deploy with database connection"
