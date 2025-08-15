#!/usr/bin/env python3
"""Show sample enhanced AI message."""

import sqlite3

conn = sqlite3.connect('data/unified_leads.db')
cursor = conn.execute('SELECT full_name, company, business_type, ai_message FROM leads WHERE full_name = "Pascal Jarry"')
lead = cursor.fetchone()

if lead:
    print(f'Enhanced AI Message for {lead[0]} at {lead[1]} ({lead[2]}):')
    print('='*60)
    print(lead[3])
else:
    print("Lead not found")

conn.close()
