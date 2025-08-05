# 4Runr Lead Scraper - Deployment Guide

This guide covers deploying the 4Runr Lead Scraper system for production use.

## 🎯 Pre-Deployment Checklist

### System Requirements
- [ ] Python 3.8+ installed
- [ ] SerpAPI account with active API key
- [ ] Airtable account and API access (optional)
- [ ] Sufficient disk space (1GB+ recommended)
- [ ] Outbound HTTPS access for APIs

### Configuration
- [ ] `.env` file configured with production API keys
- [ ] Database path accessible and writable
- [ ] Log directory permissions set correctly
- [ ] Backup directory configured

### Testing
- [ ] Run `python test_complete_system.py` - all tests pass
- [ ] Verify API connectivity with test scrape
- [ ] Confirm database operations work
- [ ] Test integration with other 4Runr systems

## 🚀 Deployment Steps

### 1. Environment Setup

```bash
# Navigate to deployment directory
cd /path/to/4runr-lead-scraper

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy and configure environment
cp .env.example .env

# Edit with production values
nano .env
```

**Production .env example:**
```env
# API Keys (REQUIRED)
SERPAPI_API_KEY=your_production_serpapi_key
AIRTABLE_API_KEY=your_production_airtable_key
AIRTABLE_BASE_ID=your_production_base_id
AIRTABLE_TABLE_NAME=Leads

# Database Configuration
LEAD_DATABASE_PATH=data/leads.db
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_RETENTION_DAYS=30

# Logging
LOG_LEVEL=INFO
LOG_DIRECTORY=logs

# Performance
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=1
RATE_LIMIT_DELAY=60

# Email Enrichment
EMAIL_FINDER_TIMEOUT=30
MAX_ENRICHMENT_RETRIES=3
```

### 3. Database Initialization

```bash
# Test database connectivity
python -c "
import sqlite3
conn = sqlite3.connect('data/leads.db')
print('Database connection successful')
conn.close()
"

# Run system validation
python test_complete_system.py
```

### 4. Data Migration (if applicable)

```bash
# If migrating from old systems
python scripts/migrate_data.py --discover
python scripts/migrate_data.py --migrate

# Verify migration
python run_cli.py stats
```

### 5. Daily Automation Setup

#### Linux/Mac (cron)
```bash
# Edit crontab
crontab -e

# Add daily automation (runs at 9 AM)
0 9 * * * cd /path/to/4runr-lead-scraper && /path/to/venv/bin/python scripts/daily_scraper.py >> logs/cron.log 2>&1

# Add weekly database maintenance (runs Sunday at 2 AM)
0 2 * * 0 cd /path/to/4runr-lead-scraper && /path/to/venv/bin/python run_cli.py db --vacuum >> logs/maintenance.log 2>&1
```

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:00 AM
4. Set action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `scripts/daily_scraper.py`
   - Start in: `C:\path\to\4runr-lead-scraper`

### 6. Log Rotation Setup

#### Linux/Mac (logrotate)
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/4runr-lead-scraper

# Add configuration
/path/to/4runr-lead-scraper/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 user group
}
```

#### Windows (PowerShell script)
```powershell
# Create log rotation script
# Save as rotate_logs.ps1
$LogPath = "C:\path\to\4runr-lead-scraper\logs"
$MaxAge = 30

Get-ChildItem $LogPath -Filter "*.log" | 
Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-$MaxAge)} |
Remove-Item -Force
```

## 🔧 Production Configuration

### Performance Tuning

**High Volume (1000+ leads/day):**
```env
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=0.5
DATABASE_BACKUP_ENABLED=true
LOG_LEVEL=WARNING
```

**Conservative (100-500 leads/day):**
```env
MAX_CONCURRENT_REQUESTS=2
REQUEST_DELAY=2
DATABASE_BACKUP_ENABLED=true
LOG_LEVEL=INFO
```

**Development/Testing:**
```env
MAX_CONCURRENT_REQUESTS=1
REQUEST_DELAY=3
DATABASE_BACKUP_ENABLED=false
LOG_LEVEL=DEBUG
```

### Security Considerations

1. **API Key Protection:**
   ```bash
   # Set restrictive permissions on .env
   chmod 600 .env
   
   # Ensure .env is in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Database Security:**
   ```bash
   # Set appropriate database permissions
   chmod 644 data/leads.db
   
   # Restrict directory access
   chmod 755 data/
   ```

3. **Log Security:**
   ```bash
   # Ensure logs don't contain sensitive data
   # Review log output regularly
   tail -f logs/scraper.log
   ```

## 📊 Monitoring and Maintenance

