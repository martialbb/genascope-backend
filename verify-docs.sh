#!/bin/bash
# Documentation Verification Script
# Verifies that all Docker optimization documentation is complete and consistent

echo "🔍 Verifying Docker Optimization Documentation..."

# Check required files exist
echo "📄 Checking documentation files..."
files=(
    "README.md"
    "DOCKER_OPTIMIZATION.md"
    "DEPLOYMENT.md"
    "DEVELOPMENT_SETUP.md"
    "CHANGELOG.md"
    "Dockerfile"
    "build.sh"
    ".dockerignore"
    "docker-compose.override.yml"
    ".github/workflows/fly-deploy.yml"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

# Check Docker build script is executable
echo ""
echo "🔧 Checking build script permissions..."
if [ -x "build.sh" ]; then
    echo "✅ build.sh is executable"
else
    echo "❌ build.sh is not executable (run: chmod +x build.sh)"
fi

# Verify Docker optimization files contain expected content
echo ""
echo "📊 Verifying documentation content..."

if grep -qi "multi.*stage" DOCKER_OPTIMIZATION.md 2>/dev/null; then
    echo "✅ DOCKER_OPTIMIZATION.md contains multi-stage build info"
else
    echo "❌ DOCKER_OPTIMIZATION.md missing multi-stage build info"
fi

if grep -q "build.sh" README.md 2>/dev/null; then
    echo "✅ README.md references build script"
else
    echo "❌ README.md missing build script reference"
fi

if grep -q "Docker" DEVELOPMENT_SETUP.md 2>/dev/null; then
    echo "✅ DEVELOPMENT_SETUP.md includes Docker information"
else
    echo "❌ DEVELOPMENT_SETUP.md missing Docker information"
fi

# Test Docker build script (dry run)
echo ""
echo "🐳 Testing Docker build script..."
if ./build.sh --help 2>/dev/null || ./build.sh --dry-run 2>/dev/null; then
    echo "✅ Build script is functional"
else
    echo "❌ Build script has issues (try: ./build.sh dev)"
fi

echo ""
echo "🎉 Documentation verification complete!"
echo "📚 Next steps:"
echo "   1. Test Docker build: ./build.sh dev"
echo "   2. Test development setup: docker-compose up --build"
echo "   3. Review updated documentation"
