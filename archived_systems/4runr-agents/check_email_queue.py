#!/usr/bin/env python3
"""
Check Email Queue Status

This script checks the current status of the email queue to understand
why messages aren't being delivered.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def check_queue_status():
    """Check the current queue status"""
    print("🔍 Checking Email Queue Status")
    print("=" * 50)
    
    # Find the queue database
    outreach_dir = Path(__file__).parent.parent / "4runr-outreach-system"
    queue_db = outreach_dir / "campaign_system" / "campaigns.db"
    
    if not queue_db.exists():
        print(f"❌ Queue database not found: {queue_db}")
        return
        
    print(f"📁 Queue database: {queue_db}")
    
    try:
        conn = sqlite3.connect(str(queue_db))
        cursor = conn.cursor()
        
        # Check queue table structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables found: {[table[0] for table in tables]}")
        
        # Check message_queue contents (this is the correct table name)
        cursor.execute("SELECT * FROM message_queue ORDER BY created_at DESC LIMIT 10;")
        rows = cursor.fetchall()
        
        if not rows:
            print("📭 Message queue is empty")
        else:
            # Get column names
            cursor.execute("PRAGMA table_info(message_queue);")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"📋 Message Queue Columns: {columns}")
            
            print(f"\n📬 Recent Queue Entries (Last 10):")
            print("-" * 80)
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                print(f"Queue ID: {row_dict.get('queue_id', 'N/A')}")
                print(f"Status: {row_dict.get('status', 'N/A')}")
                print(f"Campaign ID: {row_dict.get('campaign_id', 'N/A')}")
                print(f"Message #: {row_dict.get('message_number', 'N/A')}")
                print(f"Created: {row_dict.get('created_at', 'N/A')}")
                print(f"Scheduled: {row_dict.get('scheduled_for', 'N/A')}")
                print("-" * 40)
                
        # Check status counts
        cursor.execute("SELECT status, COUNT(*) FROM message_queue GROUP BY status;")
        status_counts = cursor.fetchall()
        
        print(f"\n📊 Message Queue Status Summary:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
            
        # Check campaigns table
        cursor.execute("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 5;")
        campaign_rows = cursor.fetchall()
        
        if campaign_rows:
            cursor.execute("PRAGMA table_info(campaigns);")
            campaign_columns = [col[1] for col in cursor.fetchall()]
            
            print(f"\n📋 Recent Campaigns:")
            print("-" * 60)
            for row in campaign_rows:
                row_dict = dict(zip(campaign_columns, row))
                print(f"Campaign ID: {row_dict.get('campaign_id', 'N/A')}")
                print(f"Lead ID: {row_dict.get('lead_id', 'N/A')}")
                print(f"Status: {row_dict.get('campaign_status', 'N/A')}")
                print(f"Email: {row_dict.get('lead_email', 'N/A')}")
                print(f"Created: {row_dict.get('created_at', 'N/A')}")
                print("-" * 30)
        
        # Check recent test messages by looking for our test queue IDs
        test_queue_ids = ['queue_90c9fc', 'queue_c117b8', 'queue_cebb2c']
        for queue_id_prefix in test_queue_ids:
            cursor.execute("""
                SELECT * FROM message_queue 
                WHERE queue_id LIKE ? 
                ORDER BY created_at DESC 
                LIMIT 2;
            """, (f"{queue_id_prefix}%",))
            test_messages = cursor.fetchall()
        
            if test_messages:
                print(f"\n🧪 Test Messages for {queue_id_prefix}:")
                print("-" * 50)
                for row in test_messages:
                    cursor.execute("PRAGMA table_info(message_queue);")
                    columns = [col[1] for col in cursor.fetchall()]
                    row_dict = dict(zip(columns, row))
                    print(f"Queue ID: {row_dict.get('queue_id', 'N/A')}")
                    print(f"Status: {row_dict.get('status', 'N/A')}")
                    print(f"Campaign: {row_dict.get('campaign_id', 'N/A')}")
                    print(f"Scheduled: {row_dict.get('scheduled_for', 'N/A')}")
                    print("-" * 25)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking queue: {str(e)}")

if __name__ == "__main__":
    check_queue_status()