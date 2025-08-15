#!/usr/bin/env python3
"""
System Status Report

Generate a comprehensive status report of the lead generation system.
"""

import json
from datetime import datetime
from production_db_manager import db_manager

def generate_status_report():
    """Generate comprehensive status report."""
    
    # Get database stats
    stats = db_manager.get_database_stats()
    
    # Get recent activity
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) as recent_leads 
            FROM leads 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        recent_leads = cursor.fetchone()['recent_leads']
        
        cursor = conn.execute("""
            SELECT COUNT(*) as ready_leads 
            FROM leads 
            WHERE ready_for_outreach = 1
        """)
        ready_leads = cursor.fetchone()['ready_leads']
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_stats': stats,
        'recent_activity': {
            'leads_added_7_days': recent_leads,
            'leads_ready_for_outreach': ready_leads
        },
        'system_status': 'healthy' if stats['total_leads'] > 0 else 'needs_attention'
    }
    
    # Save report
    report_file = f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("📊 SYSTEM STATUS REPORT")
    print("="*40)
    print(f"Total Leads: {stats['total_leads']}")
    print(f"With Emails: {stats['leads_with_email']} ({stats['email_percentage']}%)")
    print(f"Ready for Outreach: {ready_leads}")
    print(f"Recent Activity (7 days): {recent_leads} new leads")
    print(f"System Status: {report['system_status']}")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    generate_status_report()
