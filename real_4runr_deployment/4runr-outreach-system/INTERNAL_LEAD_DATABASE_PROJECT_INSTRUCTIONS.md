# Internal Lead Database Project Instructions

## 🎯 **Project Goal**
Extend the existing LocalDatabaseManager to create a complete internal lead storage system that:
- Stores all leads internally (reducing Airtable API calls)
- Syncs changes to Airtable automatically
- Uses the same field structure as Airtable
- Is Docker-ready for production deployment
- Has robust backup and security measures

## 📋 **Current State Analysis**

### ✅ **What Already Exists:**
- `engager/local_database_manager.py` - 925 lines of SQLite database code
- `data/leads_cache.db` - Active database with engagement tracking
- `data/backups/` - Backup directory structure
- Comprehensive engagement tracking system
- Backup system with integrity verification
- Thread-safe operations with connection pooling

### ❌ **What Needs to Be Built:**
1. **Full Lead Management** - Complete CRUD operations for leads
2. **Airtable Field Mapping** - Match exact Airtable schema
3. **Bidirectional Sync Manager** - Auto-sync with Airtable
4. **JSON Migration System** - Import existing lead files
5. **Docker Configuration** - Production deployment ready
6. **API Interface** - REST API for lead operations

## 🏗️ **Implementation Plan**

### **Phase 1: Extend Database Schema (Priority: HIGH)**

#### Task 1.1: Update Lead Table Schema
**File:** `shared/lead_database_manager.py` (extend existing)

**Current Schema Issues:**
- Missing critical Airtable fields
- No UUID system for lead identification
- No sync status tracking

**Required Schema Updates:**
```sql
-- Extend existing leads table with Airtable fields
ALTER TABLE leads ADD COLUMN uuid TEXT UNIQUE;
ALTER TABLE leads ADD COLUMN linkedin_url TEXT;
ALTER TABLE leads ADD COLUMN title TEXT;
ALTER TABLE leads ADD COLUMN location TEXT;
ALTER TABLE leads ADD COLUMN industry TEXT;
ALTER TABLE leads ADD COLUMN company_size TEXT;
ALTER TABLE leads ADD COLUMN verified BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN enriched BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN needs_enrichment BOOLEAN DEFAULT TRUE;
ALTER TABLE leads ADD COLUMN status TEXT DEFAULT 'new';
ALTER TABLE leads ADD COLUMN source TEXT;
ALTER TABLE leads ADD COLUMN scraped_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN enriched_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN airtable_id TEXT;
ALTER TABLE leads ADD COLUMN airtable_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN sync_pending BOOLEAN DEFAULT TRUE;
ALTER TABLE leads ADD COLUMN last_sync_attempt TIMESTAMP;
ALTER TABLE leads ADD COLUMN sync_error TEXT;
ALTER TABLE leads ADD COLUMN raw_data TEXT; -- JSON blob for additional fields
```

#### Task 1.2: Create Sync Status Table
```sql
CREATE TABLE sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT REFERENCES leads(id),
    operation TEXT,  -- 'create', 'update', 'delete'
    status TEXT,     -- 'pending', 'success', 'failed'
    attempt_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Task 1.3: Create Migration Log Table
```sql
CREATE TABLE migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    leads_migrated INTEGER,
    leads_failed INTEGER,
    migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    error_details TEXT
);
```

### **Phase 2: Airtable Field Mapping (Priority: HIGH)**

#### Task 2.1: Analyze Current Airtable Schema
**Action:** Run this command to get current Airtable fields:
```bash
python check_airtable_fields.py
```

#### Task 2.2: Create Field Mapping Configuration
**File:** `shared/airtable_field_mapping.json`
```json
{
  "lead_fields": {
    "id": "airtable_id",
    "Full Name": "name",
    "Email": "email",
    "Company": "company",
    "Website": "company_website",
    "LinkedIn URL": "linkedin_url",
    "Title": "title",
    "Location": "location",
    "Industry": "industry",
    "Company Size": "company_size",
    "Verified": "verified",
    "Enriched": "enriched",
    "Needs Enrichment": "needs_enrichment",
    "Status": "status",
    "Source": "source",
    "Scraped At": "scraped_at",
    "Enriched At": "enriched_at"
  },
  "sync_fields": {
    "Last Sync": "last_sync_attempt",
    "Sync Status": "airtable_synced",
    "Sync Error": "sync_error"
  }
}
```

### **Phase 3: Build Lead Database Manager (Priority: HIGH)**

#### Task 3.1: Create Enhanced Lead Database Manager
**File:** `shared/lead_database_manager.py`

**Key Methods to Implement:**
```python
class LeadDatabaseManager:
    def __init__(self, db_path: str = "data/leads.db")
    
    # Core CRUD Operations
    def add_lead(self, lead_data: dict) -> str
    def get_lead(self, lead_id: str) -> dict
    def update_lead(self, lead_id: str, updates: dict) -> bool
    def delete_lead(self, lead_id: str) -> bool
    def search_leads(self, filters: dict) -> List[dict]
    def get_all_leads(self) -> List[dict]
    
    # Duplicate Management
    def find_duplicates(self, lead_data: dict) -> Optional[str]
    def merge_leads(self, primary_id: str, duplicate_id: str) -> bool
    
    # Sync Management
    def mark_for_sync(self, lead_id: str) -> bool
    def get_sync_pending_leads(self) -> List[dict]
    def update_sync_status(self, lead_id: str, status: str, error: str = None) -> bool
    
    # Migration Support
    def migrate_from_json(self, json_files: List[str]) -> dict
    def validate_migration(self) -> dict
