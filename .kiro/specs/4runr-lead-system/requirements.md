# Requirements Document

## Introduction

The 4Runr AI Lead System is a backend-only lead generation and outreach system designed to automate the process of finding, enriching, and engaging with potential leads through LinkedIn and email. Phase 1 focuses on establishing the foundation of this system with a clean backend structure, Airtable integration, and a simulated scraper agent. The system will be built using Node.js and will use Airtable as its primary data store. The system will be deployed on AWS EC2 (Ubuntu 22.04 LTS) using Docker, with manual triggering via SSH or cron jobs.

## Requirements

### Requirement 1: Project Setup and Structure

**User Story:** As a developer, I want a well-organized Node.js project structure, so that the codebase is maintainable and scalable.

#### Acceptance Criteria

1. WHEN initializing the project THEN the system SHALL create a proper Node.js project with package.json.
2. WHEN setting up the project THEN the system SHALL establish a clean directory structure with separate folders for different modules.
3. WHEN organizing code THEN the system SHALL follow modular design principles with clear separation of concerns.
4. WHEN setting up the project THEN the system SHALL include proper documentation in the form of a README.md file.

### Requirement 2: Airtable Integration

**User Story:** As a system administrator, I want secure and reusable Airtable integration, so that lead data can be stored and retrieved efficiently.

#### Acceptance Criteria

1. WHEN integrating with Airtable THEN the system SHALL provide functions to add new leads to Airtable.
2. WHEN integrating with Airtable THEN the system SHALL provide functions to fetch leads marked as "Needs Enrichment".
3. WHEN accessing Airtable THEN the system SHALL use environment variables for API keys and configuration.
4. WHEN implementing Airtable integration THEN the system SHALL handle errors gracefully and provide meaningful error messages.
5. WHEN creating the Airtable module THEN the system SHALL ensure it is importable from any agent module.

### Requirement 3: Simulated Lead Scraper

**User Story:** As a business user, I want a simulated lead scraper, so that I can test the system's ability to collect and store lead information.

#### Acceptance Criteria

1. WHEN running the scraper THEN the system SHALL create mock lead objects with name, LinkedIn URL, company, and title.
2. WHEN creating lead objects THEN the system SHALL mark email as missing.
3. WHEN saving leads THEN the system SHALL mark them with "Needs Enrichment = true".
4. WHEN the scraper runs THEN the system SHALL save the lead to Airtable via the wrapper module.
5. WHEN the scraper completes THEN the system SHALL provide clear console output about the operation's success or failure.

### Requirement 4: Configuration Management

**User Story:** As a system administrator, I want secure configuration management, so that sensitive information is not exposed in the codebase.

#### Acceptance Criteria

1. WHEN setting up the project THEN the system SHALL use a .env file to store sensitive configuration.
2. WHEN accessing configuration THEN the system SHALL load environment variables using the dotenv package.
3. WHEN storing configuration THEN the system SHALL include Airtable API key, Base ID, and Table name.
4. WHEN distributing the code THEN the system SHALL ensure .env files are not committed to version control.
5. WHEN documenting the project THEN the system SHALL provide a template .env file with placeholder values.

### Requirement 5: Documentation

**User Story:** As a developer, I want comprehensive documentation, so that I can understand, use, and extend the system.

#### Acceptance Criteria

1. WHEN documenting the code THEN the system SHALL include inline comments explaining complex logic.
2. WHEN creating the README.md THEN the system SHALL include project overview, module descriptions, and usage instructions.
3. WHEN documenting the project THEN the system SHALL provide expected outputs and examples.
4. WHEN documenting the project THEN the system SHALL include a preview of next steps (Phase 2).
5. WHEN writing documentation THEN the system SHALL ensure it is clear, concise, and helpful for future developers.

### Requirement 6: Infrastructure Setup

**User Story:** As a system administrator, I want the system to be containerized and deployable to AWS EC2, so that it can run reliably in a production environment.

#### Acceptance Criteria

1. WHEN setting up the project THEN the system SHALL include Docker configuration for containerization.
2. WHEN configuring Docker THEN the system SHALL use a multi-stage build process for optimized image size.
3. WHEN deploying the system THEN it SHALL be compatible with AWS EC2 running Ubuntu 22.04 LTS.
4. WHEN running the system THEN it SHALL support manual triggering via SSH or cron jobs.
5. WHEN documenting deployment THEN the system SHALL include clear instructions for setting up the infrastructure.
6. WHEN handling secrets THEN the system SHALL use .env files that are never committed to Git.