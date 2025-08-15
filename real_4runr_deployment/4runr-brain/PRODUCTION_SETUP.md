# 🚀 Campaign Brain Production Setup

Complete guide for deploying the LangGraph Campaign Brain as a production service integrated with the 4Runr Outreach System.

## 📋 Prerequisites

### System Requirements
- **Docker** and **Docker Compose** installed
- **Python 3.11+** (if running without Docker)
- **Redis** (for memory storage - included in Docker setup)
- **OpenAI API Key** with GPT-4o access
- **Airtable API Key** (for 4Runr integration)

### Environment Setup
```bash
# Clone or navigate to the campaign brain directory
cd 4runr-brain

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### Required Configuration
```bash
# Essential settings in .env
OPENAI_API_KEY=your-actual-openai-api-key
AIRTABLE_API_KEY=your-airtable-api-key
AIRTABLE_BASE_ID=your-base-id
AIRTABLE_TABLE_NAME=Table 1

# Optional tuning
CAMPAIGN_QUALITY_THRESHOLD=80.0
CAMPAIGN_MAX_RETRIES=2
LOG_LEVEL=INFO
```

## 🐳 Docker Deployment (Recommended)

### Quick Start
```bash
# Check prerequisites
python deploy.py deploy --mode production

# This will:
# ✅ Validate configuration
# ✅ Build Docker images
# ✅ Start services (Campaign Brain + Redis)
# ✅ Run health checks
# ✅ Show service status
```

### Manual Docker Setup
```bash
# Build and start services
docker-compose up -d --build

# Check health
docker-compose exec campaign-brain python serve_campaign_brain.py --health-check

# View logs
docker-compose logs -f campaign-brain
```

## 🔧 Standalone Installation

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Service
```bash
# Process batch of leads
python serve_campaign_brain.py --batch-size 10

# Process specific lead
python serve_campaign_brain.py --lead-id rec123456789

# Dry run (no injection)
python serve_campaign_brain.py --batch-size 5 --dry-run
```

## 🔗 Integration with 4Runr System

### Airtable Integration
The service automatically integrates with your existing Airtable setup:

**Lead Selection Criteria:**
- Has `Company_Description` (enriched)
- Missing `Custom_Message` (not yet processed)
- `Brain_Status` ≠ 'Processed'

**Fields Updated:**
- `Brain_Status`: 'Processed'
- `Brain_Quality_Score`: Overall quality score
- `Brain_Final_Status`: approved/manual_review/error
- `Detected_Traits`: Top 5 detected traits
- `Messaging_Angle`: Selected messaging strategy
- `Campaign_Tone`: Communication tone
- `Custom_Message`: First generated message
- `Campaign_Injected`: True if successfully queued

### Queue Integration
Approved campaigns are automatically injected into the existing campaign system:
- Uses existing `CampaignInjector` class
- Maintains 3-message sequence (hook → proof → fomo)
- Preserves quality scores and metadata
- Follows existing scheduling logic

## 📊 Monitoring and Management

### Health Checks
```bash
# Check service health
python serve_campaign_brain.py --health-check

# Or via deployment manager
python deploy.py health
```

**Health Check Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-29T14:30:22",
  "config_valid": true,
  "integrations": {
    "airtable": true,
    "campaign_injector": true,
    "openai": true
  },
  "stats": {
    "processed": 45,
    "approved": 38,
    "approval_rate": 84.4
  }
}
```

### Service Statistics
```bash
# Get processing statistics
python serve_campaign_brain.py --stats

# Or via deployment manager
python deploy.py status
```

### Log Management
```bash
# View recent logs
python deploy.py logs --tail 100

# Follow logs in real-time
python deploy.py logs --follow

# Docker logs directly
docker-compose logs -f campaign-brain
```

## 🔄 Production Operations

### Daily Operations
```bash
# Process daily batch
python deploy.py process --batch-size 20

# Check health and status
python deploy.py health
python deploy.py status
```

### Batch Processing
```bash
# Large batch processing
python serve_campaign_brain.py --batch-size 50

# Dry run for testing
python serve_campaign_brain.py --batch-size 10 --dry-run
```

### Service Management
```bash
# Restart service
python deploy.py restart

# Stop service
python deploy.py stop

# Deploy updates
python deploy.py deploy
```

## 📈 Performance Tuning

