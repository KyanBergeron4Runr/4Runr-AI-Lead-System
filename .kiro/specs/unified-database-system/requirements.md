# Requirements Document

## Introduction

This feature consolidates all 4Runr systems to use a single centralized database for lead management, eliminates data silos, provides terminal access for database operations, and establishes a clean bidirectional sync with Airtable. The goal is to simplify the architecture while maintaining all existing functionality.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want all 4Runr systems to connect to one centralized database, so that lead data is consistent across all agents and systems.

#### Acceptance Criteria

1. WHEN any system (4runr-agents, 4runr-brain, 4runr-outreach-system, 4runr-lead-system) needs database access THEN it SHALL connect to the main database at `4runr-agents/data/leads.db`
2. WHEN a lead is created or updated by any system THEN all other systems SHALL see the same data immediately
3. WHEN the system starts THEN it SHALL automatically create the main database if it doesn't exist
4. IF a system cannot connect to the main database THEN it SHALL log an error and fail gracefully

### Requirement 2

**User Story:** As a developer, I want to access and manage the database from the terminal using simple commands, so that I can inspect data, run queries, and troubleshoot issues easily.

#### Acceptance Criteria

1. WHEN I run a database command from the terminal THEN it SHALL connect to the main centralized database
2. WHEN I use the command `python db_cli.py --list-leads` THEN it SHALL display all leads in a readable format
3. WHEN I use the command `python db_cli.py --query "SELECT * FROM leads LIMIT 5"` THEN it SHALL execute the SQL query and display results
4. WHEN I use the command `python db_cli.py --stats` THEN it SHALL show database statistics (total leads, by stage, recent activity)
5. WHEN I use the command `python db_cli.py --backup` THEN it SHALL create a backup of the database
6. WHEN I use the command `python db_cli.py --help` THEN it SHALL display all available commands

### Requirement 3

**User Story:** As a business user, I want the database to sync with Airtable in both directions with proper scheduling, so that I can work with lead data in Airtable while keeping the local system as the source of truth.

#### Acceptance Criteria

1. WHEN new leads are added to the database THEN they SHALL be synced to Airtable within 5 minutes
2. WHEN leads are updated in the database THEN the changes SHALL be synced to Airtable within 5 minutes
3. WHEN leads are updated in Airtable THEN they SHALL be synced to the database once daily at a scheduled time
4. WHEN a sync conflict occurs (same lead updated in both places) THEN the database version SHALL take precedence
5. WHEN a sync fails THEN it SHALL be retried up to 3 times with exponential backoff
6. WHEN sync operations complete THEN they SHALL log success/failure status with timestamps

### Requirement 4

**User Story:** As a system administrator, I want to migrate existing data from separate databases to the unified system, so that no lead data is lost during the consolidation.

#### Acceptance Criteria

1. WHEN the migration runs THEN it SHALL identify all existing database files across all systems
2. WHEN duplicate leads are found during migration THEN it SHALL merge them intelligently based on email address
3. WHEN the migration completes THEN it SHALL create a backup of all original database files
4. WHEN the migration completes THEN it SHALL generate a report showing what data was migrated
5. IF the migration fails THEN it SHALL restore the original state and log detailed error information

### Requirement 5

**User Story:** As a developer, I want all systems to use the same database connection pattern and configuration, so that the codebase is consistent and maintainable.

#### Acceptance Criteria

1. WHEN any system needs database access THEN it SHALL use the centralized connection manager
2. WHEN database configuration changes THEN it SHALL be managed through environment variables only
3. WHEN a system starts THEN it SHALL validate database connectivity before proceeding
4. WHEN database operations fail THEN they SHALL use consistent error handling and logging patterns
5. WHEN the database schema needs updates THEN they SHALL be applied automatically through migrations