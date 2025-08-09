#!/usr/bin/env python3
"""
Verify that all field references match the exact Airtable schema
"""

import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent / "4runr-lead-scraper"))

try:
    from config.settings import get_settings
    import requests
    from urllib.parse import quote
    
    def verify_exact_field_match():
        """Verify field names match exactly"""
        print("🔍 Verifying Exact Field Match")
        print("=" * 40)
        
        # Your exact field list
        expected_fields = [
            'Full Name',
            'LinkedIn URL',
            'Job Title',
            'Company',
            'Email',
            'Source',
            'Needs Enrichment',
            'AI Message',
            'Replied',
            'Response Date',
            'Response Notes',
            'Lead Quality',
            'Date Scraped',
            'Date Enriched',
            'Date Messaged',
            'Extra info',
            'Level Engaged',
            'Engagement_Status',
            'Email_Confidence_Level',
            'Website',
            'Created At',
            'Business_Type',
            'Follow_Up_Stage',
            'Response_Status'
        ]
        
        # Get settings
        settings = get_settings()
        api_key = settings.airtable.api_key
        base_id = settings.airtable.base_id
        table_name = settings.airtable.table_name
        
        # Get table schema
        try:
            url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
            headers = {'Authorization': f'Bearer {api_key}'}
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                tables = result.get('tables', [])
                
                target_table = None
                for table in tables:
                    if table['name'] == table_name:
                        target_table = table
                        break
                
                if target_table:
                    actual_fields = [field['name'] for field in target_table['fields']]
                    
                    print(f"📋 Table: {table_name}")
                    print(f"📊 Expected: {len(expected_fields)} fields")
                    print(f"📊 Actual: {len(actual_fields)} fields")
                    
                    # Check exact matches
                    print(f"\n✅ Fields that match exactly:")
                    matched = []
                    for field in expected_fields:
                        if field in actual_fields:
                            matched.append(field)
                            print(f"   ✅ {field}")
                    
                    # Check missing fields
                    missing = [field for field in expected_fields if field not in actual_fields]
                    if missing:
                        print(f"\n❌ Expected fields not found in Airtable:")
                        for field in missing:
                            print(f"   ❌ {field}")
                    
                    # Check extra fields
                    extra = [field for field in actual_fields if field not in expected_fields]
                    if extra:
                        print(f"\n⚠️ Extra fields in Airtable (not in expected list):")
                        for field in extra:
                            print(f"   ⚠️ {field}")
                    
                    print(f"\n📊 Summary:")
                    print(f"   Matched: {len(matched)}/{len(expected_fields)} ({len(matched)/len(expected_fields)*100:.1f}%)")
                    print(f"   Missing: {len(missing)}")
                    print(f"   Extra: {len(extra)}")
                    
                    # Test field access with exact names
                    print(f"\n🧪 Testing field access with exact names:")
                    
                    # Get a sample record
                    encoded_table_name = quote(table_name)
                    record_url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}?maxRecords=1"
                    record_response = requests.get(record_url, headers=headers, timeout=30)
                    
                    if record_response.status_code == 200:
                        record_result = record_response.json()
                        records = record_result.get('records', [])
                        
                        if records:
                            fields = records[0].get('fields', {})
                            
                            # Test key field access patterns
                            test_fields = [
                                'Full Name',
                                'Job Title', 
                                'AI Message',
                                'Engagement_Status',
                                'Email_Confidence_Level',
                                'Website',
                                'Extra info'
                            ]
                            
                            for field in test_fields:
                                value = fields.get(field, '')
                                status = "✅" if field in fields else "⚪"
                                print(f"   {status} fields.get('{field}') → {type(value).__name__}")
                    
                    return len(missing) == 0
                else:
                    print(f"❌ Table '{table_name}' not found")
                    return False
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False
    
    if __name__ == "__main__":
        success = verify_exact_field_match()
        
        if success:
            print("\n🎉 Perfect match! All expected fields exist in Airtable.")
        else:
            print("\n⚠️ Some expected fields are missing from Airtable.")
            
except ImportError as e:
    print(f"❌ Import error: {e}")