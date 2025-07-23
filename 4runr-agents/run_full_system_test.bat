@echo off
REM 4Runr AI Lead Scraper Full System Test for Windows
REM This script runs a full system test of the 4Runr AI Lead Scraper system

echo 4Runr AI Lead Scraper Full System Test

REM Set timestamp for logs
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "TIMESTAMP=%dt:~0,8%_%dt:~8,6%"
set "TEST_DIR=test_results_%TIMESTAMP%"
set "LOG_FILE=%TEST_DIR%\system_test.log"

REM Create test results directory
mkdir "%TEST_DIR%" 2>nul

REM Start the test
echo [%date% %time%] [INFO] Starting 4Runr AI Lead Scraper Full System Test > "%LOG_FILE%"
echo [%date% %time%] [INFO] Test results will be saved to: %TEST_DIR% >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Starting 4Runr AI Lead Scraper Full System Test
echo [%date% %time%] [INFO] Test results will be saved to: %TEST_DIR%

REM Step 1: Validate environment
echo [%date% %time%] [INFO] Step 1: Validating environment... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Step 1: Validating environment...

REM Check if we're in the correct directory
if not exist "shared" (
    echo [%date% %time%] [ERROR] Not in the correct directory. Please run this script from the 4runr-agents directory. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Not in the correct directory. Please run this script from the 4runr-agents directory.
    exit /b 1
)

if not exist "docker-compose.yml" (
    echo [%date% %time%] [ERROR] Not in the correct directory. Please run this script from the 4runr-agents directory. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Not in the correct directory. Please run this script from the 4runr-agents directory.
    exit /b 1
)

REM Check if Docker is running
docker info > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Docker is not running. Please start Docker and try again. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Check if required containers are running
echo [%date% %time%] [INFO] Checking Docker containers... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Checking Docker containers...
docker-compose ps | findstr /R "scraper enricher engager pipeline cron" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Some containers are not running. Please start them with 'docker-compose up -d'. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Some containers are not running. Please start them with 'docker-compose up -d'.
    exit /b 1
) else (
    echo [%date% %time%] [SUCCESS] All required containers are running. >> "%LOG_FILE%"
    echo [%date% %time%] [SUCCESS] All required containers are running.
)

REM Check if .env file exists
if not exist ".env" (
    echo [%date% %time%] [ERROR] .env file not found. Please create it from .env.example. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] .env file not found. Please create it from .env.example.
    exit /b 1
)

REM Check if .env file contains required API keys
echo [%date% %time%] [INFO] Checking .env file for required API keys... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Checking .env file for required API keys...
findstr /R "AIRTABLE_API_KEY OPENAI_API_KEY" .env > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Required API keys not found in .env file. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Required API keys not found in .env file.
    exit /b 1
) else (
    echo [%date% %time%] [SUCCESS] Required API keys found in .env file. >> "%LOG_FILE%"
    echo [%date% %time%] [SUCCESS] Required API keys found in .env file.
)

echo [%date% %time%] [SUCCESS] Environment validation completed successfully. >> "%LOG_FILE%"
echo [%date% %time%] [SUCCESS] Environment validation completed successfully.

REM Step 2: Prepare test data
echo [%date% %time%] [INFO] Step 2: Preparing test data... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Step 2: Preparing test data...

REM Create test data templates directory if it doesn't exist
if not exist "test_data_templates" (
    echo [%date% %time%] [INFO] Creating test data templates directory... >> "%LOG_FILE%"
    echo [%date% %time%] [INFO] Creating test data templates directory...
    mkdir "test_data_templates" 2>nul
)

REM Create test lead template if it doesn't exist
if not exist "test_data_templates\test_lead.json" (
    echo [%date% %time%] [INFO] Creating test lead template... >> "%LOG_FILE%"
    echo [%date% %time%] [INFO] Creating test lead template...
    echo {"name": "John Test","company": "Acme AI","linkedin_url": "https://linkedin.com/in/fakejohnsmith"} > "test_data_templates\test_lead.json"
)

REM Check if shared/leads.json exists
if not exist "shared\leads.json" (
    echo [%date% %time%] [WARNING] shared\leads.json not found. Creating new file. >> "%LOG_FILE%"
    echo [%date% %time%] [WARNING] shared\leads.json not found. Creating new file.
    echo [] > "shared\leads.json"
) else (
    REM Backup existing leads.json
    echo [%date% %time%] [INFO] Backing up existing leads.json... >> "%LOG_FILE%"
    echo [%date% %time%] [INFO] Backing up existing leads.json...
    copy "shared\leads.json" "%TEST_DIR%\leads.json.backup" > nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [%date% %time%] [ERROR] Failed to create backup of leads.json. >> "%LOG_FILE%"
        echo [%date% %time%] [ERROR] Failed to create backup of leads.json.
    ) else (
        echo [%date% %time%] [SUCCESS] Backup created: %TEST_DIR%\leads.json.backup >> "%LOG_FILE%"
        echo [%date% %time%] [SUCCESS] Backup created: %TEST_DIR%\leads.json.backup
    )
)

