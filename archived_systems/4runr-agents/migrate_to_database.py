#!/usr/bin/env python3
"""
Migration Script for 4Runr Lead System

This script helps migrate from JSON-based lead storage to the new database system.
It handles data migration, agent updates, and validation.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add database directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))

from database.migration_manager import MigrationManager
from database.lead_database import get_lead_database

def main():
    """Main migration function"""
    print("🔄 4Runr Lead System Database Migration")
    print("=" * 45)
    
    try:
        # Step 1: Initialize migration manager
        print("\\n📋 Step 1: Initializing Migration Manager")
        migration_manager = MigrationManager()
        
        # Step 2: Show current status
        print("\\n📊 Step 2: Current System Status")
        
        # Check JSON files
        json_files = ['raw_leads.json', 'enriched_leads.json', 'leads.json', 'custom_enriched_leads.json']
        json_lead_count = 0
        
        for json_file in json_files:
            file_path = Path('shared') / json_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        print(f"   📁 {json_file}: {len(data)} leads")
                        json_lead_count += len(data)
                except Exception as e:
                    print(f"   ❌ {json_file}: Error reading - {e}")
            else:
                print(f"   ⏭️ {json_file}: Not found")
        
        print(f"   📊 Total JSON leads: {json_lead_count}")
        
        # Check database
        db = get_lead_database()
        db_count = db.get_lead_count()
        print(f"   🗄️ Database leads: {db_count}")
        
        # Step 3: Migration decision
        print("\\n🤔 Step 3: Migration Decision")
        
        if json_lead_count == 0:
            print("   ✅ No JSON leads found - database system ready to use")
            print("   💡 You can start using the new database system immediately")
            return
        
        if db_count > 0:
            print(f"   ⚠️ Database already contains {db_count} leads")
            print("   🔄 Migration will merge JSON data with existing database data")
        else:
            print("   📝 Database is empty - ready for migration")
        
        # Ask for confirmation
        print(f"\\n❓ Ready to migrate {json_lead_count} leads from JSON files to database?")
        print("   This will:")
        print("   • Create backups of your JSON files")
        print("   • Migrate all lead data to the database")
        print("   • Handle duplicates automatically")
        print("   • Preserve all existing data")
        
        confirm = input("\\nProceed with migration? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Migration cancelled")
            return
        
        # Step 4: Run migration
        print("\\n🔄 Step 4: Running Migration")
        
        summary = migration_manager.migrate_all_json_files(create_backups=True)
        
        # Step 5: Show results
        print("\\n📊 Step 5: Migration Results")
        print(f"   Files processed: {summary.total_files_processed}")
        print(f"   Leads processed: {summary.total_leads_processed}")
        print(f"   Leads migrated: {summary.total_leads_migrated}")
        print(f"   Duplicates merged: {summary.total_duplicates_merged}")
        print(f"   Failed: {summary.total_leads_failed}")
        print(f"   Duration: {summary.total_duration_seconds:.2f}s")
        
        if summary.backups_created:
            print(f"\\n💾 Backups created:")
            for backup in summary.backups_created:
                print(f"   • {backup}")
        
        if summary.errors:
            print(f"\\n⚠️ Errors encountered:")
            for error in summary.errors:
                print(f"   • {error}")
        
        # Step 6: Validation
        print("\\n🔍 Step 6: Validating Migration")
        
        validation = migration_manager.validate_migration()
        
        print(f"   JSON leads: {validation['total_json_leads']}")
        print(f"   Database leads: {validation['total_db_leads']}")
        
        if validation['success']:
            print("   ✅ Migration validation passed!")
        else:
            print("   ⚠️ Migration validation had issues:")
            for error in validation['validation_errors']:
                print(f"     • {error}")
        
        # Step 7: Next steps
        print("\\n🎯 Step 7: Next Steps")
        
        if summary.success and validation['success']:
            print("   ✅ Migration completed successfully!")
            print("\\n📋 What to do next:")
            print("   1. Update your agents to use the new database system")
            print("   2. Test the new system with a few operations")
            print("   3. Once confident, you can archive the JSON files")
            print("\\n📚 Resources:")
            print("   • Agent Integration Guide: database/AGENT_INTEGRATION_GUIDE.md")
            print("   • Example updated agent: daily_enricher_agent_updated.py")
            print("   • Database documentation: database/README.md")
            
            # Create rollback script
            rollback_script = migration_manager.create_rollback_script()
            print(f"   • Rollback script: {rollback_script}")
            
        else:
            print("   ❌ Migration completed with issues")
            print("   📋 Recommended actions:")
            print("   1. Review the errors above")
            print("   2. Check your JSON files for data issues")
            print("   3. Run migration again after fixing issues")
            print("   4. Contact support if problems persist")
        
        # Step 8: Quick test
        print("\\n🧪 Step 8: Quick Database Test")
        
        try:
            # Test basic operations
            final_count = db.get_lead_count()
            recent_leads = db.get_recent_leads(days=1, limit=5)
            stats = db.get_search_statistics()
            
            print(f"   📊 Final database count: {final_count}")
            print(f"   🕐 Recent leads (24h): {len(recent_leads)}")
            print(f"   ✨ Enriched leads: {stats['enriched_count']}")
            print(f"   ✅ Database system is working correctly!")
            
        except Exception as e:
            print(f"   ❌ Database test failed: {e}")
            print("   🔧 Please check your database configuration")
        
        print("\\n🎉 Migration process completed!")
        
    except KeyboardInterrupt:
        print("\\n⚠️ Migration cancelled by user")
    except Exception as e:
        print(f"\\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

def show_agent_examples():
    """Show examples of how to update agents"""
    print("\\n📚 Agent Update Examples")
    print("=" * 30)
    
    print("\\n🔄 OLD WAY (JSON files):")
    print("""
# Loading leads
with open('shared/leads.json', 'r') as f:
    leads = json.load(f)

# Adding leads
leads.append(new_lead)
with open('shared/leads.json', 'w') as f:
    json.dump(leads, f)
""")
    
    print("\\n✅ NEW WAY (Database):")
    print("""
from database.lead_database import get_lead_database

# Get database instance
db = get_lead_database()

# Loading leads
leads = db.get_all_leads()

# Adding leads (with automatic duplicate detection)
lead_id = db.add_lead(new_lead)

# Searching leads
tech_leads = db.search_leads({'industry': 'Technology'})

# Getting leads that need enrichment
to_enrich = db.get_leads_needing_enrichment(limit=10)
""")
    
    print("\\n📖 For complete examples, see:")
    print("   • database/AGENT_INTEGRATION_GUIDE.md")
    print("   • daily_enricher_agent_updated.py")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--examples':
        show_agent_examples()
    else:
        main()