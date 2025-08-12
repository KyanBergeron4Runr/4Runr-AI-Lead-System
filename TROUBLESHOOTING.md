# 🔧 Troubleshooting Guide

## Quick Diagnostics

### System Health Check
```bash
# Run comprehensive system check
python check_live_system.py

# Check service status
sudo systemctl status 4runr-automation
sudo systemctl status 4runr-sync
sudo systemctl status 4runr-enricher

# Check logs
tail -f logs/daily_sync.log
tail -f logs/backup_recovery.log
```

## 🚨 Common Issues

### 1. Database Connection Errors

#### Symptoms
- `sqlite3.OperationalError: database is locked`
- `db_path is required for first connection pool initialization`
- Connection timeouts

#### Solutions
```bash
# Check database file permissions
ls -la data/leads_cache.db
sudo chown ubuntu:ubuntu data/leads_cache.db

# Check for long-running processes
ps aux | grep python

# Kill stuck processes
sudo pkill -f "automation_engine.py"

# Restart services
sudo systemctl restart 4runr-automation
```

#### Database Recovery
```bash
# Check database integrity
sqlite3 data/leads_cache.db "PRAGMA integrity_check;"

# Repair database if needed
sqlite3 data/leads_cache.db ".recover" > recovered_database.sql
sqlite3 data/leads_cache_new.db < recovered_database.sql
```

### 2. API Rate Limiting

#### Symptoms
- `429 Too Many Requests` errors
- Slow API responses
- Failed enrichment operations

#### Solutions
```bash
# Check API usage in logs
grep -i "rate limit" logs/*.log

# Adjust rate limiting in .env
RATE_LIMIT_DELAY=3
OPENAI_MAX_TOKENS=1000
AIRTABLE_SYNC_INTERVAL_MINUTES=60
```

#### API Key Issues
```bash
# Test API keys
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Test OpenAI
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
try:
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'test'}],
        max_tokens=5
    )
    print('✅ OpenAI API working')
except Exception as e:
    print(f'❌ OpenAI API error: {e}')

# Test Airtable
import requests
headers = {'Authorization': f'Bearer {os.getenv(\"AIRTABLE_API_KEY\")}'}
response = requests.get(f'https://api.airtable.com/v0/{os.getenv(\"AIRTABLE_BASE_ID\")}/{os.getenv(\"AIRTABLE_TABLE_NAME\")}', headers=headers)
print(f'Airtable API: {response.status_code}')
"
```

### 3. Memory Issues

#### Symptoms
- `MemoryError` exceptions
- System becoming unresponsive
- High swap usage

#### Solutions
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Reduce batch sizes in .env
BATCH_SIZE=10
CONCURRENT_LIMIT=2
LEAD_DATABASE_MAX_CONNECTIONS=5

# Restart services to clear memory
sudo systemctl restart 4runr-automation
```

#### Memory Optimization
```python
# Add to automation_engine.py
import gc
import psutil

def check_memory_usage():
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 85:
        gc.collect()  # Force garbage collection
        return True
    return False
```

### 4. Service Not Starting

#### Symptoms
- Services fail to start
- `systemctl status` shows failed state
- No log output

#### Solutions
```bash
# Check service logs
sudo journalctl -u 4runr-automation -f
sudo journalctl -u 4runr-sync -f

# Check file permissions
ls -la automation_engine.py
chmod +x automation_engine.py

# Check Python path in service file
sudo cat /etc/systemd/system/4runr-automation.service

# Reload systemd configuration
sudo systemctl daemon-reload
sudo systemctl restart 4runr-automation
```

#### Service Configuration Issues
```bash
# Recreate service file
sudo tee /etc/systemd/system/4runr-automation.service > /dev/null <<EOF
[Unit]
Description=4Runr Lead Automation Engine
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/4Runr-AI-Lead-System/4runr-outreach-system
Environment=PATH=/home/ubuntu/4Runr-AI-Lead-System/4runr-outreach-system/venv/bin
ExecStart=/home/ubuntu/4Runr-AI-Lead-System/4runr-outreach-system/venv/bin/python automation_engine.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable 4runr-automation
sudo systemctl start 4runr-automation
```

### 5. Data Sync Issues

#### Symptoms
- Airtable sync failing
- Missing leads in database
- Duplicate entries

#### Solutions
```bash
# Manual sync test
python sync_airtable_to_db.py

# Check Airtable connection
python test_airtable_connection.py

# Check for duplicates
sqlite3 data/leads_cache.db "SELECT email, COUNT(*) FROM leads GROUP BY email HAVING COUNT(*) > 1;"

# Remove duplicates
sqlite3 data/leads_cache.db "DELETE FROM leads WHERE rowid NOT IN (SELECT MIN(rowid) FROM leads GROUP BY email);"
```

### 6. Data Cleaning Failures

#### Symptoms
- `'DataCleaner' object has no attribute 'clean_lead_data'`
- Cleaning results in errors
- Invalid cleaned data

#### Solutions
```bash
# Test data cleaner
python -c "
from shared.data_cleaner import DataCleaner
cleaner = DataCleaner()
print('Available methods:', [m for m in dir(cleaner) if not m.startswith('_')])

# Test cleaning
test_data = {'name': 'Test', 'email': 'test@example.com'}
context = {'source': 'test', 'campaign': 'test', 'priority': 'normal'}
result = cleaner.clean_and_validate(test_data, context)
print('Cleaning result type:', type(result))
"

