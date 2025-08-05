#!/usr/bin/env python3
"""
Simple System Test

Basic test to verify core functionality without complex imports.
"""

import os
import sys
import sqlite3
from pathlib import Path

def test_environment():
    """Test environment variables."""
    print("🧪 Testing Environment Variables...")
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        return False
    
    # Load environment manually
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    # Check required variables
    required_vars = ['SERPAPI_KEY', 'AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID']
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} configured")
        else:
            print(f"❌ {var} missing")
            return False
    
    return True

def test_database_creation():
    """Test database creation."""
    print("\n🧪 Testing Database Creation...")
    
    try:
        # Create data directory
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Test SQLite connection
        db_path = data_dir / 'leads.db'
        conn = sqlite3.connect(str(db_path))
        
        # Create a simple test table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        ''')
        
        # Test insert
        conn.execute("INSERT OR REPLACE INTO test_leads (id, name, email) VALUES (?, ?, ?)", 
                    ('test1', 'Test User', 'test@example.com'))
        conn.commit()
        
        # Test select
        cursor = conn.execute("SELECT COUNT(*) FROM test_leads")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database created successfully")
        print(f"   Path: {db_path}")
        print(f"   Test records: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_dependencies():
    """Test required Python dependencies."""
    print("\n🧪 Testing Dependencies...")
    
    required_packages = [
        'requests',
        'python-dotenv',
        'click',
        'dns.resolver',
        'beautifulsoup4'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            if package == 'dns.resolver':
                import dns.resolver
            elif package == 'python-dotenv':
                import dotenv
            elif package == 'beautifulsoup4':
                import bs4
            else:
                __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def test_file_structure():
    """Test file structure."""
    print("\n🧪 Testing File Structure...")
    
    required_files = [
        'config/settings.py',
        'database/models.py',
        'scraper/serpapi_scraper.py',
        'enricher/email_enricher.py',
        'sync/airtable_sync.py',
        'cli/cli.py',
        'requirements.txt'
    ]
    
    missing = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            missing.append(file_path)
    
    return len(missing) == 0

def main():
    """Run simple tests."""
    print("🚀 4Runr Lead Scraper - Simple System Test")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_dependencies,
        test_environment,
        test_database_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ Basic system checks passed!")
        print("\nNext steps:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Test CLI: python cli/cli.py --help")
        print("3. Test scraping: python cli/cli.py scrape leads --max-leads 1 --dry-run")
        return 0
    else:
        print("❌ Some basic checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())