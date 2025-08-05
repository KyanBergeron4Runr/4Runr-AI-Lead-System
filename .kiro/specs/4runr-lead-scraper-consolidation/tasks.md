# Implementation Plan

- [x] 1. Create the new 4runr-lead-scraper directory structure


  - Create the main directory `4runr-lead-scraper/` with all subdirectories (scraper, enricher, database, sync, cli, data, config, utils, scripts)
  - Set up basic Python package structure with `__init__.py` files
  - Create `requirements.txt` with necessary dependencies (no Playwright, focus on SerpAPI, SQLite, requests)
  - Create `.env.example` template with required environment variables
  - _Requirements: 1.1, 2.3_

- [x] 2. Extract and consolidate the working SerpAPI scraper from 4runr-agents


  - Copy the working `serpapi_linkedin_scraper.py` from 4runr-agents to `scraper/serpapi_scraper.py`
  - Remove any Playwright or unused scraping code
  - Create `scraper/lead_finder.py` for lead discovery logic
  - Ensure SerpAPI key validation and error handling
  - _Requirements: 2.1, 2.4, 3.2_

- [x] 3. Extract and enhance the database system from 4runr-agents



  - Copy the working database connection manager from `4runr-agents/database/connection.py`
  - Create enhanced `database/models.py` with the consolidated lead schema
  - Implement `database/migrations.py` for schema management and updates
  - Add database backup and restore functionality
  - _Requirements: 2.2, 3.1, 4.1_

- [x] 4. Extract and consolidate the lead enrichment system


  - Copy working enrichment logic from 4runr-agents to `enricher/email_enricher.py`
  - Create `enricher/profile_enricher.py` for additional data enrichment
  - Remove any unused enrichment methods or APIs
  - Ensure enrichment results are properly saved to the database
  - _Requirements: 3.4, 4.2_

- [x] 5. Create the unified CLI interface



  - Implement `cli/cli.py` with argument parsing for all lead operations
  - Create command modules in `cli/commands/` for scrape, list, show, stats, enrich, db, and sync operations
  - Implement `--list-leads`, `--scrape`, `--enrich`, and `--stats` commands
  - Add database query and backup commands to the CLI
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 6. Implement Airtable synchronization system



  - Copy working Airtable sync logic from 4runr-agents to `sync/airtable_sync.py`
  - Create `sync/sync_manager.py` for coordinating sync operations
  - Ensure leads are synced to Airtable after scraping and enrichment
  - Add CLI commands for manual sync operations (`--sync-to-airtable`, `--sync-from-airtable`)
  - _Requirements: 4.1, 4.3_

- [x] 7. Create data migration tool to consolidate existing data



  - Implement `scripts/migrate_data.py` to combine data from 4runr-agents and 4runr-lead-system
  - Add logic to detect and merge duplicate leads based on email or LinkedIn URL
  - Create backup functionality for original databases before migration
  - Generate detailed migration report showing consolidated data
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 8. Implement configuration and utilities


  - Create `config/settings.py` with unified configuration classes for scraper, database, and Airtable
  - Implement `utils/logging.py` with consistent logging across all modules
  - Create `utils/validators.py` for data validation and cleaning
  - Ensure all modules use the centralized configuration system
  - _Requirements: 3.1, 3.5_

- [x] 9. Create daily automation script



  - Implement `scripts/daily_scraper.py` that runs scraping, enrichment, and sync operations
  - Add proper error handling and logging for automated operations
  - Ensure leads are marked with proper status after each operation (scraped, enriched, ready for outreach)
  - Create scheduling documentation for cron job setup
  - _Requirements: 4.3, 4.4_

- [x] 10. Run data migration and validate consolidation


  - Execute the data migration tool to combine all existing lead data
  - Validate that no data was lost during the migration process
  - Test that all CLI commands work with the migrated data
  - Verify that Airtable sync works correctly with the consolidated database
  - _Requirements: 6.1, 6.4, 6.5_

- [x] 11. Update other systems to connect to the new database


  - Update `4runr-brain/.env` to set `LEAD_DATABASE_PATH=../4runr-lead-scraper/data/leads.db`
  - Update `4runr-outreach-system/.env` to set `LEAD_DATABASE_PATH=../4runr-lead-scraper/data/leads.db`
  - Test that 4runr-brain can successfully read lead data from the new database
  - Test that 4runr-outreach-system can successfully read lead data from the new database
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 12. Test the complete consolidated system


  - Run end-to-end tests: scraping → enrichment → database storage → Airtable sync
  - Test all CLI commands with real data to ensure functionality
  - Verify that daily automation script works correctly
  - Test integration with 4runr-brain and 4runr-outreach-system
  - _Requirements: 1.1, 3.5, 4.1, 5.4_

- [x] 13. Archive old systems and clean up codebase


  - Create backups of 4runr-agents and 4runr-lead-system directories
  - Archive or remove the old system directories after confirming everything works
  - Update any documentation or README files to reference the new system
  - Remove unused dependencies and clean up the workspace
  - _Requirements: 1.3, 2.3_

- [x] 14. Create comprehensive documentation







  - Write detailed README.md for the 4runr-lead-scraper system
  - Document all CLI commands with examples and usage instructions
  - Create setup and installation guide for new developers
  - Document the database schema and integration points for other systems
  - _Requirements: 3.1, 3.2, 5.3_