# Unified Database System Design

## Overview

The unified database system consolidates all 4Runr lead management into a single SQLite database with centralized access patterns, terminal CLI tools, and bidirectional Airtable synchronization. This design eliminates data silos while maintaining simplicity and reliability.

## Architecture

### Database Location and Access Pattern

```
4runr-agents/data/leads.db (MAIN DATABASE)
├── 4runr-agents/ (direct access)
├── 4runr-brain/ (connects via relative path)
├── 4runr-outreach-system/ (connects via relative path)
└── 4runr-lead-system/ (connects via relative path)
```

All systems will use the same connection manager pattern with environment variable configuration:
- `LEAD_DATABASE_PATH=../4runr-agents/data/leads.db` (for non-agents systems)
- `LEAD_DATABASE_PATH=data/leads.db` (for agents system)

### Centralized Connection Manager

The existing `4runr-agents/database/connection.py` will be enhanced and reused across all systems:

```python
# Enhanced connection manager features:
- Automatic path resolution (relative/absolute)
- Connection pooling and thread safety
- Automatic schema initialization
- Health checks and monitoring
- Backup and restore capabilities
```

## Components and Interfaces

### 1. Database CLI Tool (`db_cli.py`)

A command-line interface for database operations:

```bash
# Basic operations
python db_cli.py --list-leads [--limit N] [--stage STAGE]
python db_cli.py --query "SQL_QUERY"
python db_cli.py --stats
python db_cli.py --health-check

# Data management
python db_cli.py --backup [--path BACKUP_PATH]
python db_cli.py --restore --path BACKUP_PATH
python db_cli.py --migrate-data

# Sync operations
python db_cli.py --sync-to-airtable [--force]
python db_cli.py --sync-from-airtable [--force]
python db_cli.py --sync-status
```

### 2. Unified Connection Manager

Enhanced version of existing connection manager:

```python
class UnifiedDatabaseManager:
    def __init__(self, db_path: Optional[str] = None)
    def get_connection(self) -> ContextManager[sqlite3.Connection]
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor
    def execute_update(self, query: str, params: tuple = ()) -> int
    def health_check(self) -> Dict[str, Any]
    def backup_database(self, backup_path: str) -> bool
    def restore_database(self, backup_path: str) -> bool
```

### 3. Airtable Sync Manager

Handles bidirectional synchronization with Airtable:

```python
class AirtableSyncManager:
    def __init__(self, db_manager: UnifiedDatabaseManager)
    def sync_to_airtable(self, force: bool = False) -> SyncResult
    def sync_from_airtable(self, force: bool = False) -> SyncResult
    def schedule_sync_operations(self) -> None
    def resolve_conflicts(self, conflicts: List[Conflict]) -> List[Resolution]
```

### 4. Data Migration Tool

Consolidates data from existing separate databases:

```python
class DataMigrationManager:
    def discover_existing_databases(self) -> List[str]
    def migrate_all_data(self) -> MigrationResult
    def merge_duplicate_leads(self, leads: List[Lead]) -> Lead
    def create_migration_backup(self) -> str
    def generate_migration_report(self) -> MigrationReport
```

## Data Models

### Enhanced Lead Schema

The main database will use an enhanced schema that supports all system requirements:

```sql
CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    company TEXT,
    company_website TEXT,
    linkedin_url TEXT,
    phone TEXT,
    title TEXT,
    
    -- Engagement tracking
    engagement_stage TEXT DEFAULT '1st degree',
    last_contacted TIMESTAMP,
    engagement_history TEXT, -- JSON array of engagement events
    
    -- Enrichment data
    enrichment_status TEXT DEFAULT 'pending',
    enrichment_attempts INTEGER DEFAULT 0,
    enrichment_last_attempt TIMESTAMP,
    
    -- Sync tracking
    airtable_id TEXT,
    airtable_synced TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    source_system TEXT, -- Which system created this lead
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL, -- 'to_airtable', 'from_airtable'
    lead_id TEXT,
    status TEXT NOT NULL, -- 'success', 'failed', 'conflict'
    error_message TEXT,
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
);
```

### Sync Configuration

```python
@dataclass
class SyncConfig:
    # To Airtable (frequent)
    to_airtable_interval: int = 300  # 5 minutes
    to_airtable_batch_size: int = 50
    
    # From Airtable (daily)
    from_airtable_schedule: str = "02:00"  # 2 AM daily
    from_airtable_batch_size: int = 100
    
    # Retry configuration
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    # Conflict resolution
    conflict_resolution: str = "database_wins"
```

## Error Handling

### Database Connection Errors
- Automatic retry with exponential backoff
- Fallback to read-only mode if write operations fail
- Detailed logging with context information
- Health check endpoints for monitoring

### Sync Errors
- Failed syncs are logged and queued for retry
- Conflict resolution follows "database wins" strategy
- Manual conflict resolution tools available via CLI
- Sync status monitoring and alerting

### Migration Errors
- Automatic rollback on migration failure
- Detailed error reporting with affected records
- Backup creation before any migration attempt
- Manual recovery tools and procedures

## Testing Strategy

### Unit Tests
- Database connection manager functionality
- CRUD operations across all systems
- Sync manager operations (mocked Airtable API)
- CLI tool commands and error handling
- Data migration logic with test datasets

### Integration Tests
- End-to-end sync workflows with test Airtable base
- Multi-system database access patterns
- Migration from existing database files
- CLI tool integration with actual database

### Performance Tests
- Database performance under concurrent access
- Sync performance with large datasets
- Memory usage during migration operations
- Connection pooling efficiency

### Monitoring and Observability
- Database health checks and metrics
- Sync operation success/failure rates
- Performance monitoring (query times, connection counts)
- Error rate tracking and alerting

## Implementation Phases

### Phase 1: Database Consolidation
1. Enhance existing connection manager
2. Update all system configurations
3. Create data migration tool
4. Test multi-system access

### Phase 2: CLI Tool Development
1. Create database CLI tool
2. Implement basic operations (list, query, stats)
3. Add backup/restore functionality
4. Add migration commands

### Phase 3: Airtable Sync Implementation
1. Create sync manager
2. Implement to-Airtable sync (frequent)
3. Implement from-Airtable sync (daily)
4. Add conflict resolution logic

### Phase 4: Testing and Deployment
1. Comprehensive testing across all systems
2. Performance optimization
3. Documentation and training
4. Gradual rollout with monitoring