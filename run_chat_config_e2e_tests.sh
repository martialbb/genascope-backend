#!/bin/bash

# Chat Configuration E2E Test Runner
# This script runs the chat configuration end-to-end tests against a live backend service

set -e

echo "🚀 Starting Chat Configuration E2E Tests"
echo "=========================================="

# Check if backend service is running
echo "📡 Checking if backend service is available..."
if ! curl -s -f http://localhost:8000/api/v1/chat-configuration/health > /dev/null; then
    echo "❌ Backend service is not available at http://localhost:8000"
    echo "   Please start the backend service first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "✅ Backend service is available"

# Check if we're in the correct directory
if [ ! -f "app/tests/e2e/api/test_chat_configuration_e2e.py" ]; then
    echo "❌ Please run this script from the genascope-backend root directory"
    exit 1
fi

# Set test environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TEST_MODE=true

echo "🧪 Running Chat Configuration E2E Tests..."
echo ""

# Run the specific test file with verbose output
python -m pytest app/tests/e2e/api/test_chat_configuration_e2e.py \
    -v \
    --tb=short \
    --disable-warnings \
    -m e2e \
    --color=yes

echo ""
echo "✅ Chat Configuration E2E Tests Complete!"
echo "=========================================="
