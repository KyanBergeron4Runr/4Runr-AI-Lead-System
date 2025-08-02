# Local Lead Database Design

## Overview

The Local Lead Database system will provide a SQLite-based data layer for the 4Runr AI Lead System. This design implements a comprehensive database schema that captures all lead data, pipeline states, and relationships while providing a clean API for data operations and seamless integration with existing systems.

## Architecture

### Database Technology Choice: SQLite

**Why SQLite:**
- **File-based**: Single file database that's easy to backup, version, and deploy
- **Zero configuration**: No server setup required, works out of the box
- **ACID compliant**: Reliable transactions and data integrity
- **Cross-platform**: Works on all development and deployment environments
- **Lightweight**: Perfect for local development and moderate data volumes
- **SQL support**: Full SQL query capabilities for complex operations

### Database Location and Structure

```
4runr-agents/
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── connection.py      # Database connection management
│   ├── operations.py      # High-level database operations
│   ├── sync.py           # Airtable synchronization
│   ├── migrations/       # Database schema migrations
│   └── seeds/           # Sample data for development
├── data/
│   ├── leads.db         # Main SQLite database file
│   ├── leads_test.db    # Test database
│   └── backups/         # Database backups
```

## Data Models

### Core Tables

#### 1. Leads Table
```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,           -- Unique identifier
    airtable_id TEXT UNIQUE,             -- Airtable record ID
    
    -- Basic Information
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    company TEXT NOT NULL,
    email TEXT,
    linkedin_url TEXT,
    website TEXT,
    location TEXT,
    
    -- Pipeline Status
    status TEXT DEFAULT 'raw',           -- raw, scraped, enriched, engaged
    pipeline_stage TEXT DEFAULT 'new',   -- new, processing, completed, failed
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    
    -- Soft delete
    deleted_at TIMESTAMP NULL
);
```

#### 2. Lead Enrichment Table
```sql
CREATE TABLE lead_enrichment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    
    -- Website Analysis
    website_content TEXT,
    company_description TEXT,
    services TEXT,
    tone TEXT,
    website_insights TEXT,
    
    -- Email Enrichment
    email_confidence TEXT,              -- real, pattern, guess
    email_source TEXT,                  -- scraped, generated, verified
    email_verification_status TEXT,     -- verified, unverified, bounced
    
    -- Traits and Analysis
    detected_traits TEXT,               -- JSON array of traits
    trait_confidence_scores TEXT,       -- JSON object with confidence scores
    business_focus TEXT,
    company_size TEXT,
    
    -- Enrichment Metadata
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enrichment_method TEXT,             -- manual, automated, ai
    confidence_score REAL,
    
    FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
);
```

#### 3. Campaigns Table
```sql
CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    campaign_id TEXT UNIQUE NOT NULL,
    
    -- Campaign Details
    campaign_type TEXT NOT NULL,        -- initial, followup, recycled
    message_type TEXT,                  -- hook, proof, fomo
    subject_line TEXT,
    message_content TEXT,
    
    -- Campaign Status
    status TEXT DEFAULT 'draft',        -- draft, queued, sent, delivered, opened, replied
    quality_score REAL,
    
    -- Scheduling
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    replied_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
);
```

#### 4. Pipeline Activities Table
```sql
CREATE TABLE pipeline_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    
    -- Activity Details
    activity_type TEXT NOT NULL,        -- scraped, enriched, campaign_created, email_sent
    activity_status TEXT NOT NULL,      -- success, failed, pending
    description TEXT,
    
    -- Activity Data
    input_data TEXT,                    -- JSON of input parameters
    output_data TEXT,                   -- JSON of results
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    
    -- Agent Information
    agent_name TEXT,                    -- scraper, enricher, engager, brain
    agent_version TEXT,
    
    FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
);
```

#### 5. Sync Log Table
```sql
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Sync Details
    sync_type TEXT NOT NULL,            -- pull_from_airtable, push_to_airtable
    sync_status TEXT NOT NULL,          -- success, failed, partial
    
    -- Statistics
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    
    -- Error Handling
    error_message TEXT,
    error_details TEXT                  -- JSON with detailed error info
);
```

### Database Indexes

