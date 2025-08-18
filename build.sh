#!/bin/bash

# ==============================================================================
# Optimized Docker Build Script for genascope-backend
# ==============================================================================

set -e

# Configuration
IMAGE_NAME="genascope-backend"
DOCKER_BUILDKIT=1
REGISTRY=${REGISTRY:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
ENVIRONMENT="production"
PUSH=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            ENVIRONMENT="development"
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev, --development    Build for development environment"
            echo "  --push                  Push image to registry after build"
            echo "  --no-cache             Build without using cache"
            echo "  --registry REGISTRY    Specify container registry"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set image tag based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    TAG="dev"
else
    TAG="latest"
fi

if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

log_info "Building Docker image for $ENVIRONMENT environment"
log_info "Image name: $FULL_IMAGE_NAME"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Prepare build arguments
BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --no-cache"
fi

# Enable BuildKit for better performance
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build the image
log_info "Starting Docker build..."
start_time=$(date +%s)

if docker build \
    $BUILD_ARGS \
    --target production \
    --tag "$FULL_IMAGE_NAME" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --cache-from "$IMAGE_NAME:latest" \
    .; then
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    log_success "Docker build completed in ${duration} seconds"
else
    log_error "Docker build failed"
    exit 1
fi

# Check image size
IMAGE_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
log_info "Image size: $IMAGE_SIZE"

# Push to registry if requested
if [ "$PUSH" = true ]; then
    if [ -z "$REGISTRY" ]; then
        log_warning "No registry specified, skipping push"
    else
        log_info "Pushing image to registry..."
        if docker push "$FULL_IMAGE_NAME"; then
            log_success "Image pushed successfully"
        else
            log_error "Failed to push image"
            exit 1
        fi
    fi
fi

# Clean up dangling images
log_info "Cleaning up dangling images..."
docker image prune -f >/dev/null 2>&1 || true

log_success "Build process completed!"
log_info "You can run the image with:"
echo "docker run -p 8080:8080 $FULL_IMAGE_NAME"
