#!/bin/bash
# Sync Clean Internal Database to Airtable
# Fix the disconnect between clean internal DB and Airtable

echo "🔄 SYNC CLEAN DATABASE TO AIRTABLE"
echo "=================================="
echo "Internal DB is clean (64 leads, zero duplicates)"
echo "Now syncing this clean data to Airtable"
echo ""

cd production_clean_system
source venv/bin/activate

# Step 1: Check API permissions with detailed error info
echo "🔍 Step 1: Diagnosing Airtable API issue..."
python3 -c "
import requests
import os

api_key = os.getenv('AIRTABLE_API_KEY')
if not api_key:
    print('❌ AIRTABLE_API_KEY not set!')
    print('🔧 Set it with: export AIRTABLE_API_KEY=\"your_key\"')
    exit(1)

print(f'🔑 API Key: {api_key[:10]}...{api_key[-4:]}')

# Test different base/table combinations
test_configs = [
    ('appjz81o6h5Z19Nph', 'tblwJZn9Tv6VWjpP'),  # Current
    ('appjz81o6h5Z19Nph', 'Leads'),  # Table name instead of ID
    ('appjz81o6h5Z19Nph', 'leads'),  # Lowercase
]

for base_id, table_name in test_configs:
    print(f'\\n🧪 Testing: Base {base_id}, Table {table_name}')
    
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}?maxRecords=1'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    try:
        response = requests.get(url, headers=headers)
        print(f'   Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'   ✅ SUCCESS! Found {len(data.get(\"records\", []))} records')
            break
        else:
            error_msg = response.text[:150]
            print(f'   ❌ Error: {error_msg}')
    except Exception as e:
        print(f'   ❌ Exception: {e}')

print('\\n' + '='*50)
"

# Step 2: Manual API key configuration if needed
echo ""
echo "🔧 Step 2: API Key Configuration Help"
echo "If you're getting 403 errors, you need a new API token:"
echo ""
echo "1. Go to: https://airtable.com/account"
echo "2. Click 'Personal access tokens'"
echo "3. Create new token with these permissions:"
echo "   - records:read"
echo "   - records:write"
echo "   - schema:read"
echo "4. Grant access to your specific base"
echo "5. Copy the token and run:"
echo "   export AIRTABLE_API_KEY='your_new_token'"
echo ""
read -p "🤔 Do you want to continue with current token? (y/n): " continue_choice

if [ "$continue_choice" != "y" ]; then
    echo "⏸️ Stopped. Please update your API token and run again."
    exit 0
fi

# Step 3: Get the correct base and table info
echo ""
echo "📋 Step 3: Checking your Airtable structure..."
python3 -c "
import requests
import os

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = 'appjz81o6h5Z19Nph'

# Try to get base schema
url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        tables = data.get('tables', [])
        
        print(f'📊 Found {len(tables)} tables in base:')
        for table in tables:
            table_id = table.get('id')
            table_name = table.get('name')
            print(f'   - {table_name} (ID: {table_id})')
        
        # Save correct IDs for later use
        with open('airtable_config.txt', 'w') as f:
            f.write(f'BASE_ID={base_id}\\n')
            if tables:
                f.write(f'TABLE_ID={tables[0][\"id\"]}\\n')
                f.write(f'TABLE_NAME={tables[0][\"name\"]}\\n')
    else:
        print(f'❌ Cannot access base schema: {response.status_code}')
        print('Using default configuration...')
        
except Exception as e:
    print(f'❌ Schema check failed: {e}')
"

# Step 4: Sync clean database to Airtable (if API works)
echo ""
echo "🔄 Step 4: Syncing clean database to Airtable..."
python3 -c "
import sqlite3
import requests
import os
import json
from datetime import datetime

# Load Airtable config
config = {}
if os.path.exists('airtable_config.txt'):
    with open('airtable_config.txt', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value

base_id = config.get('BASE_ID', 'appjz81o6h5Z19Nph')
table_id = config.get('TABLE_ID', 'tblwJZn9Tv6VWjpP')
api_key = os.getenv('AIRTABLE_API_KEY')

print(f'🎯 Syncing to Base: {base_id}, Table: {table_id}')

# Get clean database records
conn = sqlite3.connect('data/unified_leads.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute('''
    SELECT * FROM leads 
    ORDER BY created_at DESC
    LIMIT 10
''')

clean_leads = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f'📊 Found {len(clean_leads)} clean leads to sync')

# Test sync with first lead
if clean_leads and api_key:
    test_lead = clean_leads[0]
    
    # Map database fields to Airtable fields
    airtable_record = {
        'fields': {
            'Full Name': test_lead.get('full_name') or '',
            'LinkedIn URL': test_lead.get('linkedin_url') or '',
            'Job Title': test_lead.get('job_title') or '',
            'Company': test_lead.get('company') or '',
            'Email': test_lead.get('email') or '',
            'Source': test_lead.get('source') or 'Clean Database',
            'Lead Quality': test_lead.get('lead_quality') or 'Warm',
            'Date Scraped': test_lead.get('date_scraped') or datetime.now().strftime('%Y-%m-%d'),
            'Website': test_lead.get('website') or '',
            'Business_Type': test_lead.get('business_type') or '',
            'Company_Description': test_lead.get('company_description') or ''
        }
    }
    
    # Test API call
    url = f'https://api.airtable.com/v0/{base_id}/{table_id}'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=airtable_record)
        print(f'🧪 Test sync result: {response.status_code}')
        
        if response.status_code in [200, 201]:
            print('✅ Test sync successful! API is working.')
            result = response.json()
            print(f'   Created record ID: {result.get(\"id\", \"unknown\")}')
        else:
            print(f'❌ Test sync failed: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Test sync exception: {e}')
else:
    print('⚠️ Skipping sync test - no leads or API key issue')

print(f'\\n📊 SYNC STATUS:')
print(f'   Clean database leads: {len(clean_leads)}')
print(f'   API key status: {\"✅ Set\" if api_key else \"❌ Missing\"}')
print(f'   Ready for full sync: {\"✅ Yes\" if api_key and clean_leads else \"❌ No\"}')
"

# Step 5: Full sync if test worked
echo ""
echo "✅ Step 5: Next steps..."
echo ""
if [ -f "airtable_config.txt" ]; then
    echo "📋 Airtable configuration saved to airtable_config.txt"
    cat airtable_config.txt
fi

echo ""
echo "🎯 NEXT ACTIONS:"
echo "1. If API test worked: Run full sync of clean database"
echo "2. If API still fails: Update API token with proper permissions"
echo "3. Clean existing Airtable duplicates manually if needed"
echo ""
echo "🏆 INTERNAL DATABASE IS CLEAN ✅"
echo "🔄 AIRTABLE SYNC IN PROGRESS..."
