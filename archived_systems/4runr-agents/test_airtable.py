#!/usr/bin/env python3
"""
Test Airtable Connection

This script tests the Airtable connection and tries to send a simple lead.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Airtable configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Generated leads')

print("🔍 Testing Airtable Connection")
print("=" * 40)
print(f"API Key: {AIRTABLE_API_KEY[:10]}..." if AIRTABLE_API_KEY else "❌ No API Key")
print(f"Base ID: {AIRTABLE_BASE_ID}")
print(f"Table Name: {AIRTABLE_TABLE_NAME}")
print()

if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    print("❌ Missing Airtable configuration")
    exit(1)

# Test 1: Get table schema
print("📋 Step 1: Getting table schema...")
schema_url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(schema_url, headers=headers)
    print(f"Schema request status: {response.status_code}")
    
    if response.status_code == 200:
        schema_data = response.json()
        
        # Find our table
        target_table = None
        for table in schema_data.get('tables', []):
            if table['name'] == AIRTABLE_TABLE_NAME:
                target_table = table
                break
        
        if target_table:
            print(f"✅ Found table: {target_table['name']}")
            print("Available fields:")
            for field in target_table.get('fields', []):
                print(f"  - {field['name']} ({field['type']})")
        else:
            print(f"❌ Table '{AIRTABLE_TABLE_NAME}' not found")
            print("Available tables:")
            for table in schema_data.get('tables', []):
                print(f"  - {table['name']}")
    else:
        print(f"❌ Schema request failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error getting schema: {e}")

print()

# Test 2: Try to send a simple lead
print("📤 Step 2: Testing lead submission...")

# Create a minimal test lead
test_lead = {
    "fields": {
        "Full Name": "Test Lead",
        "Company": "Test Company",
        "Job Title": "CEO",
        "LinkedIn URL": "https://linkedin.com/in/test",
        "Email": "test@example.com",
        "Source": "Test"
    }
}

api_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

try:
    response = requests.post(api_url, headers=headers, json=test_lead)
    print(f"Lead submission status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Successfully sent test lead to Airtable!")
        result = response.json()
        print(f"Record ID: {result.get('id')}")
    else:
        print(f"❌ Failed to send lead: {response.text}")
        
        # Try with even simpler data
        print("\n🔄 Trying with minimal data...")
        minimal_lead = {
            "fields": {
                "Full Name": "Minimal Test",
                "Company": "Test Co"
            }
        }
        
        response2 = requests.post(api_url, headers=headers, json=minimal_lead)
        print(f"Minimal lead status: {response2.status_code}")
        
        if response2.status_code == 200:
            print("✅ Minimal lead worked!")
        else:
            print(f"❌ Minimal lead also failed: {response2.text}")
        
except Exception as e:
    print(f"❌ Error sending lead: {e}")

print("\n🎯 Summary:")
print("If the schema request worked, check the available fields above.")
print("If the lead submission failed, the table might need different field names.")
print("Common issues:")
print("  - Field names must match exactly (case-sensitive)")
print("  - Required fields must be included")
print("  - Field types must match (text, email, URL, etc.)")