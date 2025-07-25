#!/bin/bash

# Build script for LinkedIn scraper with Playwright support

echo "🔨 Building LinkedIn Scraper Container"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check which Dockerfile to use
if [ "$1" = "optimized" ]; then
    echo "📦 Using optimized single-stage build..."
    DOCKERFILE="Dockerfile.optimized"
else
    echo "📦 Using multi-stage build..."
    DOCKERFILE="Dockerfile"
fi

echo "🧹 Cleaning up old images..."
docker rmi 4runr/scraper:latest 2>/dev/null || true

echo "🏗️  Building scraper container..."
echo "   This may take 10-15 minutes for the first build..."
echo "   Installing Node.js, Chromium, and all dependencies..."

# Build with progress output
docker build \
    --file scraper/$DOCKERFILE \
    --tag 4runr/scraper:latest \
    --progress=plain \
    scraper/

if [ $? -eq 0 ]; then
    echo "✅ Scraper container built successfully!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Test the container: docker run --rm --env-file .env 4runr/scraper:latest"
    echo "   2. Run with compose: docker-compose up scraper"
    echo "   3. Check logs: docker-compose logs -f scraper"
else
    echo "❌ Build failed. Check the error messages above."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Ensure Docker has enough memory (8GB recommended)"
    echo "   2. Check internet connection for package downloads"
    echo "   3. Try: docker system prune -a"
    exit 1
fi