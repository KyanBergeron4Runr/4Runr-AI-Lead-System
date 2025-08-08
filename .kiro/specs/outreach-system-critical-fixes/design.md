# Design Document

## Overview

The Outreach System Critical Fixes will address seven critical technical issues that prevent the 4runr outreach system from functioning properly in production. The current system suffers from import errors, OpenAI SDK compatibility issues, Airtable API integration problems, unreliable healthchecks, and engagement pipeline failures.

This design provides a comprehensive solution that transforms the system from a broken state to a production-ready outreach pipeline capable of scraping leads, generating personalized messages, and engaging prospects reliably.

## Architecture

### Current System Issues

The outreach system has a modular architecture with the following components:
- **Website Scraper**: Extracts company data from websites
- **Message Generator**: Creates personalized outreach messages using AI
- **Email Validator**: Processes and validates Airtable lead data
- **Engager**: Sends outreach messages to prospects

However, the system currently fails due to:
1. Relative import errors preventing module loading
2. Deprecated OpenAI SDK usage causing crashes
3. Incorrect Airtable field names causing 422 errors
4. Blocking healthchecks that fail when pipeline crashes
5. Engager skipping all leads due to upstream failures

### Target Architecture

The fixed system will maintain the same modular structure but with:
- **Absolute Import System**: All modules use `from outreach.module import component` pattern
- **Modern OpenAI Integration**: Uses openai>=1.30.0 with proper proxy support via httpx
- **Configurable Airtable Integration**: Field names from environment variables with fallback handling
- **Non-blocking Web Service**: Health endpoint independent of pipeline state
- **Resilient Engagement Pipeline**: Fallback message generation when upstream fails

## Components and Interfaces

### 1. Import System Restructuring

**Problem**: Relative imports like `from ..shared.config import config` fail with "attempted relative import beyond top-level package"

**Solution**: Convert to absolute imports and proper package structure

**Implementation**:
```python
# BEFORE (broken)
from ..shared.config import config
from ..shared.logging_utils import get_logger

# AFTER (fixed)
from outreach.shared.config import config
from outreach.shared.logging_utils import get_logger
```

**Package Structure**:
```
4runr-outreach-system/
├── outreach/                    # Main package
│   ├── __init__.py             # Package marker
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging_utils.py
│   ├── website_scraper/
│   │   ├── __init__.py
│   │   ├── main.py             # Entry point
│   │   └── scraping_engine.py
│   ├── message_generator/
│   │   ├── __init__.py
│   │   ├── main.py             # Entry point
│   │   └── ai_generator.py
│   └── engager/
│       ├── __init__.py
│       ├── main.py             # Entry point
│       └── enhanced_engager_agent.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

**Docker Configuration**:
```dockerfile
WORKDIR /app
ENV PYTHONPATH=/app
CMD ["python", "-m", "outreach.api"]
```

**Module Execution**:
```bash
# Instead of: python website_scraper/main.py
python -m outreach.website_scraper.main

# Instead of: python message_generator/ai_generator.py  
python -m outreach.message_generator.main
```

### 2. OpenAI SDK Modernization

**Problem**: Current code uses deprecated `openai==1.3.7` with old API patterns

**Solution**: Upgrade to `openai>=1.30.0` with modern client initialization

**Current Broken Code**:
```python
# Multiple instances found in codebase
openai.api_key = self.ai_config['api_key']
self.client = openai.OpenAI(api_key=self.ai_config['api_key'])
# Duplicated lines suggest copy-paste errors
```

**Fixed Implementation**:
```python
import os
import httpx
from openai import OpenAI

class AIMessageGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        
        if proxy:
            http_client = httpx.Client(proxies=proxy, timeout=60)
            self.client = OpenAI(api_key=api_key, http_client=http_client)
        else:
            self.client = OpenAI(api_key=api_key)
    
    def generate_message(self, prompt):
        response = self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a professional outreach specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
```

**Requirements Update**:
```txt
openai>=1.30.0
httpx>=0.27.0
```

### 3. Airtable Integration Fix

**Problem**: Hard-coded field names cause INVALID_FILTER_BY_FORMULA 422 errors

**Solution**: Configurable field names with defensive error handling

**Environment Configuration**:
```env
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_TABLE_NAME=Table 1
AIRTABLE_FIELD_WEBSITE=Website
AIRTABLE_FIELD_COMPANY_DESCRIPTION=Company Description
AIRTABLE_FIELD_EMAIL=Email
AIRTABLE_FIELD_COMPANY_NAME=Company Name
```

**Fixed Airtable Client**:
```python
import os
import urllib.parse as up
from pyairtable import Api