REM Inject test lead data
echo [%date% %time%] [INFO] Injecting test lead data... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Injecting test lead data...
if exist "inject_test_data.py" (
    python inject_test_data.py --template test_data_templates\test_lead.json --output shared\leads.json --backup
    if %ERRORLEVEL% neq 0 (
        echo [%date% %time%] [ERROR] Failed to inject test lead data. >> "%LOG_FILE%"
        echo [%date% %time%] [ERROR] Failed to inject test lead data.
    ) else (
        echo [%date% %time%] [SUCCESS] Test lead data injected successfully. >> "%LOG_FILE%"
        echo [%date% %time%] [SUCCESS] Test lead data injected successfully.
    )
) else (
    REM Fallback to direct file creation
    echo [{"name": "John Test","company": "Acme AI","linkedin_url": "https://linkedin.com/in/fakejohnsmith"}] > "shared\leads.json"
    if %ERRORLEVEL% neq 0 (
        echo [%date% %time%] [ERROR] Failed to create test lead data. >> "%LOG_FILE%"
        echo [%date% %time%] [ERROR] Failed to create test lead data.
    ) else (
        echo [%date% %time%] [SUCCESS] Test lead data created successfully. >> "%LOG_FILE%"
        echo [%date% %time%] [SUCCESS] Test lead data created successfully.
    )
)

echo [%date% %time%] [SUCCESS] Test data preparation completed successfully. >> "%LOG_FILE%"
echo [%date% %time%] [SUCCESS] Test data preparation completed successfully.

REM Step 3: Run the pipeline
echo [%date% %time%] [INFO] Step 3: Running the pipeline... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Step 3: Running the pipeline...

REM Run the pipeline
echo [%date% %time%] [INFO] Executing pipeline... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Executing pipeline...
if exist "run_pipeline_test.py" (
    python run_pipeline_test.py --docker --output-dir %TEST_DIR%
    set PIPELINE_STATUS=%ERRORLEVEL%
) else (
    REM Fallback to direct execution
    docker-compose exec -T 4runr-pipeline python run_pipeline.py > "%TEST_DIR%\pipeline_output.log" 2>&1
    set PIPELINE_STATUS=%ERRORLEVEL%
)

if %PIPELINE_STATUS% equ 0 (
    echo [%date% %time%] [SUCCESS] Pipeline execution completed successfully. >> "%LOG_FILE%"
    echo [%date% %time%] [SUCCESS] Pipeline execution completed successfully.
) else (
    echo [%date% %time%] [ERROR] Pipeline execution failed. Check logs for details. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Pipeline execution failed. Check logs for details.
)

REM Step 4: Monitor logs
echo [%date% %time%] [INFO] Step 4: Collecting logs... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Step 4: Collecting logs...

REM Collect logs from all containers
echo [%date% %time%] [INFO] Collecting logs from all containers... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Collecting logs from all containers...
if exist "monitor_logs.py" (
    python monitor_logs.py --output "%TEST_DIR%\container_logs.log"
) else (
    REM Fallback to direct log collection
    docker-compose logs --no-color > "%TEST_DIR%\container_logs.log" 2>&1
)

if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] [ERROR] Failed to collect logs. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Failed to collect logs.
) else (
    echo [%date% %time%] [SUCCESS] Logs collected successfully. >> "%LOG_FILE%"
    echo [%date% %time%] [SUCCESS] Logs collected successfully.
)

REM Step 5: Verify results
echo [%date% %time%] [INFO] Step 5: Verifying results... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Step 5: Verifying results...

REM Check if the enricher processed the test lead
echo [%date% %time%] [INFO] Checking if enricher processed the test lead... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Checking if enricher processed the test lead...
findstr /R "Enriching lead.*John Test Successfully enriched lead" "%TEST_DIR%\container_logs.log" > nul 2>&1
set ENRICHER_STATUS=%ERRORLEVEL%

REM Check if the engager processed the test lead
echo [%date% %time%] [INFO] Checking if engager processed the test lead... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Checking if engager processed the test lead...
findstr /R "Engaging with lead.*John Test Message sent to John Test" "%TEST_DIR%\container_logs.log" > nul 2>&1
set ENGAGER_STATUS=%ERRORLEVEL%

REM Check for container crashes or API failures
echo [%date% %time%] [INFO] Checking for container crashes or API failures... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Checking for container crashes or API failures...
findstr /R "Error Exception Failed Crash" "%TEST_DIR%\container_logs.log" > "%TEST_DIR%\errors.log" 2>&1
for /f %%a in ('type "%TEST_DIR%\errors.log" ^| find /c /v ""') do set ERROR_COUNT=%%a

REM Generate test results
echo [%date% %time%] [INFO] Generating test results... >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Generating test results...

REM Create test results file
echo # 4Runr AI Lead Scraper System Test Results > "%TEST_DIR%\test_results.md"
echo. >> "%TEST_DIR%\test_results.md"
echo **Date:** %date% %time% >> "%TEST_DIR%\test_results.md"
echo **Test ID:** %TIMESTAMP% >> "%TEST_DIR%\test_results.md"
echo. >> "%TEST_DIR%\test_results.md"
echo ## Test Summary >> "%TEST_DIR%\test_results.md"
echo. >> "%TEST_DIR%\test_results.md"

