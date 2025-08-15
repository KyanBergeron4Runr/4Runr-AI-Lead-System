#!/usr/bin/env python3
"""
Test script to verify all dependencies can be imported correctly.
"""

import sys
from typing import List, Tuple

def test_import(package_name: str, import_statement: str) -> Tuple[bool, str]:
    """Test if a package can be imported."""
    try:
        exec(import_statement)
        return True, f"✅ {package_name}: Successfully imported"
    except ImportError as e:
        return False, f"❌ {package_name}: Import failed - {e}"
    except Exception as e:
        return False, f"⚠️ {package_name}: Unexpected error - {e}"

def main():
    """Test all required dependencies."""
    print("🧪 Testing Dependencies Installation")
    print("=" * 40)
    
    # Define packages to test with their import statements
    packages_to_test = [
        ("python-dotenv", "from dotenv import load_dotenv"),
        ("pyairtable", "from pyairtable import Api"),
        ("validators", "import validators"),
        ("requests", "import requests"),
        ("beautifulsoup4", "from bs4 import BeautifulSoup"),
        ("playwright", "from playwright.async_api import async_playwright"),
        ("openai", "from openai import OpenAI"),
        ("jinja2", "from jinja2 import Template"),
    ]
    
    results = []
    success_count = 0
    
    for package_name, import_statement in packages_to_test:
        success, message = test_import(package_name, import_statement)
        results.append((success, message))
        if success:
            success_count += 1
        print(message)
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {success_count}/{len(packages_to_test)} packages imported successfully")
    
    if success_count == len(packages_to_test):
        print("🎉 All dependencies are working correctly!")
        return True
    else:
        print("⚠️ Some dependencies failed to import. Check installation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)