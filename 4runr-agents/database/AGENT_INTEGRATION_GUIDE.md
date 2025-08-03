# Agent Integration Guide

This guide shows how to integrate your agents with the new Lead Database system for safe, efficient lead management.

## Quick Start

### Basic Setup

```python
from database.lead_database import get_lead_database

# Get database instance (singleton - safe to call multiple times)
db = get_lead_database()
```

### Adding Leads (Replaces JSON file writing)

```python
# OLD WAY (JSON files)
leads = []
leads.append({
    'full_name': 'John Smith',
    'email': 'john@company.com',
    'company': 'TechCorp'
})
with open('shared/leads.json', 'w') as f:
    json.dump(leads, f)

# NEW WAY (Database with automatic duplicate detection)
lead_data = {
    'full_name': 'John Smith',
    'email': 'john@company.com',
    'company': 'TechCorp',
    'title': 'CEO',
    'location': 'Montreal, QC',
    'industry': 'Technology',
    'source': 'LinkedIn Scraper',
    'scraped_at': datetime.now().isoformat()
}

# This automatically handles duplicates and returns existing ID if duplicate found
lead_id = db.add_lead(lead_data)
print(f"Lead added/updated: {lead_id}")
```

### Searching Leads (Replaces JSON file reading)

```python
# OLD WAY (JSON files)
with open('shared/leads.json', 'r') as f:
    all_leads = json.load(f)
    
tech_leads = [lead for lead in all_leads if lead.get('industry') == 'Technology']

# NEW WAY (Database with powerful search)
# Simple search
tech_leads = db.search_leads({'industry': 'Technology'})

# Advanced search with multiple criteria
montreal_ceos = db.search_leads({
    'location': '%Montreal%',  # Wildcard search
    'title': '%CEO%',
    'verified': True
})

# Quick search across multiple fields
search_results = db.quick_search('TechCorp')

# Get recent leads
recent_leads = db.get_recent_leads(days=7, limit=50)
```

### Updating Leads

```python
# Update lead data
updates = {
    'verified': True,
    'enriched': True,
    'enriched_at': datetime.now().isoformat(),
    'status': 'contacted'
}

success = db.update_lead(lead_id, updates)
if success:
    print("Lead updated successfully")
```

## Agent-Specific Integration Examples

### 1. Scraper Agents

```python
#!/usr/bin/env python3
"""
Example: LinkedIn Scraper Agent Integration
"""

from database.lead_database import get_lead_database
from datetime import datetime

def scrape_and_store_leads():
    """Scrape leads and store in database"""
    db = get_lead_database()
    
    # Your scraping logic here
    scraped_leads = scrape_linkedin_profiles()
    
    for lead_data in scraped_leads:
        # Prepare lead data
        lead_record = {
            'full_name': lead_data['name'],
            'linkedin_url': lead_data['profile_url'],
            'company': lead_data.get('company'),
            'title': lead_data.get('title'),
            'location': lead_data.get('location'),
            'source': 'LinkedIn Scraper',
            'scraped_at': datetime.now().isoformat(),
            'needs_enrichment': True,
            'verified': False
        }
        
        # Add to database (handles duplicates automatically)
        lead_id = db.add_lead(lead_record)
        print(f"Processed lead: {lead_record['full_name']} (ID: {lead_id})")
    
    print(f"Scraping completed. Total leads in database: {db.get_lead_count()}")
```

### 2. Enrichment Agents

```python
#!/usr/bin/env python3
"""
Example: Lead Enrichment Agent Integration
"""

from database.lead_database import get_lead_database

def enrich_leads():
    """Enrich leads that need enrichment"""
    db = get_lead_database()
    
    # Get leads that need enrichment
    leads_to_enrich = db.get_leads_needing_enrichment(limit=10)
    
    for lead in leads_to_enrich:
        print(f"Enriching: {lead['full_name']}")
        
        # Your enrichment logic here
        enriched_data = enrich_lead_data(lead)
        
        # Update lead with enriched data
        updates = {
            'email': enriched_data.get('email'),
            'phone': enriched_data.get('phone'),
            'industry': enriched_data.get('industry'),
            'company_size': enriched_data.get('company_size'),
            'enriched': True,
            'enriched_at': datetime.now().isoformat(),
            'needs_enrichment': False,
            'raw_data': {
                'enrichment_source': 'clearbit',
                'confidence_score': enriched_data.get('confidence', 0.8),
                'enriched_fields': list(enriched_data.keys())
            }
        }
        
        success = db.update_lead(lead['id'], updates)
        if success:
            print(f"✅ Enriched: {lead['full_name']}")
        else:
            print(f"❌ Failed to update: {lead['full_name']}")
```

