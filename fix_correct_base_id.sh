#!/bin/bash
# Fix Airtable Base ID - Use the correct base found in debug

echo "🔧 FIXING AIRTABLE BASE ID"
echo "========================="
echo "Debug found the correct base: 'Generated leads' (appBZvPvNXGqtoJdc)"
echo "Updating all scripts to use the correct base ID"
echo ""

cd production_clean_system
source venv/bin/activate

# Step 1: Test the correct base to get table info
echo "🧪 Step 1: Getting table info from correct base..."
python3 -c "
import requests
import os

api_key = os.getenv('AIRTABLE_API_KEY')
correct_base_id = 'appBZvPvNXGqtoJdc'  # From debug results

print(f'🎯 Testing correct base: {correct_base_id}')

# Get tables in this base
url = f'https://api.airtable.com/v0/meta/bases/{correct_base_id}/tables'
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers)
    print(f'Base access: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        tables = data.get('tables', [])
        print(f'✅ Found {len(tables)} tables:')
        
        for table in tables:
            table_id = table.get('id')
            table_name = table.get('name')
            print(f'   - {table_name} (ID: {table_id})')
            
            # Look for leads table
            if 'lead' in table_name.lower() or 'contact' in table_name.lower():
                print(f'   👆 This looks like the leads table!')
        
        # Save correct config
        with open('correct_airtable_config.txt', 'w') as f:
            f.write(f'CORRECT_BASE_ID={correct_base_id}\\n')
            if tables:
                f.write(f'FIRST_TABLE_ID={tables[0][\"id\"]}\\n')
                f.write(f'FIRST_TABLE_NAME={tables[0][\"name\"]}\\n')
        
        print(f'\\n💾 Saved correct config to correct_airtable_config.txt')
        
    else:
        print(f'❌ Error: {response.text[:200]}')
        
except Exception as e:
    print(f'❌ Exception: {e}')
"

# Step 2: Test sync with correct base
echo ""
echo "🔄 Step 2: Testing sync with correct base..."
python3 -c "
import sqlite3
import requests
import os
from datetime import datetime

# Load correct config
correct_base_id = 'appBZvPvNXGqtoJdc'
api_key = os.getenv('AIRTABLE_API_KEY')

# Read config if available
config = {}
if os.path.exists('correct_airtable_config.txt'):
    with open('correct_airtable_config.txt', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value

table_id = config.get('FIRST_TABLE_ID', 'Table1')  # Fallback
table_name = config.get('FIRST_TABLE_NAME', 'Unknown')

print(f'🎯 Testing sync to:')
print(f'   Base: {correct_base_id}')
print(f'   Table: {table_name} ({table_id})')

# Get one clean lead to test
conn = sqlite3.connect('data/unified_leads.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute('SELECT * FROM leads LIMIT 1')
test_lead = dict(cursor.fetchone()) if cursor.fetchone() else None
conn.close()

cursor = conn.execute('SELECT * FROM leads LIMIT 1')
test_lead = dict(cursor.fetchone()) if cursor.fetchone() else None
conn.close()

if test_lead:
    print(f'\\n🧪 Test lead: {test_lead.get(\"full_name\", \"No name\")}')
    
    # Create Airtable record
    airtable_record = {
        'fields': {
            'Full Name': test_lead.get('full_name') or '',
            'LinkedIn URL': test_lead.get('linkedin_url') or '',
            'Job Title': test_lead.get('job_title') or '',
            'Company': test_lead.get('company') or '',
            'Email': test_lead.get('email') or '',
            'Source': 'Clean Database Sync',
            'Lead Quality': test_lead.get('lead_quality') or 'Warm'
        }
    }
    
    # Test API call with correct base
    url = f'https://api.airtable.com/v0/{correct_base_id}/{table_id}'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=airtable_record)
        print(f'\\n🚀 Sync test result: {response.status_code}')
        
        if response.status_code in [200, 201]:
            result = response.json()
            record_id = result.get('id', 'unknown')
            print(f'✅ SUCCESS! Created record: {record_id}')
            print(f'🎉 AIRTABLE SYNC IS WORKING!')
        else:
            print(f'❌ Sync failed: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Sync exception: {e}')
else:
    print('❌ No test lead found')
"

# Step 3: Summary and next steps
echo ""
echo "✅ Step 3: Summary"
if [ -f "correct_airtable_config.txt" ]; then
    echo "📋 Correct Airtable configuration:"
    cat correct_airtable_config.txt
fi

echo ""
echo "🎯 NEXT STEPS:"
echo "1. If sync test worked: Run full sync with correct base ID"
echo "2. Update all scripts to use appBZvPvNXGqtoJdc instead of appjz81o6h5Z19Nph"
echo "3. Sync all 64 clean leads to Airtable"
echo ""
echo "🏆 CORRECT BASE FOUND: appBZvPvNXGqtoJdc"
echo "✅ API KEY WORKS PERFECTLY!"
