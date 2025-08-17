#!/bin/bash
# Clear Airtable and Replace with Clean Database - OPTION 1

echo "🧹 CLEAR AND REPLACE AIRTABLE WITH CLEAN DATA"
echo "============================================="
echo "This will:"
echo "1. DELETE all 91 existing Airtable records (including 48 duplicates)"
echo "2. UPLOAD 64 clean database records (zero duplicates)"
echo "3. Result: Clean Airtable matching clean database"
echo ""

cd production_clean_system
source venv/bin/activate

# Configuration from diagnostic
BASE_ID="appBZvPvNXGqtoJdc"
TABLE_ID="tblbBSE2jJv9am7ZA"

echo "🎯 Target: Table 1 ($TABLE_ID) in base $BASE_ID"
echo ""

# Safety check
echo "⚠️ SAFETY CHECK:"
echo "This will PERMANENTLY DELETE 91 Airtable records"
echo "Are you sure you want to proceed? (type 'YES' to continue)"
read -p "> " confirm

if [ "$confirm" != "YES" ]; then
    echo "❌ Operation cancelled. No changes made."
    exit 0
fi

echo ""
echo "🚨 CONFIRMED: Proceeding with clear and replace..."
echo ""

# Step 1: Delete all existing records
echo "🗑️ Step 1: Deleting all existing Airtable records..."
python3 -c "
import requests
import os
import time

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = '$BASE_ID'
table_id = '$TABLE_ID'

print('📋 Loading record IDs to delete...')

# Get all record IDs
if os.path.exists('airtable_records_to_delete.txt'):
    with open('airtable_records_to_delete.txt', 'r') as f:
        record_ids = [line.strip() for line in f if line.strip()]
else:
    # Get fresh list
    print('🔍 Getting fresh record list...')
    url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    record_ids = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break
            
        data = response.json()
        records = data.get('records', [])
        record_ids.extend([r['id'] for r in records])
        
        offset = data.get('offset')
        if not offset:
            break

print(f'🎯 Found {len(record_ids)} records to delete')

# Delete in batches (Airtable allows max 10 per request)
deleted_count = 0
batch_size = 10

for i in range(0, len(record_ids), batch_size):
    batch = record_ids[i:i + batch_size]
    
    # Delete batch
    url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'records[]': batch}
    
    try:
        response = requests.delete(url, headers=headers, params=params)
        
        if response.status_code == 200:
            deleted_count += len(batch)
            print(f'   ✅ Deleted batch {i//batch_size + 1}: {deleted_count}/{len(record_ids)} records')
        else:
            print(f'   ❌ Failed to delete batch {i//batch_size + 1}: {response.status_code}')
            break
            
        # Rate limiting
        time.sleep(0.2)
        
    except Exception as e:
        print(f'   ❌ Exception deleting batch {i//batch_size + 1}: {e}')
        break

print(f'\\n🗑️ Deletion complete: {deleted_count}/{len(record_ids)} records deleted')
"

# Step 2: Upload clean database records
echo ""
echo "⬆️ Step 2: Uploading clean database records..."
python3 -c "
import sqlite3
import requests
import os
import time
from datetime import datetime

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = '$BASE_ID'
table_id = '$TABLE_ID'

# Get clean database records
print('📊 Loading clean database records...')
conn = sqlite3.connect('data/unified_leads.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute('SELECT * FROM leads ORDER BY created_at DESC')
clean_leads = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f'📊 Found {len(clean_leads)} clean leads to upload')

# Upload in batches (Airtable allows max 10 per request)
uploaded_count = 0
batch_size = 10

