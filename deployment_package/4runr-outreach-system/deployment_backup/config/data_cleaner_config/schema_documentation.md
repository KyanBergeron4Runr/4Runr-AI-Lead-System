# Data Cleaner Configuration Schema Documentation

This document provides comprehensive documentation for the Data Cleaner configuration files, including schema definitions, examples, and best practices.

## Overview

The Data Cleaner system uses two main configuration files:

1. **`cleaning_rules.yaml`** - Defines patterns and rules for cleaning and normalizing data
2. **`validation_rules.yaml`** - Defines quality thresholds and validation criteria

## Configuration Files

### cleaning_rules.yaml

This file defines how raw data should be cleaned and normalized before validation.

#### Schema Structure

```yaml
company_name:
  remove_patterns: [string]      # Regex patterns to remove from company names
  normalize_patterns:            # Patterns to normalize company names
    - pattern: string            # Regex pattern to match
      replacement: string        # Replacement text
  min_length: integer           # Minimum allowed length
  max_length: integer           # Maximum allowed length

website_url:
  remove_patterns: [string]      # Domains/patterns to reject
  required_protocols: [string]   # Allowed URL protocols
  domain_validation: boolean     # Enable domain format validation
  ssl_preferred: boolean         # Prefer HTTPS over HTTP
  normalize_patterns:            # URL normalization patterns
    - pattern: string
      replacement: string

search_artifacts:
  remove_patterns: [string]      # Search engine artifacts to remove

text_normalization:
  character_replacements:        # Character-level replacements
    - pattern: string
      replacement: string
  encoding_fixes:               # Fix encoding issues
    - pattern: string
      replacement: string

processing:
  max_processing_time: integer   # Max processing time per field (seconds)
  max_text_length: integer      # Max text length to process
  modules:                      # Enable/disable cleaning modules
    search_artifacts: boolean
    html_fragments: boolean
    text_normalization: boolean
    company_normalization: boolean
    url_normalization: boolean
```

#### Key Sections

##### company_name

Defines cleaning rules for company names to remove garbage data and normalize legal entity suffixes.

**remove_patterns**: Array of regex patterns that identify garbage data to remove:
- Search engine artifacts (google, linkedin, etc.)
- Specific garbage patterns ("Some results may have been delisted")
- HTML fragments and markup
- Placeholder values (unknown, null, etc.)
- Test data indicators

**normalize_patterns**: Array of pattern/replacement pairs for standardizing company names:
- Legal entity suffixes (Inc, LLC, Corp, etc.)
- International entities (GmbH, SA, Pty Ltd, etc.)
- Common abbreviations and formatting

##### website_url

Defines rules for cleaning and validating website URLs.

**remove_patterns**: Domains that should be rejected as non-business websites:
- Search engines (google.com, bing.com)
- Social media platforms (linkedin.com, facebook.com)
- Generic/test domains (example.com, test.com)
- Email providers (gmail.com, yahoo.com)

**normalize_patterns**: URL normalization rules:
- Protocol standardization
- Trailing slash removal
- www prefix handling

##### search_artifacts

Comprehensive patterns for removing Google search artifacts and navigation elements.

**remove_patterns**: Specific search result artifacts:
- "Some results may have been delisted consistent with local laws"
- Search navigation ("Learn more Next", "About X results")
- Time-based artifacts ("2 hours ago")
- Advertisement indicators ("Ad", "Sponsored")

### validation_rules.yaml

This file defines quality thresholds and validation criteria for determining data acceptability.

#### Schema Structure

```yaml
company_name:
  min_confidence: float          # Minimum confidence threshold (0.0-1.0)
  required_patterns: [string]    # Patterns company names must match
  forbidden_patterns: [string]   # Patterns that indicate invalid names
  professional_indicators: [string] # Terms that indicate professional companies
  min_length: integer           # Minimum length
  max_length: integer           # Maximum length
  scoring:                      # Quality scoring weights
    has_legal_entity: float
    proper_capitalization: float
    business_words: float
    reasonable_length: float
    no_forbidden_patterns: float

website_url:
  min_confidence: float          # Minimum confidence threshold
  required_format: string        # Regex pattern for valid URLs
  forbidden_domains: [string]    # Domains to reject
  professional_domains: [string] # Professional domain indicators
  ssl_preferred: boolean         # Prefer HTTPS
  ssl_bonus_score: float        # Bonus score for HTTPS
  scoring:                      # Quality scoring weights
    valid_format: float
    professional_domain: float
    https_protocol: float
    reasonable_length: float

data_quality:
  min_overall_confidence: float  # Overall quality threshold
  required_fields: [string]      # Fields that must be present
  optional_fields: [string]      # Fields that improve quality
  professional_standards_threshold: float
  international_support: boolean
  cultural_variations: boolean
  field_requirements:            # Per-field requirements
    field_name:
      min_length: integer
      max_length: integer
      required_confidence: float
  completeness_scoring:          # Completeness scoring weights
    required_field_weight: float
    optional_field_weight: float
    quality_penalty: float

validation_engine:
  modules:                      # Enable/disable validation modules
    company_name_validation: boolean
    website_url_validation: boolean
    data_completeness_validation: boolean
    professional_standards_validation: boolean
    context_consistency_validation: boolean
    business_legitimacy_validation: boolean
    data_freshness_validation: boolean
  max_validation_time: integer  # Max validation time (seconds)
  track_statistics: boolean     # Enable statistics tracking
  statistics_retention_days: integer
  strict_mode: boolean          # Fail on any validation error
  fallback_to_defaults: boolean # Use defaults on failure

context_validation:
  domain_matching:              # Company-website consistency
    enabled: boolean
    fuzzy_matching: boolean
    international_characters: boolean
    similarity_threshold: float
  name_consistency:             # Lead name consistency
    enabled: boolean
    check_name_in_company: boolean
    suspicious_threshold: float
  legitimacy_checks:            # Business legitimacy
    entity_indicators: boolean
    professional_domains: boolean
    reasonable_naming: boolean
    no_test_data: boolean

international:
  character_sets: [string]      # Supported character sets
  normalize_characters: boolean # Enable character normalization
  business_entities: [string]   # International business entities
  country_rules:               # Country-specific rules
    enabled: boolean
    fallback_to_international: boolean

performance:
  max_processing_time: integer  # Max total processing time
  max_memory_usage: integer     # Max memory usage (MB)
  batch_size: integer          # Batch processing size
  parallel_processing: boolean  # Enable parallel processing
  max_workers: integer         # Max worker threads
  monitoring:                  # Monitoring settings
    enabled: boolean
    alert_on_high_rejection_rate: boolean
    rejection_rate_threshold: float
    performance_monitoring: boolean
    quality_trend_tracking: boolean
```

