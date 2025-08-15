#!/usr/bin/env python3
"""
Module entry point for the API service.
Can be run with: python -m outreach.api
"""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the main API
from api import main

if __name__ == '__main__':
    main()