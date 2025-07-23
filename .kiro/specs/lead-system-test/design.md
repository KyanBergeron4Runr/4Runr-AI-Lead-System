# Design Document

## Overview

This document outlines the design for a manual system test of the 4Runr AI Lead Scraper system. The test is designed to verify that the complete lead generation pipeline (scraper → enricher → engager) is functioning correctly in the production environment. The test will use a controlled test lead to ensure consistent and predictable results.

## Architecture

The 4Runr AI Lead Scraper system consists of several Docker containers running on an EC2 instance:

1. **Scraper**: Responsible for collecting lead data from various sources
2. **Enricher**: Processes leads with additional information using OpenAI
3. **Engager**: Sends processed leads through outreach channels (Microsoft Graph or Make.com)
4. **Pipeline**: Orchestrates the flow between components
5. **Cron**: Manages scheduled execution of the pipeline

The test will interact with these containers to verify the end-to-end functionality of the system.

## Components and Interfaces

### Test Environment Validator

**Purpose**: Verify that the test environment is properly configured before running the test.

**Interfaces**:
- File System: Check for the existence of required files (.env)
- Docker: Check for active containers
- Shell: Execute commands to navigate to the correct directory

**Operations**:
1. Navigate to the project directory
2. Verify that all required Docker containers are active
3. Check that the .env file exists and contains necessary API keys

### Test Data Manager

**Purpose**: Prepare and inject controlled test data into the system.

**Interfaces**:
- File System: Read/write to shared/leads.json
- JSON: Format test lead data

**Operations**:
1. Create a backup of the existing leads.json file (if it exists)
2. Create a new leads.json file with a single test lead
3. Verify that the test lead has all required fields

### Pipeline Executor

**Purpose**: Execute the pipeline manually and observe its operation.

**Interfaces**:
- Docker: Execute commands to run the pipeline
- Shell: Observe logs in real-time

**Operations**:
1. Execute the pipeline using docker-compose
2. Stream logs to the console for real-time observation
3. Verify that the pipeline completes without container crashes

### Result Validator

**Purpose**: Verify that the pipeline processed the test lead correctly.

**Interfaces**:
- Docker Logs: Analyze logs for evidence of successful processing
- Shell: Extract relevant information from logs

**Operations**:
1. Check logs for evidence that the enricher detected and processed the test lead
2. Verify that the engager attempted to send the lead
3. Check for any API failures or errors

### Test Documenter

**Purpose**: Document the test process and results.

**Interfaces**:
- Console: Output test results
- File System: Optionally save test results to a file

**Operations**:
1. Document the test procedure with all commands used
2. Include relevant log excerpts
3. Provide a clear pass/fail status with supporting evidence

## Data Models

### Test Lead

```json
{
  "name": "John Test",
  "company": "Acme AI",
  "linkedin_url": "https://linkedin.com/in/fakejohnsmith"
}
```

This minimal test lead contains only the required fields to trigger the pipeline processing.

### Test Result

The test result will be a structured report containing:

1. Environment validation status
2. Test data preparation status
3. Pipeline execution status
4. Result validation status
5. Overall pass/fail status
6. Relevant log excerpts
7. Recommendations for any identified issues

## Error Handling

The test will handle the following error scenarios:

1. **Environment Validation Errors**: If the environment is not properly configured, the test will provide clear error messages and exit.
2. **Test Data Preparation Errors**: If the test data cannot be prepared, the test will provide clear error messages and exit.
3. **Pipeline Execution Errors**: If the pipeline fails to execute, the test will capture the error messages and include them in the test result.
4. **Result Validation Errors**: If the pipeline does not process the test lead correctly, the test will document the specific issues.

## Testing Strategy

This is a manual test designed to be executed by a system administrator. The test will be executed in the following steps:

1. **Environment Validation**: Verify that the test environment is properly configured.
2. **Test Data Preparation**: Prepare and inject the test lead.
3. **Pipeline Execution**: Execute the pipeline manually and observe its operation.
4. **Result Validation**: Verify that the pipeline processed the test lead correctly.
5. **Test Documentation**: Document the test process and results.

The test will be considered successful if the test lead is successfully processed through all stages of the pipeline without errors.