#!/usr/bin/env python3
"""
REAL UNKNOWN LEADS TEST - THE HONEST TRUTH
==========================================
Testing our system with REAL unknown small business owners from our database.
No famous people, no easy targets - just the actual leads we're trying to enrich.

This is the REAL test that matters.
"""

import sqlite3
import json
from datetime import datetime
from pattern_based_email_engine import PatternBasedEmailEngine
import requests
import socket
import dns.resolver
import time

class RealUnknownLeadsTest:
    """Test our system with actual unknown leads from our database"""
    
    def __init__(self):
        self.our_engine = PatternBasedEmailEngine()
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'test_type': 'Real Unknown Small Business Leads',
            'leads_tested': [],
            'success_metrics': {},
            'honest_assessment': {}
        }
    
    def get_real_unknown_leads(self):
        """Get actual unknown leads from our database"""
        try:
            conn = sqlite3.connect('data/unified_leads.db')
            conn.row_factory = sqlite3.Row
            
            # Get leads that are NOT famous people - real small business owners
            cursor = conn.execute("""
                SELECT full_name, company, job_title, email, linkedin_url, 
                       business_type, website, created_at
                FROM leads 
                WHERE full_name IS NOT NULL 
                AND company IS NOT NULL
                AND full_name != ''
                AND company != ''
                AND company NOT LIKE '%Apple%'
                AND company NOT LIKE '%Microsoft%'
                AND company NOT LIKE '%Google%'
                AND company NOT LIKE '%Amazon%'
                AND company NOT LIKE '%Facebook%'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            leads = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            print(f"📊 Found {len(leads)} real unknown leads in database")
            return leads
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return []
    
    def validate_small_business_domain(self, company_name):
        """Try to find and validate the domain for a small business"""
        if not company_name:
            return None
        
        # Clean company name and try common domain patterns
        clean_name = company_name.lower()
        clean_name = clean_name.replace('inc', '').replace('llc', '').replace('corp', '')
        clean_name = clean_name.replace(' ', '').replace(',', '').strip()
        
        potential_domains = [
            f"{clean_name}.com",
            f"{clean_name}.co", 
            f"{clean_name}.net",
            f"{clean_name}.org",
            f"{clean_name}.io"
        ]
        
        for domain in potential_domains:
            try:
                # Check if domain exists
                socket.gethostbyname(domain)
                
                # Check MX records
                try:
                    mx_records = dns.resolver.resolve(domain, 'MX')
                    if len(mx_records) > 0:
                        return {
                            'domain': domain,
                            'exists': True,
                            'has_mx': True,
                            'mx_count': len(mx_records)
                        }
                except:
                    return {
                        'domain': domain,
                        'exists': True,
                        'has_mx': False,
                        'mx_count': 0
                    }
            except:
                continue
        
        return None
    
    def test_with_real_unknown_lead(self, lead):
        """Test our engine with one real unknown lead"""
        print(f"\n🔍 TESTING: {lead['full_name']} at {lead['company']}")
        if lead.get('job_title'):
            print(f"   Title: {lead['job_title']}")
        if lead.get('known_email'):
            print(f"   Known email: {lead['email']}")
        print("-" * 60)
        
        # Try to find the company domain
        domain_info = self.validate_small_business_domain(lead['company'])
        
        if not domain_info:
            print("❌ Could not find valid domain for this company")
            return {
                'lead': lead,
                'domain_found': False,
                'emails_found': 0,
                'success': False,
                'reason': 'No valid domain found'
            }
        
        print(f"✅ Found domain: {domain_info['domain']}")
        print(f"   Domain exists: {domain_info['exists']}")
        print(f"   Has MX records: {domain_info['has_mx']} ({domain_info['mx_count']} records)")
        
        # Test our email discovery
        start_time = time.time()
        try:
            email_results = self.our_engine.discover_emails(lead)
            processing_time = (time.time() - start_time) * 1000
            
            print(f"\n📧 EMAIL DISCOVERY RESULTS:")
            print(f"   Emails found: {len(email_results)}")
            print(f"   Processing time: {processing_time:.2f}ms")
            
            if email_results:
                print(f"   Top candidates:")
                for i, result in enumerate(email_results[:10], 1):
                    print(f"   {i}. {result.email} ({result.confidence.value})")
                    
                    # Check if we found the known email
                    if lead.get('email') and result.email.lower() == lead['email'].lower():
                        print(f"      🎯 EXACT MATCH! Found the known email!")
                
                # Confidence breakdown
                confidence_counts = {}
                for result in email_results:
                    conf = result.confidence.value
                    confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
                
                print(f"   Confidence breakdown: {confidence_counts}")
                
                return {
                    'lead': lead,
                    'domain_found': True,
                    'domain_info': domain_info,
                    'emails_found': len(email_results),
                    'processing_time_ms': processing_time,
                    'confidence_breakdown': confidence_counts,
                    'top_emails': [r.email for r in email_results[:10]],
                    'found_known_email': any(r.email.lower() == lead.get('email', '').lower() for r in email_results),
                    'success': len(email_results) > 0
                }
            else:
                print("   ❌ No valid email candidates found")
                return {
                    'lead': lead,
                    'domain_found': True,
                    'domain_info': domain_info,
                    'emails_found': 0,
                    'success': False,
                    'reason': 'No valid emails generated'
                }
                
        except Exception as e:
            print(f"   ❌ Engine failed: {e}")
            return {
                'lead': lead,
                'domain_found': True,
                'domain_info': domain_info,
                'emails_found': 0,
                'success': False,
                'reason': f'Engine error: {e}'
            }
    
    def run_real_test(self):
        """Run the test with real unknown leads"""
        print("🔍 REAL UNKNOWN LEADS TEST")
        print("=" * 60)
        print("Testing with ACTUAL small business owners from our database")
        print("NOT famous people - real unknown prospects we're trying to enrich")
        print("=" * 60)
        
        # Get real unknown leads
        unknown_leads = self.get_real_unknown_leads()
        
        if not unknown_leads:
            print("❌ No unknown leads found in database")
            return
        
        print(f"\n📋 TESTING {len(unknown_leads)} REAL UNKNOWN LEADS:")
        for i, lead in enumerate(unknown_leads, 1):
            print(f"{i}. {lead['full_name']} at {lead['company']}")
        
        # Test each lead
        all_results = []
        successful_tests = 0
        total_emails_found = 0
        domains_found = 0
        known_emails_matched = 0
        
        for lead in unknown_leads:
            result = self.test_with_real_unknown_lead(lead)
            all_results.append(result)
            
            if result['success']:
                successful_tests += 1
                total_emails_found += result['emails_found']
            
            if result['domain_found']:
                domains_found += 1
            
            if result.get('found_known_email'):
                known_emails_matched += 1
        
        # Calculate metrics
        self.results['leads_tested'] = all_results
        self.results['success_metrics'] = {
            'total_leads_tested': len(unknown_leads),
            'successful_enrichments': successful_tests,
            'success_rate_percentage': round((successful_tests / len(unknown_leads)) * 100, 1),
            'domains_found': domains_found,
            'domain_discovery_rate': round((domains_found / len(unknown_leads)) * 100, 1),
            'total_emails_found': total_emails_found,
            'average_emails_per_lead': round(total_emails_found / len(unknown_leads), 1),
            'known_emails_matched': known_emails_matched,
            'known_email_match_rate': round((known_emails_matched / len(unknown_leads)) * 100, 1)
        }
        
        # Print honest results
        self.print_honest_results()
        
        # Save results
        self.save_results()
    
    def print_honest_results(self):
        """Print honest assessment of results"""
        print("\n" + "🎯" * 60)
        print("🔍 HONEST RESULTS - REAL UNKNOWN LEADS TEST")
        print("🎯" * 60)
        
        metrics = self.results['success_metrics']
        
        print(f"\n📊 SUCCESS METRICS:")
        print(f"   Leads tested: {metrics['total_leads_tested']}")
        print(f"   Successful enrichments: {metrics['successful_enrichments']}")
        print(f"   Success rate: {metrics['success_rate_percentage']}%")
        print(f"   Domains found: {metrics['domains_found']}/{metrics['total_leads_tested']}")
        print(f"   Domain discovery rate: {metrics['domain_discovery_rate']}%")
        print(f"   Total emails found: {metrics['total_emails_found']}")
        print(f"   Average emails per lead: {metrics['average_emails_per_lead']}")
        print(f"   Known emails matched: {metrics['known_emails_matched']}")
        
        print(f"\n🎯 HONEST ASSESSMENT:")
        
        if metrics['success_rate_percentage'] >= 80:
            print("   ✅ EXCELLENT: System works well on unknown leads")
        elif metrics['success_rate_percentage'] >= 60:
            print("   ✅ GOOD: System works reasonably well on unknown leads")
        elif metrics['success_rate_percentage'] >= 40:
            print("   ⚠️ MODERATE: System works but has limitations")
        else:
            print("   ❌ POOR: System struggles with unknown leads")
        
        print(f"\n🔍 KEY CHALLENGES WITH UNKNOWN LEADS:")
        print("   1. Domain discovery is harder (small businesses have varied domains)")
        print("   2. Less public information available") 
        print("   3. Company names may not match domains exactly")
        print("   4. Some small businesses may not have professional email domains")
        
        print(f"\n🚀 WHAT THIS PROVES:")
        if metrics['success_rate_percentage'] >= 60:
            print("   ✅ Our system works on REAL unknown prospects")
            print("   ✅ Pattern generation is effective even without fame")
            print("   ✅ Domain discovery works for small businesses")
        else:
            print("   ⚠️ System needs improvement for unknown leads")
            print("   ⚠️ Domain discovery is the main bottleneck")
            print("   ⚠️ Need additional data sources beyond pattern matching")
        
        print("\n" + "🎯" * 60)
    
    def save_results(self):
        """Save results for documentation"""
        filename = f"real_unknown_leads_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
        return filename

def main():
    """Run the real unknown leads test"""
    tester = RealUnknownLeadsTest()
    tester.run_real_test()
    
    print("\n🎯 THE REAL QUESTION:")
    print("=" * 50)
    print("This test shows how our system performs on ACTUAL unknown prospects.")
    print("Not famous people, not easy targets - real small business leads.")
    print("This is the honest truth about our system's capabilities.")

if __name__ == "__main__":
    main()
