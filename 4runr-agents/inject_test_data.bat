@echo off
REM 4Runr Test Data Injection Tool for Windows
REM This script injects test data into the shared/leads.json file for system testing.

echo 4Runr Test Data Injection Tool

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

REM Run the Python script
python inject_test_data.py %*

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to inject test data.
    exit /b 1
)

echo Test data injection completed successfully.
exit /b 0