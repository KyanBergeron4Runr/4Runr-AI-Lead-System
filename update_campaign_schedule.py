#!/usr/bin/env python3
"""Update campaign schedule to have messages ready to send"""

import sqlite3
from datetime import datetime

def main():
    conn = sqlite3.connect('4runr-outreach-system/campaign_system/campaigns.db')
    
    # Update some proof messages to be ready now
    conn.execute("""
        UPDATE campaign_messages 
        SET scheduled_date = ? 
        WHERE rowid IN (
            SELECT rowid FROM campaign_messages 
            WHERE status = 'scheduled' 
            AND message_type = 'proof'
            LIMIT 2
        )
    """, (datetime.now().isoformat(),))
    
    conn.commit()
    
    # Check what's ready now
    cursor = conn.execute("""
        SELECT message_type, scheduled_date, status 
        FROM campaign_messages 
        WHERE status = 'scheduled' 
        AND datetime(scheduled_date) <= datetime('now')
        ORDER BY scheduled_date
    """)
    
    ready_messages = cursor.fetchall()
    print(f"✅ Updated campaign schedule")
    print(f"📧 Messages ready to send now: {len(ready_messages)}")
    
    for msg in ready_messages:
        print(f"  {msg[0]} - {msg[1]} ({msg[2]})")
    
    conn.close()

if __name__ == "__main__":
    main()