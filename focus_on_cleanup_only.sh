#!/bin/bash
# FOCUS ON CLEANUP ONLY - Remove all duplicates from database and Airtable

echo "🧹 FOCUS: DATABASE AND AIRTABLE CLEANUP ONLY"
echo "============================================="
echo "This script focuses ONLY on removing duplicates"
echo "No enrichment - just pure cleanup"
echo ""

cd production_clean_system
source venv/bin/activate

# Step 1: Check current duplicate situation
echo "🔍 Step 1: Analyzing current duplicate situation..."
python3 -c "
import sqlite3
from real_time_duplicate_prevention import RealTimeDuplicatePrevention
from intelligent_lead_cleaner import IntelligentLeadCleaner

print('📊 DATABASE DUPLICATE ANALYSIS:')
print('=' * 50)

# Check database duplicates
conn = sqlite3.connect('data/unified_leads.db')

# Basic stats
cursor = conn.execute('SELECT COUNT(*) FROM leads')
total = cursor.fetchone()[0]
print(f'Total leads in database: {total}')

# Check for obvious duplicates (same name + same company)
cursor = conn.execute('''
    SELECT full_name, company, COUNT(*) as count 
    FROM leads 
    WHERE full_name IS NOT NULL AND full_name != \"\"
    GROUP BY LOWER(full_name), LOWER(COALESCE(company, \"\"))
    HAVING COUNT(*) > 1
    ORDER BY count DESC
''')
name_company_dups = cursor.fetchall()
print(f'Name+Company duplicates: {len(name_company_dups)}')
for dup in name_company_dups[:5]:  # Show top 5
    print(f'  - {dup[0]} at {dup[1]}: {dup[2]} copies')

# Check for LinkedIn URL duplicates
cursor = conn.execute('''
    SELECT linkedin_url, COUNT(*) as count 
    FROM leads 
    WHERE linkedin_url IS NOT NULL AND linkedin_url != \"\"
    GROUP BY linkedin_url
    HAVING COUNT(*) > 1
    ORDER BY count DESC
''')
linkedin_dups = cursor.fetchall()
print(f'LinkedIn URL duplicates: {len(linkedin_dups)}')
for dup in linkedin_dups[:5]:  # Show top 5
    print(f'  - {dup[0]}: {dup[1]} copies')

# Check for email duplicates
cursor = conn.execute('''
    SELECT email, COUNT(*) as count 
    FROM leads 
    WHERE email IS NOT NULL AND email != \"\"
    GROUP BY email
    HAVING COUNT(*) > 1
    ORDER BY count DESC
''')
email_dups = cursor.fetchall()
print(f'Email duplicates: {len(email_dups)}')
for dup in email_dups[:5]:  # Show top 5
    print(f'  - {dup[0]}: {dup[1]} copies')

conn.close()

print('')
print('🎯 DUPLICATE SUMMARY:')
total_duplicate_groups = len(name_company_dups) + len(linkedin_dups) + len(email_dups)
print(f'Total duplicate groups found: {total_duplicate_groups}')
"

# Step 2: Run comprehensive database cleanup
echo ""
echo "🧹 Step 2: Running comprehensive database cleanup..."
python3 -c "
from intelligent_lead_cleaner import IntelligentLeadCleaner
import sqlite3
import json
from datetime import datetime

print('🧹 Starting comprehensive database cleanup...')

cleaner = IntelligentLeadCleaner('data/unified_leads.db')

# Load all leads
leads = cleaner.load_all_leads()
print(f'📊 Loaded {len(leads)} leads')

# Find all types of duplicates
exact_dups = cleaner.detect_exact_duplicates(leads)
fuzzy_dups = cleaner.detect_fuzzy_duplicates(leads)

print(f'🎯 Found {len(exact_dups)} exact duplicates')
print(f'🎯 Found {len(fuzzy_dups)} fuzzy duplicates')

total_duplicates = len(exact_dups) + len(fuzzy_dups)

if total_duplicates > 0:
    print(f'🔧 Resolving {total_duplicates} duplicates...')
    
    # Resolve duplicates
    resolved_leads = cleaner.resolve_duplicates(exact_dups + fuzzy_dups, leads)
    
    # Apply to database
    cleaner.apply_duplicate_resolution(resolved_leads, exact_dups + fuzzy_dups)
    
    print(f'✅ Resolved {total_duplicates} duplicates')
    
    # Save cleanup results
    cleanup_results = {
        'timestamp': datetime.now().isoformat(),
        'total_leads_before': len(leads),
        'exact_duplicates_found': len(exact_dups),
        'fuzzy_duplicates_found': len(fuzzy_dups),
        'total_duplicates_removed': total_duplicates,
        'final_lead_count': len(resolved_leads)
    }
    
    with open('cleanup_results.json', 'w') as f:
        json.dump(cleanup_results, f, indent=2)
    
    print(f'📊 Results saved to cleanup_results.json')
