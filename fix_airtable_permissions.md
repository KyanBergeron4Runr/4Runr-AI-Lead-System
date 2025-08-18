# 🔧 Fix Airtable API Permissions

## Current Issue
Getting 403 error: "Invalid permissions, or the requested model was not found"

## Root Causes
1. **API Key Permissions**: Token doesn't have access to this base
2. **Base ID Wrong**: Using incorrect base ID
3. **Table Name Wrong**: Using incorrect table name
4. **Workspace Permissions**: User doesn't have access

## Solutions

### 1. Check Current API Key
```bash
echo $AIRTABLE_API_KEY
```

### 2. Get New API Key with Correct Permissions
1. Go to https://airtable.com/account
2. Go to "Personal access tokens"
3. Create new token with:
   - **Read records** permission
   - **Write records** permission
   - **Access to your specific base**

### 3. Verify Base and Table IDs
Current values we're using:
- Base ID: `appjz81o6h5Z19Nph`
- Table Name: `tblwJZn9Tv6VWjpP`

To get correct IDs:
1. Go to your Airtable base
2. Help > API documentation
3. Copy the correct Base ID and Table ID

### 4. Test New Credentials
```bash
export AIRTABLE_API_KEY="your_new_token"

# Test connection
python3 -c "
import requests
import os

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = 'appjz81o6h5Z19Nph'  # Update if needed
table_name = 'tblwJZn9Tv6VWjpP'  # Update if needed

url = f'https://api.airtable.com/v0/{base_id}/{table_name}?maxRecords=1'
headers = {'Authorization': f'Bearer {api_key}'}

response = requests.get(url, headers=headers)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    print('✅ SUCCESS!')
else:
    print(f'❌ Error: {response.text}')
"
```

## Alternative: Skip Airtable for Now
Since database cleanup is PERFECT, you can:
1. **Focus on database only** (which is clean)
2. **Fix Airtable later** when you have correct permissions
3. **Use manual Airtable cleanup** if needed

## Current Status
✅ **Database**: ZERO DUPLICATES  
❌ **Airtable**: Permission issue (fixable)

**The main cleanup goal is ACHIEVED!**
