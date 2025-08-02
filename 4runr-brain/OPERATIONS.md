# 🛠️ Campaign Brain Operations Guide

Complete operational guide for daily management, monitoring, and maintenance of the Campaign Brain production system.

## 📅 Daily Operations

### Automated Daily Processing

The Campaign Brain runs automatically every morning at 8:00 AM via cron job:

```bash
# Check if daily processing is set up
./monitor_daily_batch.sh

# Manual daily run (if needed)
python daily_batch_processor.py --batch-size 20

# Dry run for testing
python daily_batch_processor.py --batch-size 5 --dry-run
```

### Daily Checklist

**Morning (9:00 AM):**
- [ ] Check daily batch completion: `./monitor_daily_batch.sh`
- [ ] Review processing statistics
- [ ] Check for error notifications
- [ ] Verify Airtable updates

**Evening (6:00 PM):**
- [ ] Review approval rates and quality scores
- [ ] Check trace logs for optimization opportunities
- [ ] Monitor system health: `./health_check.sh`

## 🔍 Monitoring and Alerts

### Health Monitoring

```bash
# Service health check
python serve_campaign_brain.py --health-check

# Service statistics
python serve_campaign_brain.py --stats

# Docker service status (if using Docker)
python deploy.py status
```

### Log Monitoring

```bash
# View daily batch logs
tail -f logs/daily/daily_batch_$(date +%Y%m%d).log

# View service logs
tail -f logs/campaign_brain_service.log

# View error logs
ls -la logs/errors/

# Docker logs (if using Docker)
python deploy.py logs --follow
```

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Approval Rate | 80%+ | < 70% |
| Error Rate | < 5% | > 10% |
| Processing Time | < 60s/lead | > 120s/lead |
| Quality Score | 85+ average | < 80 average |
| Service Uptime | 99.5%+ | < 99% |

## 🚨 Error Handling and Recovery

### Common Issues and Solutions

**High Error Rate (>10%):**
```bash
# Check recent errors
ls -la logs/errors/

# Review failed leads
python qa_validator.py --batch-size 3 --verbose

# Check API connectivity
python serve_campaign_brain.py --health-check
```

**Low Approval Rate (<70%):**
```bash
# Review quality threshold
echo $CAMPAIGN_QUALITY_THRESHOLD

# Test with sample leads
python serve_campaign_brain.py --lead-id sample_lead --dry-run --verbose

# Check trait detection accuracy
python qa_validator.py --quick
```

**Service Not Responding:**
```bash
# Docker deployment
python deploy.py restart

# Standalone deployment
pkill -f serve_campaign_brain
python serve_campaign_brain.py --batch-size 10
```

**Airtable Sync Issues:**
```bash
# Test Airtable connection
python -c "from shared.airtable_client import get_airtable_client; print(get_airtable_client().get_leads_for_message_generation(1))"

# Check API key and permissions
grep AIRTABLE_API_KEY .env
```

### Error Recovery Procedures

**1. Service Recovery:**
```bash
# Stop all processes
python deploy.py stop

# Check system resources
df -h  # Disk space
free -h  # Memory
ps aux | grep campaign  # Running processes

# Restart services
python deploy.py deploy
```

**2. Data Recovery:**
```bash
# Backup current state
python deploy.py backup

# Check trace logs for last successful run
ls -la trace_logs/ | tail -10

# Restore from backup if needed
cp -r backup_YYYYMMDD_HHMMSS/* ./
```

**3. Queue Recovery:**
```bash
# Check queue status
ls -la queue/

# Reprocess failed campaigns
python serve_campaign_brain.py --batch-size 5 --dry-run

# Clear stuck queue items (if needed)
rm queue/campaign_*.json
```

## 📊 Performance Optimization

### Configuration Tuning

**High-Volume Processing:**
```bash
# .env settings for high throughput
CAMPAIGN_QUALITY_THRESHOLD=75.0
CAMPAIGN_MAX_RETRIES=1
CONCURRENT_LIMIT=5
DAILY_BATCH_SIZE=50
```

