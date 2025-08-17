#!/usr/bin/env python3
"""
Emergency Fake Data Cleanup
===========================
Immediately removes all fake LinkedIn URLs and associated fake data.
"""

import sqlite3
import json
from datetime import datetime
import re

class EmergencyFakeDataCleanup:
    def __init__(self, db_path='data/unified_leads.db'):
        self.db_path = db_path
        
    def identify_fake_linkedin_urls(self) -> list:
        """Identify all fake LinkedIn URLs with number patterns"""
        print("🔍 Identifying fake LinkedIn URLs...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Get all LinkedIn URLs
        cursor = conn.execute('''
            SELECT id, full_name, linkedin_url, email, company, source, created_at
            FROM leads 
            WHERE linkedin_url IS NOT NULL 
            AND linkedin_url != ''
        ''')
        
        all_records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        fake_patterns = [
            r'-\d{4}$',  # Ends with -1749, -0953, etc.
            r'-\d{3,}$', # Ends with any 3+ digit number
        ]
        
        fake_records = []
        
        for record in all_records:
            url = record['linkedin_url']
            
            # Check for fake patterns
            for pattern in fake_patterns:
                if re.search(pattern, url):
                    fake_records.append(record)
                    break
        
        print(f"🚨 Found {len(fake_records)} fake LinkedIn URLs out of {len(all_records)} total")
        
        return fake_records
    
    def analyze_fake_data(self, fake_records: list) -> dict:
        """Analyze the fake data patterns"""
        print("📊 Analyzing fake data patterns...")
        
        analysis = {
            'total_fake': len(fake_records),
            'number_patterns': {},
            'name_patterns': {},
            'sources': {},
            'fake_examples': fake_records[:10]
        }
        
        for record in fake_records:
            url = record['linkedin_url']
            name = record['full_name'] or 'Unknown'
            source = record['source'] or 'Unknown'
            
            # Extract number pattern
            match = re.search(r'-(\d+)$', url)
            if match:
                number = match.group(1)
                analysis['number_patterns'][number] = analysis['number_patterns'].get(number, 0) + 1
            
            # Track name patterns
            first_name = name.split()[0] if name and ' ' in name else name
            analysis['name_patterns'][first_name] = analysis['name_patterns'].get(first_name, 0) + 1
            
            # Track sources
            analysis['sources'][source] = analysis['sources'].get(source, 0) + 1
        
        print(f"📊 Fake Data Analysis:")
        print(f"   Total fake records: {analysis['total_fake']}")
        print(f"   Number patterns: {dict(list(analysis['number_patterns'].items())[:5])}")
        print(f"   Top fake names: {dict(list(analysis['name_patterns'].items())[:5])}")
        print(f"   Sources generating fake data: {analysis['sources']}")
        
        return analysis
    
    def delete_fake_records(self, fake_records: list, confirm: bool = False) -> int:
        """Delete all fake records from database"""
        if not confirm:
            print("⚠️ DELETE operation requires confirmation")
            return 0
        
        print(f"🗑️ Deleting {len(fake_records)} fake records...")
        
        conn = sqlite3.connect(self.db_path)
        
        fake_ids = [record['id'] for record in fake_records]
        deleted_count = 0
        
        # Delete in batches
        batch_size = 50
        for i in range(0, len(fake_ids), batch_size):
            batch = fake_ids[i:i + batch_size]
            placeholders = ','.join(['?' for _ in batch])
            
            cursor = conn.execute(f'DELETE FROM leads WHERE id IN ({placeholders})', batch)
            deleted_count += cursor.rowcount
            
            print(f"   Deleted batch {i//batch_size + 1}: {deleted_count}/{len(fake_ids)} records")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully deleted {deleted_count} fake records")
        return deleted_count
    
    def verify_cleanup(self) -> dict:
        """Verify that fake data has been cleaned"""
        print("✅ Verifying cleanup...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Check for remaining fake patterns
        cursor = conn.execute('''
            SELECT COUNT(*) FROM leads 
            WHERE linkedin_url LIKE '%-1749'
            OR linkedin_url LIKE '%-0953'
            OR linkedin_url REGEXP '-[0-9]{3,}$'
        ''')
        
        remaining_fake = cursor.fetchone()[0]
        
        # Get total remaining records
        cursor = conn.execute('SELECT COUNT(*) FROM leads')
        total_remaining = cursor.fetchone()[0]
        
        # Get records with LinkedIn URLs
        cursor = conn.execute('''
            SELECT COUNT(*) FROM leads 
            WHERE linkedin_url IS NOT NULL 
            AND linkedin_url != ''
        ''')
        
        with_linkedin = cursor.fetchone()[0]
        
        conn.close()
        
        verification = {
            'remaining_fake': remaining_fake,
            'total_remaining': total_remaining,
            'with_linkedin': with_linkedin,
            'cleanup_success': remaining_fake == 0
        }
        
        print(f"📊 Cleanup Verification:")
        print(f"   Remaining fake URLs: {verification['remaining_fake']}")
        print(f"   Total remaining records: {verification['total_remaining']}")
        print(f"   Records with LinkedIn: {verification['with_linkedin']}")
        print(f"   Cleanup successful: {'✅ YES' if verification['cleanup_success'] else '❌ NO'}")
        
        return verification
    
    def emergency_cleanup(self, confirm_delete: bool = False) -> dict:
        """Run complete emergency fake data cleanup"""
        print("🚨 EMERGENCY FAKE DATA CLEANUP STARTING")
        print("=" * 50)
        
        # Step 1: Identify fake data
        fake_records = self.identify_fake_linkedin_urls()
        
        if not fake_records:
            print("✅ No fake LinkedIn URLs found")
            return {'status': 'clean', 'deleted': 0}
        
        # Step 2: Analyze fake data
        analysis = self.analyze_fake_data(fake_records)
        
        # Step 3: Save backup before deletion
        backup_file = f"fake_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump({
                'analysis': analysis,
                'fake_records': fake_records
            }, f, indent=2, default=str)
        
        print(f"💾 Backup saved to: {backup_file}")
        
        # Step 4: Delete fake data (if confirmed)
        if confirm_delete:
            deleted_count = self.delete_fake_records(fake_records, confirm=True)
        else:
            print("⚠️ SIMULATION MODE - No data deleted")
            print("   To actually delete fake data, run with confirm_delete=True")
            deleted_count = 0
        
        # Step 5: Verify cleanup
        verification = self.verify_cleanup()
        
        # Step 6: Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'fake_records_found': len(fake_records),
            'fake_records_deleted': deleted_count,
            'backup_file': backup_file,
            'analysis': analysis,
            'verification': verification,
            'status': 'completed' if confirm_delete else 'simulation'
        }
        
        print(f"\n🏆 EMERGENCY CLEANUP COMPLETED")
        print("=" * 50)
        print(f"🚨 Fake records found: {len(fake_records)}")
        print(f"🗑️ Fake records deleted: {deleted_count}")
        print(f"📊 Database status: {'✅ CLEAN' if verification['cleanup_success'] else '❌ STILL HAS FAKE DATA'}")
        
        return report

