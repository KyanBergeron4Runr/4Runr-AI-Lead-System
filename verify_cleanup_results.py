#!/usr/bin/env python3
"""
Verify Cleanup Results - Check what remains after fake data removal
==================================================================
"""

import sqlite3
import json
from datetime import datetime

def verify_cleanup_results(db_path='data/unified_leads.db'):
    """Verify the cleanup results and show what's left"""
    print("✅ VERIFYING CLEANUP RESULTS")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Total remaining records
    cursor = conn.execute('SELECT COUNT(*) FROM leads')
    total_remaining = cursor.fetchone()[0]
    
    # Records with LinkedIn URLs
    cursor = conn.execute('''
        SELECT COUNT(*) FROM leads 
        WHERE linkedin_url IS NOT NULL 
        AND linkedin_url != ''
    ''')
    with_linkedin = cursor.fetchone()[0]
    
    # Check for fake patterns manually (without REGEXP)
    cursor = conn.execute('''
        SELECT COUNT(*) FROM leads 
        WHERE linkedin_url LIKE '%-1749'
        OR linkedin_url LIKE '%-0953'
        OR linkedin_url LIKE '%-1749%'
        OR linkedin_url LIKE '%-0953%'
    ''')
    fake_patterns = cursor.fetchone()[0]
    
    # Check for AutoGen sources
    cursor = conn.execute('''
        SELECT COUNT(*) FROM leads 
        WHERE source LIKE 'AutoGen%'
    ''')
    autogen_records = cursor.fetchone()[0]
    
    # Get sample of remaining records
    cursor = conn.execute('''
        SELECT full_name, linkedin_url, email, company, source, created_at
        FROM leads 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    sample_records = [dict(row) for row in cursor.fetchall()]
    
    # Get source breakdown
    cursor = conn.execute('''
        SELECT source, COUNT(*) as count
        FROM leads 
        GROUP BY source
        ORDER BY count DESC
    ''')
    source_breakdown = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    print(f"📊 CLEANUP VERIFICATION RESULTS:")
    print(f"   Total remaining records: {total_remaining}")
    print(f"   Records with LinkedIn URLs: {with_linkedin}")
    print(f"   Fake pattern URLs remaining: {fake_patterns}")
    print(f"   AutoGen source records: {autogen_records}")
    
    print(f"\n📋 SOURCE BREAKDOWN:")
    for source in source_breakdown:
        print(f"   {source['source']}: {source['count']} records")
    
    print(f"\n📝 SAMPLE REMAINING RECORDS:")
    for i, record in enumerate(sample_records, 1):
        name = record['full_name'] or 'No name'
        linkedin = record['linkedin_url'] or 'No LinkedIn'
        email = record['email'] or 'No email'
        source = record['source'] or 'No source'
        print(f"   {i}. {name}")
        print(f"      LinkedIn: {linkedin}")
        print(f"      Email: {email}")
        print(f"      Source: {source}")
        print()
    
    # Assessment
    print(f"🎯 CLEANUP ASSESSMENT:")
    if fake_patterns == 0:
        print("   ✅ SUCCESS: No fake LinkedIn patterns remaining")
    else:
        print(f"   ⚠️ WARNING: {fake_patterns} fake patterns still found")
    
    if autogen_records == 0:
        print("   ✅ SUCCESS: No AutoGen records remaining")
    else:
        print(f"   ⚠️ WARNING: {autogen_records} AutoGen records still found")
    
    if total_remaining > 0:
        real_data_rate = (total_remaining - fake_patterns - autogen_records) / total_remaining * 100
        print(f"   📊 Real data rate: {real_data_rate:.1f}%")
    
    # Save verification report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_remaining': total_remaining,
        'with_linkedin': with_linkedin,
        'fake_patterns': fake_patterns,
        'autogen_records': autogen_records,
        'source_breakdown': source_breakdown,
        'sample_records': sample_records
    }
    
    report_file = f"cleanup_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Verification report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    verify_cleanup_results()