else:
    print('✅ No duplicates found - database is clean!')
"

# Step 3: Check Airtable for duplicates
echo ""
echo "📊 Step 3: Checking Airtable for duplicates..."
python3 -c "
import requests
import os
from collections import defaultdict

api_key = os.getenv('AIRTABLE_API_KEY')
if not api_key:
    print('⚠️ No AIRTABLE_API_KEY - skipping Airtable cleanup')
    exit()

base_id = 'appjz81o6h5Z19Nph'
table_name = 'tblwJZn9Tv6VWjpP'

print('📊 AIRTABLE DUPLICATE ANALYSIS:')
print('=' * 50)

try:
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    all_records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f'❌ Airtable API error: {response.status_code}')
            break
            
        data = response.json()
        records = data.get('records', [])
        all_records.extend(records)
        
        offset = data.get('offset')
        if not offset:
            break
    
    print(f'📊 Total Airtable records: {len(all_records)}')
    
    # Check for duplicates by name
    name_groups = defaultdict(list)
    linkedin_groups = defaultdict(list)
    email_groups = defaultdict(list)
    
    for record in all_records:
        fields = record.get('fields', {})
        
        # Group by full name
        full_name = fields.get('Full Name', '').strip().lower()
        if full_name:
            name_groups[full_name].append(record)
        
        # Group by LinkedIn URL
        linkedin_url = fields.get('LinkedIn URL', '').strip()
        if linkedin_url:
            linkedin_groups[linkedin_url].append(record)
        
        # Group by email
        email = fields.get('Email', '').strip().lower()
        if email:
            email_groups[email].append(record)
    
    # Find duplicate groups
    name_dups = {k: v for k, v in name_groups.items() if len(v) > 1}
    linkedin_dups = {k: v for k, v in linkedin_groups.items() if len(v) > 1}
    email_dups = {k: v for k, v in email_groups.items() if len(v) > 1}
    
    print(f'Name duplicates: {len(name_dups)} groups')
    print(f'LinkedIn duplicates: {len(linkedin_dups)} groups')
    print(f'Email duplicates: {len(email_dups)} groups')
    
    # Show examples
    for i, (name, records) in enumerate(list(name_dups.items())[:3]):
        print(f'  - \"{name}\": {len(records)} copies')
    
    total_airtable_dups = len(name_dups) + len(linkedin_dups) + len(email_dups)
    print(f'🎯 Total Airtable duplicate groups: {total_airtable_dups}')
    
    if total_airtable_dups > 0:
        print('⚠️ AIRTABLE HAS DUPLICATES - CLEANUP NEEDED!')
    else:
        print('✅ Airtable appears clean')
        
except Exception as e:
    print(f'❌ Airtable check failed: {e}')
"

# Step 4: Final verification
echo ""
echo "✅ Step 4: Final verification..."
python3 -c "
import sqlite3

conn = sqlite3.connect('data/unified_leads.db')

cursor = conn.execute('SELECT COUNT(*) FROM leads')
final_count = cursor.fetchone()[0]

print(f'📊 Final database lead count: {final_count}')

# Quick duplicate check
cursor = conn.execute('''
    SELECT COUNT(*) FROM (
        SELECT full_name, linkedin_url, COUNT(*) 
        FROM leads 
        WHERE full_name IS NOT NULL AND linkedin_url IS NOT NULL
        GROUP BY full_name, linkedin_url
        HAVING COUNT(*) > 1
    )
''')
remaining_dups = cursor.fetchone()[0]

print(f'🎯 Remaining obvious duplicates: {remaining_dups}')

if remaining_dups == 0:
    print('✅ DATABASE IS CLEAN!')
else:
    print('⚠️ Still has duplicates - needs more cleanup')

conn.close()
"

echo ""
echo "🏆 CLEANUP FOCUS COMPLETED!"
echo "=========================="
echo "✅ Database analyzed and cleaned"
echo "✅ Airtable checked for duplicates"
echo "✅ Results documented"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. Review cleanup results"
echo "2. Clean Airtable duplicates if found"
echo "3. Verify zero duplicates in both systems"