REM Add test summary based on results
if %ENRICHER_STATUS% equ 0 if %ENGAGER_STATUS% equ 0 if %ERROR_COUNT% equ 0 (
    echo **Status:** ✅ PASS >> "%TEST_DIR%\test_results.md"
    echo [%date% %time%] [SUCCESS] Test completed successfully! >> "%LOG_FILE%"
    echo [%date% %time%] [SUCCESS] Test completed successfully!
) else (
    echo **Status:** ❌ FAIL >> "%TEST_DIR%\test_results.md"
    echo [%date% %time%] [ERROR] Test failed. See %TEST_DIR%\test_results.md for details. >> "%LOG_FILE%"
    echo [%date% %time%] [ERROR] Test failed. See %TEST_DIR%\test_results.md for details.
)

REM Add component results
echo. >> "%TEST_DIR%\test_results.md"
echo ## Component Results >> "%TEST_DIR%\test_results.md"
echo. >> "%TEST_DIR%\test_results.md"

echo ### Enricher >> "%TEST_DIR%\test_results.md"
if %ENRICHER_STATUS% equ 0 (
    echo **Status:** ✅ PASS >> "%TEST_DIR%\test_results.md"
    echo **Details:** Successfully enriched test lead >> "%TEST_DIR%\test_results.md"
) else (
    echo **Status:** ❌ FAIL >> "%TEST_DIR%\test_results.md"
    echo **Details:** Failed to enrich test lead >> "%TEST_DIR%\test_results.md"
)
echo. >> "%TEST_DIR%\test_results.md"

echo ### Engager >> "%TEST_DIR%\test_results.md"
if %ENGAGER_STATUS% equ 0 (
    echo **Status:** ✅ PASS >> "%TEST_DIR%\test_results.md"
    echo **Details:** Successfully processed test lead for outreach >> "%TEST_DIR%\test_results.md"
) else (
    echo **Status:** ❌ FAIL >> "%TEST_DIR%\test_results.md"
    echo **Details:** Failed to process test lead for outreach >> "%TEST_DIR%\test_results.md"
)
echo. >> "%TEST_DIR%\test_results.md"

echo ### System Health >> "%TEST_DIR%\test_results.md"
if %ERROR_COUNT% equ 0 (
    echo **Status:** ✅ PASS >> "%TEST_DIR%\test_results.md"
    echo **Details:** No errors detected >> "%TEST_DIR%\test_results.md"
) else (
    echo **Status:** ❌ FAIL >> "%TEST_DIR%\test_results.md"
    echo **Details:** %ERROR_COUNT% errors detected >> "%TEST_DIR%\test_results.md"
)
echo. >> "%TEST_DIR%\test_results.md"

echo ## Log Files >> "%TEST_DIR%\test_results.md"
echo. >> "%TEST_DIR%\test_results.md"
echo - Full container logs: %TEST_DIR%\container_logs.log >> "%TEST_DIR%\test_results.md"
echo - Pipeline output: %TEST_DIR%\pipeline_output.log >> "%TEST_DIR%\test_results.md"
echo - Error log: %TEST_DIR%\errors.log >> "%TEST_DIR%\test_results.md"
echo. >> "%TEST_DIR%\test_results.md"

REM Add error details if any
if %ERROR_COUNT% gtr 0 (
    echo ## Error Details >> "%TEST_DIR%\test_results.md"
    echo. >> "%TEST_DIR%\test_results.md"
    echo ``` >> "%TEST_DIR%\test_results.md"
    type "%TEST_DIR%\errors.log" | findstr /n "^" | findstr /b "[1-9][0-9]*:" >> "%TEST_DIR%\test_results.md"
    if %ERROR_COUNT% gtr 20 (
        echo ... %ERROR_COUNT% more errors ... >> "%TEST_DIR%\test_results.md"
    )
    echo ``` >> "%TEST_DIR%\test_results.md"
)

echo [%date% %time%] [INFO] Test results saved to %TEST_DIR%\test_results.md >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Test results saved to %TEST_DIR%\test_results.md

REM Step 6: Clean up (optional)
echo [%date% %time%] [INFO] Test execution completed. >> "%LOG_FILE%"
echo [%date% %time%] [INFO] Test execution completed.
echo [%date% %time%] [INFO] To restore the original leads.json file, run: >> "%LOG_FILE%"
echo [%date% %time%] [INFO] To restore the original leads.json file, run:
echo [%date% %time%] [INFO] copy %TEST_DIR%\leads.json.backup shared\leads.json >> "%LOG_FILE%"
echo [%date% %time%] [INFO] copy %TEST_DIR%\leads.json.backup shared\leads.json

REM Final message
echo [%date% %time%] [SUCCESS] System test completed. Please review the test results in %TEST_DIR%\test_results.md >> "%LOG_FILE%"
echo [%date% %time%] [SUCCESS] System test completed. Please review the test results in %TEST_DIR%\test_results.md

exit /b 0