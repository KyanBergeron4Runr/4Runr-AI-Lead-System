#!/usr/bin/env python3
"""Remove the last 2 test data entries."""

import sqlite3

# Find and remove the last 2 test entries
conn = sqlite3.connect('data/unified_leads.db')
cursor = conn.execute("""
SELECT id, full_name, email, company FROM leads 
WHERE LOWER(email) LIKE '%example%' 
   OR LOWER(email) LIKE '%test%'
   OR LOWER(full_name) LIKE '%test%'
   OR LOWER(company) LIKE '%test%'
""")
test_leads = cursor.fetchall()
print(f'Found {len(test_leads)} test entries:')
for lead in test_leads:
    print(f'  ID {lead[0]}: {lead[1]} - {lead[2]} - {lead[3]}')

# Delete them
for lead in test_leads:
    conn.execute('DELETE FROM leads WHERE id = ?', (lead[0],))
    print(f'Deleted lead {lead[0]}')

conn.commit()
conn.close()
print('Test data cleanup complete!')