class ConfigurableAirtableClient:
    def __init__(self):
        self.api = Api(os.getenv("AIRTABLE_API_KEY"))
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME", "Table 1")
        
        # Configurable field names
        self.field_website = os.getenv("AIRTABLE_FIELD_WEBSITE", "Website")
        self.field_description = os.getenv("AIRTABLE_FIELD_COMPANY_DESCRIPTION", "Company Description")
        self.field_email = os.getenv("AIRTABLE_FIELD_EMAIL", "Email")
        
    def get_leads_for_processing(self, max_records=20):
        try:
            # Primary filter - exact field names
            formula = f"AND({{{self.field_website}}} != '', {{{self.field_description}}} = '')"
            
            records = self.api.table(self.base_id, self.table_name).all(
                formula=formula,
                max_records=max_records
            )
            
            if records:
                self.logger.info(f"Retrieved {len(records)} records with primary filter")
                return records
                
        except Exception as e:
            self.logger.warning(f"Primary filter failed: {e}")
            
            # Fallback filter - looser criteria
            try:
                fallback_formula = f"{{{self.field_website}}} != ''"
                records = self.api.table(self.base_id, self.table_name).all(
                    formula=fallback_formula,
                    max_records=max_records
                )
                self.logger.info(f"Retrieved {len(records)} records with fallback filter")
                return records
                
            except Exception as fallback_error:
                self.logger.error(f"Both filters failed. Available fields might be: {self._get_field_names()}")
                return []
    
    def _get_field_names(self):
        """Attempt to get available field names for debugging"""
        try:
            sample = self.api.table(self.base_id, self.table_name).first()
            return list(sample['fields'].keys()) if sample else "Unable to retrieve"
        except:
            return "Unable to retrieve"
```

### 4. Non-blocking Health Check System

**Problem**: Current healthcheck depends on pipeline state and blocks container startup

**Solution**: Lightweight health endpoint independent of background processes

**Current Broken Healthcheck**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from shared.config import config; print('OK')" || exit 1
```

**Fixed Web Service Architecture**:
```python
from fastapi import FastAPI
import threading
import uvicorn
from outreach.shared.logging_utils import get_logger

app = FastAPI()
logger = get_logger('api')

@app.get("/health")
def health_check():
    """Lightweight health check that doesn't depend on pipeline state"""
    return {"status": "ok", "service": "outreach-system"}

@app.get("/pipeline/status")
def pipeline_status():
    """Optional detailed status endpoint"""
    # This can include pipeline state if needed
    return {"pipeline": "running", "last_check": "2025-01-01T00:00:00Z"}

def run_pipeline_background():
    """Run the outreach pipeline in background thread"""
    try:
        from outreach.pipeline import OutreachPipeline
        pipeline = OutreachPipeline()
        pipeline.run_continuous()
    except Exception as e:
        logger.exception(f"Background pipeline crashed: {e}")
        # Pipeline failure doesn't crash the web service

def start_background_pipeline():
    """Start pipeline in daemon thread"""
    pipeline_thread = threading.Thread(
        target=run_pipeline_background, 
        daemon=True,
        name="outreach-pipeline"
    )
    pipeline_thread.start()
    logger.info("Background pipeline started")

if __name__ == "__main__":
    # Start pipeline in background
    start_background_pipeline()
    
    # Start web service (this keeps container alive)
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Updated Docker Configuration**:
```dockerfile
# Expose port for health checks
EXPOSE 8080

# Updated healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=30s \
    CMD curl -fsS http://localhost:8080/health || exit 1

# Start web service instead of pipeline directly
CMD ["python", "-m", "outreach.api"]
```

**Updated docker-compose.yml**:
```yaml
services:
  outreach:
    build: .
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8080/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 30s
```

### 5. Resilient Engagement Pipeline

**Problem**: Engager skips all leads when upstream modules (scraper, generator) fail

**Solution**: Fallback message generation and defensive lead processing

**Current Broken Logic**:
```python
# Engager skips leads when custom_message is empty
if not lead.custom_message:
    logger.info(f"Skipping lead {lead.email} - no custom message")
    continue
```

**Fixed Engagement Logic**:
```python
class ResilientEngager:
    def process_lead(self, lead):
        """Process lead with fallback message generation"""
        
        # Try to use generated message first
        if lead.custom_message and len(lead.custom_message.strip()) > 10:
            message = lead.custom_message
            logger.info(f"Using generated message for {lead.email}")
        else:
            # Generate fallback message from basic data
            message = self.generate_fallback_message(lead)
            logger.warning(f"Using fallback message for {lead.email} - upstream generation failed")
        
        # Only skip if no email or explicitly filtered
        if not lead.email or not self.should_engage_lead(lead):
            logger.info(f"Skipping {lead.email} - filtered out", extra={
                "reason": "no_email" if not lead.email else "filtered",
                "lead_id": lead.id
            })
            return False
            
        # Proceed with engagement
        return self.send_message(lead, message)
    
    def generate_fallback_message(self, lead):
        """Generate minimal message from basic lead data"""
        company_name = getattr(lead, 'company_name', 'your company')
        website = getattr(lead, 'website', '')
        
        # Simple template-based fallback
        message = f"""Hi there,

I noticed {company_name} and thought you might be interested in how we help companies like yours streamline their operations.

Would you be open to a brief conversation about your current challenges?

Best regards,
[Your Name]"""
        
        return message
    
    def should_engage_lead(self, lead):
        """Determine if lead should be engaged based on business rules"""
        # Add your filtering logic here
        if not lead.email or '@' not in lead.email:
            return False
        
        # Check if already contacted recently
        if self.recently_contacted(lead.email):
            return False
            
        return True