```sql
-- Performance indexes
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_company ON leads(company);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_airtable_id ON leads(airtable_id);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_campaigns_lead_id ON campaigns(lead_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_activities_lead_id ON pipeline_activities(lead_id);
CREATE INDEX idx_activities_type ON pipeline_activities(activity_type);
```

## Components and Interfaces

### 1. Database Connection Manager (`connection.py`)

```python
class DatabaseManager:
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
        self.engine = None
        self.session_factory = None
    
    def initialize(self):
        """Initialize database connection and create tables"""
        
    def get_session(self):
        """Get database session for operations"""
        
    def close(self):
        """Close database connections"""
        
    def backup(self, backup_path: str):
        """Create database backup"""
        
    def restore(self, backup_path: str):
        """Restore from backup"""
```

### 2. Lead Operations API (`operations.py`)

```python
class LeadOperations:
    def create_lead(self, lead_data: dict) -> Lead:
        """Create a new lead"""
        
    def get_lead(self, lead_id: int) -> Lead:
        """Get lead by ID"""
        
    def find_leads(self, **filters) -> List[Lead]:
        """Find leads with filters"""
        
    def update_lead(self, lead_id: int, updates: dict) -> Lead:
        """Update lead data"""
        
    def delete_lead(self, lead_id: int, soft_delete: bool = True):
        """Delete lead (soft delete by default)"""
        
    def get_leads_by_status(self, status: str) -> List[Lead]:
        """Get leads by pipeline status"""
        
    def search_leads(self, query: str) -> List[Lead]:
        """Full-text search across leads"""
        
    def get_lead_history(self, lead_id: int) -> List[PipelineActivity]:
        """Get complete activity history for a lead"""
```

### 3. Airtable Synchronization (`sync.py`)

```python
class AirtableSync:
    def __init__(self, airtable_client, db_operations):
        self.airtable = airtable_client
        self.db = db_operations
    
    def pull_from_airtable(self) -> SyncResult:
        """Pull all leads from Airtable to local DB"""
        
    def push_to_airtable(self, lead_ids: List[int] = None) -> SyncResult:
        """Push local changes to Airtable"""
        
    def sync_bidirectional(self) -> SyncResult:
        """Two-way sync with conflict resolution"""
        
    def resolve_conflicts(self, conflicts: List[Conflict]) -> List[Resolution]:
        """Handle sync conflicts (Airtable wins by default)"""
```

### 4. Migration System (`migrations/`)

```python
class Migration:
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
    
    def up(self, db_session):
        """Apply migration"""
        pass
    
    def down(self, db_session):
        """Rollback migration"""
        pass

class MigrationRunner:
    def run_migrations(self):
        """Run pending migrations"""
        
    def rollback_migration(self, target_version: str):
        """Rollback to specific version"""
```

## Error Handling

### Database Error Types

1. **Connection Errors**: Database file locked, permission issues
2. **Schema Errors**: Migration failures, constraint violations
3. **Sync Errors**: Airtable API failures, network issues
4. **Data Integrity Errors**: Duplicate keys, foreign key violations

### Error Recovery Strategies

1. **Automatic Retry**: For transient network/API errors
2. **Graceful Degradation**: Continue with local data if sync fails
3. **Data Validation**: Prevent corrupt data from entering the system
4. **Backup Recovery**: Restore from backup if database corruption occurs

## Testing Strategy

### Unit Tests
- Database model validation
- CRUD operations
- Migration scripts
- Sync logic

### Integration Tests
- Airtable synchronization
- Pipeline integration
- Error handling scenarios

### Performance Tests
- Query performance with large datasets
- Bulk operation efficiency
- Concurrent access handling

## Implementation Plan

### Phase 1: Core Database Setup
1. Create database schema and models
2. Implement basic CRUD operations
3. Set up migration system
4. Create development seeds

### Phase 2: Airtable Integration
1. Implement sync mechanisms
2. Add conflict resolution
3. Create sync monitoring and logging
4. Test with production Airtable data

### Phase 3: Pipeline Integration
1. Update agents to use database
2. Maintain JSON compatibility layer
3. Add activity logging
4. Performance optimization

### Phase 4: Advanced Features
1. Full-text search capabilities
2. Data analytics and reporting
3. Advanced backup/restore
4. Performance monitoring