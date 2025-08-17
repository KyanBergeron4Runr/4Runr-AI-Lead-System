#!/usr/bin/env python3
"""
Fix LinkedIn URL Numbers
========================
Removes numbers from LinkedIn URLs and validates they work.
Prevents 404 errors by cleaning up bad URLs.
"""

import sqlite3
import requests
import re
import time
from datetime import datetime
from typing import List, Dict, Tuple
import json

class LinkedInURLFixer:
    def __init__(self, db_path='data/unified_leads.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_all_linkedin_urls(self) -> List[Dict]:
        """Get all LinkedIn URLs from database"""
        print("📊 Loading all LinkedIn URLs from database...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute('''
            SELECT id, full_name, company, linkedin_url, email, source, created_at 
            FROM leads 
            WHERE linkedin_url IS NOT NULL 
            AND linkedin_url != ''
            AND linkedin_url LIKE '%linkedin.com%'
            ORDER BY created_at DESC
        ''')
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ Found {len(records)} records with LinkedIn URLs")
        return records
    
    def analyze_linkedin_urls(self, records: List[Dict]) -> Dict:
        """Analyze LinkedIn URL patterns"""
        print("🔍 Analyzing LinkedIn URL patterns...")
        
        analysis = {
            'total_urls': len(records),
            'good_urls': [],
            'bad_urls': [],
            'number_patterns': {},
            'domain_patterns': {},
            'fixable_urls': []
        }
        
        for record in records:
            url = record['linkedin_url']
            name = record['full_name'] or 'Unknown'
            
            # Categorize domain
            if 'ca.linkedin.com' in url:
                analysis['domain_patterns']['ca.linkedin.com'] = analysis['domain_patterns'].get('ca.linkedin.com', 0) + 1
            else:
                analysis['domain_patterns']['linkedin.com'] = analysis['domain_patterns'].get('linkedin.com', 0) + 1
            
            # Check for number patterns (bad URLs)
            number_match = re.search(r'-(\d+)$', url)
            if number_match:
                number = number_match.group(1)
                analysis['number_patterns'][number] = analysis['number_patterns'].get(number, 0) + 1
                analysis['bad_urls'].append({
                    'record': record,
                    'url': url,
                    'name': name,
                    'number': number,
                    'reason': f'Ends with -{number}'
                })
                
                # Try to create fixed version
                fixed_url = re.sub(r'-\d+$', '', url)
                analysis['fixable_urls'].append({
                    'record_id': record['id'],
                    'name': name,
                    'original_url': url,
                    'fixed_url': fixed_url
                })
            else:
                analysis['good_urls'].append({
                    'record': record,
                    'url': url,
                    'name': name,
                    'reason': 'No numbers detected'
                })
        
        print(f"📊 URL Analysis Results:")
        print(f"   Total URLs: {analysis['total_urls']}")
        print(f"   Good URLs: {len(analysis['good_urls'])}")
        print(f"   Bad URLs (with numbers): {len(analysis['bad_urls'])}")
        print(f"   Fixable URLs: {len(analysis['fixable_urls'])}")
        print(f"   Number patterns: {analysis['number_patterns']}")
        print(f"   Domain patterns: {analysis['domain_patterns']}")
        
        return analysis
    
    def test_linkedin_url(self, url: str) -> Tuple[bool, str, int]:
        """Test if a LinkedIn URL works"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            status_code = response.status_code
            
            if status_code == 200:
                return True, "Working", status_code
            elif status_code == 404:
                return False, "Not Found (404)", status_code
            elif status_code == 403:
                return False, "Forbidden (403)", status_code
            elif status_code in [301, 302]:
                return True, "Redirected (working)", status_code
            else:
                return False, f"Error ({status_code})", status_code
                
        except requests.exceptions.Timeout:
            return False, "Timeout", 0
        except requests.exceptions.ConnectionError:
            return False, "Connection Error", 0
        except Exception as e:
            return False, f"Error: {str(e)[:50]}", 0
    
    def validate_url_fixes(self, fixable_urls: List[Dict], max_test: int = 5) -> List[Dict]:
        """Test if fixed URLs actually work"""
        print(f"🧪 Testing up to {max_test} URL fixes...")
        
        validated_fixes = []
        
        for i, fix in enumerate(fixable_urls[:max_test]):
            name = fix['name']
            original_url = fix['original_url']
            fixed_url = fix['fixed_url']
            
            print(f"   Testing {i+1}/{min(len(fixable_urls), max_test)}: {name}")
            print(f"   Original: {original_url}")
            print(f"   Fixed: {fixed_url}")
            
            # Test original URL
            orig_works, orig_status, orig_code = self.test_linkedin_url(original_url)
            print(f"   Original status: {orig_status}")
            
            # Test fixed URL
            fixed_works, fixed_status, fixed_code = self.test_linkedin_url(fixed_url)
            print(f"   Fixed status: {fixed_status}")
            
            fix_result = {
                **fix,
                'original_works': orig_works,
                'original_status': orig_status,
                'fixed_works': fixed_works,
                'fixed_status': fixed_status,
                'should_fix': not orig_works and fixed_works
            }
            
            if fix_result['should_fix']:
                print(f"   ✅ Fix recommended: Original broken, fixed works")
            elif orig_works:
                print(f"   ⚠️ Original works: No fix needed")
            elif not fixed_works:
                print(f"   ❌ Neither works: Cannot fix")
            
            validated_fixes.append(fix_result)
            print()
            
            # Rate limiting
            time.sleep(2)
        
        return validated_fixes
    
    def apply_url_fixes(self, validated_fixes: List[Dict], apply_changes: bool = False) -> int:
        """Apply URL fixes to database"""
        
        fixes_to_apply = [fix for fix in validated_fixes if fix['should_fix']]
        
        if not fixes_to_apply:
            print("✅ No URL fixes needed")
            return 0
        
        print(f"🔧 Found {len(fixes_to_apply)} URLs that can be fixed")
        
        if not apply_changes:
            print("⚠️ SIMULATION MODE - No changes will be made")
            for fix in fixes_to_apply:
                print(f"   Would fix: {fix['name']}")
                print(f"   {fix['original_url']} → {fix['fixed_url']}")
            return 0
        
        print("🔧 Applying URL fixes to database...")
        
        conn = sqlite3.connect(self.db_path)
        fixed_count = 0
        
        for fix in fixes_to_apply:
            try:
                conn.execute(
                    'UPDATE leads SET linkedin_url = ? WHERE id = ?',
                    (fix['fixed_url'], fix['record_id'])
                )
                fixed_count += 1
                print(f"   ✅ Fixed: {fix['name']}")
                print(f"      {fix['original_url']} → {fix['fixed_url']}")
            except Exception as e:
                print(f"   ❌ Error fixing {fix['name']}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully fixed {fixed_count} LinkedIn URLs")
        return fixed_count
    
    def remove_bad_urls(self, bad_urls: List[Dict], apply_changes: bool = False) -> int:
        """Remove URLs that can't be fixed"""
        
        unfixable_urls = [url for url in bad_urls if not any(
            fix['record_id'] == url['record']['id'] and fix['should_fix'] 
            for fix in self.validated_fixes if hasattr(self, 'validated_fixes')
        )]
        
        if not unfixable_urls:
            print("✅ No unfixable URLs to remove")
            return 0
        
        print(f"🗑️ Found {len(unfixable_urls)} unfixable URLs")
        
        if not apply_changes:
            print("⚠️ SIMULATION MODE - No removals will be made")
            for url_info in unfixable_urls[:5]:  # Show first 5
                print(f"   Would remove: {url_info['name']} - {url_info['url']}")
            return 0
        
        print("🗑️ Removing unfixable URLs from database...")
        
        conn = sqlite3.connect(self.db_path)
        removed_count = 0
        
        for url_info in unfixable_urls:
            try:
                conn.execute(
                    'UPDATE leads SET linkedin_url = NULL WHERE id = ?',
                    (url_info['record']['id'],)
                )
                removed_count += 1
                print(f"   ✅ Removed bad URL: {url_info['name']}")
            except Exception as e:
                print(f"   ❌ Error removing URL for {url_info['name']}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully removed {removed_count} bad LinkedIn URLs")
        return removed_count
    
    def comprehensive_url_fix(self, apply_changes: bool = False) -> Dict:
        """Complete URL fixing process"""
        print("🔧 COMPREHENSIVE LINKEDIN URL FIX")
        print("=" * 50)
        print("Fixing LinkedIn URLs with numbers that cause 404 errors")
        print("")
        
        # Step 1: Get and analyze URLs
        records = self.get_all_linkedin_urls()
        if not records:
            return {'status': 'no_urls', 'message': 'No LinkedIn URLs found'}
        
        analysis = self.analyze_linkedin_urls(records)
        
        # Step 2: Test URL fixes
        if analysis['fixable_urls']:
            print(f"\n🧪 TESTING URL FIXES")
            print("-" * 30)
            validated_fixes = self.validate_url_fixes(analysis['fixable_urls'])
            self.validated_fixes = validated_fixes
        else:
            validated_fixes = []
        
        # Step 3: Apply fixes
        print(f"\n🔧 APPLYING FIXES")
        print("-" * 30)
        fixed_count = self.apply_url_fixes(validated_fixes, apply_changes)
        
        # Step 4: Remove unfixable URLs
        print(f"\n🗑️ REMOVING UNFIXABLE URLS")
        print("-" * 30)
        removed_count = self.remove_bad_urls(analysis['bad_urls'], apply_changes)
        
        # Step 5: Final results
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_urls': analysis['total_urls'],
            'good_urls': len(analysis['good_urls']),
            'bad_urls': len(analysis['bad_urls']),
            'fixable_urls': len(analysis['fixable_urls']),
            'urls_fixed': fixed_count,
            'urls_removed': removed_count,
            'status': 'completed',
            'simulation_mode': not apply_changes
        }
        
        print(f"\n✅ URL FIX COMPLETED")
        print("=" * 50)
        print(f"📊 Results:")
        print(f"   Total URLs processed: {results['total_urls']}")
        print(f"   Good URLs (no changes): {results['good_urls']}")
        print(f"   Bad URLs found: {results['bad_urls']}")
        print(f"   URLs fixed: {results['urls_fixed']}")
        print(f"   URLs removed: {results['urls_removed']}")
        print(f"   Mode: {'SIMULATION' if not apply_changes else 'APPLIED CHANGES'}")
        
        # Save report
        report_file = f"linkedin_url_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Report saved to: {report_file}")
        
        return results

def main():
    """Run LinkedIn URL fixer"""
    print("🔧 LinkedIn URL Number Fixer")
    print("Removes numbers from URLs that cause 404 errors")
    print("")
    
    try:
        fixer = LinkedInURLFixer()
        
        # First run in simulation mode
        print("📋 STEP 1: SIMULATION MODE")
        results = fixer.comprehensive_url_fix(apply_changes=False)
        
        if results['bad_urls'] > 0:
            print(f"\n🚨 FOUND {results['bad_urls']} BAD LINKEDIN URLS!")
            print("These URLs have numbers and likely give 404 errors")
            print("\n⚠️ To actually fix these URLs, run:")
            print("python3 fix_linkedin_url_numbers.py --fix")
        else:
            print("✅ All LinkedIn URLs look good - no fixes needed")
        
        return 0
        
    except Exception as e:
        print(f"❌ URL fix failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    
    # Check for fix flag
    apply_fixes = '--fix' in sys.argv
    
    if apply_fixes:
        print("🔧 FIX MODE - WILL ACTUALLY MODIFY URLs")
        fixer = LinkedInURLFixer()
        results = fixer.comprehensive_url_fix(apply_changes=True)
        
        print(f"\n🎯 SUMMARY:")
        print(f"✅ Fixed {results['urls_fixed']} LinkedIn URLs")
        print(f"🗑️ Removed {results['urls_removed']} unfixable URLs")
        print(f"🎉 LinkedIn URLs should now work without 404 errors!")
    else:
        main()
