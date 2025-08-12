# 4Runr Outreach System Deployment Guide

## Overview

This guide covers deploying the 4Runr Outreach System with all critical fixes applied, including:
- Fixed import system with absolute imports
- Modern OpenAI SDK integration with proxy support
- Configurable Airtable integration with defensive error handling
- Non-blocking health check system
- Resilient engagement pipeline with fallback message generation

## Prerequisites

### System Requirements
- Docker and Docker Compose
- Python 3.11+ (for local development)
- 4GB+ RAM recommended
- Network access to Airtable and OpenAI APIs

### Required API Keys
- **Airtable API Key**: Get from https://airtable.com/account
- **Airtable Base ID**: From your Airtable base URL
- **OpenAI API Key**: Get from https://platform.openai.com/api-keys
- **Microsoft Graph Credentials** (optional but recommended for email sending)

## Quick Start

### 1. Environment Setup

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Required - Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=Leads

# Required - OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Optional - Microsoft Graph (recommended for email)
MS_GRAPH_CLIENT_ID=your_graph_client_id_here
MS_GRAPH_CLIENT_SECRET=your_graph_client_secret_here
MS_GRAPH_TENANT_ID=your_graph_tenant_id_here
MS_GRAPH_SENDER_EMAIL=your_sender_email@yourdomain.com
```

### 2. Airtable Field Configuration

Ensure your Airtable field names match the configuration in `.env`:
```env
AIRTABLE_FIELD_WEBSITE=Website
AIRTABLE_FIELD_COMPANY_DESCRIPTION=Company Description
AIRTABLE_FIELD_EMAIL=Email
AIRTABLE_FIELD_COMPANY_NAME=Company Name
# ... (see .env.example for complete list)
```

**Important**: Field names are case-sensitive and must match your Airtable schema exactly.

### 3. Docker Deployment

Build and start the system:
```bash
# Build the Docker image
docker-compose build

# Start the system
docker-compose up -d

# Check health
curl http://localhost:8080/health
```

### 4. Verify Deployment

Check that all components are working:
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f

# Test health endpoints
curl http://localhost:8080/health
curl http://localhost:8080/pipeline/status
curl http://localhost:8080/system/info
```

## Advanced Configuration

### Custom Build

Use the build script for advanced options:
```bash
# Development build
./build.sh --dev

# Production build with no cache
./build.sh --no-cache

# Build and push to registry
./build.sh --push
```

### Environment Variables Reference

#### Core Configuration
```env
# System behavior
BATCH_SIZE=10                    # Leads processed per cycle
RATE_LIMIT_DELAY=1              # Delay between lead processing (seconds)
PIPELINE_CYCLE_DELAY=300        # Delay between pipeline cycles (seconds)

# API settings
API_HOST=0.0.0.0                # API bind address
API_PORT=8080                   # API port

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
SAVE_JSON_LOGS=true            # Save structured JSON logs
LOG_DIRECTORY=logs             # Log file directory
```

#### OpenAI Configuration
```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4              # or gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000          # Max tokens per request
OPENAI_TEMPERATURE=0.7          # Response creativity (0.0-1.0)

# Proxy support (optional)
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=https://proxy:8080
```

#### Airtable Field Mapping
```env
# Map logical field names to your Airtable schema
AIRTABLE_FIELD_WEBSITE=Website
AIRTABLE_FIELD_COMPANY_DESCRIPTION=Company Description
AIRTABLE_FIELD_EMAIL=Email
AIRTABLE_FIELD_COMPANY_NAME=Company Name
AIRTABLE_FIELD_NAME=Name
AIRTABLE_FIELD_JOB_TITLE=Job Title
AIRTABLE_FIELD_EMAIL_CONFIDENCE_LEVEL=Email_Confidence_Level
AIRTABLE_FIELD_CUSTOM_MESSAGE=Custom_Message
AIRTABLE_FIELD_ENGAGEMENT_STATUS=Engagement_Status
AIRTABLE_FIELD_DATE_MESSAGED=Date Messaged
```

### Individual Module Execution

Run specific modules independently:
```bash
# Website scraper only
docker-compose run --rm website-scraper

# Message generator only
docker-compose run --rm message-generator

# Email validator only
docker-compose run --rm email-validator

# Engager only
docker-compose run --rm engager
```

## Testing and Validation

