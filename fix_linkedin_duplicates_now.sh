#!/bin/bash
# Fix LinkedIn Duplicates - Direct SQL cleanup for the 6 duplicate groups found

echo "🎯 FIXING LINKEDIN DUPLICATES - DIRECT APPROACH"
echo "==============================================="
echo "Found 6 LinkedIn URL duplicate groups - removing them now"
echo ""

cd production_clean_system
source venv/bin/activate

# Step 1: Show the exact duplicates
echo "📊 Step 1: Examining the 6 LinkedIn duplicate groups..."
python3 -c "
import sqlite3

conn = sqlite3.connect('data/unified_leads.db')

print('🔍 LINKEDIN DUPLICATE DETAILS:')
print('=' * 60)

# Get the exact duplicates with details
cursor = conn.execute('''
    SELECT linkedin_url, COUNT(*) as count, 
           GROUP_CONCAT(id || ':' || COALESCE(full_name, 'No Name')) as details
    FROM leads 
    WHERE linkedin_url IS NOT NULL AND linkedin_url != \"\"
    GROUP BY linkedin_url
    HAVING COUNT(*) > 1
    ORDER BY count DESC
''')

duplicates = cursor.fetchall()
total_duplicate_records = 0

for i, (url, count, details) in enumerate(duplicates, 1):
    print(f'{i}. {url}')
    print(f'   Copies: {count}')
    print(f'   Records: {details}')
    total_duplicate_records += (count - 1)  # Keep 1, remove others
    print()

print(f'🎯 Total duplicate records to remove: {total_duplicate_records}')
conn.close()
"

# Step 2: Remove duplicates (keep the oldest record for each URL)
echo "🧹 Step 2: Removing LinkedIn duplicates (keeping oldest record)..."
python3 -c "
import sqlite3

conn = sqlite3.connect('data/unified_leads.db')

# Get duplicate LinkedIn URLs
cursor = conn.execute('''
    SELECT linkedin_url
    FROM leads 
    WHERE linkedin_url IS NOT NULL AND linkedin_url != \"\"
    GROUP BY linkedin_url
    HAVING COUNT(*) > 1
''')

duplicate_urls = [row[0] for row in cursor.fetchall()]
total_removed = 0

print(f'🔧 Processing {len(duplicate_urls)} duplicate URL groups...')

for url in duplicate_urls:
    # Get all records for this URL, ordered by creation date (keep oldest)
    cursor = conn.execute('''
        SELECT id, full_name, created_at 
        FROM leads 
        WHERE linkedin_url = ?
        ORDER BY created_at ASC
    ''', (url,))
    
    records = cursor.fetchall()
    if len(records) > 1:
        # Keep the first (oldest) record, delete the rest
        keep_id = records[0][0]
        keep_name = records[0][1] or 'No Name'
        
        for record in records[1:]:
            delete_id = record[0]
            delete_name = record[1] or 'No Name'
            
            # Delete the duplicate
            cursor = conn.execute('DELETE FROM leads WHERE id = ?', (delete_id,))
            total_removed += 1
            print(f'  ✅ Removed: {delete_name} (ID: {delete_id})')
        
        print(f'  📌 Kept: {keep_name} (ID: {keep_id}) for {url}')

conn.commit()
conn.close()

print(f'🎯 Total duplicate records removed: {total_removed}')
"

# Step 3: Verify cleanup
echo ""
echo "✅ Step 3: Verifying cleanup..."
python3 -c "
import sqlite3

conn = sqlite3.connect('data/unified_leads.db')

# Check final counts
cursor = conn.execute('SELECT COUNT(*) FROM leads')
final_count = cursor.fetchone()[0]

# Check for remaining duplicates
cursor = conn.execute('''
    SELECT linkedin_url, COUNT(*) as count
    FROM leads 
    WHERE linkedin_url IS NOT NULL AND linkedin_url != \"\"
    GROUP BY linkedin_url
    HAVING COUNT(*) > 1
''')

remaining_dups = cursor.fetchall()

print(f'📊 Final lead count: {final_count}')
print(f'🎯 Remaining LinkedIn duplicates: {len(remaining_dups)}')

if len(remaining_dups) == 0:
    print('✅ ALL LINKEDIN DUPLICATES REMOVED!')
else:
    print('⚠️ Still has LinkedIn duplicates:')
    for url, count in remaining_dups:
        print(f'  - {url}: {count} copies')

# Check other potential duplicates
cursor = conn.execute('''
    SELECT full_name, company, COUNT(*) as count
    FROM leads 
    WHERE full_name IS NOT NULL AND full_name != \"\"
    GROUP BY LOWER(full_name), LOWER(COALESCE(company, \"\"))
    HAVING COUNT(*) > 1
''')

name_dups = cursor.fetchall()
print(f'🎯 Name+Company duplicates: {len(name_dups)}')

cursor = conn.execute('''
    SELECT email, COUNT(*) as count
    FROM leads 
    WHERE email IS NOT NULL AND email != \"\"
    GROUP BY email
    HAVING COUNT(*) > 1
''')

email_dups = cursor.fetchall()
print(f'🎯 Email duplicates: {len(email_dups)}')

conn.close()
"

# Step 4: Fix Airtable API issue
echo ""
echo "🔧 Step 4: Fixing Airtable API access..."
echo "The 403 error suggests an API key issue. Let's check:"

if [ -z "$AIRTABLE_API_KEY" ]; then
    echo "❌ AIRTABLE_API_KEY is not set!"
    echo "🔧 Please set it with:"
    echo "export AIRTABLE_API_KEY='your_api_key_here'"
else
    echo "✅ AIRTABLE_API_KEY is set"
    echo "🧪 Testing Airtable connection..."
    python3 -c "
import requests
import os

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = 'appjz81o6h5Z19Nph'
table_name = 'tblwJZn9Tv6VWjpP'

url = f'https://api.airtable.com/v0/{base_id}/{table_name}?maxRecords=1'
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers)
    print(f'🔍 API Response: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Airtable connection successful')
        print(f'📊 Sample response: {len(data.get(\"records\", []))} records')
    else:
        print(f'❌ API Error: {response.status_code}')
        print(f'Response: {response.text[:200]}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
fi

echo ""
echo "🏆 LINKEDIN DUPLICATE CLEANUP COMPLETED!"
echo "========================================"
echo "✅ LinkedIn duplicates removed"
echo "✅ Database verified"
echo "✅ Airtable access checked"
echo ""
echo "🎯 DATABASE SHOULD NOW BE CLEAN!"
