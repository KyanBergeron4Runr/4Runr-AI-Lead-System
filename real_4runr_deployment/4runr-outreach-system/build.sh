#!/bin/bash
"""
Build script for 4Runr Outreach System Docker image.

This script builds the Docker image with proper tagging and
provides options for development and production builds.
"""

set -e  # Exit on any error

# Configuration
IMAGE_NAME="4runr/outreach-system"
VERSION="2.0.0"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

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
PUSH_IMAGE=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            ENVIRONMENT="development"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev, --development    Build for development environment"
            echo "  --push                  Push image to registry after build"
            echo "  --no-cache             Build without using cache"
            echo "  --help, -h             Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build configuration
if [ "$ENVIRONMENT" = "development" ]; then
    TAG_SUFFIX="-dev"
    TARGET="production"  # Still use production target but with dev tag
else
    TAG_SUFFIX=""
    TARGET="production"
fi

FULL_TAG="${IMAGE_NAME}:${VERSION}${TAG_SUFFIX}"
LATEST_TAG="${IMAGE_NAME}:latest${TAG_SUFFIX}"

log_info "Building 4Runr Outreach System Docker image"
log_info "Environment: $ENVIRONMENT"
log_info "Target: $TARGET"
log_info "Tag: $FULL_TAG"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile not found. Please run this script from the project root."
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt not found. Please run this script from the project root."
    exit 1
fi

# Build Docker image
log_info "Starting Docker build..."

BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="--no-cache"
fi

# Build the image
docker build \
    $BUILD_ARGS \
    --target $TARGET \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg VERSION="$VERSION" \
    --tag "$FULL_TAG" \
    --tag "$LATEST_TAG" \
    .

if [ $? -eq 0 ]; then
    log_success "Docker image built successfully!"
    log_info "Image tags:"
    log_info "  - $FULL_TAG"
    log_info "  - $LATEST_TAG"
else
    log_error "Docker build failed!"
    exit 1
fi

# Show image size
IMAGE_SIZE=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$FULL_TAG" | awk '{print $2}')
log_info "Image size: $IMAGE_SIZE"

# Push image if requested
if [ "$PUSH_IMAGE" = true ]; then
    log_info "Pushing image to registry..."
    
    docker push "$FULL_TAG"
    docker push "$LATEST_TAG"
    
    if [ $? -eq 0 ]; then
        log_success "Image pushed successfully!"
    else
        log_error "Failed to push image!"
        exit 1
    fi
fi

# Show next steps
log_success "Build completed successfully!"
echo ""
log_info "Next steps:"
log_info "  1. Test the image: docker run --rm -p 8080:8080 $FULL_TAG"
log_info "  2. Run with docker-compose: docker-compose up"
log_info "  3. Check health: curl http://localhost:8080/health"

# Show image information
echo ""
log_info "Image information:"
docker images | grep "$IMAGE_NAME" | head -5