```

## Data Models

### Lead Data Model
```python
@dataclass
class Lead:
    id: str
    email: str
    company_name: str
    website: str
    custom_message: Optional[str] = None
    company_description: Optional[str] = None
    contact_history: List[dict] = field(default_factory=list)
    
    def has_valid_email(self) -> bool:
        return bool(self.email and '@' in self.email)
    
    def needs_fallback_message(self) -> bool:
        return not self.custom_message or len(self.custom_message.strip()) < 10
```

### Configuration Model
```python
@dataclass
class OutreachConfig:
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    http_proxy: Optional[str] = None
    
    # Airtable Configuration
    airtable_api_key: str
    airtable_base_id: str
    airtable_table_name: str = "Table 1"
    field_website: str = "Website"
    field_company_description: str = "Company Description"
    field_email: str = "Email"
    field_company_name: str = "Company Name"
    
    # Pipeline Configuration
    max_records_per_batch: int = 20
    engagement_delay_hours: int = 24
```

## Error Handling

### Import Error Handling
```python
# Graceful handling of missing modules
try:
    from outreach.shared.config import config
except ImportError as e:
    logger.error(f"Import failed: {e}")
    logger.error("Ensure PYTHONPATH=/app and run with 'python -m outreach.module'")
    sys.exit(1)
```

### OpenAI Error Handling
```python
def safe_openai_call(self, prompt, retries=3):
    """Make OpenAI API call with retry logic"""
    for attempt in range(retries):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"OpenAI call attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                logger.error("All OpenAI attempts failed, using fallback")
                return self.generate_template_message()
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Airtable Error Handling
```python
def safe_airtable_query(self, formula, max_records=20):
    """Query Airtable with fallback handling"""
    try:
        records = self.table.all(formula=formula, max_records=max_records)
        logger.info(f"Airtable query successful: {len(records)} records")
        return records
        
    except Exception as e:
        if "INVALID_FILTER_BY_FORMULA" in str(e):
            logger.error(f"Filter formula invalid: {formula}")
            logger.error(f"Available fields: {self._get_available_fields()}")
            
            # Try simpler fallback formula
            fallback_formula = f"{{{self.field_website}}} != ''"
            return self.safe_airtable_query(fallback_formula, max_records)
        else:
            logger.error(f"Airtable query failed: {e}")
            return []
```

## Testing Strategy

### Unit Testing
```python
# Test import resolution
def test_absolute_imports():
    """Verify all modules can be imported with absolute paths"""
    from outreach.shared.config import config
    from outreach.website_scraper.main import WebsiteScraper
    from outreach.message_generator.main import MessageGenerator
    assert config is not None

# Test OpenAI integration
def test_openai_client():
    """Verify OpenAI client works with current SDK"""
    generator = MessageGenerator()
    response = generator.generate_message("Test prompt")
    assert len(response) > 0

# Test Airtable integration
def test_airtable_query():
    """Verify Airtable queries work with configurable fields"""
    client = ConfigurableAirtableClient()
    records = client.get_leads_for_processing(max_records=1)
    assert isinstance(records, list)
```

### Integration Testing
```bash
# Test complete pipeline
docker-compose build outreach
docker-compose up -d outreach

# Wait for health check
sleep 30
curl -f http://localhost:8080/health

# Test individual modules
docker exec outreach python -m outreach.website_scraper.main --dry-run
docker exec outreach python -m outreach.message_generator.main --dry-run

# Verify logs show success
docker logs outreach | grep "OpenAI API connection established"
docker logs outreach | grep "Processed: [1-9]"  # Non-zero processing
```

### Smoke Test Script
```python
#!/usr/bin/env python3
"""Comprehensive smoke test for outreach system fixes"""

import subprocess
import time
import requests
import sys

def run_smoke_tests():
    """Run all smoke tests and report results"""
    tests = [
        ("Docker Build", test_docker_build),
        ("Container Startup", test_container_startup),
        ("Health Check", test_health_check),
        ("Module Imports", test_module_imports),
        ("Airtable Connection", test_airtable_connection),
        ("OpenAI Connection", test_openai_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            test_func()
            results[test_name] = "PASS"
            print(f"✅ {test_name}: PASS")
        except Exception as e:
            results[test_name] = f"FAIL: {e}"
            print(f"❌ {test_name}: FAIL - {e}")
    
    # Summary
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
```

This comprehensive design addresses all seven critical issues while maintaining the existing system architecture and ensuring production readiness.