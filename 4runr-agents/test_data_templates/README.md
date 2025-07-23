# Test Data Templates

This directory contains templates for test data used in system tests of the 4Runr AI Lead Scraper system.

## Test Lead

The `test_lead.json` file contains a template for a test lead that can be used to verify the functionality of the lead processing pipeline. This template includes the minimum required fields for a lead to be processed by the system.

### Schema

```json
{
  "name": "John Test",       // Name of the test lead (should be clearly identifiable as a test)
  "company": "Acme AI",      // Company name (should be clearly identifiable as a test)
  "linkedin_url": "https://linkedin.com/in/fakejohnsmith"  // LinkedIn URL (should be a non-existent profile)
}
```

### Usage

To use this template in a system test:

1. Copy the template to `shared/leads.json`
2. Run the pipeline
3. Verify that the lead is processed correctly

### Additional Fields

The following fields may be added to the test lead for more comprehensive testing:

- `title`: Job title of the lead
- `email`: Email address (if testing with pre-enriched leads)
- `status`: Status of the lead (e.g., "new", "contacted", "responded")
- `notes`: Additional notes about the lead

### Example with Additional Fields

```json
{
  "name": "Jane Test",
  "company": "Test Corp",
  "linkedin_url": "https://linkedin.com/in/faketestuser",
  "title": "CTO",
  "email": "test@example.com",
  "status": "new",
  "notes": "This is a test lead for system testing"
}
```

## Batch Test Leads

For testing with multiple leads, you can use an array of test leads:

```json
[
  {
    "name": "John Test",
    "company": "Acme AI",
    "linkedin_url": "https://linkedin.com/in/fakejohnsmith"
  },
  {
    "name": "Jane Test",
    "company": "Test Corp",
    "linkedin_url": "https://linkedin.com/in/faketestuser"
  }
]
```