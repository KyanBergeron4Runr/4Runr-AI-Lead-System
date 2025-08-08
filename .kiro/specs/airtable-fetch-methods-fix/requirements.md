# Requirements Document

## Introduction

The Airtable Fetch Methods Fix will address missing method signatures in the ConfigurableAirtableClient that are causing AttributeError exceptions in the outreach pipeline background jobs. The pipeline expects three specific methods with `limit` parameters, but the current implementation uses different method signatures with `max_records` parameters, causing the background jobs to fail.

## Requirements

### Requirement 1

**User Story:** As a background job process, I want to call `get_leads_for_outreach(limit: int | None = None)` on the ConfigurableAirtableClient, so that I can retrieve leads for website scraping without AttributeError exceptions.

#### Acceptance Criteria

1. WHEN the background job calls `get_leads_for_outreach(limit=10)` THEN the system SHALL return a list of lead records without raising AttributeError
2. WHEN the limit parameter is None THEN the system SHALL use a default limit value from configuration
3. WHEN the limit parameter is provided THEN the system SHALL pass it to Airtable as max_records
4. WHEN field mappings exist in configuration THEN the system SHALL build appropriate formulas for filtering leads
5. WHEN field mappings are missing or invalid THEN the system SHALL fall back to no formula to return some rows

### Requirement 2

**User Story:** As a background job process, I want to call `get_leads_for_message_generation(limit: int | None = None)` on the ConfigurableAirtableClient, so that I can retrieve leads that need AI message generation without method signature errors.

#### Acceptance Criteria

1. WHEN the background job calls `get_leads_for_message_generation(limit=20)` THEN the system SHALL return a list of lead records without raising AttributeError
2. WHEN the limit parameter is None THEN the system SHALL use a default limit value
3. WHEN building formulas THEN the system SHALL check for email and message fields from field mappings
4. WHEN formula building fails THEN the system SHALL return None to avoid breaking the query
5. WHEN Airtable queries succeed THEN the system SHALL log the number of leads retrieved

### Requirement 3

**User Story:** As a background job process, I want to call `get_leads_for_engagement(limit: int | None = None)` on the ConfigurableAirtableClient, so that I can retrieve leads ready for outreach engagement without unexpected keyword argument errors.

#### Acceptance Criteria

1. WHEN the background job calls `get_leads_for_engagement(limit=15)` THEN the system SHALL return a list of lead records without raising AttributeError
2. WHEN the limit parameter is None THEN the system SHALL use a default limit value
3. WHEN building engagement formulas THEN the system SHALL check for email, message, and contacted fields from mappings
4. WHEN field mappings are incomplete THEN the system SHALL build defensive formulas that don't break
5. WHEN all formula attempts fail THEN the system SHALL return an empty list rather than raising exceptions

### Requirement 4

**User Story:** As a system administrator, I want the ConfigurableAirtableClient to use a shared internal helper method for fetching records, so that the code is maintainable and consistent across all fetch methods.

#### Acceptance Criteria

1. WHEN any fetch method is called THEN the system SHALL use a single internal `_fetch_records(formula: str | None, limit: int | None)` helper method
2. WHEN the helper method is called THEN the system SHALL convert limit to max_records for the Airtable API
3. WHEN a formula is provided THEN the system SHALL pass it to `self.table.all(formula=formula, max_records=max_records)`
4. WHEN no formula is provided THEN the system SHALL call `self.table.all(max_records=max_records)` without formula parameter
5. WHEN Airtable API calls fail THEN the system SHALL log errors and return empty lists

### Requirement 5

**User Story:** As a developer, I want the formula builders to be defensive and handle missing field mappings gracefully, so that the system continues to function even with incomplete configuration.

#### Acceptance Criteria

1. WHEN a formula builder cannot find a required field mapping THEN the system SHALL return None instead of building an invalid formula
2. WHEN field mappings exist THEN the system SHALL build appropriate Airtable formulas using the mapped field names
3. WHEN building formulas THEN the system SHALL use proper Airtable formula syntax with curly braces around field names
4. WHEN multiple conditions are needed THEN the system SHALL use AND() and OR() functions correctly
5. WHEN formula building encounters any error THEN the system SHALL log the error and return None

### Requirement 6

**User Story:** As a system operator, I want the application to boot without errors and maintain healthy status, so that the outreach pipeline can run continuously without manual intervention.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL not raise AttributeError for missing methods
2. WHEN the healthcheck endpoint is called THEN the system SHALL return 200 OK status
3. WHEN background jobs run THEN the system SHALL log successful method calls or "no leads" messages instead of errors
4. WHEN the pipeline processes leads THEN the system SHALL show steps running in logs
5. WHEN no matching leads are found THEN the system SHALL log informational messages without raising exceptions