#!/bin/bash

# GitHub Repository Setup Script
# This script provides instructions for setting up GitHub repository variables and secrets

echo "🔧 GitHub Repository Setup for CI/CD Pipeline"
echo "=============================================="
echo ""

echo "📍 Step 1: Navigate to your GitHub repository"
echo "   Go to: https://github.com/martialbb/genascope-backend"
echo ""

echo "🔐 Step 2: Set up Environment"
echo "   Navigate to: Settings > Environments"
echo "   Create a new environment called 'dev'"
echo ""

echo "📋 Step 3: Set up Repository Variables"
echo "   Navigate to: Settings > Secrets and variables > Actions > Variables tab"
echo "   Add the following variables:"
echo ""
echo "   Variable Name: POSTGRES_DB"
echo "   Variable Value: genascope_test"
echo ""
echo "   Variable Name: POSTGRES_USER" 
echo "   Variable Value: genascope_user"
echo ""

echo "🔑 Step 4: Set up Environment Secrets"
echo "   Navigate to: Settings > Environments > dev > Add secret"
echo "   Add the following secrets to the 'dev' environment:"
echo ""
echo "   Secret Name: POSTGRES_PASSWORD"
echo "   Secret Value: your_secure_test_password"
echo ""
echo "   Secret Name: OPENAI_API_KEY"
echo "   Secret Value: your_openai_api_key"
echo ""

echo "🚀 Step 5: Test the Pipeline"
echo "   1. Make a small change to any file"
echo "   2. Commit and push to main branch:"
echo "      git add ."
echo "      git commit -m 'test: trigger CI/CD pipeline'"
echo "      git push origin main"
echo ""
echo "   3. Check the Actions tab to see the pipeline running"
echo "      https://github.com/martialbb/genascope-backend/actions"
echo ""

echo "📦 Step 6: Verify Published Image"
echo "   After successful pipeline run, verify the image:"
echo "   docker pull ghcr.io/martialbb/genascope-backend:latest"
echo ""

echo "✅ Setup Complete!"
echo "Your CI/CD pipeline is now ready to automatically build and publish Docker images."
echo "Every push to the main branch will trigger the pipeline."
