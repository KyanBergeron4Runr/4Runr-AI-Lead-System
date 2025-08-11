# EC2 Deployment Guide for Lead Database System with Concurrent Access Safety

This guide walks you through deploying the complete lead database system with concurrent access safety features to your EC2 instance.

## 🚀 Quick Start

### 1. Check Current EC2 Status

First, let's see what's already deployed on your EC2 instance:

```bash
python check_ec2_status.py --host YOUR_EC2_HOST --key ~/.ssh/your-key.pem
```

**Example:**
```bash
python check_ec2_status.py --host ec2-54-123-456-789.compute-1.amazonaws.com --key ~/.ssh/4runr-key.pem
```

This will show you:
- ✅ What's already deployed
- ❌ What's missing
- 🏥 System health status
- 💡 Recommendations for next steps

### 2. Deploy the System

If the status check shows missing components, deploy the complete system:

```bash
python deploy_to_ec2.py --host YOUR_EC2_HOST --key ~/.ssh/your-key.pem
```

**Example:**
```bash
python deploy_to_ec2.py --host ec2-54-123-456-789.compute-1.amazonaws.com --key ~/.ssh/4runr-key.pem
```

### 3. Verify Deployment

After deployment, run the status check again to verify everything is working:

```bash
python check_ec2_status.py --host YOUR_EC2_HOST --key ~/.ssh/your-key.pem
```

## 📋 What Gets Deployed

### Core Concurrent Access Safety Components
- `database_connection_pool.py` - Thread-safe connection pooling
- `concurrent_access_manager.py` - Deadlock detection and operation coordination
- `lead_database.py` - Enhanced database API with thread safety
- `database_logger.py` - Comprehensive operation logging
- `database_config.py` - Configuration management
- `database_backup.py` - Automated backup system
- `database_health.py` - Health monitoring

### Updated Agent Files
- `daily_enricher_agent_updated.py` - Thread-safe enricher agent
- `sync_to_airtable_updated.py` - Thread-safe sync agent
- `scraper_agent_database.py` - Database-integrated scraper

### Test Suite
- `test_concurrent_access_stress.py` - High concurrency stress tests
- `test_thread_safety.py` - Thread safety validation
- `test_concurrent_integration.py` - Integration tests
- `run_concurrent_access_tests.py` - Comprehensive test runner

### System Services
- **4runr-sync** - Systemd service for Airtable synchronization
- **4runr-enricher** - Systemd service for lead enrichment

### Maintenance Tasks
- **Daily backups** - Automated at 2 AM
- **Weekly health checks** - Sundays at 3 AM
- **Monthly cleanup** - 1st of month at 4 AM

## 🔧 Manual Configuration Steps

After deployment, you'll need to configure a few things manually:

### 1. Update Environment Variables

SSH into your EC2 instance and update the `.env` file:

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_EC2_HOST
cd 4runr-outreach-system
nano .env
```

Update these key variables:
```env
# Database Configuration
LEAD_DATABASE_PATH=data/leads_cache.db
LEAD_DATABASE_MAX_CONNECTIONS=20
LEAD_DATABASE_ENABLE_LOGGING=true

# Airtable Configuration
AIRTABLE_API_KEY=your_actual_api_key_here
AIRTABLE_BASE_ID=your_actual_base_id_here
AIRTABLE_TABLE_NAME=your_actual_table_name_here

# Email Configuration (if using)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 2. Start Services

Start the systemd services:

```bash
sudo systemctl start 4runr-sync
sudo systemctl start 4runr-enricher

# Check status
sudo systemctl status 4runr-sync
sudo systemctl status 4runr-enricher
```

### 3. Initialize Database

Run the initial database setup:

```bash
cd 4runr-outreach-system
source venv/bin/activate
python -c "from lead_database import LeadDatabase; db = LeadDatabase(); print('Database initialized!')"
```

## 🧪 Testing the Deployment

### Quick Health Check

```bash
cd 4runr-outreach-system
source venv/bin/activate
python -c "
from lead_database import LeadDatabase
from concurrent_access_manager import get_concurrent_access_manager

db = LeadDatabase()
access_manager = get_concurrent_access_manager(db.db_path)
health = access_manager.health_check()
print(f'System health: {health[\"status\"]}')
"
```

### Run Concurrent Access Tests

Test the concurrent access safety features:

```bash
# Quick thread safety test
python run_concurrent_access_tests.py --test-type thread-safety --quick

# Full test suite (takes longer)
python run_concurrent_access_tests.py --test-type all
```