### 3. Sync Agents (Airtable Integration)

```python
#!/usr/bin/env python3
"""
Example: Airtable Sync Agent Integration
"""

from database.lead_database import get_lead_database

def sync_to_airtable():
    """Sync pending leads to Airtable"""
    db = get_lead_database()
    
    # Get leads that need syncing
    pending_leads = db.get_sync_pending_leads()
    
    print(f"Found {len(pending_leads)} leads to sync")
    
    for lead in pending_leads:
        try:
            # Your Airtable sync logic here
            airtable_record = sync_lead_to_airtable(lead)
            
            # Update lead with sync status
            updates = {
                'airtable_synced': True,
                'airtable_id': airtable_record['id'],
                'sync_pending': False,
                'last_sync_attempt': datetime.now().isoformat(),
                'sync_error': None
            }
            
            db.update_lead(lead['id'], updates)
            print(f"✅ Synced: {lead['full_name']}")
            
        except Exception as e:
            # Update with error status
            updates = {
                'last_sync_attempt': datetime.now().isoformat(),
                'sync_error': str(e)
            }
            
            db.update_lead(lead['id'], updates)
            print(f"❌ Sync failed: {lead['full_name']} - {e}")
```

### 4. Analysis and Reporting Agents

```python
#!/usr/bin/env python3
"""
Example: Lead Analysis Agent Integration
"""

from database.lead_database import get_lead_database

def generate_lead_report():
    """Generate comprehensive lead analysis report"""
    db = get_lead_database()
    
    # Get comprehensive statistics
    stats = db.get_search_statistics()
    
    print("📊 Lead Database Report")
    print("=" * 30)
    print(f"Total Leads: {stats['total_leads']}")
    print(f"Verified: {stats['verified_count']} ({stats['verified_count']/stats['total_leads']*100:.1f}%)")
    print(f"Enriched: {stats['enriched_count']} ({stats['enriched_count']/stats['total_leads']*100:.1f}%)")
    
    # Industry breakdown
    print(f"\\nTop Industries:")
    for industry, count in list(stats['top_industries'].items())[:5]:
        print(f"  {industry}: {count}")
    
    # Recent activity
    recent_leads = db.get_recent_leads(days=7)
    print(f"\\nRecent Activity (7 days): {len(recent_leads)} new leads")
    
    # Quality metrics
    unverified = db.get_unverified_leads()
    needs_enrichment = db.get_leads_needing_enrichment()
    
    print(f"\\nData Quality:")
    print(f"  Needs verification: {len(unverified)}")
    print(f"  Needs enrichment: {len(needs_enrichment)}")
    
    # Advanced search examples
    montreal_tech = db.search_leads({
        'location': '%Montreal%',
        'industry': 'Technology',
        'verified': True
    })
    print(f"  Montreal Tech (verified): {len(montreal_tech)}")
```

## Advanced Features

### 1. Complex Searches

```python
from database.search_engine import SearchQuery, SearchFilter, SortCriteria, ComparisonOperator, SortOrder

# Build complex search query
filters = [
    SearchFilter('industry', ComparisonOperator.IN, ['Technology', 'Software', 'Fintech']),
    SearchFilter('verified', ComparisonOperator.EQUALS, True),
    SearchFilter('created_at', ComparisonOperator.GREATER_THAN, '2024-01-01')
]

sort_criteria = [
    SortCriteria('company', SortOrder.ASC),
    SortCriteria('full_name', SortOrder.ASC)
]

query = SearchQuery(
    filters=filters,
    sort_by=sort_criteria,
    limit=50,
    offset=0
)

result = db.advanced_search(query)
print(f"Found {len(result['leads'])} leads in {result['query_time_ms']:.2f}ms")
```

### 2. Duplicate Detection

```python
# Check for duplicates before adding
potential_duplicates = db.find_all_duplicates(lead_data)

if potential_duplicates:
    print("Potential duplicates found:")
    for dup in potential_duplicates:
        print(f"  {dup['match_type']}: {dup['confidence']:.2f} - {dup['existing_lead']['full_name']}")

# Add lead (will merge with duplicates automatically)
lead_id = db.add_lead(lead_data)
```

