# 4Runr Lead Scraper Consolidation Design

## Overview

The consolidated 4runr-lead-scraper system combines the best working parts of 4runr-agents (Python, SerpAPI, SQLite database) and 4runr-lead-system (clean architecture, CLI tools) into a single, focused lead management system. This eliminates redundancy while maintaining all proven functionality.

## Architecture

### System Structure

```
4runr-lead-scraper/
├── scraper/                 # SerpAPI-based lead scraping
│   ├── serpapi_scraper.py   # Main scraping engine
│   └── lead_finder.py       # Lead discovery logic
├── enricher/                # Lead data enrichment
│   ├── email_enricher.py    # Email finding (web scraping)
│   └── profile_enricher.py  # Additional data enrichment
├── database/                # Database management
│   ├── connection.py        # SQLite connection manager
│   ├── models.py           # Lead data models
│   └── migrations.py       # Schema management
├── sync/                    # External integrations
│   ├── airtable_sync.py    # Airtable synchronization
│   └── sync_manager.py     # Sync coordination
├── cli/                     # Command-line interface
│   ├── cli.py              # Main CLI commands
│   └── commands/           # Individual command modules
├── data/                    # Data storage
│   └── leads.db            # Main SQLite database
├── config/                  # Configuration management
│   └── settings.py         # Environment and settings
├── utils/                   # Shared utilities
│   ├── logging.py          # Logging configuration
│   └── validators.py       # Data validation
├── scripts/                 # Automation scripts
│   ├── daily_scraper.py    # Daily automation
│   └── migrate_data.py     # Data migration tool
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # Documentation
```

### Data Flow

```
SerpAPI → Lead Scraper → Database → Enricher → Database → Airtable Sync
    ↓                        ↑                      ↑
CLI Commands ←──────────────┘              Other Systems
                                          (4runr-brain,
                                           4runr-outreach)
```

## Components and Interfaces

### 1. SerpAPI Scraper Engine

Consolidates the working SerpAPI scraping logic from 4runr-agents:

```python
class SerpAPILeadScraper:
    def __init__(self, api_key: str)
    def search_montreal_ceos(self, max_results: int = 10) -> List[Lead]
    def search_by_company_type(self, company_type: str, location: str) -> List[Lead]
    def validate_linkedin_profiles(self, leads: List[Lead]) -> List[Lead]
    def save_leads_to_database(self, leads: List[Lead]) -> bool
```

### 2. Database Management

Enhanced version of the working database system from 4runr-agents:

```python
class LeadDatabase:
    def __init__(self, db_path: str = "data/leads.db")
    def create_lead(self, lead_data: dict) -> str
    def get_lead(self, lead_id: str) -> Optional[Lead]
    def update_lead(self, lead_id: str, updates: dict) -> bool
    def search_leads(self, filters: dict) -> List[Lead]
    def get_leads_needing_enrichment(self) -> List[Lead]
    def mark_lead_enriched(self, lead_id: str, enrichment_data: dict) -> bool
```

### 3. Lead Enrichment System

Combines the working enrichment logic:

```python
class LeadEnricher:
    def __init__(self, database: LeadDatabase)
    def enrich_lead_emails(self, lead: Lead) -> EnrichmentResult
    def enrich_company_data(self, lead: Lead) -> EnrichmentResult
    def batch_enrich_leads(self, max_leads: int = 50) -> List[EnrichmentResult]
    def save_enrichment_results(self, results: List[EnrichmentResult]) -> bool
```

### 4. CLI Interface

Clean command-line interface combining best practices from both systems:

```bash
# Lead scraping
python cli.py scrape --max-leads 10 --location "Montreal"
python cli.py scrape --company-type "tech startups"

# Lead management
python cli.py list --status "needs_enrichment" --limit 20
python cli.py show --lead-id "lead_123"
python cli.py stats --date-range "last_week"

# Enrichment operations
python cli.py enrich --max-leads 50
python cli.py enrich --lead-id "lead_123"

# Database operations
python cli.py db --backup
python cli.py db --query "SELECT * FROM leads WHERE enriched = 1"
python cli.py db --migrate

# Sync operations
python cli.py sync --to-airtable
python cli.py sync --from-airtable
python cli.py sync --status
```

### 5. Airtable Synchronization

Maintains the working sync functionality:

```python
class AirtableSync:
    def __init__(self, database: LeadDatabase, airtable_config: dict)
    def sync_leads_to_airtable(self, leads: List[Lead]) -> SyncResult
    def sync_updates_from_airtable(self) -> SyncResult
    def handle_sync_conflicts(self, conflicts: List[Conflict]) -> List[Resolution]
    def schedule_automatic_sync(self) -> None
```

## Data Models

### Enhanced Lead Schema