```

#### Task 3.2: Implement Duplicate Detection Logic
**Priority Logic:**
1. LinkedIn URL match (highest priority)
2. Email match (high priority)
3. Name + Company fuzzy match (medium priority)
4. Phone number match (if available)

### **Phase 4: Airtable Sync Manager (Priority: HIGH)**

#### Task 4.1: Create Airtable Sync Manager
**File:** `shared/airtable_sync_manager.py`

**Key Features:**
```python
class AirtableSyncManager:
    def __init__(self, db_manager: LeadDatabaseManager, airtable_client: AirtableClient)
    
    # Sync Operations
    def sync_to_airtable(self, lead_ids: List[str] = None) -> dict
    def sync_from_airtable(self) -> dict
    def bidirectional_sync(self) -> dict
    
    # Conflict Resolution
    def handle_sync_conflicts(self, conflicts: List[dict]) -> dict
    def resolve_conflict(self, local_lead: dict, airtable_lead: dict) -> dict
    
    # Batch Operations
    def batch_sync_to_airtable(self, batch_size: int = 10) -> dict
    def schedule_sync(self, interval_minutes: int = 30) -> bool
```

#### Task 4.2: Implement Sync Strategies
- **Push Strategy**: New/updated leads → Airtable
- **Pull Strategy**: Airtable changes → Local DB
- **Conflict Resolution**: Last-modified-wins with manual override
- **Retry Logic**: Exponential backoff for failed syncs

### **Phase 5: JSON Migration System (Priority: MEDIUM)**

#### Task 5.1: Create Migration Manager
**File:** `shared/migration_manager.py`

**Migration Process:**
1. Scan for existing JSON files in shared directory
2. Parse and validate JSON data
3. Detect duplicates before insertion
4. Create backup of original files
5. Generate migration report

#### Task 5.2: Implement Migration Scripts
**Files to Create:**
- `migrate_json_to_database.py` - Main migration script
- `validate_migration.py` - Post-migration validation
- `rollback_migration.py` - Emergency rollback

### **Phase 6: API Interface (Priority: MEDIUM)**

#### Task 6.1: Create REST API
**File:** `api/lead_api.py`

**Endpoints:**
```python
# Lead Management
GET    /api/leads              # List all leads
GET    /api/leads/{id}         # Get specific lead
POST   /api/leads              # Create new lead
PUT    /api/leads/{id}         # Update lead
DELETE /api/leads/{id}         # Delete lead

# Search and Filter
GET    /api/leads/search       # Search leads
GET    /api/leads/duplicates   # Find duplicates

# Sync Management
POST   /api/sync/to-airtable   # Trigger sync to Airtable
POST   /api/sync/from-airtable # Trigger sync from Airtable
GET    /api/sync/status        # Get sync status

# Statistics
GET    /api/stats/leads        # Lead statistics
GET    /api/stats/sync         # Sync statistics
```

### **Phase 7: Docker Configuration (Priority: MEDIUM)**

#### Task 7.1: Update Dockerfile
**File:** `Dockerfile`

**Required Changes:**
```dockerfile
# Add database volume
VOLUME ["/app/data"]

# Expose API port
EXPOSE 8000