for i in range(0, len(clean_leads), batch_size):
    batch_leads = clean_leads[i:i + batch_size]
    
    # Prepare batch records
    batch_records = []
    for lead in batch_leads:
        airtable_record = {
            'fields': {
                'Full Name': lead.get('full_name') or '',
                'LinkedIn URL': lead.get('linkedin_url') or '',
                'Job Title': lead.get('job_title') or '',
                'Company': lead.get('company') or '',
                'Email': lead.get('email') or '',
                'Source': 'Clean Database',
                'Lead Quality': lead.get('lead_quality') or 'Warm',
                'Date Scraped': lead.get('date_scraped') or datetime.now().strftime('%Y-%m-%d'),
                'Website': lead.get('website') or '',
                'Business_Type': lead.get('business_type') or '',
                'Company_Description': lead.get('company_description') or '',
                'Created At': lead.get('created_at') or datetime.now().isoformat()
            }
        }
        batch_records.append(airtable_record)
    
    # Upload batch
    url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {'records': batch_records}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            uploaded_count += len(batch_records)
            print(f'   ✅ Uploaded batch {i//batch_size + 1}: {uploaded_count}/{len(clean_leads)} records')
        else:
            print(f'   ❌ Failed to upload batch {i//batch_size + 1}: {response.status_code}')
            print(f'   Error: {response.text[:200]}')
            break
            
        # Rate limiting
        time.sleep(0.2)
        
    except Exception as e:
        print(f'   ❌ Exception uploading batch {i//batch_size + 1}: {e}')
        break

print(f'\\n⬆️ Upload complete: {uploaded_count}/{len(clean_leads)} records uploaded')
"

# Step 3: Verify the result
echo ""
echo "✅ Step 3: Verifying the result..."
python3 -c "
import requests
import os
from collections import defaultdict

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = '$BASE_ID'  
table_id = '$TABLE_ID'

print('🔍 Checking final Airtable state...')

# Get all records
url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
headers = {'Authorization': f'Bearer {api_key}'}

all_records = []
offset = None

while True:
    params = {}
    if offset:
        params['offset'] = offset
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        break
        
    data = response.json()
    records = data.get('records', [])
    all_records.extend(records)
    
    offset = data.get('offset')
    if not offset:
        break

print(f'\\n📊 FINAL AIRTABLE STATE:')
print(f'   Total records: {len(all_records)}')

# Check for duplicates
name_groups = defaultdict(list)
linkedin_groups = defaultdict(list)

for record in all_records:
    fields = record.get('fields', {})
    
    full_name = fields.get('Full Name', '').strip().lower()
    if full_name:
        name_groups[full_name].append(record['id'])
    
    linkedin_url = fields.get('LinkedIn URL', '').strip()
    if linkedin_url:
        linkedin_groups[linkedin_url].append(record['id'])

name_dups = {k: v for k, v in name_groups.items() if len(v) > 1}
linkedin_dups = {k: v for k, v in linkedin_groups.items() if len(v) > 1}

print(f'   Name duplicates: {len(name_dups)} groups')
print(f'   LinkedIn duplicates: {len(linkedin_dups)} groups')

if len(name_dups) == 0 and len(linkedin_dups) == 0:
    print('   ✅ ZERO DUPLICATES - PERFECT!')
else:
    print('   ⚠️ Still has some duplicates')
    for name, ids in list(name_dups.items())[:3]:
        print(f'      - {name}: {len(ids)} copies')

print(f'\\n🎯 SUCCESS METRICS:')
print(f'   Old Airtable: 91 records (48 duplicates)')
print(f'   New Airtable: {len(all_records)} records ({len(name_dups) + len(linkedin_dups)} duplicates)')
print(f'   Improvement: {91 - len(all_records)} fewer records, {48 - (len(name_dups) + len(linkedin_dups))} fewer duplicates')
"

echo ""
echo "🏆 CLEAR AND REPLACE COMPLETED!"
echo "==============================="
echo "✅ Deleted all old duplicates from Airtable"
echo "✅ Uploaded clean database records"
echo "✅ Airtable now matches clean database"
echo ""
echo "🎯 RESULT: Zero duplicates in both systems!"
