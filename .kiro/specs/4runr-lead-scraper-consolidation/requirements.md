# Requirements Document

## Introduction

This feature consolidates the redundant 4runr-agents and 4runr-lead-system into a single, focused "4runr-lead-scraper" system. The goal is to eliminate confusion, remove duplicate functionality, and create one clean system that handles lead scraping and management using the proven tools (SerpAPI, SQLite database) without unnecessary complexity.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to consolidate 4runr-agents and 4runr-lead-system into a single 4runr-lead-scraper system, so that there's no confusion about which system to use for lead management.

#### Acceptance Criteria

1. WHEN the consolidation is complete THEN there SHALL be only one system called "4runr-lead-scraper" for lead operations
2. WHEN I need to scrape leads THEN I SHALL use the 4runr-lead-scraper system only
3. WHEN the consolidation is complete THEN the old 4runr-agents and 4runr-lead-system directories SHALL be archived or removed
4. WHEN other systems need lead data THEN they SHALL connect to the 4runr-lead-scraper database

### Requirement 2

**User Story:** As a system administrator, I want the consolidated system to use only the proven tools (SerpAPI for scraping, SQLite for database), so that we eliminate unused code and focus on what actually works.

#### Acceptance Criteria

1. WHEN scraping leads THEN the system SHALL use SerpAPI exclusively (no Playwright or other scraping methods)
2. WHEN storing lead data THEN the system SHALL use SQLite database at `4runr-lead-scraper/data/leads.db`
3. WHEN unused code is found (Playwright, mock scrapers, etc.) THEN it SHALL be removed from the codebase
4. WHEN the system starts THEN it SHALL validate that SerpAPI key is configured and working

### Requirement 3

**User Story:** As a developer, I want clear, focused functionality in the consolidated system, so that I can easily understand and maintain the lead scraping operations.

#### Acceptance Criteria

1. WHEN I examine the system structure THEN it SHALL have clear modules: scraper, enricher, database, and CLI
2. WHEN I need to run lead scraping THEN there SHALL be simple commands like `python scrape_leads.py`
3. WHEN I need to view leads THEN there SHALL be CLI commands like `python cli.py --list-leads`
4. WHEN I need to enrich leads THEN there SHALL be commands like `python enrich_leads.py`
5. WHEN the system runs THEN it SHALL log operations clearly and save results to the database

### Requirement 4

**User Story:** As a business user, I want the consolidated system to maintain all existing functionality while being simpler to use, so that lead operations continue working without disruption.

#### Acceptance Criteria

1. WHEN leads are scraped THEN they SHALL be saved to both the local database and synced to Airtable
2. WHEN leads are enriched THEN the enrichment data SHALL be added to existing lead records
3. WHEN the system runs daily THEN it SHALL automatically scrape and enrich new leads
4. WHEN leads are processed THEN they SHALL be marked with proper status (scraped, enriched, ready for outreach)

### Requirement 5

**User Story:** As a system integrator, I want other systems (4runr-brain, 4runr-outreach-system) to easily connect to the consolidated lead scraper database, so that the entire pipeline works seamlessly.

#### Acceptance Criteria

1. WHEN 4runr-brain needs lead data THEN it SHALL connect to `../4runr-lead-scraper/data/leads.db`
2. WHEN 4runr-outreach-system needs lead data THEN it SHALL connect to `../4runr-lead-scraper/data/leads.db`
3. WHEN the database schema is updated THEN it SHALL be compatible with existing integrations
4. WHEN other systems connect THEN they SHALL use the same connection patterns and error handling

### Requirement 6

**User Story:** As a developer, I want to migrate existing data from both old systems to the new consolidated system, so that no lead data is lost during the transition.

#### Acceptance Criteria

1. WHEN migration runs THEN it SHALL combine data from both 4runr-agents and 4runr-lead-system databases
2. WHEN duplicate leads are found THEN they SHALL be merged intelligently based on email or LinkedIn URL
3. WHEN migration completes THEN it SHALL create backups of original data before deletion
4. WHEN migration completes THEN it SHALL generate a report showing what data was consolidated
5. IF migration fails THEN it SHALL restore original state and provide detailed error information