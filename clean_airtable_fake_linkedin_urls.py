#!/usr/bin/env python3
"""
Clean Fake LinkedIn URLs from Airtable
======================================
Identifies and fixes fake LinkedIn URLs with numbers in Airtable
"""

import os
import requests
import re
from datetime import datetime
import json
from typing import List, Dict, Optional

class AirtableFakeURLCleaner:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'  # Your correct base ID
        self.table_id = 'tblbBSE2jJv9am7ZA'  # Table 1
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY environment variable not set")
    
    def get_all_airtable_records(self) -> List[Dict]:
        """Get all records from Airtable"""
        print("📊 Loading all records from Airtable...")
        
        all_records = []
        offset = None
        
        while True:
            url = self.base_url
            params = {'pageSize': 100}
            if offset:
                params['offset'] = offset
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                raise Exception(f"Airtable API error: {response.status_code} - {response.text}")
            
            data = response.json()
            all_records.extend(data['records'])
            
            offset = data.get('offset')
            if not offset:
                break
        
        print(f"✅ Loaded {len(all_records)} records from Airtable")
        return all_records
    
    def identify_fake_linkedin_urls(self, records: List[Dict]) -> Dict:
        """Identify records with fake LinkedIn URLs"""
        print("🔍 Analyzing LinkedIn URLs for fake patterns...")
        
        analysis = {
            'total_records': len(records),
            'records_with_linkedin': 0,
            'fake_linkedin_records': [],
            'real_linkedin_records': [],
            'no_linkedin_records': [],
            'fake_patterns': {}
        }
        
        # Common fake patterns
        fake_patterns = [
            r'-\d{4}$',  # Ends with -1749, -0953, etc.
            r'-\d{3,}$', # Ends with any 3+ digit number
            r'-\d+$'     # Ends with any number
        ]
        
        for record in records:
            record_id = record['id']
            fields = record.get('fields', {})
            name = fields.get('Full Name', 'Unknown')
            linkedin_url = fields.get('LinkedIn URL', '')
            
            if not linkedin_url:
                analysis['no_linkedin_records'].append({
                    'record_id': record_id,
                    'name': name,
                    'reason': 'No LinkedIn URL'
                })
                continue
            
            analysis['records_with_linkedin'] += 1
            
            # Check for fake patterns
            is_fake = False
            fake_pattern_found = None
            
            for pattern in fake_patterns:
                if re.search(pattern, linkedin_url):
                    is_fake = True
                    fake_pattern_found = pattern
                    
                    # Track pattern frequency
                    match = re.search(r'-(\d+)$', linkedin_url)
                    if match:
                        number = match.group(1)
                        analysis['fake_patterns'][number] = analysis['fake_patterns'].get(number, 0) + 1
                    break
            
            if is_fake:
                analysis['fake_linkedin_records'].append({
                    'record_id': record_id,
                    'name': name,
                    'linkedin_url': linkedin_url,
                    'pattern': fake_pattern_found,
                    'fields': fields
                })
            else:
                analysis['real_linkedin_records'].append({
                    'record_id': record_id,
                    'name': name,
                    'linkedin_url': linkedin_url,
                    'fields': fields
                })
        
        print(f"📊 LinkedIn URL Analysis:")
        print(f"   Total records: {analysis['total_records']}")
        print(f"   With LinkedIn URLs: {analysis['records_with_linkedin']}")
        print(f"   Fake LinkedIn URLs: {len(analysis['fake_linkedin_records'])}")
        print(f"   Real LinkedIn URLs: {len(analysis['real_linkedin_records'])}")
        print(f"   No LinkedIn URL: {len(analysis['no_linkedin_records'])}")
        print(f"   Fake patterns found: {analysis['fake_patterns']}")
        
        return analysis
    
    def attempt_url_fixes(self, fake_records: List[Dict]) -> List[Dict]:
        """Try to fix fake URLs by removing numbers"""
        print("\n🔧 Attempting to fix fake LinkedIn URLs...")
        
        fixable_records = []
        
        for record in fake_records[:10]:  # Test first 10
            original_url = record['linkedin_url']
            name = record['name']
            
            # Try to fix by removing number suffix
            fixed_url = re.sub(r'-\d+$', '', original_url)
            
            if fixed_url != original_url:
                fixable_records.append({
                    **record,
                    'original_url': original_url,
                    'fixed_url': fixed_url,
                    'fixable': True
                })
                print(f"   Fixable: {name}")
                print(f"      {original_url} → {fixed_url}")
            else:
                fixable_records.append({
                    **record,
                    'original_url': original_url,
                    'fixed_url': None,
                    'fixable': False
                })
                print(f"   Not fixable: {name} - {original_url}")
        
        print(f"✅ Found {len([r for r in fixable_records if r['fixable']])} fixable URLs")
        
        return fixable_records
    
    def update_airtable_record(self, record_id: str, fields: Dict) -> bool:
        """Update a single Airtable record"""
        url = f"{self.base_url}/{record_id}"
        
        data = {'fields': fields}
        
        response = requests.patch(url, headers=self.headers, json=data)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error updating record {record_id}: {response.status_code} - {response.text}")
            return False
    
    def delete_airtable_record(self, record_id: str) -> bool:
        """Delete a single Airtable record"""
        url = f"{self.base_url}/{record_id}"
        
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error deleting record {record_id}: {response.status_code} - {response.text}")
            return False
    
    def clean_fake_urls(self, action='fix', apply_changes=False, max_changes=10):
        """Clean fake LinkedIn URLs from Airtable"""
        print("🧹 CLEANING FAKE LINKEDIN URLS FROM AIRTABLE")
        print("=" * 60)
        print(f"Action: {action}")
        print(f"Apply changes: {apply_changes}")
        print(f"Max changes: {max_changes}")
        print("")
        
        # Step 1: Get all records
        records = self.get_all_airtable_records()
        
        # Step 2: Identify fake URLs
        analysis = self.identify_fake_linkedin_urls(records)
        
        if len(analysis['fake_linkedin_records']) == 0:
            print("✅ No fake LinkedIn URLs found in Airtable!")
            return analysis
        
        print(f"\n🚨 Found {len(analysis['fake_linkedin_records'])} fake LinkedIn URLs!")
        
        # Step 3: Show examples
        print("\n📋 Examples of fake URLs:")
        for i, record in enumerate(analysis['fake_linkedin_records'][:5]):
            print(f"   {i+1}. {record['name']}: {record['linkedin_url']}")
        
        if not apply_changes:
            print(f"\n⚠️ SIMULATION MODE - No changes will be made")
            print(f"To actually clean the URLs, run with apply_changes=True")
            return analysis
        
        # Step 4: Apply changes
        print(f"\n🔧 Applying {action} to fake LinkedIn URLs...")
        
        changes_made = 0
        successful_changes = 0
        
        for record in analysis['fake_linkedin_records']:
            if changes_made >= max_changes:
                print(f"⚠️ Reached maximum changes limit ({max_changes})")
                break
            
            record_id = record['record_id']
            name = record['name']
            original_url = record['linkedin_url']
            
            if action == 'fix':
                # Try to fix URL by removing numbers
                fixed_url = re.sub(r'-\d+$', '', original_url)
                
                if fixed_url != original_url:
                    success = self.update_airtable_record(record_id, {'LinkedIn URL': fixed_url})
                    if success:
                        print(f"✅ Fixed: {name}")
                        print(f"   {original_url} → {fixed_url}")
                        successful_changes += 1
                    else:
                        print(f"❌ Failed to fix: {name}")
                else:
                    print(f"⚠️ Cannot fix: {name} - {original_url}")
            
            elif action == 'remove_url':
                # Remove the LinkedIn URL field
                success = self.update_airtable_record(record_id, {'LinkedIn URL': ''})
                if success:
                    print(f"✅ Removed URL: {name}")
                    successful_changes += 1
                else:
                    print(f"❌ Failed to remove URL: {name}")
            
            elif action == 'delete_record':
                # Delete the entire record
                success = self.delete_airtable_record(record_id)
                if success:
                    print(f"✅ Deleted record: {name}")
                    successful_changes += 1
                else:
                    print(f"❌ Failed to delete: {name}")
            
            changes_made += 1
        
        # Step 5: Results
        results = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'total_fake_urls': len(analysis['fake_linkedin_records']),
            'changes_attempted': changes_made,
            'successful_changes': successful_changes,
            'analysis': analysis
        }
        
        print(f"\n🎯 CLEANUP RESULTS:")
        print(f"   Action: {action}")
        print(f"   Fake URLs found: {results['total_fake_urls']}")
        print(f"   Changes attempted: {results['changes_attempted']}")
        print(f"   Successful changes: {results['successful_changes']}")
        print(f"   Success rate: {(results['successful_changes']/results['changes_attempted']*100):.1f}%" if results['changes_attempted'] > 0 else 0)
        
        # Save report
        report_file = f"airtable_cleanup_{action}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Report saved to: {report_file}")
        
        return results

