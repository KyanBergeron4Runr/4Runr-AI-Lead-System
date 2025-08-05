#!/bin/bash
# Script to run the full system test and capture the output

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if the test script exists
if [ ! -f "scripts/test_full_system.py" ]; then
    echo "Error: Test script not found: scripts/test_full_system.py"
    exit 1
fi

# Create a log file
LOG_FILE="system_test_$(date +%Y%m%d_%H%M%S).log"

echo "Running full system test..."
echo "Log file: $LOG_FILE"

# Run the test script and capture the output
python3 scripts/test_full_system.py | tee "$LOG_FILE"

# Check the exit code
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ Test completed successfully!"
    echo "See $LOG_FILE for details"
else
    echo -e "\n❌ Test failed with exit code $EXIT_CODE"
    echo "See $LOG_FILE for details"
fi

exit $EXIT_CODE