def main():
    """Run emergency fake data cleanup"""
    print("🚨 EMERGENCY: Cleaning fake LinkedIn URLs")
    print("This will identify and remove all fake LinkedIn URLs ending with numbers")
    print("")
    
    try:
        cleanup = EmergencyFakeDataCleanup()
        
        # First run in simulation mode
        print("📋 STEP 1: SIMULATION MODE (no deletion)")
        report = cleanup.emergency_cleanup(confirm_delete=False)
        
        if report['fake_records_found'] > 0:
            print(f"\n🚨 FOUND {report['fake_records_found']} FAKE RECORDS!")
            print("This includes URLs like:")
            for example in report['analysis']['fake_examples'][:3]:
                print(f"   - {example['full_name']}: {example['linkedin_url']}")
            
            print("\n⚠️ To actually delete these fake records, run:")
            print("python3 emergency_fake_data_cleanup.py --confirm")
        else:
            print("✅ No fake records found - database is clean")
        
        return 0
        
    except Exception as e:
        print(f"❌ Emergency cleanup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    
    # Check for confirmation flag
    confirm_delete = '--confirm' in sys.argv
    
    if confirm_delete:
        print("🚨 DELETION MODE - WILL ACTUALLY DELETE FAKE DATA")
        cleanup = EmergencyFakeDataCleanup()
        report = cleanup.emergency_cleanup(confirm_delete=True)
        
        # Save final report
        report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Final report saved to: {report_file}")
    else:
        main()
