@echo off
REM 4Runr AI Lead Scraper System Setup and Test
REM This script sets up and runs a full system test of the 4Runr AI Lead Scraper system

echo [%date% %time%] [INFO] Checking if Docker is running...
docker info > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Docker is not running. Please start Docker and try again.
    exit /b 1
)
echo [%date% %time%] [SUCCESS] Docker is running.

echo [%date% %time%] [INFO] Checking if docker-compose is available...
docker-compose --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] docker-compose is not available. Please install it and try again.
    exit /b 1
)
echo [%date% %time%] [SUCCESS] docker-compose is available.

echo [%date% %time%] [INFO] Rebuilding Docker containers with updated dependencies...
docker-compose build
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Failed to rebuild Docker containers.
    exit /b 1
)
echo [%date% %time%] [SUCCESS] Docker containers rebuilt successfully.

echo [%date% %time%] [INFO] Starting Docker containers...
docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Failed to start Docker containers.
    exit /b 1
)
echo [%date% %time%] [SUCCESS] Docker containers started successfully.

echo [%date% %time%] [INFO] Checking if all containers are running...
docker-compose ps | findstr /R "scraper enricher engager pipeline cron" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Some containers are not running.
    exit /b 1
)
echo [%date% %time%] [SUCCESS] All required containers are running.

echo [%date% %time%] [INFO] Running system test...
call run_full_system_test.bat
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] System test failed.
    exit /b 1
)
echo [%date% %time%] [SUCCESS] System test completed successfully.

echo [%date% %time%] [SUCCESS] Setup and test completed successfully.