**High-Quality Processing:**
```bash
# .env settings for maximum quality
CAMPAIGN_QUALITY_THRESHOLD=85.0
CAMPAIGN_MAX_RETRIES=3
CONCURRENT_LIMIT=2
DAILY_BATCH_SIZE=20
```

### Performance Monitoring

```bash
# Check processing speed
grep "execution_time" trace_logs/*.json | tail -10

# Monitor resource usage
top -p $(pgrep -f serve_campaign_brain)

# Check API usage and costs
grep "openai" logs/campaign_brain_service.log | tail -20
```

### Optimization Strategies

1. **Batch Size Optimization:**
   - Start with 10-20 leads per batch
   - Increase gradually based on performance
   - Monitor memory usage and API rate limits

2. **Quality Threshold Tuning:**
   - Monitor approval rates over time
   - Adjust threshold based on business requirements
   - Balance quality vs. throughput

3. **Concurrent Processing:**
   - Limit based on OpenAI rate limits
   - Monitor for API errors and timeouts
   - Adjust based on system resources

## 🔧 Maintenance Tasks

### Weekly Maintenance

**Every Monday:**
```bash
# Review weekly statistics
find logs/daily_results -name "*.json" -mtime -7 | xargs grep -l "approval_rate"

# Check log disk usage
du -sh logs/

# Rotate logs if needed
./rotate_logs.sh

# Update dependencies (if needed)
pip install -r requirements.txt --upgrade
```

### Monthly Maintenance

**First Monday of Month:**
```bash
# Comprehensive QA testing
python qa_validator.py --batch-size 10

# Performance analysis
python -c "
import json
from pathlib import Path
files = list(Path('logs/daily_results').glob('*.json'))
data = [json.load(open(f)) for f in files[-30:]]  # Last 30 days
avg_approval = sum(d['statistics']['approval_rate'] for d in data) / len(data)
print(f'30-day average approval rate: {avg_approval:.1f}%')
"

# Backup critical data
python deploy.py backup

# Review and clean old backups
find . -name "backup_*" -mtime +90 -exec rm -rf {} \;
```

### Quarterly Maintenance

**Every 3 Months:**
```bash
# Full system audit
python qa_validator.py --verbose

# Review and optimize prompts
ls -la prompts/
# Manually review prompt performance in trace logs

# Update documentation
# Review and update this operations guide

# Security audit
# Review API keys and access permissions
# Update dependencies for security patches
```

## 📈 Analytics and Reporting

### Daily Reports

```bash
# Generate daily summary
python daily_batch_processor.py --report-only

# View processing trends
tail -20 logs/daily_results/daily_results_$(date +%Y%m%d).json
```

### Weekly Reports

```bash
# Weekly performance summary
find logs/daily_results -name "*.json" -mtime -7 | while read file; do
    echo "$(basename $file): $(jq '.statistics.approval_rate' $file)% approval"
done
```

### Monthly Analytics

```bash
# Monthly trend analysis
python -c "
import json
from pathlib import Path
from datetime import datetime, timedelta

# Get last 30 days of data
files = list(Path('logs/daily_results').glob('*.json'))
recent_files = [f for f in files if f.stat().st_mtime > (datetime.now() - timedelta(days=30)).timestamp()]

data = []
for f in recent_files:
    try:
        with open(f) as file:
            data.append(json.load(file))
    except:
        continue

if data:
    avg_approval = sum(d['statistics']['approval_rate'] for d in data) / len(data)
    avg_quality = sum(d['batch_result']['stats']['approval_rate'] for d in data if 'batch_result' in d and 'stats' in d['batch_result']) / len(data)
    total_processed = sum(d['statistics']['processed'] for d in data)
    
    print(f'📊 30-Day Analytics:')
    print(f'  Average Approval Rate: {avg_approval:.1f}%')
    print(f'  Total Leads Processed: {total_processed}')
    print(f'  Days with Data: {len(data)}')
else:
    print('No data available for analysis')
"
```

## 🔐 Security and Compliance

### Security Checklist

