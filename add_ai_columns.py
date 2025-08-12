#!/usr/bin/env python3
"""Add AI message columns to the database"""

import sqlite3

def add_ai_columns():
    conn = sqlite3.connect('4runr-lead-scraper/data/leads.db')
    
    try:
        # Add AI message column
        conn.execute('ALTER TABLE leads ADD COLUMN ai_message TEXT')
        print("✅ Added ai_message column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ ai_message column already exists")
        else:
            print(f"❌ Error adding ai_message: {e}")
    
    try:
        # Add engagement status column
        conn.execute('ALTER TABLE leads ADD COLUMN engagement_status TEXT DEFAULT "New"')
        print("✅ Added engagement_status column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ engagement_status column already exists")
        else:
            print(f"❌ Error adding engagement_status: {e}")
    
    try:
        # Add date messaged column
        conn.execute('ALTER TABLE leads ADD COLUMN date_messaged TEXT')
        print("✅ Added date_messaged column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ date_messaged column already exists")
        else:
            print(f"❌ Error adding date_messaged: {e}")
    
    # Update some leads with sample AI messages for testing
    conn.execute("""
        UPDATE leads 
        SET ai_message = 'Hi there! I noticed your company ' || company || ' and wanted to reach out about a potential partnership opportunity.',
            engagement_status = 'Auto-Send'
        WHERE id IN (
            SELECT id FROM leads 
            WHERE ai_message IS NULL 
            AND email IS NOT NULL 
            AND email != ''
            LIMIT 3
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database schema updated successfully")

if __name__ == "__main__":
    add_ai_columns()