### Configuration Optimization
```bash
# High-volume processing
CAMPAIGN_QUALITY_THRESHOLD=75.0  # Lower threshold for higher throughput
CAMPAIGN_MAX_RETRIES=1           # Fewer retries for speed
CONCURRENT_LIMIT=5               # More concurrent processing

# High-quality processing
CAMPAIGN_QUALITY_THRESHOLD=85.0  # Higher threshold for quality
CAMPAIGN_MAX_RETRIES=3           # More retries for quality
CONCURRENT_LIMIT=2               # Less concurrent for stability
```

### Scaling Considerations
- **Concurrent Processing**: Adjust `CONCURRENT_LIMIT` based on OpenAI rate limits
- **Batch Size**: Start with 10-20 leads per batch, scale based on performance
- **Quality Threshold**: Balance between quality and throughput
- **Memory Usage**: Monitor Redis memory usage for large-scale deployments

## 🔒 Security and Compliance

### API Key Security
- Store API keys in environment variables only
- Use Docker secrets for production deployments
- Rotate keys regularly
- Monitor API usage and costs

### Data Protection
- All lead data is processed in memory only
- Trace logs contain no sensitive information
- Redis memory is cleared on restart
- Backup procedures for logs and traces

### Access Control
- Restrict Docker container access
- Use non-root user in containers
- Implement network security policies
- Monitor service access logs

## 🚨 Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check configuration
python serve_campaign_brain.py --health-check

# Check Docker logs
docker-compose logs campaign-brain

# Verify environment
cat .env | grep -v "^#"
```

**Low Approval Rates:**
```bash
# Check quality threshold
echo $CAMPAIGN_QUALITY_THRESHOLD

# Review trace logs
ls -la trace_logs/

# Test with dry run
python serve_campaign_brain.py --batch-size 5 --dry-run --verbose
```

**Integration Issues:**
```bash
# Test Airtable connection
python -c "from shared.airtable_client import get_airtable_client; print(get_airtable_client().get_leads_for_message_generation(1))"

# Check campaign injector
python -c "from campaign_system.campaign_injector import CampaignInjector; print('Injector OK')"
```

### Performance Issues
- **Slow Processing**: Reduce batch size, check OpenAI API latency
- **High Memory Usage**: Restart Redis, check for memory leaks
- **Queue Backlog**: Increase concurrent processing, optimize quality threshold

### Error Recovery
```bash
# Restart all services
python deploy.py restart

# Clear Redis memory
docker-compose exec redis redis-cli FLUSHDB

# Backup and clean logs
python deploy.py backup
rm -rf logs/* trace_logs/*
```

## 📊 Monitoring Dashboard

### Key Metrics to Track
- **Processing Rate**: Leads processed per hour
- **Approval Rate**: Percentage of campaigns approved
- **Quality Scores**: Distribution of quality scores
- **Error Rate**: Percentage of processing errors
- **API Usage**: OpenAI API calls and costs
- **Memory Usage**: Redis memory consumption

### Alerting Thresholds
- Approval rate < 70%
- Error rate > 10%
- Processing time > 2 minutes per lead
- Service health check failures

## 🔄 Backup and Recovery

### Automated Backups
```bash
# Create backup
python deploy.py backup

# Backup includes:
# - All trace logs
# - Service logs  
# - Queue data
# - Configuration snapshots
```

### Recovery Procedures
```bash
# Restore from backup
cp -r backup_20241129_143022/* ./

# Restart services
python deploy.py restart

# Verify health
python deploy.py health
```

## 🎯 Production Checklist

### Pre-Deployment
- [ ] OpenAI API key configured and tested
- [ ] Airtable integration verified
- [ ] Quality thresholds tuned
- [ ] Docker environment tested
- [ ] Backup procedures established
- [ ] Monitoring alerts configured

### Post-Deployment
- [ ] Health check passes
- [ ] Processing statistics look normal
- [ ] Airtable updates working
- [ ] Campaign injection successful
- [ ] Logs are being generated
- [ ] Performance meets expectations

### Daily Operations
- [ ] Check service health
- [ ] Review processing statistics
- [ ] Monitor approval rates
- [ ] Check for errors in logs
- [ ] Verify Airtable updates
- [ ] Backup critical data

---

## 🎉 Success Metrics

**Target Performance:**
- **Processing Speed**: 30-60 seconds per lead
- **Approval Rate**: 80%+ campaigns approved
- **Quality Score**: 85+ average quality score
- **Uptime**: 99.5% service availability
- **Error Rate**: <5% processing errors

The Campaign Brain is now ready to serve as the intelligent core of your 4Runr Outreach System, processing leads at scale while maintaining the highest quality standards!