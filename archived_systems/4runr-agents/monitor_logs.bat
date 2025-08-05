@echo off
REM 4Runr Log Monitor for Windows
REM This script monitors logs from the 4Runr pipeline in real-time.

echo 4Runr Log Monitor

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

REM Install required packages if not already installed
pip show colorama >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing required packages...
    pip install colorama
)

REM Run the Python script
python monitor_logs.py %*

exit /b 0