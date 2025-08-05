# 4Runr Lead Scraper

A consolidated lead management system that combines the best functionality from 4runr-agents and 4runr-lead-system into a single, focused tool for lead scraping, enrichment, and management.

## 🎯 Overview

The 4Runr Lead Scraper is the unified solution for all lead management needs in the 4Runr ecosystem. It consolidates previously separate systems into one powerful, reliable tool that handles the complete lead lifecycle from discovery to outreach readiness.

**Key Benefits:**
- ✅ **Unified Database**: Single source of truth for all lead data
- ✅ **Proven Technology**: Uses SerpAPI (not Playwright) for reliable scraping
- ✅ **Complete Pipeline**: Scraping → Enrichment → Sync → Outreach
- ✅ **Easy Integration**: Other 4Runr systems connect seamlessly
- ✅ **Daily Automation**: Set-and-forget lead generation
- ✅ **Comprehensive CLI**: Full control from command line

## 🚀 Features

### Core Functionality
- **🔍 SerpAPI Integration**: Reliable LinkedIn lead scraping using proven API
- **📧 Lead Enrichment**: Email finding and profile enhancement with multiple sources
- **🗄️ SQLite Database**: Fast, reliable local storage with full schema management
- **🔄 Airtable Sync**: Bidirectional synchronization with conflict resolution
- **⚡ CLI Interface**: Comprehensive command-line tools for all operations
- **🤖 Daily Automation**: Scheduled scraping, enrichment, and sync operations

### Advanced Features
- **📊 Migration Tools**: Consolidate data from multiple sources
- **💾 Backup System**: Automatic database backups with retention
- **📈 Analytics**: Detailed statistics and performance monitoring
- **🔧 Configuration Management**: Centralized settings with validation
- **📝 Comprehensive Logging**: Detailed logs for debugging and monitoring
- **🧪 Testing Suite**: Complete system validation and health checks

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SerpAPI account and API key
- Airtable account and API key (optional)

### Installation

1. **Navigate to the directory:**
   ```bash
   cd 4runr-lead-scraper
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```env
   SERPAPI_API_KEY=your_serpapi_key_here
   AIRTABLE_API_KEY=your_airtable_key_here
   AIRTABLE_BASE_ID=your_base_id_here
   ```

4. **Test the installation:**
   ```bash
   python test_complete_system.py
   ```

### Basic Usage

```bash
# View all available commands
python run_cli.py --help

# Scrape new leads from LinkedIn
python run_cli.py scrape --query "CEO startup" --max-leads 10

# List leads by status
python run_cli.py list --status scraped
python run_cli.py list --status enriched

# Enrich leads with email addresses
python run_cli.py enrich --max-leads 50

# Sync leads to Airtable
python run_cli.py sync --to-airtable

# View database statistics
python run_cli.py stats

# Run daily automation
python scripts/daily_scraper.py
```

## 🏗️ Architecture

```
4runr-lead-scraper/
├── cli/                    # Command-line interface
│   ├── cli.py             # Main CLI entry point
│   └── commands/          # Individual command modules
├── scraper/               # Lead scraping functionality
│   ├── serpapi_scraper.py # SerpAPI integration
│   └── lead_finder.py     # Lead discovery logic
├── enricher/              # Lead enrichment
│   ├── email_enricher.py  # Email finding
│   └── profile_enricher.py # Profile enhancement
├── database/              # Database management
│   ├── models.py          # Data models and ORM
│   ├── connection.py      # Database connections
│   └── migrations.py      # Schema management
├── sync/                  # External synchronization
│   ├── airtable_sync.py   # Airtable integration
│   └── sync_manager.py    # Sync coordination
├── config/                # Configuration management
│   └── settings.py        # Centralized settings
├── utils/                 # Shared utilities
│   ├── logging.py         # Logging configuration
│   └── validators.py      # Data validation
├── scripts/               # Automation scripts
│   ├── daily_scraper.py   # Daily automation
│   └── migrate_data.py    # Data migration
├── data/                  # Database storage
│   └── leads.db          # SQLite database
└── test_complete_system.py # System validation
```

## 🔗 System Integration

The 4Runr Lead Scraper serves as the central data hub for the entire 4Runr ecosystem:

### Connected Systems
- **🧠 4runr-brain**: Reads leads for AI-powered message generation
- **📧 4runr-outreach-system**: Accesses leads for email campaigns
- **📊 Airtable**: Bidirectional sync for team collaboration

### Database Schema
```sql
-- Core leads table with comprehensive lead information
CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    uuid TEXT UNIQUE,
    full_name TEXT,
    linkedin_url TEXT,
    email TEXT,
    company TEXT,
    title TEXT,
    location TEXT,
    industry TEXT,
    company_size TEXT,
    verified BOOLEAN DEFAULT 0,
    enriched BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'scraped',
    source TEXT,
    scraped_at TEXT,
    enriched_at TEXT,
    updated_at TEXT,
    created_at TEXT,
    airtable_id TEXT,
    airtable_synced BOOLEAN DEFAULT 0,
    raw_data TEXT
);
```

## 📚 CLI Commands Reference

### Lead Management
```bash
# Scraping
python run_cli.py scrape --query "CEO fintech" --max-leads 20
python run_cli.py scrape --company "TechCorp" --location "Toronto"

