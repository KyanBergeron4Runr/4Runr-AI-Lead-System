#!/usr/bin/env python3
"""
Check Real Data in Databases
============================
Check what real data we actually have and prove real performance
"""

import sqlite3
import os
from datetime import datetime

def check_real_data():
    """Check for real data in databases"""
    print("🔍 CHECKING REAL DATA IN DATABASES")
    print("="*50)
    
    # Check for existing databases
    db_paths = [
        'data/unified_leads.db', 
        '4runr-outreach-system/data/unified_leads.db', 
        '4runr-lead-scraper/data/unified_leads.db'
    ]
    
    total_real_leads = 0
    real_linkedin_leads = 0
    real_emails = 0
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n📊 Found database: {db_path}")
            conn = sqlite3.connect(db_path)
            
            # Check tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Tables: {[t[0] for t in tables]}")
            
            # Check leads if exists
            try:
                cursor = conn.execute('SELECT COUNT(*) FROM leads')
                count = cursor.fetchone()[0]
                print(f"   Total leads: {count}")
                total_real_leads += count
                
                if count > 0:
                    # Check for real LinkedIn URLs
                    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE linkedin_url LIKE '%linkedin.com/in/%'")
                    linkedin_count = cursor.fetchone()[0]
                    print(f"   Real LinkedIn URLs: {linkedin_count}")
                    real_linkedin_leads += linkedin_count
                    
                    # Check for real emails
                    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
                    email_count = cursor.fetchone()[0]
                    print(f"   Has emails: {email_count}")
                    real_emails += email_count
                    
                    # Show some real data
                    cursor = conn.execute('''
                        SELECT full_name, company, email, source, linkedin_url, date_scraped 
                        FROM leads 
                        WHERE linkedin_url LIKE '%linkedin.com/in/%' 
                        LIMIT 5
                    ''')
                    leads = cursor.fetchall()
                    
                    if leads:
                        print("   REAL LEADS FOUND:")
                        for lead in leads:
                            name, company, email, source, linkedin, date_scraped = lead
                            print(f"     ✅ {name} - {company}")
                            print(f"        LinkedIn: {linkedin}")
                            print(f"        Email: {email or 'None'}")
                            print(f"        Source: {source}")
                            print(f"        Date: {date_scraped}")
                            print()
                    
                    # Check for SerpAPI real data
                    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE source LIKE '%SerpAPI%'")
                    serpapi_count = cursor.fetchone()[0]
                    print(f"   SerpAPI sourced: {serpapi_count}")
                    
                    # Check for recent data (last 7 days)
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM leads 
                        WHERE date_scraped >= date('now', '-7 days')
                    """)
                    recent_count = cursor.fetchone()[0]
                    print(f"   Recent (7 days): {recent_count}")
                    
            except Exception as e:
                print(f"   ❌ Error checking leads: {e}")
            
            conn.close()
        else:
            print(f"\n❌ Database not found: {db_path}")
    
    print("\n" + "="*50)
    print("📊 REAL DATA SUMMARY:")
    print(f"   Total leads across all DBs: {total_real_leads}")
    print(f"   Real LinkedIn profiles: {real_linkedin_leads}")
    print(f"   Leads with emails: {real_emails}")
    
    if real_linkedin_leads > 0:
        print("✅ WE HAVE REAL DATA!")
        print("🎯 Can perform real performance analysis!")
        return True
    else:
        print("❌ NO REAL DATA FOUND")
        print("⚠️ Need to run real scraper first")
        return False

def analyze_real_performance():
    """Analyze real performance of our existing data"""
    print("\n🔬 ANALYZING REAL PERFORMANCE")
    print("="*40)
    
    # Find the database with the most real data
    best_db = None
    max_real_leads = 0
    
    db_paths = [
        'data/unified_leads.db', 
        '4runr-outreach-system/data/unified_leads.db', 
        '4runr-lead-scraper/data/unified_leads.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE linkedin_url LIKE '%linkedin.com/in/%'")
                count = cursor.fetchone()[0]
                if count > max_real_leads:
                    max_real_leads = count
                    best_db = db_path
            except:
                pass
            conn.close()
    
    if not best_db or max_real_leads == 0:
        print("❌ No real data to analyze")
        return {}
    
    print(f"📊 Analyzing {best_db} with {max_real_leads} real leads")
    
    conn = sqlite3.connect(best_db)
    
    # Real performance metrics
    metrics = {}
    
    # 1. LinkedIn URL validation rate
    cursor = conn.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE linkedin_url LIKE '%linkedin.com/in/%'")
    valid_linkedin = cursor.fetchone()[0]
    
    metrics['linkedin_validation_rate'] = (valid_linkedin / total * 100) if total > 0 else 0
    
    # 2. Email discovery rate
    cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
    has_email = cursor.fetchone()[0]
    
    metrics['email_discovery_rate'] = (has_email / total * 100) if total > 0 else 0
    
    # 3. Data completeness
    cursor = conn.execute("""
        SELECT COUNT(*) FROM leads 
        WHERE full_name IS NOT NULL 
        AND company IS NOT NULL 
        AND linkedin_url LIKE '%linkedin.com/in/%'
    """)
    complete_data = cursor.fetchone()[0]
    
    metrics['data_completeness_rate'] = (complete_data / total * 100) if total > 0 else 0
    
    # 4. Source analysis
    cursor = conn.execute("SELECT source, COUNT(*) FROM leads GROUP BY source")
    sources = cursor.fetchall()
    metrics['sources'] = dict(sources)
    
    # 5. Quality analysis
    cursor = conn.execute("SELECT lead_quality, COUNT(*) FROM leads WHERE lead_quality IS NOT NULL GROUP BY lead_quality")
    quality_dist = cursor.fetchall()
    metrics['quality_distribution'] = dict(quality_dist)
    
    # 6. Recent activity
    cursor = conn.execute("""
        SELECT COUNT(*) FROM leads 
        WHERE date_scraped >= date('now', '-7 days')
    """)
    recent = cursor.fetchone()[0]
    metrics['recent_activity'] = recent
    
    conn.close()
    
    # Display real performance
    print("\n🎯 REAL PERFORMANCE METRICS:")
    print(f"   LinkedIn Validation Rate: {metrics['linkedin_validation_rate']:.1f}%")
    print(f"   Email Discovery Rate: {metrics['email_discovery_rate']:.1f}%")
    print(f"   Data Completeness Rate: {metrics['data_completeness_rate']:.1f}%")
    print(f"   Recent Activity (7 days): {metrics['recent_activity']} leads")
    
    print(f"\n📊 DATA SOURCES:")
    for source, count in metrics['sources'].items():
        print(f"   {source}: {count} leads")
    
    if metrics['quality_distribution']:
        print(f"\n⭐ QUALITY DISTRIBUTION:")
        for quality, count in metrics['quality_distribution'].items():
            print(f"   {quality}: {count} leads")
    
    # Performance grade
    avg_performance = (
        metrics['linkedin_validation_rate'] + 
        metrics['email_discovery_rate'] + 
        metrics['data_completeness_rate']
    ) / 3
    
    print(f"\n🏆 OVERALL REAL PERFORMANCE: {avg_performance:.1f}%")
    
    if avg_performance >= 80:
        grade = "A"
        verdict = "✅ EXCELLENT real-world performance!"
    elif avg_performance >= 70:
        grade = "B"
        verdict = "🥇 GOOD real-world performance!"
    elif avg_performance >= 60:
        grade = "C"
        verdict = "🥉 DECENT real-world performance"
    else:
        grade = "F"
        verdict = "❌ Needs improvement"
    
    print(f"📝 GRADE: {grade}")
    print(f"🎯 VERDICT: {verdict}")
    
    return metrics

if __name__ == "__main__":
    has_real_data = check_real_data()
    
    if has_real_data:
        analyze_real_performance()
    else:
        print("\n💡 NEXT STEPS:")
        print("1. Set SERPAPI_KEY environment variable")
        print("2. Run the real scraper to get actual data")
        print("3. Then we can prove real performance!")
