@echo off
REM 4Runr AI Lead System - Daily Sync Script for Windows

cd /d "%~dp0"
echo %date% %time%: Starting daily sync >> logs\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

REM Run daily scraper
python 4runr-lead-scraper\scripts\daily_scraper.py --max-leads 5 >> logs\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1

REM Run enricher agent
python 4runr-outreach-system\daily_enricher_agent_updated.py --max-leads 20 >> logs\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1

REM Run message generator
python 4runr-outreach-system\message_generator\app.py --limit 20 >> logs\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1

echo %date% %time%: Daily sync completed >> logs\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log