# Listing and Filtering
python run_cli.py list                           # All leads
python run_cli.py list --status enriched        # By status
python run_cli.py list --company "TechCorp"     # By company
python run_cli.py list --limit 10               # Limit results

# Enrichment
python run_cli.py enrich                         # Enrich all unenriched
python run_cli.py enrich --max-leads 25         # Limit enrichment
python run_cli.py enrich --force                 # Re-enrich existing

# Statistics
python run_cli.py stats                          # Overall statistics
python run_cli.py stats --detailed              # Detailed breakdown
```

### Database Operations
```bash
# Database management
python run_cli.py db --backup                    # Create backup
python run_cli.py db --restore backup.db        # Restore from backup
python run_cli.py db --vacuum                    # Optimize database
python run_cli.py db --check                     # Integrity check

# Data migration
python scripts/migrate_data.py --discover       # Find data sources
python scripts/migrate_data.py --migrate        # Migrate all data
```

### Synchronization
```bash
# Airtable sync
python run_cli.py sync --to-airtable            # Push to Airtable
python run_cli.py sync --from-airtable          # Pull from Airtable
python run_cli.py sync --bidirectional          # Two-way sync
```

## 🤖 Daily Automation

Set up automated lead generation with cron:

```bash
# Add to crontab (crontab -e)
# Run daily at 9 AM
0 9 * * * cd /path/to/4runr-lead-scraper && python scripts/daily_scraper.py

# Or run manually
python scripts/daily_scraper.py
```

The daily script performs:
1. 🔍 Scrapes new leads based on configured queries
2. 📧 Enriches leads with email addresses
3. 🔄 Syncs data to Airtable
4. 📊 Generates performance reports
5. 🧹 Performs database maintenance

## 🔧 Configuration

### Environment Variables
```env
# Required
SERPAPI_API_KEY=your_serpapi_key_here
LEAD_DATABASE_PATH=data/leads.db

# Optional
AIRTABLE_API_KEY=your_airtable_key_here
AIRTABLE_BASE_ID=your_base_id_here
AIRTABLE_TABLE_NAME=Table 1

# Advanced
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_RETENTION_DAYS=30
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=5
```

### Customization
- **Scraping Queries**: Edit `config/settings.py` for default search terms
- **Enrichment Sources**: Configure email finding services in enricher modules
- **Sync Frequency**: Adjust automation schedules in `scripts/daily_scraper.py`

## 🧪 Testing and Validation

### System Health Check
```bash
# Run comprehensive system test
python test_complete_system.py

# Test specific components
python -m pytest tests/                         # Unit tests
python scripts/migrate_data.py --dry-run        # Migration test
```

### Monitoring
- **Logs**: Check `logs/` directory for detailed operation logs
- **Database**: Use `python run_cli.py stats` for health metrics
- **Integration**: Verify other systems can connect to the database

## 🚀 Deployment

### Production Setup
1. **Environment**: Set up production `.env` with real API keys
2. **Database**: Ensure `data/` directory has proper permissions
3. **Automation**: Configure cron jobs for daily operations
4. **Monitoring**: Set up log rotation and monitoring alerts
5. **Backups**: Verify backup system is working

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 100MB for application, additional for database growth
- **Network**: Outbound HTTPS access for APIs

## 📋 Migration from Old Systems

If migrating from 4runr-agents or 4runr-lead-system:

1. **Backup existing data**:
   ```bash
   cp 4runr-agents/data/leads.db backups/agents_backup.db
   ```

2. **Run migration**:
   ```bash
   python scripts/migrate_data.py --migrate
   ```

3. **Validate migration**:
   ```bash
   python test_complete_system.py
   ```

4. **Update integrations**: Other systems automatically use the new database

## 🆘 Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python run_cli.py --help
```

**Database Locked**:
```bash
# Check for running processes
ps aux | grep python
# Kill if necessary, then retry
```

**API Rate Limits**:
- SerpAPI: Check your usage at serpapi.com
- Reduce concurrent requests in settings

**Sync Issues**:
- Verify Airtable API key and base ID
- Check table permissions in Airtable

### Getting Help
1. Check logs in `logs/` directory
2. Run system test: `python test_complete_system.py`
3. Verify configuration: `python run_cli.py stats`
4. Review migration logs in database

## 📄 License

UNLICENSED - Private use only for 4Runr systems