### Configuration Tests

Test your configuration before deployment:
```bash
# Test Airtable configuration
python test_airtable_config.py

# Test health check system
python test_health_check.py

# Test resilient engagement
python test_resilient_engagement.py
```

### Smoke Tests

Run comprehensive smoke tests:
```bash
# Build and test
docker-compose build
docker-compose up -d

# Wait for startup
sleep 30

# Run tests
curl -f http://localhost:8080/health
curl -f http://localhost:8080/pipeline/status
curl -f http://localhost:8080/system/info

# Check logs for errors
docker-compose logs | grep -i error
```

### Module Testing

Test individual modules:
```bash
# Test website scraper
docker exec outreach-system python -m outreach.website_scraper.main --dry-run

# Test message generator
docker exec outreach-system python -m outreach.message_generator.main --dry-run

# Test engager
docker exec outreach-system python -m outreach.engager.main --dry-run
```

## Monitoring and Maintenance

### Health Monitoring

The system provides multiple health endpoints:

- **`/health`**: Basic health check (always returns 200 if service is running)
- **`/pipeline/status`**: Detailed pipeline status and statistics
- **`/system/info`**: System component status (Airtable, OpenAI, etc.)

### Log Monitoring

Monitor logs for issues:
```bash
# Follow logs
docker-compose logs -f

# Check for errors
docker-compose logs | grep -i error

# Check specific module
docker-compose logs engager
```

### Performance Monitoring

Key metrics to monitor:
- Pipeline cycle completion time
- Lead processing success rate
- API response times
- Memory and CPU usage

### Backup and Recovery

Important data to backup:
- `.env` configuration file
- Log files in `./logs/` directory
- Any custom configuration files

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Symptom**: "attempted relative import beyond top-level package"
**Solution**: Ensure using `python -m outreach.module.main` format

#### 2. OpenAI API Errors
**Symptom**: "Client.__init__() got an unexpected keyword argument 'proxies'"
**Solution**: Verify OpenAI SDK version is >= 1.30.0

#### 3. Airtable 422 Errors
**Symptom**: "INVALID_FILTER_BY_FORMULA"
**Solution**: Check field names in `.env` match Airtable schema exactly

#### 4. Health Check Failures
**Symptom**: Container marked as unhealthy
**Solution**: Check if port 8080 is accessible and API is responding

#### 5. Engagement Pipeline Skipping Leads
**Symptom**: All leads marked as "skipped"
**Solution**: Check email confidence levels and custom message availability

### Debug Commands

```bash
# Check container health
docker inspect outreach-system | grep Health -A 10

# Test API endpoints
curl -v http://localhost:8080/health
curl -v http://localhost:8080/system/info

# Check Airtable connection
docker exec outreach-system python test_airtable_config.py

# Check module imports
docker exec outreach-system python -c "from outreach.shared.config import config; print('OK')"

# View detailed logs
docker-compose logs --tail=100 outreach-system
```

### Getting Help

If you encounter issues:

1. Check the logs for specific error messages
2. Verify your `.env` configuration
3. Test individual components using the test scripts
4. Check that all required API keys are valid and have proper permissions
5. Ensure your Airtable schema matches the field configuration

## Production Deployment

### Security Considerations

- Use strong, unique API keys
- Restrict network access to necessary ports only
- Regularly rotate API keys
- Monitor logs for suspicious activity
- Use HTTPS in production environments

### Scaling Considerations

- Adjust `BATCH_SIZE` based on your lead volume
- Increase `PIPELINE_CYCLE_DELAY` for lower API usage
- Monitor API rate limits (OpenAI, Airtable)
- Consider horizontal scaling for high-volume deployments

### Backup Strategy

- Regular backups of configuration files
- Log rotation and archival
- Database backups if using local storage
- API key backup and rotation schedule

## Updates and Maintenance

### Updating the System

1. Pull latest changes
2. Review changelog for breaking changes
3. Update `.env` if new variables are added
4. Rebuild Docker image
5. Test in staging environment
6. Deploy to production

### Dependency Updates

```bash
# Update requirements
pip install --upgrade -r requirements.txt
pip freeze > requirements-lock.txt

# Rebuild image
docker-compose build --no-cache
```

This deployment guide ensures a smooth setup and operation of the 4Runr Outreach System with all critical fixes applied.