# Check configuration files
ls -la shared/data_cleaner_config/
cat shared/data_cleaner_config/cleaning_rules.yaml | head -20
```

### 7. Monitoring Dashboard Issues

#### Symptoms
- Dashboard not accessible
- Missing metrics
- Slow loading

#### Solutions
```bash
# Check if dashboard is running
ps aux | grep monitoring_dashboard

# Start dashboard
python monitoring_dashboard.py &

# Check port availability
netstat -tlnp | grep 8080

# Access dashboard
curl http://localhost:8080/health
```

## 🔍 Diagnostic Commands

### System Information
```bash
# System resources
df -h
free -h
uptime
ps aux --sort=-%cpu | head -10

# Network connectivity
ping -c 3 api.airtable.com
ping -c 3 api.openai.com

# Service status
systemctl list-units --failed
systemctl list-timers
```

### Database Diagnostics
```bash
# Database size and stats
ls -lh data/leads_cache.db
sqlite3 data/leads_cache.db "SELECT COUNT(*) as total_leads FROM leads;"
sqlite3 data/leads_cache.db "SELECT engagement_stage, COUNT(*) FROM leads GROUP BY engagement_stage;"

# Database performance
sqlite3 data/leads_cache.db "PRAGMA compile_options;"
sqlite3 data/leads_cache.db "PRAGMA cache_size;"
sqlite3 data/leads_cache.db "PRAGMA journal_mode;"
```

### Log Analysis
```bash
# Recent errors
grep -i error logs/*.log | tail -20
grep -i failed logs/*.log | tail -20

# API calls
grep -i "api" logs/*.log | tail -20

# Performance metrics
grep -i "processing time" logs/*.log | tail -10
```

## 🛠️ Recovery Procedures

### Emergency Recovery
```bash
# Stop all services
sudo systemctl stop 4runr-automation
sudo systemctl stop 4runr-sync
sudo systemctl stop 4runr-enricher

# Backup current state
python backup_recovery.py backup

# Check system health
python check_live_system.py

# Restart services one by one
sudo systemctl start 4runr-automation
sleep 30
sudo systemctl start 4runr-sync
sleep 30
sudo systemctl start 4runr-enricher
```

### Database Recovery
```bash
# Create backup before recovery
cp data/leads_cache.db data/leads_cache_backup_$(date +%Y%m%d_%H%M%S).db

# Restore from backup
python backup_recovery.py restore --file backups/4runr_full_backup_YYYYMMDD_HHMMSS.tar.gz

# Verify restoration
python check_live_system.py
```

### Configuration Reset
```bash
# Backup current config
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)

# Reset to defaults
cp .env.example .env

# Edit with correct values
nano .env

# Restart services
sudo systemctl restart 4runr-automation
```

## 📊 Performance Issues

### High CPU Usage
```bash
# Identify CPU-intensive processes
top -p $(pgrep -d',' python)

# Reduce concurrent operations
# Edit .env:
CONCURRENT_LIMIT=2
BATCH_SIZE=10

# Restart services
sudo systemctl restart 4runr-automation
```

### High Memory Usage
```bash
# Check memory usage by process
ps aux --sort=-%mem | head -10

# Clear system cache
sudo sync && sudo sysctl vm.drop_caches=3

# Reduce memory usage in .env:
LEAD_DATABASE_MAX_CONNECTIONS=5
LEAD_DATABASE_CACHE_SIZE=-32000
```

### Disk Space Issues
```bash
# Check disk usage
df -h
du -sh logs/
du -sh database_logs/
du -sh backups/

# Clean up old logs
find logs/ -name "*.log" -mtime +30 -delete
find database_logs/ -name "*.json" -mtime +7 -delete

# Clean up old backups
python backup_recovery.py cleanup --keep-days 14
```

## 🚨 Emergency Contacts

### Critical System Failure
1. Stop all services immediately
2. Create emergency backup
3. Check system logs for root cause
4. Contact system administrator

### Data Loss Prevention
1. Never delete database files without backup
2. Always test recovery procedures
3. Monitor backup integrity regularly
4. Keep multiple backup copies

## 📋 Maintenance Checklist

### Daily
- [ ] Check service status
- [ ] Review error logs
- [ ] Verify sync operations
- [ ] Monitor system resources

### Weekly
- [ ] Run full system backup
- [ ] Clean up old logs
- [ ] Check database integrity
- [ ] Review performance metrics

### Monthly
- [ ] Update system packages
- [ ] Review and optimize configuration
- [ ] Test recovery procedures
- [ ] Archive old backups

## 🔧 Advanced Troubleshooting

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with verbose output
python automation_engine.py --debug

# Check detailed logs
tail -f logs/debug.log
```

### Network Issues
```bash
# Test external connectivity
curl -I https://api.airtable.com
curl -I https://api.openai.com

# Check DNS resolution
nslookup api.airtable.com
nslookup api.openai.com

# Test with different DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf.backup
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/4Runr-AI-Lead-System/
chmod +x *.py
chmod +x *.sh

# Fix service permissions
sudo chown root:root /etc/systemd/system/4runr-*.service
sudo chmod 644 /etc/systemd/system/4runr-*.service
```

---

*If issues persist after following this guide, create a system backup and contact technical support with the backup file and relevant log files.*