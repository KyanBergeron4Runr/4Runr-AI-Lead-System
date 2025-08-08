# Requirements Document

## Introduction

The Outreach System Critical Fixes will address seven critical technical issues preventing the 4runr outreach system from functioning properly in production. These fixes target import errors, OpenAI SDK compatibility, Airtable API integration, healthcheck reliability, and overall system stability to ensure the outreach pipeline can scrape leads, generate messages, and engage prospects successfully.

## Requirements

### Requirement 1

**User Story:** As a system operator, I want the website scraper to start without import errors, so that the system can produce lead and company data files consistently.

#### Acceptance Criteria

1. WHEN the website scraper is started THEN the system SHALL resolve all imports without "attempted relative import beyond top-level package" errors
2. WHEN running modules THEN the system SHALL use absolute imports from the project root (e.g., `from outreach.utils.scrape import fetch`)
3. WHEN starting the scraper THEN the system SHALL use `python -m outreach.scraper.main` instead of direct file execution
4. WHEN the Docker container starts THEN the system SHALL set PYTHONPATH=/app and expose the package properly
5. WHEN running `docker-compose build outreach && docker-compose up outreach` THEN the container SHALL start without ImportError exceptions

### Requirement 2

**User Story:** As a message generator, I want to use the current OpenAI SDK without crashes, so that I can generate personalized outreach messages for leads.

#### Acceptance Criteria

1. WHEN initializing the OpenAI client THEN the system SHALL use openai>=1.30.0 without the deprecated `proxies` argument
2. WHEN making API calls THEN the system SHALL use `client.chat.completions.create()` with the current SDK format
3. WHEN proxy configuration is needed THEN the system SHALL use httpx.Client with proxy settings passed to OpenAI constructor
4. WHEN the message generator starts THEN the system SHALL log "OpenAI API connection established" without exceptions
5. WHEN testing the client THEN the system SHALL successfully return a completion without SDK compatibility errors

### Requirement 3

**User Story:** As an Airtable integration user, I want queries to return rows without INVALID_FILTER_BY_FORMULA errors, so that the pipeline can process lead data from Airtable.

#### Acceptance Criteria

1. WHEN querying Airtable THEN the system SHALL use exact field names that match the Airtable schema (case-sensitive)
2. WHEN building filter formulas THEN the system SHALL use configurable field names from environment variables
3. WHEN Airtable responds with 422 errors THEN the system SHALL log available field names and use a fallback filter
4. WHEN the pipeline runs THEN the Email Validator SHALL log "Processed: N > 0" indicating successful row retrieval
5. WHEN field names are incorrect THEN the system SHALL gracefully fallback to a looser filter to keep the pipeline moving

### Requirement 4

**User Story:** As a system administrator, I want the healthcheck to return 200 within 10 seconds after container start, so that I can monitor system availability reliably.

#### Acceptance Criteria

1. WHEN the container starts THEN the /health endpoint SHALL return 200 OK regardless of pipeline state
2. WHEN the web app initializes THEN the system SHALL start the pipeline in a background thread to prevent blocking
3. WHEN the healthcheck runs THEN the system SHALL respond within 5 seconds with a lightweight status check
4. WHEN the pipeline fails THEN the web app SHALL continue running and serving the health endpoint
5. WHEN Docker healthcheck executes THEN the system SHALL turn healthy within 30-60 seconds of container start

### Requirement 5

**User Story:** As an engagement system user, I want the engager to process leads instead of skipping them, so that outreach messages are actually sent to prospects.

#### Acceptance Criteria

1. WHEN a lead has no custom message THEN the system SHALL generate a fallback message instead of skipping
2. WHEN upstream modules fail THEN the engager SHALL create minimal messages from basic lead data
3. WHEN processing leads THEN the system SHALL only skip leads with no email or explicit filter criteria
4. WHEN the engager runs THEN the system SHALL log structured reasons for any skipped leads
5. WHEN Airtable has at least one row THEN the engager SHALL log ≥1 "sent" or "queued" message rather than all "skipped"

### Requirement 6

**User Story:** As a developer, I want proper package structure and dependency management, so that the system can be deployed reliably without import or dependency issues.

#### Acceptance Criteria

1. WHEN examining the codebase THEN all module directories SHALL contain __init__.py files
2. WHEN installing dependencies THEN the system SHALL use pinned versions in requirements.txt or lockfile
3. WHEN building Docker images THEN the system SHALL use `python -m` module execution in CMD
4. WHEN setting environment variables THEN the system SHALL use .env file with OPENAI_API_KEY, Airtable vars, and optional proxy settings
5. WHEN running the system THEN all imports SHALL resolve correctly without relative import errors

### Requirement 7

**User Story:** As a quality assurance tester, I want a comprehensive test plan to verify all fixes, so that I can confirm the system works end-to-end before deployment.

#### Acceptance Criteria

1. WHEN running the test plan THEN the system SHALL complete fresh Docker build and startup successfully
2. WHEN testing the scraper THEN `python -m outreach.scraper.main --dry-run` SHALL complete without ImportError
3. WHEN testing the generator THEN `python -m outreach.message_generator.main --dry-run` SHALL complete successfully
4. WHEN checking Airtable integration THEN logs SHALL show >0 records retrieved from Airtable queries
5. WHEN verifying healthcheck THEN `curl -i http://localhost:8080/health` SHALL return 200 OK within 10 seconds