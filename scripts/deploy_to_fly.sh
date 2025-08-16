#!/bin/bash
# Complete deployment script for Genascope on fly.io

set -e

echo "🚀 Deploying Genascope to fly.io..."

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

echo "📍 Step 1: Creating PostgreSQL database..."

# Create PostgreSQL cluster with pgvector support
if ! fly apps list | grep -q "genascope\s"; then
    echo "Creating PostgreSQL cluster..."
    fly postgres create \
      --name genascope \
      --region sjc \
      --vm-size shared-cpu-1x \
      --initial-cluster-size 1 \
      --volume-size 10
    
    echo "⏳ Waiting for database to be ready..."
    sleep 30
    
    echo "🔌 Enabling pgvector extension..."
    fly postgres connect -a genascope -c "CREATE EXTENSION IF NOT EXISTS vector;" || {
        echo "⚠️  Manual pgvector setup needed. Run:"
        echo "fly postgres connect -a genascope"
        echo "Then run: CREATE EXTENSION IF NOT EXISTS vector;"
        read -p "Press Enter after enabling pgvector..."
    }
else
    echo "✅ PostgreSQL cluster already exists"
fi

echo "📎 Step 2: Attaching database to backend..."
fly postgres attach --app genascope-backend genascope

echo "🔐 Step 3: Setting production secrets..."

# Generate secure SECRET_KEY
SECRET_KEY=$(openssl rand -base64 32)
fly secrets set SECRET_KEY="$SECRET_KEY" -a genascope-backend

# Set other secrets (you'll need to provide real values)
echo "⚠️  You need to set these secrets with real production values:"
echo "fly secrets set OPENAI_API_KEY='your-real-openai-key' -a genascope-backend"
echo "fly secrets set AWS_ACCESS_KEY_ID='your-production-aws-key' -a genascope-backend"
echo "fly secrets set AWS_SECRET_ACCESS_KEY='your-production-aws-secret' -a genascope-backend"
echo "fly secrets set LAB_API_KEY='your-production-lab-key' -a genascope-backend"
echo ""
read -p "Have you set the production secrets? Press Enter to continue..."

echo "📧 Step 4: Deploying MailDev..."
if ! fly apps list | grep -q "genascope-maildev"; then
    echo "Creating MailDev app..."
    fly apps create genascope-maildev
fi

fly deploy --app genascope-maildev --config maildev.fly.toml

echo "🔗 Step 5: Configuring SMTP settings..."
fly secrets set SMTP_SERVER="genascope-maildev.flycast" -a genascope-backend
fly secrets set SMTP_PORT="1025" -a genascope-backend
fly secrets set EMAIL_ENABLED="true" -a genascope-backend

echo "🎯 Step 6: Deploying backend..."
fly deploy -a genascope-backend

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check your deployment:"
echo "Backend URL: https://genascope-backend.fly.dev"
echo "MailDev URL: https://genascope-maildev.fly.dev"
echo ""
echo "🔍 Useful commands:"
echo "fly status -a genascope-backend"
echo "fly logs -a genascope-backend"
echo "fly secrets list -a genascope-backend"
echo "fly postgres connect -a genascope"
echo ""
echo "🎉 Your Genascope backend is now live!"
