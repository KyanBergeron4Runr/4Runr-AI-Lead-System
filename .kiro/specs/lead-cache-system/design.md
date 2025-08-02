# Lead Cache System Design

## Overview

A lightweight caching layer that sits between agents and Airtable, providing fast local access to lead data while minimizing API calls. Uses a simple JSON file cache with smart synchronization.

## Architecture

### Persistent Database Cache (Works Locally + Deployed)
```
4runr-agents/
├── cache/
│   ├── __init__.py
│   ├── lead_cache.py      # Main cache manager
│   ├── sync_manager.py    # Airtable sync logic
│   └── models.py          # Database models
├── data/
│   ├── leads_cache.db     # SQLite database (persistent)
│   └── backups/           # Database backups
```

**Why SQLite for Cache:**
- **Persistent**: Survives container restarts and deployments
- **Shared**: Multiple agent instances can access same database
- **Fast**: Local database queries are still very fast (10-50ms)
- **Reliable**: ACID transactions, no data corruption
- **Portable**: Single file, easy to backup and restore

## Core Components

### 1. Lead Cache Manager (`lead_cache.py`)

```python
class LeadCache:
    def __init__(self, db_path="data/leads_cache.db"):
        self.db_path = db_path
        self.connection = None
        self._init_database()
        
    # Fast read operations (no API calls)
    def get_all_leads(self) -> List[dict]:
        """Get all cached leads instantly"""
        
    def get_leads_by_status(self, status: str) -> List[dict]:
        """Get leads by status from cache"""
        
    def get_lead_by_id(self, lead_id: str) -> dict:
        """Get specific lead from cache"""
        
    def search_leads(self, query: str) -> List[dict]:
        """Search leads in cache (name, company, email)"""
        
    # Write operations (cache + mark for sync)
    def update_lead(self, lead_id: str, updates: dict):
        """Update lead in cache and mark for sync"""
        
    def add_lead(self, lead_data: dict):
        """Add new lead to cache and mark for sync"""
        
    # Cache management
    def is_cache_fresh(self, max_age_hours: int = 2) -> bool:
        """Check if cache is still fresh"""
        
    def refresh_cache(self, force: bool = False):
        """Refresh cache from Airtable if needed"""
        
    def sync_pending_changes(self):
        """Push pending changes back to Airtable"""
```

### 2. Sync Manager (`sync_manager.py`)

```python
class SyncManager:
    def __init__(self, airtable_client, cache_manager):
        self.airtable = airtable_client
        self.cache = cache_manager
        
    def pull_from_airtable(self) -> dict:
        """Pull all leads from Airtable to cache"""
        
    def push_to_airtable(self, pending_changes: dict) -> dict:
        """Push pending changes to Airtable"""
        
    def incremental_sync(self) -> dict:
        """Smart sync - only changed records"""
```

## Usage Examples

### For Agents (Simple API)

```python
from cache.lead_cache import LeadCache

# Initialize cache (loads automatically)
cache = LeadCache()

# Fast operations - no API calls
leads = cache.get_all_leads()
enriched_leads = cache.get_leads_by_status('scraped')
lead = cache.get_lead_by_id('rec123456')

# Update lead (cached + marked for sync)
cache.update_lead('rec123456', {
    'status': 'enriched',
    'email': 'found@company.com'
})

# Search leads locally
results = cache.search_leads('TechCorp')

# Refresh if needed
if not cache.is_cache_fresh():
    cache.refresh_cache()
```

### Database Schema (SQLite)

#### `leads` table
```sql
CREATE TABLE leads (
    id TEXT PRIMARY KEY,           -- Airtable record ID
    name TEXT,
    company TEXT,
    email TEXT,
    status TEXT,
    title TEXT,
    linkedin_url TEXT,
    website TEXT,
    location TEXT,
    data_json TEXT,               -- Full Airtable record as JSON
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_company ON leads(company);
```

#### `cache_meta` table
```sql
CREATE TABLE cache_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stores: last_full_sync, last_incremental_sync, total_leads, etc.
```

#### `pending_sync` table
```sql
CREATE TABLE pending_sync (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT,
    action TEXT,                  -- 'update', 'create', 'delete'
    changes_json TEXT,            -- JSON of what changed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP NULL
);
```
```

## Smart Sync Strategy

### 1. Initial Load
- Pull all leads from Airtable once
- Store in `leads_cache.json`
- Update `cache_meta.json` with timestamp

### 2. Agent Operations
- All reads from local cache (instant)
- All writes to cache + pending sync queue
- No API calls during normal operations

### 3. Background Sync
- Every 2 hours: check if cache needs refresh
- Push pending changes to Airtable
- Pull any updates from Airtable
- Clear pending sync queue

### 4. Manual Refresh
- `refresh_cache(force=True)` for immediate update
- Useful before important operations

## Implementation Benefits

### ⚡ **Performance**
- **10ms** lead access vs **500ms** API calls
- No rate limiting issues
- Works offline with cached data

### 🔄 **Smart Sync**
- Only sync when needed
- Batch updates to minimize API calls
- Automatic retry on failures

### 🛠️ **Simple Integration**
- Drop-in replacement for current Airtable calls
- Minimal code changes needed
- Backward compatible

### 📊 **Efficient**
- One API call loads all leads
- Updates batched and synced periodically
- Reduces Airtable API usage by 90%+

## Migration Path

### Phase 1: Create Cache System
1. Build `LeadCache` and `SyncManager` classes
2. Create cache files and sync logic
3. Test with small dataset

### Phase 2: Update Agents
1. Replace direct Airtable calls with cache calls
2. Update enricher agent first
3. Then scraper and engager agents

### Phase 3: Add Automation
1. Add background sync scheduling
2. Add cache refresh triggers
3. Add monitoring and logging

## Deployment Considerations

### Local Development
- Database file: `4runr-agents/data/leads_cache.db`
- Automatic creation on first run
- Easy to reset and reseed for testing

### Docker Deployment
```dockerfile
# Mount data directory as volume for persistence
VOLUME ["/app/data"]

# Database will persist across container restarts
ENV DATABASE_PATH="/app/data/leads_cache.db"
```

### EC2/Server Deployment
- Database file on persistent storage (EBS volume)
- Automatic backups to S3
- Multiple agent instances can share same database file
- Database locking handles concurrent access

### Environment Variables
```bash
# Database location (defaults to data/leads_cache.db)
LEAD_CACHE_DB_PATH="/app/data/leads_cache.db"

# Cache refresh interval in hours (default: 2)
CACHE_REFRESH_INTERVAL=2

# Airtable sync settings
AIRTABLE_API_KEY=your_key
AIRTABLE_BASE_ID=your_base
```

### Backup Strategy
```python
# Automatic daily backups
def backup_cache_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/leads_cache_{timestamp}.db"
    shutil.copy2("data/leads_cache.db", backup_path)
```

This gives you:
- **Fast local access** (10-50ms database queries)
- **Persistence** across deployments and restarts  
- **Shared access** for multiple agent instances
- **Simple deployment** - just one database file to manage
- **Airtable sync** - best of both worlds!