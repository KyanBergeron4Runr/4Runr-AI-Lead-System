# Airtable Integration Migration Guide

## Overview

The Airtable integration has been upgraded to support configurable field names and defensive error handling to fix 422 INVALID_FILTER_BY_FORMULA errors.

## Key Changes

### 1. Configurable Field Names

Field names are now configurable via environment variables. Add these to your `.env` file:

```env
# Airtable Field Names (must match your Airtable schema exactly - case sensitive)
AIRTABLE_FIELD_WEBSITE=Website
AIRTABLE_FIELD_COMPANY_DESCRIPTION=Company Description
AIRTABLE_FIELD_EMAIL=Email
AIRTABLE_FIELD_COMPANY_NAME=Company Name
AIRTABLE_FIELD_NAME=Name
AIRTABLE_FIELD_JOB_TITLE=Job Title
AIRTABLE_FIELD_EMAIL_CONFIDENCE_LEVEL=Email_Confidence_Level
AIRTABLE_FIELD_CUSTOM_MESSAGE=Custom_Message
AIRTABLE_FIELD_ENGAGEMENT_STATUS=Engagement_Status
AIRTABLE_FIELD_DATE_MESSAGED=Date Messaged
```

### 2. Defensive Error Handling

The new client includes:
- **Fallback Filters**: When primary filters fail, the system tries simpler filters
- **Field Name Debugging**: Logs available field names when queries fail
- **Graceful Degradation**: System continues working even with field name mismatches

### 3. Backward Compatibility

Existing code continues to work without changes:
```python
from shared.airtable_client import get_airtable_client

client = get_airtable_client()  # Now uses configurable client
leads = client.get_leads_for_processing()
```

## Testing Your Configuration

Run the test script to validate your setup:

```bash
python test_airtable_config.py
```

This will:
- Test your Airtable connection
- Validate field name configuration
- Show available fields for debugging
- Test defensive error handling

## Common Issues and Solutions

### Issue: 422 INVALID_FILTER_BY_FORMULA

**Cause**: Field names in environment variables don't match Airtable schema

**Solution**: 
1. Run the test script to see available field names
2. Update your `.env` file with exact field names (case-sensitive)
3. Restart the application

### Issue: No leads returned

**Cause**: Primary filters are too restrictive or field names are incorrect

**Solution**: 
- The system automatically falls back to simpler filters
- Check logs for "fallback filter" messages
- Verify field names match your Airtable schema exactly

### Issue: Connection fails

**Cause**: Invalid API key, base ID, or table name

**Solution**:
1. Verify `AIRTABLE_API_KEY` is correct
2. Verify `AIRTABLE_BASE_ID` matches your base
3. Verify `AIRTABLE_TABLE_NAME` matches your table name exactly

## Migration Steps

1. **Update Environment Variables**: Add the new field name variables to your `.env` file
2. **Test Configuration**: Run `python test_airtable_config.py`
3. **Verify Field Names**: Check that field names match your Airtable schema exactly
4. **Test Integration**: Run your normal pipeline to ensure everything works
5. **Monitor Logs**: Watch for any fallback filter usage or field name warnings

## Advanced Configuration

### Custom Field Mappings

If your Airtable uses different field names, update the environment variables:

```env
# Example: If your Airtable uses "Company_Website" instead of "Website"
AIRTABLE_FIELD_WEBSITE=Company_Website

# Example: If your Airtable uses "Description" instead of "Company Description"  
AIRTABLE_FIELD_COMPANY_DESCRIPTION=Description
```

### Debugging Field Names

To see what field names are available in your Airtable:

```python
from shared.configurable_airtable_client import get_configurable_airtable_client

client = get_configurable_airtable_client()
available_fields = client._get_available_field_names()
print("Available fields:", available_fields)
```

## Benefits

- **Reliability**: No more 422 errors due to field name mismatches
- **Flexibility**: Easy to adapt to different Airtable schemas
- **Debugging**: Clear logging when issues occur
- **Resilience**: Fallback mechanisms keep the system running
- **Compatibility**: Existing code continues to work unchanged