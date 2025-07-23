@echo off
REM 4Runr Pipeline Test Runner for Windows
REM This script runs the 4Runr pipeline and monitors its execution.

echo 4Runr Pipeline Test Runner

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

REM Run the Python script
python run_pipeline_test.py --docker %*

if %ERRORLEVEL% neq 0 (
    echo Error: Pipeline test failed.
    exit /b 1
)

echo Pipeline test completed successfully.
exit /b 0