### Add a Test Lead

```bash
python -c "
from lead_database import LeadDatabase
db = LeadDatabase()
lead_id = db.add_lead({
    'full_name': 'Test User',
    'email': 'test@example.com',
    'company': 'Test Corp',
    'source': 'deployment_test'
})
print(f'Test lead added: {lead_id}')
"
```

## 📊 Monitoring and Maintenance

### Check System Status

```bash
# Database stats
python -c "from lead_database import LeadDatabase; db = LeadDatabase(); print(db.get_database_stats())"

# Connection pool stats
python -c "from database_connection_pool import get_connection_pool; pool = get_connection_pool(); print(pool.get_pool_stats())"

# Concurrent access stats
python -c "from concurrent_access_manager import get_concurrent_access_manager; am = get_concurrent_access_manager(); print(am.get_stats())"
```

### View Logs

```bash
# Service logs
sudo journalctl -u 4runr-sync -f
sudo journalctl -u 4runr-enricher -f

# Application logs
tail -f logs/*.log
tail -f database_logs/database_operations/*.json
```

### Manual Backup

```bash
python -c "from database_backup import create_database_backup; backup = create_database_backup('manual'); print(f'Backup created: {backup.backup_id}')"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Pool Errors
```bash
# Check connection pool health
python -c "from database_connection_pool import get_connection_pool; pool = get_connection_pool(); print(pool.health_check())"

# Reset connection pool
sudo systemctl restart 4runr-sync 4runr-enricher
```

#### 2. Database Lock Issues
```bash
# Check for long-running transactions
python -c "
from concurrent_access_manager import get_concurrent_access_manager
am = get_concurrent_access_manager()
stats = am.get_stats()
print(f'Active operations: {stats[\"active_operations\"]}')
print(f'Deadlocks detected: {stats[\"concurrent_access_stats\"][\"deadlocks_detected\"]}')
"
```

#### 3. Service Won't Start
```bash
# Check service logs
sudo journalctl -u 4runr-sync --no-pager -l

# Check file permissions
ls -la 4runr-outreach-system/
sudo chown -R ubuntu:ubuntu 4runr-outreach-system/
```

#### 4. High Memory Usage
```bash
# Check system resources
free -h
df -h

# Restart services to clear memory
sudo systemctl restart 4runr-sync 4runr-enricher
```

### Performance Tuning

#### For High Load Environments

Update `.env` with higher limits:
```env
LEAD_DATABASE_MAX_CONNECTIONS=50
LEAD_DATABASE_CACHE_SIZE=-128000
LEAD_DATABASE_CONNECTION_TIMEOUT=60
```

#### For Low Resource Environments

Update `.env` with lower limits:
```env
LEAD_DATABASE_MAX_CONNECTIONS=5
LEAD_DATABASE_CACHE_SIZE=-32000
LEAD_DATABASE_CONNECTION_TIMEOUT=15
```

## 📈 Scaling Considerations

### Horizontal Scaling

To run multiple instances:

1. **Database**: Use a shared database (PostgreSQL/MySQL) instead of SQLite
2. **Load Balancer**: Distribute requests across instances
3. **Shared Storage**: Use EFS or S3 for shared files

### Vertical Scaling

For single instance scaling:

1. **Increase EC2 instance size** (more CPU/RAM)
2. **Optimize database settings** (larger cache, more connections)
3. **Tune concurrent operation limits**

## 🔐 Security Best Practices

### 1. Environment Variables
- Never commit `.env` files to version control
- Use AWS Secrets Manager for sensitive data
- Rotate API keys regularly

### 2. Network Security
- Use security groups to limit access
- Enable VPC for network isolation
- Use SSL/TLS for all external connections

### 3. File Permissions
```bash
chmod 600 .env
chmod 700 data/
chmod 700 database_logs/
```

### 4. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## 📞 Support

If you encounter issues:

1. **Check the logs** first (service logs and application logs)
2. **Run the health check** to identify specific problems
3. **Review the troubleshooting section** above
4. **Check system resources** (CPU, memory, disk space)
5. **Restart services** as a first troubleshooting step

## 🎯 Next Steps

After successful deployment:

1. **Configure your specific data sources** (scrapers, enrichers)
2. **Set up monitoring dashboards** (optional)
3. **Configure alerting** for critical issues
4. **Plan regular maintenance windows**
5. **Document your specific configuration** for your team

---

**Deployment completed successfully!** 🎉

Your lead database system with concurrent access safety is now running on EC2 with enterprise-grade reliability and performance.