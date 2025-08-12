# CLI Command: apply-defaults

The `apply-defaults` command allows you to manually apply engagement defaults to existing leads in Airtable.

## Overview

This command is useful when:
- You have existing leads that were synced before engagement defaults were enabled
- You want to apply updated default values to existing leads
- You need to fix leads that have missing engagement field values

## Usage

```bash
python cli/cli.py apply-defaults [OPTIONS]
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dry-run` | Show what would be done without making changes | False |
| `--filter-status` | Filter leads by sync status (`pending`, `synced`, `failed`, `all`) | `synced` |
| `--limit INTEGER` | Maximum number of leads to process | No limit |
| `--lead-id TEXT` | Apply defaults to a specific lead ID | None |
| `--batch-size INTEGER` | Number of leads to process in each batch | 10 |
| `--confirm` | Skip confirmation prompt | False |
| `--help` | Show help message | - |

## Examples

### 1. Dry Run - See What Would Be Done

```bash
# See what defaults would be applied to synced leads
python cli/cli.py apply-defaults --dry-run

# Check specific lead
python cli/cli.py apply-defaults --dry-run --lead-id abc123
```

### 2. Apply Defaults to All Synced Leads

```bash
# Apply defaults to all synced leads (with confirmation)
python cli/cli.py apply-defaults

# Apply defaults without confirmation prompt
python cli/cli.py apply-defaults --confirm
```

### 3. Apply Defaults to Specific Lead

```bash
# Apply defaults to a specific lead
python cli/cli.py apply-defaults --lead-id abc123

# Dry run for specific lead
python cli/cli.py apply-defaults --dry-run --lead-id abc123
```

### 4. Filter by Sync Status

```bash
# Apply defaults to pending leads
python cli/cli.py apply-defaults --filter-status pending

# Apply defaults to all leads regardless of status
python cli/cli.py apply-defaults --filter-status all
```

### 5. Limit Processing

```bash
# Process only first 50 leads
python cli/cli.py apply-defaults --limit 50

# Process in smaller batches of 5
python cli/cli.py apply-defaults --batch-size 5
```

## Default Values Applied

The command applies these default values to empty or missing fields:

- **Engagement_Status**: `"Auto-Send"`
- **Email_Confidence_Level**: `"Pattern"`
- **Level Engaged**: `""` (empty string)

## Behavior

### Field Update Logic
- Only updates fields that are **missing** or **empty**
- Preserves existing field values
- Skips leads that already have all engagement fields populated

### Batch Processing
- Processes leads in configurable batches (default: 10)
- Shows progress for each batch
- Continues processing even if some leads fail

### Error Handling
- Gracefully handles API errors
- Reports failed leads with error details
- Exits with error code if any leads fail to update

## Output Examples

### Dry Run Output
```
🎯 Engagement Defaults Application
========================================
📋 Default Values:
   • Engagement_Status: "Auto-Send"
   • Email_Confidence_Level: "Pattern"
   • Level Engaged: (empty string)

🔍 Finding leads with sync status: synced
📊 Found 25 leads to process
📦 Processing in 3 batches of 10 leads each

🧪 DRY RUN: Would process 25 leads
   No changes will be made to Airtable

📋 Sample of leads that would be processed:
   1. John Doe (ID: abc123, Airtable: rec123)
   2. Jane Smith (ID: def456, Airtable: rec456)
   ... and 23 more
```

### Successful Execution Output
```
🚀 Starting batch processing...

📦 Processing batch 1/3 (10 leads)...
Applying defaults  [####################################]  100%
   ✅ Updated: 8
   ⏭️  Skipped: 2
   ❌ Failed: 0

📦 Processing batch 2/3 (10 leads)...
Applying defaults  [####################################]  100%
   ✅ Updated: 7
   ⏭️  Skipped: 3
   ❌ Failed: 0

📊 Final Results:
   Total Leads Processed: 25
   ✅ Updated: 18
   ⏭️  Skipped: 7
   ❌ Failed: 0

🎉 Successfully applied engagement defaults to 18 leads!
```

## Prerequisites

1. **Engagement defaults must be enabled**:
   ```bash
   APPLY_ENGAGEMENT_DEFAULTS=true
   ```

2. **Valid Airtable configuration**:
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
   - `AIRTABLE_TABLE_NAME`

3. **Leads must have Airtable record IDs**:
   - Only processes leads that have been synced to Airtable
   - Skips leads without `airtable_id`

## Safety Features

- **Dry run mode** to preview changes
- **Confirmation prompts** before making changes
- **Batch processing** to handle large datasets
- **Error isolation** - failures don't stop processing
- **Non-destructive** - only updates empty fields

## Troubleshooting

### "Engagement defaults are disabled"
- Set `APPLY_ENGAGEMENT_DEFAULTS=true` in your `.env` file

### "Configuration errors found"
- Check your Airtable API credentials
- Verify `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, and `AIRTABLE_TABLE_NAME`

### "No leads found"
- Check the `--filter-status` option
- Verify leads exist in the database
- Ensure leads have been synced to Airtable

### "Lead has no Airtable record ID"
- The lead hasn't been synced to Airtable yet
- Run a sync operation first: `python cli/cli.py sync-enhanced to-airtable`

## Related Commands

- `python cli/cli.py sync-enhanced to-airtable` - Sync leads to Airtable
- `python cli/cli.py stats` - View lead statistics
- `python cli/cli.py daily --sync-only` - Run sync phase of daily automation