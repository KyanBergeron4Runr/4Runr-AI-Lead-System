# Archived Systems

This directory contains the old systems that have been consolidated into the new `4runr-lead-scraper` system.

## Archived on: August 4, 2025

## Systems Archived:

### 4runr-agents
- **Purpose**: Original lead scraping and enrichment system
- **Key Features**: SerpAPI integration, SQLite database, lead enrichment
- **Database**: `4runr-agents/data/leads.db` (21 leads migrated to new system)
- **Status**: Replaced by 4runr-lead-scraper

### 4runr-lead-system  
- **Purpose**: Node.js based lead management system
- **Key Features**: Airtable integration, Docker deployment
- **Database**: Used Airtable directly (no local database)
- **Status**: Functionality consolidated into 4runr-lead-scraper

## Migration Summary

- **Total leads migrated**: 20 leads (1 duplicate skipped)
- **Migration date**: August 4, 2025
- **Backup created**: `backups/leads_backup_20250804_180453.db`
- **New system**: `4runr-lead-scraper/`

## Data Consolidation

All lead data from these systems has been consolidated into:
- **New database**: `4runr-lead-scraper/data/leads.db`
- **Unified schema**: Enhanced lead model with all fields from both systems
- **Migration log**: Tracked in `migration_log` table

## Integration Updates

The following systems have been updated to use the new database:
- **4runr-brain**: Updated to connect to `4runr-lead-scraper/data/leads.db`
- **4runr-outreach-system**: Configuration added for future integration

## Security Note

⚠️ **Sensitive files removed**: The `.env` files containing API keys have been removed from this archive for security reasons. If you need to restore these systems, you'll need to recreate the `.env` files with your API keys.

## Restoration Instructions

If you need to restore these systems:

1. Move the directories back to the root:
   ```bash
   mv archived_systems/4runr-agents ./
   mv archived_systems/4runr-lead-system ./
   ```

2. Recreate the `.env` files with your API keys:
   ```bash
   # Copy from examples and add your keys
   cp 4runr-agents/.env.example 4runr-agents/.env
   cp 4runr-lead-system/.env.example 4runr-lead-system/.env
   # Edit the files to add your actual API keys
   ```

3. Restore the original database (if needed):
   ```bash
   cp backups/leads_backup_20250804_180453.db 4runr-agents/data/leads.db
   ```

4. Update 4runr-brain to use the old database path:
   ```python
   db_path = str(Path(__file__).parent.parent / "4runr-agents" / "data" / "leads.db")
   ```

## New System Benefits

The new `4runr-lead-scraper` system provides:
- ✅ Unified database for all lead data
- ✅ Consolidated scraping, enrichment, and sync functionality  
- ✅ Comprehensive CLI interface
- ✅ Daily automation scripts
- ✅ Better error handling and logging
- ✅ Simplified deployment and maintenance
- ✅ Elimination of duplicate functionality

## Support

For questions about the archived systems or migration, refer to:
- Migration logs in `4runr-lead-scraper/data/leads.db` (migration_log table)
- System test results from `test_complete_system.py`
- New system documentation in `4runr-lead-scraper/README.md`