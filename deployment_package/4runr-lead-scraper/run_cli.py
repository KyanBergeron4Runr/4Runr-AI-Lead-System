#!/usr/bin/env python3
"""
CLI Runner

Main entry point for the 4runr-lead-scraper CLI.
"""

import sys
import os
from pathlib import Path

# Import the working CLI
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    try:
        # Import and run the working CLI (safe version)
        from working_cli_safe import main
        main()
    except Exception as e:
        print(f"CLI error: {e}")
        sys.exit(1)