#!/usr/bin/env python3
"""
Fix LinkedIn Numbers - Simple URL Cleaner
=========================================
Removes numbers from the end of LinkedIn URLs in Airtable
"""

import os
import requests
import re
from datetime import datetime

class SimpleLinkedInFixer:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = 'appBZvPvNXGqtoJdc'
        self.table_id = 'tblbBSE2jJv9am7ZA'
        self.base_url = f'https://api.airtable.com/v0/{self.base_id}/{self.table_id}'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_all_records(self):
        """Get all records from Airtable"""
        print("📊 Loading records from Airtable...")
        
        all_records = []
        offset = None
        
        while True:
            params = {'pageSize': 100}
            if offset:
                params['offset'] = offset
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            data = response.json()
            all_records.extend(data['records'])
            
            offset = data.get('offset')
            if not offset:
                break
        
        print(f"✅ Loaded {len(all_records)} records")
        return all_records
    
    def fix_linkedin_url(self, url):
        """Remove numbers from end of LinkedIn URL"""
        if not url or 'linkedin.com' not in url:
            return url, False
        
        # Remove numbers at the end: -1749, -0953, etc.
        fixed_url = re.sub(r'-\d+$', '', url)
        
        return fixed_url, (fixed_url != url)
    
    def update_record(self, record_id, linkedin_url):
        """Update LinkedIn URL in Airtable"""
        url = f"{self.base_url}/{record_id}"
        data = {'fields': {'LinkedIn URL': linkedin_url}}
        
        response = requests.patch(url, headers=self.headers, json=data)
        return response.status_code == 200
    
    def fix_all_urls(self, apply_changes=False):
        """Fix all LinkedIn URLs with numbers"""
        print("🔧 FIXING LINKEDIN URLS WITH NUMBERS")
        print("=" * 50)
        
        records = self.get_all_records()
        
        urls_to_fix = []
        
        # Find URLs that need fixing
        for record in records:
            fields = record.get('fields', {})
            name = fields.get('Full Name', 'Unknown')
            linkedin_url = fields.get('LinkedIn URL', '')
            
            if linkedin_url:
                fixed_url, needs_fix = self.fix_linkedin_url(linkedin_url)
                
                if needs_fix:
                    urls_to_fix.append({
                        'record_id': record['id'],
                        'name': name,
                        'original_url': linkedin_url,
                        'fixed_url': fixed_url
                    })
        
        print(f"🔍 Found {len(urls_to_fix)} URLs with numbers to fix")
        
        if len(urls_to_fix) == 0:
            print("✅ No LinkedIn URLs with numbers found!")
            return
        
        # Show examples
        print(f"\n📋 Examples of URLs to fix:")
        for i, fix in enumerate(urls_to_fix[:5]):
            print(f"   {i+1}. {fix['name']}")
            print(f"      {fix['original_url']} → {fix['fixed_url']}")
        
        if not apply_changes:
            print(f"\n⚠️ SIMULATION MODE - No changes made")
            print(f"To actually fix the URLs, run with --fix flag")
            return
        
        # Apply fixes
        print(f"\n🔧 Fixing {len(urls_to_fix)} LinkedIn URLs...")
        
        successful = 0
        failed = 0
        
        for fix in urls_to_fix:
            success = self.update_record(fix['record_id'], fix['fixed_url'])
            
            if success:
                print(f"✅ Fixed: {fix['name']}")
                successful += 1
            else:
                print(f"❌ Failed: {fix['name']}")
                failed += 1
        
        print(f"\n🎯 RESULTS:")
        print(f"✅ Successfully fixed: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success rate: {(successful/(successful+failed)*100):.1f}%")
        
        print(f"\n🎉 LinkedIn URLs cleaned! Numbers removed from all URLs.")

def main():
    """Run the LinkedIn URL fixer"""
    print("🔧 Simple LinkedIn URL Number Remover")
    print("Removes numbers from LinkedIn URLs in Airtable")
    print("")
    
    try:
        fixer = SimpleLinkedInFixer()
        
        import sys
        if '--fix' in sys.argv:
            fixer.fix_all_urls(apply_changes=True)
        else:
            fixer.fix_all_urls(apply_changes=False)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
