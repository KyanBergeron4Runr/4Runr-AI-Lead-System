#!/usr/bin/env python3
"""
Airtable Field Mapping Analysis

Compare existing Airtable fields with what the code expects
and create a mapping strategy.
"""

def main():
    """Analyze field mapping between existing and expected fields."""
    print("🔍 Airtable Field Mapping Analysis")
    print("=" * 40)
    
    # Existing fields in Airtable (from user)
    existing_fields = [
        "Full Name",
        "LinkedIn URL", 
        "Job Title",
        "Company",
        "Email",
        "Source",
        "Needs Enrichment",
        "AI Message",
        "Replied",
        "Response Date",
        "Response Notes",
        "Lead Quality",
        "Date Scraped",
        "Date Enriched", 
        "Date Messaged",
        "Extra info",
        "Level Engaged"
    ]
    
    # Fields the code expects
    expected_fields = [
        "Engagement_Status",
        "Email_Confidence_Level", 
        "Level Engaged",
        "Company",
        "Title",
        "Email",
        "Custom_Message",
        "Message_Preview",
        "Last_Contacted_Date",
        "company_website_url",
        "Company_Description",
        "Top_Services",
        "Tone",
        "Website_Insights",
        "Delivery_Method"
    ]
    
    print("📋 Existing Airtable Fields:")
    for i, field in enumerate(existing_fields, 1):
        print(f"{i:2d}. {field}")
    
    print(f"\n🎯 Code Expected Fields:")
    for i, field in enumerate(expected_fields, 1):
        print(f"{i:2d}. {field}")
    
    print(f"\n🔗 Field Mapping Analysis:")
    print("-" * 50)
    
    # Create mapping
    field_mapping = {
        # Direct matches
        "Level Engaged": "Level Engaged",  # ✅ Exact match
        "Company": "Company",              # ✅ Exact match  
        "Email": "Email",                  # ✅ Exact match
        
        # Close matches that can be mapped
        "Title": "Job Title",              # Close match
        "Custom_Message": "AI Message",    # Close match
        "Last_Contacted_Date": "Date Messaged",  # Close match
        
        # Missing fields that need to be created or have alternatives
        "Engagement_Status": "MISSING - could use Lead Quality or create new",
        "Email_Confidence_Level": "MISSING - needs to be created",
        "Message_Preview": "MISSING - could derive from AI Message", 
        "company_website_url": "MISSING - needs to be created",
        "Company_Description": "MISSING - could use Extra info or create new",
        "Top_Services": "MISSING - needs to be created",
        "Tone": "MISSING - needs to be created", 
        "Website_Insights": "MISSING - needs to be created",
        "Delivery_Method": "MISSING - needs to be created"
    }
    
    print("✅ Direct Matches:")
    direct_matches = [(k, v) for k, v in field_mapping.items() if v in existing_fields]
    for expected, existing in direct_matches:
        print(f"   {expected} → {existing}")
    
    print(f"\n🔄 Fields That Can Be Mapped:")
    mappable = [(k, v) for k, v in field_mapping.items() if v in existing_fields and k != v]
    for expected, existing in mappable:
        print(f"   {expected} → {existing}")
    
    print(f"\n❌ Missing Fields:")
    missing = [(k, v) for k, v in field_mapping.items() if "MISSING" in v]
    for expected, note in missing:
        print(f"   {expected}: {note}")
    
    print(f"\n💡 Recommended Actions:")
    print("1. Update code to use existing field names where possible")
    print("2. Create missing critical fields in Airtable")
    print("3. Use alternative fields where appropriate")
    
    return field_mapping

if __name__ == "__main__":
    mapping = main()