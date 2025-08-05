# 4Runr AI Lead Scraper System Test

This directory contains scripts and tools for running system tests on the 4Runr AI Lead Scraper system.

## Overview

The system test verifies that the complete lead generation pipeline (scraper → enricher → engager) is functioning correctly using controlled test input. The test injects a predefined test lead into the system, runs the pipeline, and verifies that the lead is properly processed through all stages.

## Prerequisites

Before running the system test, ensure that:

1. The system is deployed on EC2 in the folder: `~/4Runr-AI-Lead-System/4runr-agents`
2. Docker containers are active: scraper, enricher, engager, pipeline, cron
3. The `.env` file is present and contains API keys for Airtable, OpenAI, Microsoft Graph, and Make.com

## Test Scripts

The following scripts are available for running system tests:

### Full System Test

- **Linux/macOS**: `run_full_system_test.sh`
- **Windows**: `run_full_system_test.bat`

This script performs a complete system test, including:
- Environment validation
- Test data preparation
- Pipeline execution
- Log collection
- Result verification
- Test report generation

### Individual Components

The following scripts are available for running individual components of the system test:

- **Test Data Injection**:
  - Linux/macOS: `python inject_test_data.py`
  - Windows: `inject_test_data.bat`

- **Pipeline Execution**:
  - Linux/macOS: `python run_pipeline_test.py`
  - Windows: `run_pipeline_test.bat`

- **Log Monitoring**:
  - Linux/macOS: `python monitor_logs.py`
  - Windows: `monitor_logs.bat`

## Running the System Test

To run a full system test:

### Linux/macOS

```bash
cd ~/4Runr-AI-Lead-System/4runr-agents
./run_full_system_test.sh
```

### Windows

```batch
cd C:\path\to\4Runr-AI-Lead-System\4runr-agents
run_full_system_test.bat
```

## Test Results

After running the system test, results are saved to a directory named `test_results_YYYYMMDD_HHMMSS`, where `YYYYMMDD_HHMMSS` is the timestamp when the test was started.

The test results directory contains:

- `test_results.md`: A summary of the test results
- `container_logs.log`: Logs from all containers
- `pipeline_output.log`: Output from the pipeline execution
- `errors.log`: Any errors detected during the test
- `leads.json.backup`: Backup of the original leads.json file

## Interpreting Test Results

The test results are summarized in the `test_results.md` file, which includes:

- Overall test status (PASS/FAIL)
- Component-level results (Enricher, Engager, System Health)
- Links to log files
- Error details (if any)

A test is considered successful if:

1. The enricher successfully processes the test lead
2. The engager successfully sends the lead via the configured channel
3. No container crashes or API failures occur

## Restoring the Original State

After running the test, you can restore the original state of the system by:

1. Restoring the original leads.json file:
   ```bash
   cp test_results_YYYYMMDD_HHMMSS/leads.json.backup shared/leads.json
   ```

## Troubleshooting

If the test fails, check the following:

1. **Environment Issues**:
   - Verify that all required Docker containers are running
   - Check that the `.env` file contains valid API keys

2. **Enricher Issues**:
   - Check the OpenAI API key
   - Look for errors in the enricher logs

3. **Engager Issues**:
   - Check the Microsoft Graph or Make.com API keys
   - Look for errors in the engager logs

4. **Pipeline Issues**:
   - Check that the pipeline container is running
   - Look for errors in the pipeline logs

## Additional Options

### Test Data Injection

You can inject custom test data using the `inject_test_data.py` script:

```bash
python inject_test_data.py --template custom_template.json --output shared/leads.json --backup
```

### Log Monitoring

You can monitor logs from specific containers using the `monitor_logs.py` script:

```bash
python monitor_logs.py --container scraper --follow
```

### Pipeline Execution

You can run the pipeline with custom options using the `run_pipeline_test.py` script:

```bash
python run_pipeline_test.py --docker --timeout 600 --output-dir custom_results
```