Consolidates the best fields from both systems:

```sql
CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    company TEXT,
    title TEXT,
    linkedin_url TEXT UNIQUE,
    company_website TEXT,
    phone TEXT,
    
    -- Scraping metadata
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scraping_source TEXT DEFAULT 'serpapi',
    search_query TEXT,
    search_context TEXT,
    
    -- Enrichment status
    enriched BOOLEAN DEFAULT FALSE,
    enrichment_attempts INTEGER DEFAULT 0,
    enrichment_last_attempt TIMESTAMP,
    enrichment_method TEXT,
    
    -- Lead qualification
    lead_score INTEGER,
    company_size TEXT,
    industry TEXT,
    location TEXT,
    
    -- Engagement tracking
    status TEXT DEFAULT 'scraped', -- scraped, enriched, ready, contacted, responded
    ready_for_outreach BOOLEAN DEFAULT FALSE,
    last_contacted TIMESTAMP,
    
    -- Sync tracking
    airtable_id TEXT,
    airtable_synced TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_enriched ON leads(enriched);
CREATE INDEX idx_leads_ready_for_outreach ON leads(ready_for_outreach);
CREATE INDEX idx_leads_scraped_at ON leads(scraped_at);
CREATE INDEX idx_leads_email ON leads(email);
```

### Configuration Management

Unified environment configuration:

```python
# config/settings.py
@dataclass
class ScraperConfig:
    serpapi_key: str
    max_leads_per_run: int = 10
    search_location: str = "Montreal, Quebec, Canada"
    search_queries: List[str] = field(default_factory=lambda: ["CEO", "Founder", "President"])

@dataclass
class DatabaseConfig:
    db_path: str = "data/leads.db"
    backup_enabled: bool = True
    backup_retention_days: int = 30

@dataclass
class AirtableConfig:
    api_key: str
    base_id: str
    table_name: str = "Leads"
    sync_interval_minutes: int = 30

@dataclass
class EnrichmentConfig:
    max_email_attempts: int = 2
    max_website_attempts: int = 2
    enrichment_timeout_seconds: int = 30
```

## Error Handling

### Scraping Error Management
- SerpAPI rate limiting and quota management
- Invalid LinkedIn URL handling
- Network timeout and retry logic
- Duplicate lead detection and merging

### Database Error Handling
- Connection failure recovery
- Transaction rollback on errors
- Schema migration error handling
- Backup and restore capabilities

### Enrichment Error Management
- Website scraping failures
- Email validation errors
- Rate limiting for web requests
- Partial enrichment success handling

## Testing Strategy

### Unit Tests
- SerpAPI scraper functionality with mocked API responses
- Database operations (CRUD, migrations, backups)
- Lead enrichment logic with test websites
- CLI command parsing and execution
- Airtable sync operations with mocked API

### Integration Tests
- End-to-end scraping to database workflow
- Database to Airtable synchronization
- CLI commands with real database operations
- Daily automation script execution
- Data migration from old systems

### Performance Tests
- Large batch scraping operations
- Database performance with thousands of leads
- Concurrent enrichment operations
- Memory usage during bulk operations

## Migration Strategy

### Phase 1: System Creation
1. Create new 4runr-lead-scraper directory structure
2. Extract working SerpAPI scraper from 4runr-agents
3. Extract working database system from 4runr-agents
4. Create unified CLI interface
5. Implement basic testing

### Phase 2: Data Migration
1. Create migration script to combine data from both old systems
2. Merge duplicate leads intelligently
3. Preserve all enrichment data and metadata
4. Create backups of original systems
5. Validate data integrity after migration

### Phase 3: Integration Updates
1. Update 4runr-brain to connect to new database location
2. Update 4runr-outreach-system to connect to new database location
3. Update any automation scripts or cron jobs
4. Test end-to-end pipeline functionality

### Phase 4: Cleanup
1. Archive old 4runr-agents and 4runr-lead-system directories
2. Update documentation and README files
3. Remove unused dependencies and code
4. Verify all integrations are working

## Implementation Benefits

### Simplified Architecture
- Single system for lead operations eliminates confusion
- Clear separation of concerns (scrape, enrich, sync)
- Focused codebase that's easier to maintain and debug

### Proven Technology Stack
- Uses only the working tools (SerpAPI, SQLite, Python)
- Removes unused complexity (Playwright, Node.js components)
- Maintains all existing functionality without disruption

### Better Developer Experience
- Clear CLI commands for all operations
- Comprehensive logging and error handling
- Easy integration points for other systems
- Simplified deployment and configuration

### Operational Improvements
- Single database eliminates data silos
- Consistent data models across all operations
- Reliable daily automation without conflicts
- Better monitoring and debugging capabilities