### 3. Batch Operations

```python
# Process multiple leads efficiently
leads_to_process = db.get_leads_by_status('new', limit=100)

for lead in leads_to_process:
    # Process lead
    processed_data = process_lead(lead)
    
    # Update in batch
    updates = {
        'status': 'processed',
        'processed_at': datetime.now().isoformat()
    }
    
    db.update_lead(lead['id'], updates)
```

## Migration from JSON Files

### Automatic Migration

```python
from database.migration_manager import MigrationManager

# Initialize migration manager
migration_manager = MigrationManager()

# Migrate all JSON files to database
summary = migration_manager.migrate_all_json_files(create_backups=True)

print(f"Migration completed: {summary.total_leads_migrated} leads migrated")
```

### Manual Migration Script

```bash
# Run migration script
python database/migration_manager.py

# Validate migration
python database/migration_manager.py --validate

# Create rollback script
python database/migration_manager.py --rollback-script
```

## Best Practices

### 1. Error Handling

```python
try:
    lead_id = db.add_lead(lead_data)
    print(f"Lead added: {lead_id}")
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Database error: {e}")
```

### 2. Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database operations are automatically logged
lead_id = db.add_lead(lead_data)
logger.info(f"Added lead: {lead_id}")
```

### 3. Performance

```python
# Use pagination for large datasets
offset = 0
limit = 100

while True:
    leads = db.get_all_leads(limit=limit, offset=offset)
    
    if not leads:
        break
    
    # Process leads
    for lead in leads:
        process_lead(lead)
    
    offset += limit
```

### 4. Data Validation

```python
def validate_lead_data(lead_data):
    """Validate lead data before adding to database"""
    required_fields = ['full_name']
    
    for field in required_fields:
        if not lead_data.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate email format
    if lead_data.get('email'):
        if '@' not in lead_data['email']:
            raise ValueError("Invalid email format")
    
    return True

# Use validation
if validate_lead_data(lead_data):
    lead_id = db.add_lead(lead_data)
```

## Common Patterns

### 1. Scraper Pattern

```python
def scraper_agent():
    db = get_lead_database()
    
    # Scrape data
    scraped_data = scrape_source()
    
    # Process and store
    for item in scraped_data:
        lead_data = {
            'full_name': item['name'],
            'source': 'My Scraper',
            'scraped_at': datetime.now().isoformat(),
            # ... other fields
        }
        
        db.add_lead(lead_data)
```

### 2. Enrichment Pattern

```python
def enrichment_agent():
    db = get_lead_database()
    
    # Get leads needing enrichment
    leads = db.get_leads_needing_enrichment(limit=10)
    
    for lead in leads:
        # Enrich data
        enriched = enrich_lead(lead)
        
        # Update database
        updates = {
            'enriched': True,
            'enriched_at': datetime.now().isoformat(),
            **enriched
        }
        
        db.update_lead(lead['id'], updates)
```

### 3. Sync Pattern

```python
def sync_agent():
    db = get_lead_database()
    
    # Get pending sync leads
    pending = db.get_sync_pending_leads()
    
    for lead in pending:
        try:
            # Sync to external system
            sync_result = sync_to_external(lead)
            
            # Update sync status
            db.update_lead(lead['id'], {
                'airtable_synced': True,
                'sync_pending': False,
                'airtable_id': sync_result['id']
            })
            
        except Exception as e:
            # Log error but continue
            db.update_lead(lead['id'], {
                'sync_error': str(e),
                'last_sync_attempt': datetime.now().isoformat()
            })
```

## Troubleshooting

### Common Issues

1. **Database locked**: Usually resolves automatically with retry logic
2. **Duplicate detection not working**: Check that leads have LinkedIn URL, email, or name+company
3. **Performance issues**: Use pagination and appropriate filters
4. **Migration issues**: Check JSON file format and run validation

### Debug Mode

```python
import logging
logging.getLogger('database').setLevel(logging.DEBUG)

# Now all database operations will be logged in detail
```

### Health Check

```python
# Check database health
health = db.db_conn.health_check()
print(f"Database status: {health['status']}")
print(f"Response time: {health['response_time_seconds']}s")
```

This integration guide provides everything your agents need to work with the new database system safely and efficiently!