### Health Checks

**Daily Health Check Script:**
```bash
#!/bin/bash
# save as health_check.sh

cd /path/to/4runr-lead-scraper

# Check system health
python test_complete_system.py > /tmp/health_check.log 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): System healthy" >> logs/health.log
else
    echo "$(date): System issues detected" >> logs/health.log
    # Send alert (email, Slack, etc.)
fi
```

**Add to cron:**
```bash
# Run health check every 6 hours
0 */6 * * * /path/to/health_check.sh
```

### Performance Monitoring

**Key Metrics to Monitor:**
- Database size growth
- API usage and rate limits
- Scraping success rates
- Enrichment success rates
- Sync success rates
- System response times

**Monitoring Commands:**
```bash
# Database statistics
python run_cli.py stats --detailed

# Check API usage
grep "API" logs/scraper.log | tail -20

# Monitor database size
du -h data/leads.db

# Check recent errors
grep "ERROR" logs/*.log | tail -10
```

### Backup Strategy

**Automated Backups:**
```bash
#!/bin/bash
# save as backup.sh

BACKUP_DIR="/path/to/backups"
DB_PATH="/path/to/4runr-lead-scraper/data/leads.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
cp "$DB_PATH" "$BACKUP_DIR/leads_backup_$DATE.db"

# Compress backup
gzip "$BACKUP_DIR/leads_backup_$DATE.db"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "leads_backup_*.db.gz" -mtime +30 -delete

echo "$(date): Backup completed - leads_backup_$DATE.db.gz"
```

**Add to cron (daily at 3 AM):**
```bash
0 3 * * * /path/to/backup.sh >> logs/backup.log 2>&1
```

## 🚨 Troubleshooting

### Common Deployment Issues

**1. Import Errors:**
```bash
# Solution: Fix Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or use absolute imports in code
```

**2. Permission Denied:**
```bash
# Solution: Fix file permissions
chmod +x scripts/*.py
chmod 755 data/
chmod 644 data/leads.db
```

**3. API Rate Limits:**
```bash
# Solution: Adjust rate limiting
# Edit .env:
REQUEST_DELAY=2
MAX_CONCURRENT_REQUESTS=2
```

**4. Database Locked:**
```bash
# Solution: Check for running processes
ps aux | grep python | grep 4runr
# Kill processes if necessary
```

### Emergency Procedures

**System Recovery:**
```bash
# 1. Stop all processes
pkill -f "4runr-lead-scraper"

# 2. Restore from backup
cp backups/latest_backup.db data/leads.db

# 3. Run system test
python test_complete_system.py

# 4. Restart automation
# (cron will restart automatically)
```

**Data Corruption Recovery:**
```bash
# 1. Stop system
pkill -f "4runr-lead-scraper"

# 2. Check database integrity
sqlite3 data/leads.db "PRAGMA integrity_check;"

# 3. If corrupted, restore from backup
cp backups/leads_backup_YYYYMMDD_HHMMSS.db data/leads.db

# 4. Verify restoration
python run_cli.py stats
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Run multiple instances with different search queries
- Use separate databases for different regions/markets
- Implement queue-based processing for high volume

### Vertical Scaling
- Increase `MAX_CONCURRENT_REQUESTS` gradually
- Monitor API rate limits and system resources
- Consider SSD storage for better database performance

### Integration Scaling
- Use database connection pooling for high-traffic integrations
- Implement caching for frequently accessed data
- Consider read replicas for analytics workloads

## ✅ Post-Deployment Validation

### Validation Checklist
- [ ] System health check passes
- [ ] Daily automation runs successfully
- [ ] API connectivity confirmed
- [ ] Database operations working
- [ ] Backups being created
- [ ] Logs being written correctly
- [ ] Integration with other systems working
- [ ] Performance metrics within acceptable ranges

### Success Criteria
- **Uptime**: >99% system availability
- **Data Quality**: >95% successful enrichment rate
- **Performance**: <30 seconds average response time
- **Reliability**: <1% data loss rate
- **Integration**: All connected systems functioning

## 📞 Support and Maintenance

### Regular Maintenance Tasks
- **Weekly**: Review logs for errors and performance issues
- **Monthly**: Analyze database growth and optimize if needed
- **Quarterly**: Review and update API keys and configurations
- **Annually**: Full system audit and security review

### Support Contacts
- **System Issues**: Check logs and run diagnostics
- **API Issues**: Contact SerpAPI/Airtable support
- **Data Issues**: Review migration logs and database integrity

This deployment guide ensures a robust, production-ready installation of the 4Runr Lead Scraper system.