def main():
    """Run Airtable fake URL cleaner"""
    print("🧹 Airtable Fake LinkedIn URL Cleaner")
    print("Removes fake LinkedIn URLs with numbers from Airtable")
    print("")
    
    try:
        cleaner = AirtableFakeURLCleaner()
        
        # Step 1: Analyze the problem
        print("📋 STEP 1: ANALYZE FAKE URLS")
        results = cleaner.clean_fake_urls(action='fix', apply_changes=False)
        
        if results['fake_linkedin_records']:
            print(f"\n🚨 FOUND {len(results['fake_linkedin_records'])} FAKE LINKEDIN URLS!")
            print("These URLs have numbers and likely give 404 errors")
            print("\n⚡ ACTION OPTIONS:")
            print("1. Fix URLs (remove numbers): python3 clean_airtable_fake_linkedin_urls.py --fix")
            print("2. Remove URLs only: python3 clean_airtable_fake_linkedin_urls.py --remove-urls") 
            print("3. Delete records: python3 clean_airtable_fake_linkedin_urls.py --delete-records")
        else:
            print("✅ No fake LinkedIn URLs found in Airtable!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    
    if '--fix' in sys.argv:
        cleaner = AirtableFakeURLCleaner()
        results = cleaner.clean_fake_urls(action='fix', apply_changes=True, max_changes=50)
        
    elif '--remove-urls' in sys.argv:
        cleaner = AirtableFakeURLCleaner()
        results = cleaner.clean_fake_urls(action='remove_url', apply_changes=True, max_changes=50)
        
    elif '--delete-records' in sys.argv:
        cleaner = AirtableFakeURLCleaner()
        results = cleaner.clean_fake_urls(action='delete_record', apply_changes=True, max_changes=50)
        
    else:
        main()
