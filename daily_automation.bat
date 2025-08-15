@echo off
REM Daily Lead Generation for Windows
REM Run this script with Windows Task Scheduler

cd /d "C:\Users\kyanb\4Runr AI Lead System"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run daily automation
python daily_automation.py

REM Log completion
echo %date% %time%: Daily automation completed >> logs\windows_cron.log

pause
