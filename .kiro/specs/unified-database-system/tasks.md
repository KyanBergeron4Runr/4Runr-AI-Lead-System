# Implementation Plan

- [ ] 1. Enhance the centralized database connection manager
  - Modify `4runr-agents/database/connection.py` to support relative path resolution for other systems
  - Add backup and restore functionality to the connection manager
  - Implement health check and monitoring capabilities
  - Add automatic schema migration support
  - _Requirements: 1.1, 1.3, 5.1, 5.3, 5.5_

- [ ] 2. Update environment configurations for unified database access
  - Add `LEAD_DATABASE_PATH=../4runr-agents/data/leads.db` to `4runr-brain/.env`
  - Add `LEAD_DATABASE_PATH=../4runr-agents/data/leads.db` to `4runr-outreach-system/.env`
  - Add `LEAD_DATABASE_PATH=../4runr-agents/data/leads.db` to `4runr-lead-system/.env`
  - Update all systems to use the centralized connection manager
  - _Requirements: 1.1, 5.2_

- [ ] 3. Create data migration tool for consolidating existing databases
  - Create `4runr-agents/database/migration_tool.py` to discover all existing database files
  - Implement logic to merge duplicate leads based on email address
  - Create backup functionality for original database files before migration
  - Generate detailed migration reports showing what data was consolidated
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4. Implement database CLI tool for terminal access
  - Create `4runr-agents/db_cli.py` with argument parsing and command structure
  - Implement `--list-leads` command with filtering options (limit, stage)
  - Implement `--query` command for executing custom SQL queries
  - Implement `--stats` command showing database statistics and health metrics
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Add backup and administrative commands to CLI tool
  - Implement `--backup` command to create database backups
  - Implement `--restore` command to restore from backup files
  - Implement `--migrate-data` command to run the data migration tool
  - Implement `--help` command with comprehensive usage documentation
  - _Requirements: 2.5, 2.6, 4.4_

- [ ] 6. Create Airtable sync manager for bidirectional synchronization
  - Create `4runr-agents/sync/airtable_sync_manager.py` with sync configuration
  - Implement database-to-Airtable sync functionality (frequent, 5-minute intervals)
  - Implement Airtable-to-database sync functionality (daily scheduled)
  - Add conflict resolution logic with "database wins" strategy
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 7. Implement sync retry logic and error handling
  - Add exponential backoff retry mechanism for failed sync operations
  - Implement comprehensive logging for all sync operations with timestamps
  - Create sync status tracking and monitoring capabilities
  - Add CLI commands for sync operations (`--sync-to-airtable`, `--sync-from-airtable`, `--sync-status`)
  - _Requirements: 3.5, 3.6_

- [ ] 8. Update all systems to use the unified database connection
  - Modify `4runr-brain` to use the centralized connection manager
  - Modify `4runr-outreach-system` to use the centralized connection manager instead of local database
  - Modify `4runr-lead-system` to use the centralized connection manager
  - Remove or deprecate separate database files and connection logic
  - _Requirements: 1.1, 1.2, 5.1, 5.4_

- [ ] 9. Implement comprehensive testing for the unified system
  - Create unit tests for the enhanced connection manager
  - Create integration tests for multi-system database access
  - Create tests for the CLI tool commands and functionality
  - Create tests for the Airtable sync manager with mocked API calls
  - _Requirements: 1.2, 2.1, 3.1, 5.3_

- [ ] 10. Create database schema migration and validation
  - Enhance the existing schema to support all system requirements (engagement tracking, sync status, etc.)
  - Implement automatic schema validation and migration on system startup
  - Add database integrity checks and repair functionality
  - Create schema documentation and migration history tracking
  - _Requirements: 1.3, 5.5_

- [ ] 11. Implement sync scheduling and automation
  - Create scheduled task for daily Airtable-to-database sync
  - Implement background process for frequent database-to-Airtable sync
  - Add sync monitoring and alerting for failed operations
  - Create sync performance metrics and logging
  - _Requirements: 3.2, 3.3, 3.6_

- [ ] 12. Run data migration and system validation
  - Execute the data migration tool to consolidate all existing databases
  - Validate that all systems can successfully connect to the unified database
  - Test all CLI commands with real data
  - Verify Airtable sync operations work correctly
  - Create system documentation and usage guides
  - _Requirements: 4.1, 4.4, 1.1, 2.1, 3.1_