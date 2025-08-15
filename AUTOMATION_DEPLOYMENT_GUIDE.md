# 🚀 AUTOMATION DEPLOYMENT GUIDE

## Overview
This guide shows you how to set up daily automation for your 4Runr Lead Generation System.

## Files Created
- `daily_automation.py` - Main automation script
- `daily_cron.sh` - Linux cron job script
- `4runr-daily.service` - Linux systemd service
- `4runr-daily.timer` - Linux systemd timer
- `daily_automation.bat` - Windows batch script
- `daily_automation.ps1` - Windows PowerShell script
- `health_check.py` - System health check
- `status_report.py` - Status report generator

## 🐧 Linux/Ubuntu Setup

### Option 1: Cron Job (Recommended)
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9:00 AM
0 9 * * * /home/ubuntu/4Runr-AI-Lead-System/daily_cron.sh
```

### Option 2: Systemd Timer
```bash
# Copy service and timer files
sudo cp 4runr-daily.service /etc/systemd/system/
sudo cp 4runr-daily.timer /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable 4runr-daily.timer
sudo systemctl start 4runr-daily.timer

# Check status
sudo systemctl status 4runr-daily.timer
```

## 🪟 Windows Setup

### Option 1: Task Scheduler (Recommended)
1. Open Task Scheduler
2. Create Basic Task
3. Name: "4Runr Daily Automation"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
6. Program: `C:\Users\kyanb\4Runr AI Lead System\daily_automation.bat`

### Option 2: PowerShell
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "C:\Users\kyanb\4Runr AI Lead System\daily_automation.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -TaskName "4Runr Daily Automation" -Action $action -Trigger $trigger
```

## 📊 Monitoring

### Health Check
```bash
python health_check.py
```

### Status Report
```bash
python status_report.py
```

### Manual Run
```bash
python daily_automation.py
```

## 🔧 Troubleshooting

### Check Logs
- Daily logs: `logs/daily_automation_YYYYMMDD.log`
- Health reports: `logs/health_report_YYYYMMDD.json`
- Results: `logs/daily_results_YYYYMMDD.json`

### Common Issues
1. **Permission denied**: Make scripts executable (`chmod +x *.sh`)
2. **Python not found**: Ensure virtual environment is activated
3. **Database errors**: Check database file permissions
4. **API errors**: Verify API keys in .env file

### Manual Testing
```bash
# Test the automation script
python daily_automation.py

# Check system health
python health_check.py

# Generate status report
python status_report.py
```

## 🎯 Expected Results
- **Daily**: 5 new leads scraped
- **Enrichment**: Emails found for 70%+ of leads
- **AI Messages**: Generated for all leads with emails
- **Airtable Sync**: All leads synced successfully
- **Health**: System running smoothly with no errors

## 📞 Support
If automation fails:
1. Check logs in `logs/` directory
2. Run `python health_check.py`
3. Verify API keys and database access
4. Test manually with `python daily_automation.py`
