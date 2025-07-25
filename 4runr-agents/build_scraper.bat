@echo off
REM Build script for LinkedIn scraper with Playwright support

echo 🔨 Building LinkedIn Scraper Container
echo ======================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Check which Dockerfile to use
if "%1"=="optimized" (
    echo 📦 Using optimized single-stage build...
    set DOCKERFILE=Dockerfile.optimized
) else (
    echo 📦 Using multi-stage build...
    set DOCKERFILE=Dockerfile
)

echo 🧹 Cleaning up old images...
docker rmi 4runr/scraper:latest 2>nul

echo 🏗️  Building scraper container...
echo    This may take 10-15 minutes for the first build...
echo    Installing Node.js, Chromium, and all dependencies...

REM Build with progress output
docker build --file scraper/%DOCKERFILE% --tag 4runr/scraper:latest --progress=plain scraper/

if %errorlevel% equ 0 (
    echo ✅ Scraper container built successfully!
    echo.
    echo 🚀 Next steps:
    echo    1. Test the container: docker run --rm --env-file .env 4runr/scraper:latest
    echo    2. Run with compose: docker-compose up scraper
    echo    3. Check logs: docker-compose logs -f scraper
) else (
    echo ❌ Build failed. Check the error messages above.
    echo.
    echo 🔧 Troubleshooting:
    echo    1. Ensure Docker has enough memory (8GB recommended)
    echo    2. Check internet connection for package downloads
    echo    3. Try: docker system prune -a
    exit /b 1
)