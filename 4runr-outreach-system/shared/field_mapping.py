"""
Airtable Field Mapping Configuration

Maps the field names expected by the code to the actual field names in Airtable.
This allows the system to work with the existing Airtable structure while
maintaining code readability.
"""

# Mapping from code field names to actual Airtable field names
AIRTABLE_FIELD_MAPPING = {
    # Direct matches
    "Level Engaged": "Level Engaged",
    "Company": "Company", 
    "Email": "Email",
    
    # Mapped fields
    "Title": "Job Title",
    "Custom_Message": "AI Message",
    "Last_Contacted_Date": "Date Messaged",
    "Full_Name": "Full Name",
    
    # Fields that need alternatives until created
    "Engagement_Status": "Lead Quality",  # Temporary mapping
    "Email_Confidence_Level": "Source",   # Temporary mapping - could indicate confidence
    "Message_Preview": "AI Message",      # Use same as Custom_Message for now
    "company_website_url": "Extra info",  # Temporary storage
    "Company_Description": "Extra info",  # Temporary storage
    
    # Fields that don't exist yet - will need to be created
    "Top_Services": None,
    "Tone": None,
    "Website_Insights": None,
    "Delivery_Method": None
}

# Reverse mapping for easy lookup
FIELD_MAPPING_REVERSE = {v: k for k, v in AIRTABLE_FIELD_MAPPING.items() if v is not None}

def get_airtable_field_name(code_field_name: str) -> str:
    """
    Get the actual Airtable field name for a code field name.
    
    Args:
        code_field_name: The field name used in the code
        
    Returns:
        The actual field name in Airtable, or the original name if no mapping exists
    """
    return AIRTABLE_FIELD_MAPPING.get(code_field_name, code_field_name)

def get_code_field_name(airtable_field_name: str) -> str:
    """
    Get the code field name for an Airtable field name.
    
    Args:
        airtable_field_name: The actual field name in Airtable
        
    Returns:
        The field name used in the code, or the original name if no mapping exists
    """
    return FIELD_MAPPING_REVERSE.get(airtable_field_name, airtable_field_name)

def map_lead_data(airtable_record: dict) -> dict:
    """
    Map Airtable record fields to code field names.
    
    Args:
        airtable_record: Raw record from Airtable
        
    Returns:
        Record with field names mapped to code expectations
    """
    mapped_data = {}
    
    # Copy the record ID
    if 'id' in airtable_record:
        mapped_data['id'] = airtable_record['id']
    
    # Map the fields
    fields = airtable_record.get('fields', {})
    for airtable_field, value in fields.items():
        code_field = get_code_field_name(airtable_field)
        mapped_data[code_field] = value
    
    # Add default values for missing critical fields
    if 'Engagement_Status' not in mapped_data:
        # Determine engagement status based on available data
        if mapped_data.get('Replied') == 'Yes':
            mapped_data['Engagement_Status'] = 'Sent'
        elif mapped_data.get('AI Message'):
            mapped_data['Engagement_Status'] = 'Sent'
        else:
            mapped_data['Engagement_Status'] = 'Auto-Send'
    
    if 'Email_Confidence_Level' not in mapped_data:
        # Determine email confidence based on available data
        email = mapped_data.get('Email', '')
        if '@' in email and '.' in email:
            mapped_data['Email_Confidence_Level'] = 'Real'
        else:
            mapped_data['Email_Confidence_Level'] = 'Guess'
    
    return mapped_data

def create_airtable_update_fields(code_fields: dict) -> dict:
    """
    Map code field names to Airtable field names for updates.
    
    Args:
        code_fields: Dictionary with code field names as keys
        
    Returns:
        Dictionary with Airtable field names as keys
    """
    airtable_fields = {}
    
    for code_field, value in code_fields.items():
        airtable_field = get_airtable_field_name(code_field)
        if airtable_field is not None:  # Only include fields that exist
            airtable_fields[airtable_field] = value
    
    return airtable_fields