## Configuration Examples

### Basic Company Name Cleaning

```yaml
company_name:
  remove_patterns:
    - 'Some results may have been.*'
    - 'google'
    - 'linkedin'
  normalize_patterns:
    - pattern: '\s+Inc\.?$'
      replacement: ' Inc'
    - pattern: '\s+LLC\.?$'
      replacement: ' LLC'
  min_length: 2
  max_length: 100
```

### Website URL Validation

```yaml
website_url:
  min_confidence: 0.8
  required_format: "^https?://[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}.*$"
  forbidden_domains:
    - google.com
    - linkedin.com
    - facebook.com
  ssl_preferred: true
```

### International Support

```yaml
international:
  character_sets:
    - latin
    - cyrillic
    - chinese
  business_entities:
    - GmbH
    - SA
    - 'Pty Ltd'
  country_rules:
    enabled: true
    fallback_to_international: true
```

## Best Practices

### 1. Pattern Design

- **Be Specific**: Use specific patterns rather than overly broad ones
- **Test Thoroughly**: Test patterns with real data before deployment
- **Order Matters**: Place more specific patterns before general ones
- **Escape Special Characters**: Properly escape regex special characters

### 2. Confidence Thresholds

- **Start Conservative**: Begin with higher thresholds and adjust based on results
- **Monitor Performance**: Track rejection rates and adjust thresholds accordingly
- **Field-Specific**: Use different thresholds for different field types
- **International Considerations**: Lower thresholds for international data

### 3. Performance Optimization

- **Limit Pattern Complexity**: Avoid overly complex regex patterns
- **Set Reasonable Timeouts**: Prevent processing from hanging
- **Enable Parallel Processing**: For batch operations
- **Monitor Resource Usage**: Track memory and CPU usage

### 4. Maintenance

- **Regular Updates**: Update patterns based on new garbage data patterns
- **Version Control**: Track configuration changes with version control
- **Backup Before Changes**: Always backup configurations before updates
- **Test in Staging**: Test configuration changes in staging environment

## Validation Rules

### Required Fields

All configuration files must include:
- Valid YAML syntax
- Required sections (company_name, website_url, data_quality)
- Numeric values within valid ranges (0.0-1.0 for confidence scores)
- Valid regex patterns (tested for compilation)

### Optional Fields

Optional sections that enhance functionality:
- international: For international business support
- performance: For performance tuning
- context_validation: For advanced consistency checking

## Error Handling

The configuration system includes comprehensive error handling:

1. **Syntax Validation**: YAML syntax is validated on load
2. **Schema Validation**: Configuration structure is validated
3. **Pattern Validation**: Regex patterns are tested for compilation
4. **Range Validation**: Numeric values are checked for valid ranges
5. **Fallback Behavior**: Default configurations are used if validation fails

## Migration Guide

When updating configurations:

1. **Backup Current Configuration**: Always backup before changes
2. **Validate New Configuration**: Test new patterns and thresholds
3. **Gradual Rollout**: Deploy changes incrementally
4. **Monitor Results**: Watch for unexpected rejection rates
5. **Rollback Plan**: Have a rollback plan ready

## Troubleshooting

### Common Issues

1. **High Rejection Rate**: Lower confidence thresholds or review patterns
2. **Performance Issues**: Simplify regex patterns or increase timeouts
3. **International Data Issues**: Enable international support and character normalization
4. **Pattern Conflicts**: Review pattern order and specificity

### Debugging

1. **Enable Detailed Logging**: Set log level to DEBUG
2. **Test Individual Patterns**: Test patterns in isolation
3. **Review Statistics**: Check validation statistics for patterns
4. **Use Test Data**: Test with known good and bad data samples

## Support

For additional support:
- Review the validation engine logs for detailed error messages
- Test configurations with the provided test suites
- Consult the source code documentation for implementation details
- Monitor system performance and quality metrics