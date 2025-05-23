#!/bin/bash
# Comprehensive test script for Genascope backend

# Exit on error
set -e

echo "Starting Genascope backend test suite..."
echo "========================================"

# Define test directories
UNIT_TEST_DIR="tests/unit"
INTEGRATION_TEST_DIR="tests/integration"
E2E_TEST_DIR="tests/e2e"

# Function to run a specific test suite with proper formatting
run_test_suite() {
    local test_dir=$1
    local test_type=$2
    
    echo ""
    echo "Running $test_type tests..."
    echo "--------------------------"
    
    if [ -d "$test_dir" ]; then
        python -m pytest "$test_dir" -v
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "✅ $test_type tests passed successfully!"
        else
            echo "❌ $test_type tests failed with exit code $exit_code"
            return $exit_code
        fi
    else
        echo "⚠️  $test_type test directory not found. Skipping..."
    fi
    
    echo ""
}

# Run flake8 for code quality check
echo "Running code quality checks with flake8..."
if command -v flake8 >/dev/null 2>&1; then
    flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
    echo "✅ Code quality checks passed!"
else
    echo "⚠️  flake8 not installed. Skipping code quality checks."
fi

# Run mypy for type checking if available
echo "Running type checking with mypy..."
if command -v mypy >/dev/null 2>&1; then
    mypy app/
    echo "✅ Type checking passed!"
else
    echo "⚠️  mypy not installed. Skipping type checking."
fi

# Run the test suites
run_test_suite "$UNIT_TEST_DIR" "Unit"
run_test_suite "$INTEGRATION_TEST_DIR" "Integration"
run_test_suite "$E2E_TEST_DIR" "End-to-End"

# Generate coverage report
echo "Generating test coverage report..."
if command -v pytest-cov >/dev/null 2>&1; then
    python -m pytest --cov=app tests/ --cov-report=term --cov-report=html
    echo "✅ Coverage report generated!"
    echo "View detailed HTML report at: htmlcov/index.html"
else
    echo "⚠️  pytest-cov not installed. Skipping coverage report."
fi

echo ""
echo "===================================="
echo "🎉 All tests completed successfully!"
echo "===================================="
