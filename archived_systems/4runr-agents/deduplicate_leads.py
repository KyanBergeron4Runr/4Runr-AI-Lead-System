#!/usr/bin/env python3
"""
Deduplicate leads in enriched_leads.json
"""

import json
from pathlib import Path
from datetime import datetime

def deduplicate_leads():
    """Remove duplicate leads from enriched_leads.json"""
    shared_dir = Path(__file__).parent / "shared"
    enriched_file = shared_dir / "enriched_leads.json"
    
    if not enriched_file.exists():
        print("❌ enriched_leads.json not found")
        return
    
    try:
        with open(enriched_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        print(f"📋 Original leads: {len(leads)}")
        
        # Deduplicate based on LinkedIn URL or name+company
        seen = set()
        unique_leads = []
        
        for lead in leads:
            # Create unique identifier
            linkedin_url = lead.get('linkedin_url', '')
            name = lead.get('name') or lead.get('full_name', '')
            company = lead.get('company', '')
            
            if linkedin_url:
                identifier = linkedin_url
            else:
                identifier = f"{name}|{company}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_leads.append(lead)
            else:
                print(f"   🗑️ Duplicate: {name} at {company}")
        
        print(f"✅ Unique leads: {len(unique_leads)}")
        
        if len(unique_leads) < len(leads):
            # Create backup
            backup_file = shared_dir / f"enriched_leads.json.backup_dedup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            
            # Save deduplicated leads
            with open(enriched_file, 'w', encoding='utf-8') as f:
                json.dump(unique_leads, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(unique_leads)} unique leads")
            print(f"📁 Backup: {backup_file.name}")
        else:
            print("✅ No duplicates found")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    deduplicate_leads()