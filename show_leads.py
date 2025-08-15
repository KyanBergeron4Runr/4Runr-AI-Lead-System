#!/usr/bin/env python3
"""Show all leads in the database."""

import sqlite3

# Connect to database
conn = sqlite3.connect('data/unified_leads.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute('SELECT * FROM leads ORDER BY id')
leads = cursor.fetchall()

print(f'📊 Found {len(leads)} leads in database:')
print('='*80)

for i, lead in enumerate(leads, 1):
    print(f'Lead {i} (ID: {lead["id"]}):')
    print(f'  📧 Email: {lead["email"]}')
    print(f'  👤 Name: {lead["full_name"]}')
    print(f'  🏢 Company: {lead["company"]}')
    print(f'  💼 Job Title: {lead["job_title"] or "N/A"}')
    print(f'  🌐 Website: {lead["company_website"] or "N/A"}')
    print(f'  📝 Business Type: {lead["business_type"] or "N/A"}')
    ai_msg_len = len(lead["ai_message"] or "")
    print(f'  🤖 AI Message: {"✅ Yes" if lead["ai_message"] else "❌ No"} ({ai_msg_len} chars)')
    print(f'  📅 Created: {lead["created_at"] or "N/A"}')
    print(f'  🔗 LinkedIn: {lead["linkedin_url"] or "N/A"}')
    print(f'  ✅ Ready: {"Yes" if lead["ready_for_outreach"] else "No"}')
    if i < len(leads):
        print('-'*50)

conn.close()

print(f'\n🎯 To sync to Airtable, please provide:')
print(f'  - AIRTABLE_API_KEY')
print(f'  - AIRTABLE_BASE_ID') 
print(f'  - AIRTABLE_TABLE_NAME')
