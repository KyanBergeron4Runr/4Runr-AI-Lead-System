#!/bin/bash
# Check Airtable Current State and Replace with Clean Data

echo "🔍 CHECK AND REPLACE AIRTABLE WITH CLEAN DATA"
echo "============================================="
echo "1. Check what's currently in Airtable"
echo "2. Clear all existing records (duplicates)"
echo "3. Upload only clean database records"
echo ""

cd production_clean_system
source venv/bin/activate

# Use the correct base ID found earlier
CORRECT_BASE_ID="appBZvPvNXGqtoJdc"

echo "🎯 Using correct base: $CORRECT_BASE_ID"
echo ""

# Step 1: Check current Airtable state
echo "📊 Step 1: Checking current Airtable records..."
python3 -c "
import requests
import os
from collections import defaultdict

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = '$CORRECT_BASE_ID'

# First, get the table info
print('🔍 Getting table information...')
url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        tables = data.get('tables', [])
        
        if tables:
            # Use the first table (likely the leads table)
            table_id = tables[0]['id']
            table_name = tables[0]['name']
            print(f'✅ Using table: {table_name} ({table_id})')
            
            # Get all records from this table
            print(f'📊 Getting all records from {table_name}...')
            
            url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
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
            
            print(f'📊 CURRENT AIRTABLE STATE:')
            print(f'   Total records: {len(all_records)}')
            
            # Analyze for duplicates
            name_groups = defaultdict(list)
            linkedin_groups = defaultdict(list)
            
            for record in all_records:
                fields = record.get('fields', {})
                record_id = record.get('id')
                
                # Group by name
                full_name = fields.get('Full Name', '').strip()
                if full_name:
                    name_groups[full_name.lower()].append((record_id, full_name))
                
                # Group by LinkedIn
                linkedin_url = fields.get('LinkedIn URL', '').strip()
                if linkedin_url:
                    linkedin_groups[linkedin_url].append((record_id, full_name))
            
            # Find duplicates
            name_dups = {k: v for k, v in name_groups.items() if len(v) > 1}
            linkedin_dups = {k: v for k, v in linkedin_groups.items() if len(v) > 1}
            
            print(f'   Name duplicates: {len(name_dups)} groups')
            print(f'   LinkedIn duplicates: {len(linkedin_dups)} groups')
            
            # Show examples
            for i, (name, records) in enumerate(list(name_dups.items())[:3]):
                print(f'   - \"{name}\": {len(records)} copies')
            
            for i, (url, records) in enumerate(list(linkedin_dups.items())[:3]):
                print(f'   - {url}: {len(records)} copies')
            
            # Save record IDs for deletion
            with open('airtable_records_to_delete.txt', 'w') as f:
                for record in all_records:
                    f.write(f'{record[\"id\"]}\\n')
            
            print(f'\\n💾 Saved {len(all_records)} record IDs for potential deletion')
            
            # Save table info for next steps
            with open('correct_table_info.txt', 'w') as f:
                f.write(f'BASE_ID={base_id}\\n')
                f.write(f'TABLE_ID={table_id}\\n')
                f.write(f'TABLE_NAME={table_name}\\n')
                f.write(f'TOTAL_RECORDS={len(all_records)}\\n')
        else:
            print('❌ No tables found in base')
    else:
        print(f'❌ Cannot access base: {response.status_code}')
        
except Exception as e:
    print(f'❌ Error checking Airtable: {e}')
"

# Step 2: Show clean database for comparison
echo ""
echo "📊 Step 2: Checking clean database records..."
python3 -c "
import sqlite3

conn = sqlite3.connect('data/unified_leads.db')
conn.row_factory = sqlite3.Row

# Get all clean leads
cursor = conn.execute('SELECT * FROM leads ORDER BY created_at DESC')
clean_leads = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f'📊 CLEAN DATABASE STATE:')
print(f'   Total clean leads: {len(clean_leads)}')
print(f'   Recent leads: {len([l for l in clean_leads if l.get(\"date_scraped\")])}')
print(f'   With emails: {len([l for l in clean_leads if l.get(\"email\")])}')
print(f'   With LinkedIn: {len([l for l in clean_leads if l.get(\"linkedin_url\")])}')

# Show examples
print(f'\\n📋 Example clean leads:')
for i, lead in enumerate(clean_leads[:3]):
    name = lead.get('full_name', 'No name')
    company = lead.get('company', 'No company')
    email = lead.get('email', 'No email')
    print(f'   {i+1}. {name} at {company} ({email})')

print(f'\\n💾 Ready to upload {len(clean_leads)} clean leads to Airtable')
"

# Step 3: Decision point
echo ""
echo "🤔 Step 3: What do you want to do?"
echo ""
echo "OPTIONS:"
echo "1. CLEAR Airtable and upload ONLY clean database (recommended)"
echo "2. ADD clean database to existing Airtable (might create more duplicates)"
echo "3. MANUAL cleanup - export clean data to CSV for manual import"
echo ""

if [ -f "airtable_records_to_delete.txt" ]; then
    record_count=$(wc -l < airtable_records_to_delete.txt)
    echo "📊 Found $record_count existing Airtable records"
fi

if [ -f "correct_table_info.txt" ]; then
    echo "📋 Airtable configuration:"
    cat correct_table_info.txt
fi

echo ""
echo "🎯 RECOMMENDATION: Option 1 (Clear and replace)"
echo "This guarantees zero duplicates and clean data"
echo ""
echo "⚠️ NEXT STEPS:"
echo "1. Review the analysis above"
echo "2. Choose your approach"
echo "3. Run the appropriate cleanup/sync script"