# Add database initialization
RUN python -c "from shared.lead_database_manager import LeadDatabaseManager; LeadDatabaseManager().init_database()"
```

#### Task 7.2: Update Docker Compose
**File:** `docker-compose.yml`

**Add Services:**
```yaml
services:
  lead-database:
    build: .
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    ports:
      - "8000:8000"
    environment:
      - LEAD_DATABASE_PATH=/app/data/leads.db
      - BACKUP_ENABLED=true
      - SYNC_INTERVAL=30
```

### **Phase 8: Security and Backup Enhancements (Priority: MEDIUM)**

#### Task 8.1: Enhanced Backup System
**Features to Add:**
- Automated daily backups
- Backup rotation (keep 30 days)
- Backup encryption
- Remote backup storage (optional)

#### Task 8.2: Security Measures
- Database file permissions (600)
- API authentication
- Input validation and sanitization
- SQL injection prevention (already using prepared statements)

## 🔧 **Implementation Order**

### **Week 1: Core Database (HIGH PRIORITY)**
1. Extend database schema with Airtable fields
2. Create enhanced LeadDatabaseManager
3. Implement duplicate detection
4. Test with existing data

### **Week 2: Airtable Integration (HIGH PRIORITY)**
1. Create field mapping configuration
2. Build AirtableSyncManager
3. Implement bidirectional sync
4. Test sync operations

### **Week 3: Migration and API (MEDIUM PRIORITY)**
1. Build JSON migration system
2. Create REST API interface
3. Implement search and filtering
4. Add statistics endpoints

### **Week 4: Production Ready (MEDIUM PRIORITY)**
1. Docker configuration
2. Enhanced backup system
3. Security hardening
4. Performance optimization

## 📁 **File Structure After Implementation**

```
4runr-outreach-system/
├── shared/
│   ├── lead_database_manager.py      # Enhanced lead management
│   ├── airtable_sync_manager.py      # Airtable synchronization
│   ├── migration_manager.py          # JSON migration
│   ├── airtable_field_mapping.json   # Field mappings
│   └── database_config.py            # Database configuration
├── api/
│   ├── lead_api.py                   # REST API endpoints
│   ├── sync_api.py                   # Sync endpoints
│   └── stats_api.py                  # Statistics endpoints
├── scripts/
│   ├── migrate_json_to_database.py   # Migration script
│   ├── validate_migration.py         # Validation script
│   ├── sync_scheduler.py             # Automated sync
│   └── backup_manager.py             # Backup management
├── data/
│   ├── leads.db                      # Main lead database
│   └── backups/                      # Database backups
└── tests/
    ├── test_lead_database_manager.py
    ├── test_airtable_sync_manager.py
    └── test_migration_manager.py
```

## 🚀 **Getting Started Commands**

### **For New Session:**
```bash
# 1. Check current database status
python test_database_manager.py

# 2. Analyze current Airtable fields
python check_airtable_fields.py

# 3. Start with Phase 1 - Database Schema Extension
# Create: shared/lead_database_manager.py

# 4. Test database operations
python test_lead_database_manager.py

# 5. Implement Airtable sync
# Create: shared/airtable_sync_manager.py

# 6. Test sync operations
python test_airtable_sync.py
```

## 🎯 **Success Criteria**

### **Phase 1 Complete When:**
- ✅ All leads stored internally in SQLite
- ✅ No more JSON file dependencies
- ✅ Duplicate detection working
- ✅ Database schema matches Airtable

### **Phase 2 Complete When:**
- ✅ Bidirectional sync with Airtable working
- ✅ Conflict resolution implemented
- ✅ Sync status tracking functional
- ✅ Reduced Airtable API calls by 80%+

### **Phase 3 Complete When:**
- ✅ Docker deployment ready
- ✅ Automated backups working
- ✅ REST API functional
- ✅ Production monitoring enabled

## 🚨 **Critical Notes**

1. **Data Safety**: Always backup before schema changes
2. **API Limits**: Implement rate limiting for Airtable sync
3. **Field Mapping**: Verify exact Airtable field names before implementation
4. **Testing**: Test with small dataset first
5. **Rollback**: Keep rollback scripts ready

## 📞 **Next Session Kickoff**

**Start with:** "I need to implement the internal lead database system. I have the existing LocalDatabaseManager and need to extend it for complete lead management with Airtable sync. Let's start with Phase 1 - extending the database schema."

**Key Files to Review:**
- `engager/local_database_manager.py` (existing system)
- `shared/airtable_client.py` (for field mapping)
- `check_airtable_fields.py` (for current schema)

This will give you a complete internal lead management system that reduces Airtable dependency while maintaining perfect sync!