**Monthly Security Review:**
- [ ] Rotate OpenAI API keys
- [ ] Review Airtable access permissions
- [ ] Check for unauthorized access in logs
- [ ] Update system dependencies
- [ ] Review Docker container security (if applicable)

### Data Protection

```bash
# Encrypt sensitive logs
find logs/ -name "*.json" -exec gpg --cipher-algo AES256 --compress-algo 1 --symmetric {} \;

# Secure backup
tar -czf campaign_brain_backup_$(date +%Y%m%d).tar.gz logs/ trace_logs/ queue/
gpg --cipher-algo AES256 --compress-algo 1 --symmetric campaign_brain_backup_$(date +%Y%m%d).tar.gz
```

### Compliance Monitoring

```bash
# Check data retention compliance
find trace_logs/ -name "*.json" -mtime +90  # Should be cleaned up
find logs/ -name "*.log" -mtime +30         # Should be rotated

# Audit trail verification
grep -r "lead_id" logs/daily_results/ | wc -l  # Count processed leads
```

## 🚀 Scaling and Growth

### Horizontal Scaling

**Multiple Instance Setup:**
```bash
# Run multiple instances with different batch sizes
python serve_campaign_brain.py --batch-size 10 &
python serve_campaign_brain.py --batch-size 10 &

# Load balance with different time schedules
# Instance 1: 8:00 AM
# Instance 2: 10:00 AM
# Instance 3: 2:00 PM
```

### Vertical Scaling

**Resource Optimization:**
```bash
# Monitor resource usage
htop
iotop
nethogs

# Optimize Docker resources (if using Docker)
docker stats campaign-brain-service
```

### Performance Scaling

**Configuration for High Volume:**
```bash
# High-performance settings
export CONCURRENT_LIMIT=10
export DAILY_BATCH_SIZE=100
export CAMPAIGN_QUALITY_THRESHOLD=75.0
export OPENAI_MAX_TOKENS=300  # Reduce for speed
```

## 📞 Support and Escalation

### Support Contacts

**Internal Team:**
- Campaign Brain Developer: [Your contact]
- System Administrator: [Your contact]
- Business Owner: [Your contact]

**External Vendors:**
- OpenAI Support: [If needed for API issues]
- Airtable Support: [If needed for integration issues]

### Escalation Procedures

**Level 1 - Operational Issues:**
- Error rate > 10%
- Approval rate < 70%
- Service downtime > 1 hour

**Level 2 - Business Impact:**
- Service downtime > 4 hours
- Data loss or corruption
- Security breach

**Level 3 - Critical Issues:**
- Complete system failure
- Data breach with PII exposure
- Regulatory compliance issues

### Emergency Procedures

**Service Outage:**
1. Check service health: `./health_check.sh`
2. Review recent logs for errors
3. Restart services: `python deploy.py restart`
4. If still failing, contact development team
5. Document incident and resolution

**Data Issues:**
1. Stop processing immediately
2. Backup current state: `python deploy.py backup`
3. Identify scope of issue
4. Contact development team
5. Implement recovery plan

---

## 📋 Quick Reference

### Essential Commands
```bash
# Daily operations
./monitor_daily_batch.sh          # Check daily status
python serve_campaign_brain.py --health-check  # Health check
python deploy.py status           # Service status

# Processing
python serve_campaign_brain.py --batch-size 10  # Manual batch
python daily_batch_processor.py --dry-run       # Test run

# Monitoring
tail -f logs/campaign_brain_service.log  # Live logs
python qa_validator.py --quick           # Quick QA test

# Maintenance
python deploy.py restart          # Restart services
./rotate_logs.sh                  # Rotate logs
python deploy.py backup           # Backup data
```

### Configuration Files
- `.env` - Environment configuration
- `docker-compose.yml` - Docker services
- `prompts/*.j2` - Message templates
- `logs/` - All log files
- `trace_logs/` - Execution traces

### Key Metrics
- **Approval Rate**: 80%+ target
- **Quality Score**: 85+ average
- **Processing Time**: <60s per lead
- **Error Rate**: <5%
- **Uptime**: 99.5%+

This operations guide ensures reliable, scalable, and maintainable operation of the Campaign Brain system in production.