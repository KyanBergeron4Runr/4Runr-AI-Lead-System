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
    
    # Fields the code expects (updated to match actual Airtable schema)
    expected_fields = [
        "Engagement_Status",
        "Email_Confidence_Level", 
        "Level Engaged",
        "Company",
        "Job Title",
        "Email",
        "AI Message",
        "Date Messaged",
        "Website",
        "Company Description",
        "Top Services",
        "Website Insights",
        "Business_Type",
        "Follow_Up_Stage",
        "Response_Status"
    ]
    
    print("📋 Existing Airtable Fields:")
    for i, field in enumerate(existing_fields, 1):
        print(f"{i:2d}. {field}")
    
    print(f"\n🎯 Code Expected Fields:")
    for i, field in enumerate(expected_fields, 1):
        print(f"{i:2d}. {field}")
    
    print(f"\n🔗 Field Mapping Analysis:")
    print("-" * 50)
    
    # Create mapping (updated to match actual Airtable schema)
    field_mapping = {
        # Direct matches
        "Level Engaged": "Level Engaged",  # ✅ Exact match
        "Company": "Company",              # ✅ Exact match  
        "Email": "Email",                  # ✅ Exact match
        "Full Name": "Full Name",          # ✅ Exact match
        "LinkedIn URL": "LinkedIn URL",    # ✅ Exact match
        "Job Title": "Job Title",          # ✅ Exact match
        "AI Message": "AI Message",        # ✅ Exact match
        "Response Notes": "Response Notes", # ✅ Exact match
        "Date Scraped": "Date Scraped",    # ✅ Exact match
        "Date Enriched": "Date Enriched",  # ✅ Exact match
        "Date Messaged": "Date Messaged",  # ✅ Exact match
        "Website": "Website",              # ✅ Exact match
        "Business_Type": "Business_Type",  # ✅ Exact match
        "Follow_Up_Stage": "Follow_Up_Stage", # ✅ Exact match
        "Response_Status": "Response_Status", # ✅ Exact match
        "Engagement_Status": "Engagement_Status", # ✅ Exact match
        "Email_Confidence_Level": "Email_Confidence_Level", # ✅ Exact match
        
        # Fields that need space instead of underscore
        "Company Description": "Company Description",  # ✅ Correct spacing
        "Website Insights": "Website Insights",        # ✅ Correct spacing
        "Top Services": "Top Services",                # ✅ Correct spacing
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