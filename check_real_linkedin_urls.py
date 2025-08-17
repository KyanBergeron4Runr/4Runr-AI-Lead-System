#!/usr/bin/env python3
"""
Check Real LinkedIn URLs - Verify if URLs are real or fake
=========================================================
Tests LinkedIn URLs to see if they actually work or are fake/generated.
"""

import sqlite3
import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple

class LinkedInURLChecker:
    def __init__(self, db_path='data/unified_leads.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_all_linkedin_urls(self) -> List[Dict]:
        """Get all LinkedIn URLs from database"""
        print("📊 Loading LinkedIn URLs from database...")
        
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
    
    def test_linkedin_url(self, url: str) -> Tuple[bool, str, int]:
        """Test if a LinkedIn URL is real"""
        try:
            # Clean up the URL
            url = url.strip()
            if not url.startswith('http'):
                url = 'https://' + url
            
            # Make request with timeout
            response = self.session.head(url, timeout=10, allow_redirects=True)
            
            status_code = response.status_code
            
            if status_code == 200:
                return True, "Working", status_code
            elif status_code == 404:
                return False, "Not Found (404)", status_code
            elif status_code == 403:
                return False, "Forbidden (403)", status_code
            elif status_code in [302, 301]:
                return True, "Redirected (probably real)", status_code
            else:
                return False, f"Error ({status_code})", status_code
                
        except requests.exceptions.Timeout:
            return False, "Timeout", 0
        except requests.exceptions.ConnectionError:
            return False, "Connection Error", 0
        except Exception as e:
            return False, f"Error: {str(e)[:50]}", 0
    
    def analyze_url_patterns(self, records: List[Dict]) -> Dict:
        """Analyze patterns in LinkedIn URLs to detect fake ones"""
        print("\n🔍 Analyzing LinkedIn URL patterns...")
        
        patterns = {
            'domains': {},
            'url_structures': {},
            'suspicious_patterns': [],
            'duplicate_urls': {},
            'name_mismatches': []
        }
        
        for record in records:
            url = record['linkedin_url']
            name = record['full_name'] or 'Unknown'
            
            # Extract domain
            if 'linkedin.com' in url:
                if 'ca.linkedin.com' in url:
                    patterns['domains']['ca.linkedin.com'] = patterns['domains'].get('ca.linkedin.com', 0) + 1
                else:
                    patterns['domains']['linkedin.com'] = patterns['domains'].get('linkedin.com', 0) + 1
            
            # Check for suspicious patterns
            if '-1749' in url:
                patterns['suspicious_patterns'].append(f"Contains '-1749': {url}")
            
            if url.count('-') > 3:
                patterns['suspicious_patterns'].append(f"Too many dashes: {url}")
            
            # Check for duplicates
            if url in patterns['duplicate_urls']:
                patterns['duplicate_urls'][url].append(name)
            else:
                patterns['duplicate_urls'][url] = [name]
        
        # Filter to only duplicates
        patterns['duplicate_urls'] = {url: names for url, names in patterns['duplicate_urls'].items() if len(names) > 1}
        
        print(f"📊 Pattern Analysis:")
        print(f"   Domains: {patterns['domains']}")
        print(f"   Suspicious patterns: {len(patterns['suspicious_patterns'])}")
        print(f"   Duplicate URLs: {len(patterns['duplicate_urls'])}")
        
        return patterns
    
    def check_all_urls(self, records: List[Dict], max_test: int = 10) -> Dict:
        """Check a sample of LinkedIn URLs"""
        print(f"\n🧪 Testing up to {max_test} LinkedIn URLs...")
        
        results = {
            'working': [],
            'broken': [],
            'suspicious': [],
            'errors': []
        }
        
        # Test a sample of URLs
        test_records = records[:max_test]
        
        for i, record in enumerate(test_records):
            url = record['linkedin_url']
            name = record['full_name'] or 'Unknown'
            
            print(f"   Testing {i+1}/{len(test_records)}: {name}")
            print(f"   URL: {url}")
            
            is_working, status, code = self.test_linkedin_url(url)
            
            result_info = {
                'name': name,
                'url': url,
                'status': status,
                'code': code,
                'record': record
            }
            
            if is_working:
                results['working'].append(result_info)
                print(f"   ✅ Working: {status}")
            else:
                results['broken'].append(result_info)
                print(f"   ❌ Broken: {status}")
            
            # Check for suspicious patterns
            if '-1749' in url or url.count('-') > 3:
                results['suspicious'].append(result_info)
                print(f"   🚨 Suspicious pattern detected")
            
            # Rate limiting
            time.sleep(2)
        
        return results
    
    def generate_report(self, records: List[Dict], patterns: Dict, test_results: Dict) -> str:
        """Generate a comprehensive report"""
        
        report = f"""
🔍 LINKEDIN URL VERIFICATION REPORT
==================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DATABASE OVERVIEW:
   Total records with LinkedIn URLs: {len(records)}
   Date range: {records[-1]['created_at'] if records else 'N/A'} to {records[0]['created_at'] if records else 'N/A'}

🌐 DOMAIN ANALYSIS:
"""
        for domain, count in patterns['domains'].items():
            report += f"   {domain}: {count} URLs\n"
        
        report += f"""
🚨 SUSPICIOUS PATTERNS DETECTED:
   Total suspicious patterns: {len(patterns['suspicious_patterns'])}
"""
        for pattern in patterns['suspicious_patterns'][:5]:  # Show first 5
            report += f"   - {pattern}\n"
        
        if len(patterns['suspicious_patterns']) > 5:
            report += f"   ... and {len(patterns['suspicious_patterns']) - 5} more\n"
        
        report += f"""
🔄 DUPLICATE URLS:
   Total duplicate URLs: {len(patterns['duplicate_urls'])}
"""
        for url, names in list(patterns['duplicate_urls'].items())[:3]:  # Show first 3
            report += f"   - {url}: {len(names)} copies ({', '.join(names[:2])}{'...' if len(names) > 2 else ''})\n"
        
        report += f"""
🧪 URL TESTING RESULTS:
   Working URLs: {len(test_results['working'])}
   Broken URLs: {len(test_results['broken'])}
   Suspicious URLs: {len(test_results['suspicious'])}
"""
        
        if test_results['working']:
            report += "\n✅ WORKING URLS:\n"
            for result in test_results['working'][:3]:
                report += f"   - {result['name']}: {result['url']} ({result['status']})\n"
        
        if test_results['broken']:
            report += "\n❌ BROKEN URLS:\n"
            for result in test_results['broken'][:3]:
                report += f"   - {result['name']}: {result['url']} ({result['status']})\n"
        
        if test_results['suspicious']:
            report += "\n🚨 SUSPICIOUS URLS:\n"
            for result in test_results['suspicious'][:3]:
                report += f"   - {result['name']}: {result['url']}\n"
        
        # Analysis and recommendations
        working_rate = len(test_results['working']) / max(len(test_results['working']) + len(test_results['broken']), 1) * 100
        
        report += f"""
📈 ANALYSIS:
   Working URL Rate: {working_rate:.1f}%
   Suspicious Pattern Rate: {len(patterns['suspicious_patterns']) / len(records) * 100:.1f}%
   Duplicate Rate: {sum(len(names) - 1 for names in patterns['duplicate_urls'].values()) / len(records) * 100:.1f}%

🎯 RECOMMENDATIONS:
"""
        
        if working_rate < 50:
            report += "   ❌ CRITICAL: Most URLs are broken/fake - need data source review\n"
        elif working_rate < 80:
            report += "   ⚠️ WARNING: High rate of broken URLs - data quality issues\n"
        else:
            report += "   ✅ GOOD: Most URLs appear to be working\n"
        
        if len(patterns['suspicious_patterns']) > len(records) * 0.1:
            report += "   🚨 High rate of suspicious patterns - likely generated/fake data\n"
        
        if len(patterns['duplicate_urls']) > 0:
            report += "   🔄 Duplicate URLs found - need deduplication\n"
        
        return report

def main():
    """Run the LinkedIn URL verification"""
    print("🔍 LINKEDIN URL VERIFICATION STARTING")
    print("=" * 50)
    
    try:
        checker = LinkedInURLChecker()
        
        # Get all LinkedIn URLs
        records = checker.get_all_linkedin_urls()
        
        if not records:
            print("❌ No LinkedIn URLs found in database")
            return 1
        
        # Analyze patterns
        patterns = checker.analyze_url_patterns(records)
        
        # Test URLs (limit to avoid being blocked)
        test_results = checker.check_all_urls(records, max_test=10)
        
        # Generate report
        report = checker.generate_report(records, patterns, test_results)
        
        # Save report
        report_file = f"linkedin_url_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n💾 Report saved to: {report_file}")
        
        # Return status based on findings
        working_rate = len(test_results['working']) / max(len(test_results['working']) + len(test_results['broken']), 1) * 100
        
        if working_rate < 50:
            print("\n🚨 CRITICAL ISSUE: Most LinkedIn URLs are fake/broken!")
            return 2
        elif len(patterns['suspicious_patterns']) > len(records) * 0.2:
            print("\n⚠️ WARNING: High rate of suspicious patterns detected!")
            return 1
        else:
            print("\n✅ LinkedIn URLs appear to be mostly real")
            return 0
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
