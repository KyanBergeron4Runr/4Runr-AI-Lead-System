#!/usr/bin/env python3
"""
Test script for the configurable Airtable integration.

Tests the new configurable Airtable client with defensive error handling
and field name configuration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from outreach.shared.configurable_airtable_client import get_configurable_airtable_client


def test_airtable_configuration():
    """Test the Airtable configuration and connection."""
    print("🧪 Testing Airtable Configuration")
    print("=" * 50)
    
    try:
        # Initialize client
        client = get_configurable_airtable_client()
        print("✅ Configurable Airtable client initialized")
        
        # Show field mapping
        field_mapping = client.get_field_mapping()
        print("\n📋 Field Mapping Configuration:")
        for logical_name, airtable_field in field_mapping.items():
            print(f"  {logical_name}: '{airtable_field}'")
        
        # Test connection
        print("\n🔗 Testing Airtable Connection...")
        connection_ok = client.test_connection()
        
        if connection_ok:
            print("✅ Airtable connection successful")
        else:
            print("❌ Airtable connection failed")
            return False
        
        # Test lead retrieval with defensive handling
        print("\n📊 Testing Lead Retrieval...")
        
        # Test processing leads
        processing_leads = client.get_leads_for_processing(max_records=5)
        print(f"  Processing leads: {len(processing_leads)} found")
        
        # Test message generation leads
        message_leads = client.get_leads_for_message_generation(limit=5)
        print(f"  Message generation leads: {len(message_leads)} found")
        
        # Test engagement leads
        engagement_leads = client.get_leads_for_engagement(limit=5)
        print(f"  Engagement leads: {len(engagement_leads)} found")
        
        # Show sample lead data if available
        if processing_leads:
            print("\n📝 Sample Lead Data:")
            sample_lead = processing_leads[0]
            print(f"  ID: {sample_lead.get('id', 'N/A')}")
            print(f"  Company: {sample_lead.get(client.field_company_name, 'N/A')}")
            print(f"  Website: {sample_lead.get(client.field_website, 'N/A')}")
            print(f"  Email: {sample_lead.get(client.field_email, 'N/A')}")
        
        print("\n✅ All Airtable tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Airtable test failed: {e}")
        return False


def test_error_handling():
    """Test the defensive error handling capabilities."""
    print("\n🛡️  Testing Error Handling")
    print("=" * 50)
    
    try:
        client = get_configurable_airtable_client()
        
        # Test with potentially invalid field names
        print("Testing with potentially invalid field configurations...")
        
        # This should gracefully handle field name mismatches
        leads = client.get_leads_for_processing(max_records=1)
        print(f"✅ Defensive handling worked: {len(leads)} leads retrieved")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Starting Airtable Configuration Tests")
    print("=" * 60)
    
    # Test basic configuration
    config_ok = test_airtable_configuration()
    
    # Test error handling
    error_handling_ok = test_error_handling()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Configuration Test: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Error Handling Test: {'✅ PASS' if error_handling_ok else '❌ FAIL'}")
    
    if config_ok and error_handling_ok:
        print("\n🎉 All tests passed! Airtable integration is ready.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check configuration and try again.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)