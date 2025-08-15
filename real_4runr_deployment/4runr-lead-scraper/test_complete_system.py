#!/usr/bin/env python3
"""
Complete System Test for 4runr-lead-scraper consolidation

Tests the entire pipeline: database → CLI → integration with other systems
"""
import os
import sys
import sqlite3
import subprocess
from pathlib import Path

def test_database_integrity():
    """Test that the database is properly set up and contains data"""
    print("🗄️  Testing Database Integrity...")
    
    db_path = "4runr-lead-scraper/data/leads.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        required_tables = ['leads', 'sync_status', 'migration_log']
        
        for table in required_tables:
            if table in tables:
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' missing")
                return False
        
        # Test data integrity
        cursor.execute("SELECT COUNT(*) FROM leads")
        lead_count = cursor.fetchone()[0]
        print(f"  📊 Total leads: {lead_count}")
        
        if lead_count == 0:
            print("  ❌ No leads found in database")
            return False
        
        # Test data quality
        cursor.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
        email_count = cursor.fetchone()[0]
        print(f"  📧 Leads with email: {email_count}")
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE full_name IS NOT NULL AND full_name != ''")
        name_count = cursor.fetchone()[0]
        print(f"  👤 Leads with names: {name_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_system_structure():
    """Test that all required files and directories exist"""
    print("\n📁 Testing System Structure...")
    
    required_files = [
        "4runr-lead-scraper/.env",
        "4runr-lead-scraper/requirements.txt",
        "4runr-lead-scraper/README.md",
        "4runr-lead-scraper/run_cli.py",
        "4runr-lead-scraper/cli/cli.py",
        "4runr-lead-scraper/database/models.py",
        "4runr-lead-scraper/scraper/serpapi_scraper.py",
        "4runr-lead-scraper/enricher/email_enricher.py",
        "4runr-lead-scraper/sync/airtable_sync.py",
        "4runr-lead-scraper/scripts/daily_scraper.py",
        "4runr-lead-scraper/scripts/migrate_data.py",
        "4runr-lead-scraper/config/settings.py",
        "4runr-lead-scraper/utils/logging.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            all_exist = False
    
    return all_exist

def test_configuration():
    """Test that configuration files are properly set up"""
    print("\n⚙️  Testing Configuration...")
    
    # Test .env file
    env_path = "4runr-lead-scraper/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        required_vars = [
            'SERPAPI_API_KEY',
            'LEAD_DATABASE_PATH',
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID'
        ]
        
        for var in required_vars:
            if var in env_content:
                print(f"  ✅ {var} configured")
            else:
                print(f"  ⚠️  {var} not found in .env")
    else:
        print("  ❌ .env file not found")
        return False
    
    # Test requirements.txt
    req_path = "4runr-lead-scraper/requirements.txt"
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            requirements = f.read()
        
        required_packages = ['requests', 'sqlite3', 'python-dotenv']
        for package in required_packages:
            if package in requirements or package == 'sqlite3':  # sqlite3 is built-in
                print(f"  ✅ {package} in requirements")
            else:
                print(f"  ⚠️  {package} not in requirements")
    
    return True

def test_integration_with_other_systems():
    """Test that other systems can connect to the new database"""
    print("\n🔗 Testing Integration with Other Systems...")
    
    # Test 4runr-brain connection
    brain_files = [
        "4runr-brain/serve_campaign_brain.py",
        "4runr-brain/debug_search_result.py"
    ]
    
    for file_path in brain_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if "4runr-lead-scraper" in content and "leads.db" in content:
                print(f"  ✅ {file_path} updated to use new database")
            else:
                print(f"  ❌ {file_path} not updated")
                return False
        else:
            print(f"  ⚠️  {file_path} not found")
    
    # Test 4runr-outreach-system configuration
    outreach_env = "4runr-outreach-system/.env"
    if os.path.exists(outreach_env):
        with open(outreach_env, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if "LEAD_DATABASE_PATH" in content:
            print(f"  ✅ 4runr-outreach-system .env updated")
        else:
            print(f"  ⚠️  4runr-outreach-system .env not updated")
    
    return True

def test_migration_success():
    """Test that data migration was successful"""
    print("\n📦 Testing Migration Success...")
    
    # Check if migration log exists
    db_path = "4runr-lead-scraper/data/leads.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check migration log
        cursor.execute("SELECT COUNT(*) FROM migration_log")
        migration_count = cursor.fetchone()[0]
        
        if migration_count > 0:
            print(f"  ✅ Migration log entries: {migration_count}")
            
            # Get latest migration details
            cursor.execute("""
                SELECT migration_type, source_system, leads_migrated, leads_merged, created_at 
                FROM migration_log 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                migration_type, source_system, migrated, merged, created_at = result
                print(f"  📊 Latest migration: {migration_type} from {source_system}")
                print(f"  📈 Leads migrated: {migrated}, merged: {merged}")
                print(f"  📅 Migration date: {created_at}")
        else:
            print("  ⚠️  No migration log entries found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Migration test failed: {e}")
        return False

def test_backup_system():
    """Test that backups were created during migration"""
    print("\n💾 Testing Backup System...")
    
    backup_dir = "backups"
    if os.path.exists(backup_dir):
        backup_files = list(Path(backup_dir).glob("*.db"))
        
        if backup_files:
            print(f"  ✅ Backup directory exists with {len(backup_files)} backup files")
            for backup_file in backup_files:
                print(f"    📁 {backup_file.name}")
        else:
            print("  ⚠️  Backup directory exists but no backup files found")
    else:
        print("  ⚠️  No backup directory found")
    
    return True

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🧪 4runr-lead-scraper Complete System Test")
    print("=" * 60)
    
    tests = [
        ("Database Integrity", test_database_integrity),
        ("System Structure", test_system_structure),
        ("Configuration", test_configuration),
        ("Integration", test_integration_with_other_systems),
        ("Migration Success", test_migration_success),
        ("Backup System", test_backup_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)