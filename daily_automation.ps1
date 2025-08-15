# Daily Lead Generation PowerShell Script
# Run this with Windows Task Scheduler

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Activate virtual environment
& ".venv\Scripts\Activate.ps1"

# Run daily automation
python daily_automation.py

# Log completion
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$timestamp : Daily automation completed" | Out-File -FilePath "logs\powershell_cron.log" -Append
