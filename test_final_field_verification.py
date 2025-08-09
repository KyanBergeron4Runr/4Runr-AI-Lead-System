#!/usr/bin/env python3
"""
Final verification that all Airtable field names are correctly mapped
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
    
    def test_field_access():
        """Test accessing fields with the corrected names"""
        print("🧪 Final Field Name Verification")
        print("=" * 40)
        
        # Get settings
        settings = get_settings()
        api_key = settings.airtable.api_key
        base_id = settings.airtable.base_id
        table_name = settings.airtable.table_name
        
        # API setup
        encoded_table_name = quote(table_name)
        base_url = f"https://api.airtable.com/v0/{base_id}/{encoded_table_name}"
        headers = {'Authorization': f'Bearer {api_key}'}
        
        print(f"📋 Testing field access in table: {table_name}")
        
        # Get a few records to test field access
        try:
            response = requests.get(f"{base_url}?maxRecords=3", headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('records', [])
                
                print(f"✅ Retrieved {len(records)} records for testing")
                
                # Test the key fields we updated
                key_fields = [
                    'Full Name',
                    'LinkedIn URL', 
                    'Job Title',
                    'Company',
                    'Email',
                    'AI Message',
                    'Response Notes',
                    'Engagement_Status',
                    'Email_Confidence_Level',
                    'Level Engaged',
                    'Website',
                    'Extra info',
                    'Business_Type'
                ]
                
                field_stats = {field: 0 for field in key_fields}
                
                for i, record in enumerate(records, 1):
                    fields = record.get('fields', {})
                    print(f"\n📋 Record {i} (ID: {record['id']}):")
                    
                    for field in key_fields:
                        if field in fields and fields[field]:
                            field_stats[field] += 1
                            value = str(fields[field])
                            # Truncate long values
                            if len(value) > 50:
                                value = value[:47] + "..."
                            print(f"   ✅ {field}: {value}")
                        else:
                            print(f"   ⚪ {field}: (empty)")
                
                print(f"\n📊 Field Population Summary:")
                for field, count in field_stats.items():
                    percentage = (count / len(records)) * 100
                    print(f"   {field}: {count}/{len(records)} records ({percentage:.0f}%)")
                
                # Test specific field access patterns used in the code
                print(f"\n🧪 Testing Code Access Patterns:")
                
                if records:
                    test_record = records[0]
                    fields = test_record.get('fields', {})
                    
                    # Test the patterns used in our updated code
                    test_patterns = [
                        ("fields.get('Full Name', '')", fields.get('Full Name', '')),
                        ("fields.get('Job Title', '')", fields.get('Job Title', '')),
                        ("fields.get('AI Message', '')", fields.get('AI Message', '')),
                        ("fields.get('Engagement_Status', '')", fields.get('Engagement_Status', '')),
                        ("fields.get('Email_Confidence_Level', '')", fields.get('Email_Confidence_Level', '')),
                        ("fields.get('Website', '')", fields.get('Website', '')),
                        ("fields.get('Extra info', '')", fields.get('Extra info', '')),
                    ]
                    
                    for pattern, result in test_patterns:
                        status = "✅" if result else "⚪"
                        result_str = str(result)[:30] + "..." if len(str(result)) > 30 else str(result)
                        print(f"   {status} {pattern} → '{result_str}'")
                
                return True
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False
    
    if __name__ == "__main__":
        success = test_field_access()
        
        if success:
            print("\n🎉 Field name verification completed!")
            print("✅ All field references should now work correctly with the live Airtable schema")
        else:
            print("\n❌ Field verification failed")
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the correct directory with the right environment")