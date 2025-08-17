#!/bin/bash
# Debug Airtable Connection - Find the real issue

echo "🔍 DEBUGGING AIRTABLE CONNECTION"
echo "==============================="

# Step 1: Check environment variable
echo "🔑 Step 1: Environment Variable Check"
echo "Current AIRTABLE_API_KEY: $AIRTABLE_API_KEY"
echo "Length: ${#AIRTABLE_API_KEY}"
echo "First 10 chars: ${AIRTABLE_API_KEY:0:10}"
echo "Last 4 chars: ${AIRTABLE_API_KEY: -4}"

# Step 2: Set the variable correctly and test
echo ""
echo "🔧 Step 2: Setting Variable Correctly"
export AIRTABLE_API_KEY="pat1EXE7KfOBTgJl6.28307c0b4f5eb80de65d01de18ecead5da6e7bc98f04ceea7e60b540e9773923"
echo "New AIRTABLE_API_KEY: ${AIRTABLE_API_KEY:0:10}...${AIRTABLE_API_KEY: -4}"

# Step 3: Test basic Airtable API access
echo ""
echo "🧪 Step 3: Testing Basic API Access"

cd production_clean_system
source venv/bin/activate

python3 -c "
import requests
import os

api_key = os.getenv('AIRTABLE_API_KEY')
print(f'🔑 API Key in Python: {api_key[:10] if api_key else \"None\"}...{api_key[-4:] if api_key else \"None\"}')

# Test 1: List all bases (if token has permission)
print('\\n🧪 Test 1: List accessible bases')
url = 'https://api.airtable.com/v0/meta/bases'
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        bases = data.get('bases', [])
        print(f'✅ Found {len(bases)} accessible bases:')
        for base in bases[:3]:  # Show first 3
            print(f'   - {base.get(\"name\", \"Unknown\")} (ID: {base.get(\"id\", \"Unknown\")})')
    else:
        print(f'❌ Error: {response.text[:200]}')
        
except Exception as e:
    print(f'❌ Exception: {e}')

# Test 2: Try the specific base we're using
print('\\n🧪 Test 2: Test specific base access')
base_id = 'appjz81o6h5Z19Nph'
url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers)
    print(f'Base {base_id} access: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        tables = data.get('tables', [])
        print(f'✅ Found {len(tables)} tables in base:')
        for table in tables:
            print(f'   - {table.get(\"name\", \"Unknown\")} (ID: {table.get(\"id\", \"Unknown\")})')
    else:
        print(f'❌ Base access error: {response.text[:200]}')
        
except Exception as e:
    print(f'❌ Base access exception: {e}')

# Test 3: Try different common base IDs (in case the current one is wrong)
print('\\n🧪 Test 3: Testing potential base IDs')
potential_bases = [
    'appjz81o6h5Z19Nph',  # Current
    'app1234567890',      # Example format
]

for test_base in potential_bases:
    url = f'https://api.airtable.com/v0/{test_base}/tblwJZn9Tv6VWjpP?maxRecords=1'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    try:
        response = requests.get(url, headers=headers)
        print(f'   Base {test_base}: {response.status_code}')
        
        if response.status_code == 200:
            print(f'   ✅ SUCCESS with base {test_base}!')
            break
    except:
        pass
"

# Step 4: Manual base discovery
echo ""
echo "🔍 Step 4: Manual Base Discovery"
echo "If all tests fail, you may need to:"
echo "1. Go to your Airtable workspace"
echo "2. Open your leads base/table"
echo "3. Go to Help > API documentation"
echo "4. Copy the EXACT base ID from the URL"
echo "5. Copy the EXACT table ID from the documentation"

echo ""
echo "🎯 Current Configuration:"
echo "Base ID: appjz81o6h5Z19Nph"
echo "Table ID: tblwJZn9Tv6VWjpP"

echo ""
echo "🔧 NEXT STEPS:"
echo "1. If Test 1 shows bases: Use the correct base ID"
echo "2. If Test 2 shows tables: Use the correct table ID"
echo "3. If all fail: Token needs more permissions or wrong workspace"
