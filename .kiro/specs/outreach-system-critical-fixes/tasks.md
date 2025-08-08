# Implementation Plan

- [x] 1. Fix import system and package structure



  - Add __init__.py files to all module directories to make them proper Python packages
  - Convert all relative imports (from ..shared) to absolute imports (from outreach.shared)
  - Update Dockerfile to set PYTHONPATH=/app and use module execution pattern
  - Create main.py entry points for each module that can be run with python -m



  - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.3_

- [ ] 2. Modernize OpenAI SDK integration
  - Update requirements.txt to use openai>=1.30.0 and add httpx>=0.27.0
  - Replace all deprecated OpenAI client initialization patterns with modern SDK usage



  - Implement proxy support using httpx.Client instead of deprecated proxies argument
  - Add proper error handling and connection logging for OpenAI API calls
  - Remove duplicate client initialization lines found in multiple files
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_




- [ ] 3. Implement configurable Airtable integration
  - Add Airtable field name configuration to .env.example and environment setup
  - Create ConfigurableAirtableClient class that uses environment variables for field names
  - Implement defensive error handling with fallback filters for 422 INVALID_FILTER_BY_FORMULA errors
  - Add logging of available field names when queries fail for debugging



  - Update all Airtable query code to use the new configurable client
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Create non-blocking health check system
  - Implement FastAPI web service with lightweight /health endpoint



  - Create background thread system for running pipeline without blocking web service
  - Update Dockerfile to expose port 8080 and use proper healthcheck with curl
  - Modify docker-compose.yml to use HTTP healthcheck instead of Python import check
  - Ensure web service starts even when pipeline components fail
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_




- [ ] 5. Build resilient engagement pipeline
  - Implement fallback message generation for leads without custom messages
  - Create defensive lead processing that only skips leads with no email or explicit filters
  - Add structured logging for skip reasons to help with debugging
  - Ensure engager processes leads even when upstream scraper/generator modules fail
  - Add business rule validation for lead engagement decisions
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Update dependencies and Docker configuration
  - Pin all dependencies in requirements.txt with specific versions for reproducibility
  - Update Dockerfile CMD to use python -m outreach.api for proper module execution
  - Ensure all environment variables are properly configured in .env.example
  - Add missing dependencies identified during import fixes (fastapi, uvicorn for web service)
  - Rebuild Docker images with updated configuration
  - _Requirements: 6.1, 6.2, 6.4, 6.5_

- [ ] 7. Create comprehensive test suite and validation
  - Write smoke test script that validates all fixes work end-to-end
  - Create unit tests for import resolution, OpenAI client, and Airtable integration
  - Implement integration tests for Docker build, container startup, and health checks
  - Add test commands for dry-run execution of scraper and message generator modules
  - Verify that Airtable queries return >0 records and engager processes leads successfully
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_