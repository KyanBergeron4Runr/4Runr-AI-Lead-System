#!/usr/bin/env python3
"""
Analyze and clean up lead files
"""

import json
import os
from pathlib import Path
from datetime import datetime

def analyze_lead_file(file_path):
    """Analyze a lead file"""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        
        print(f"\n📋 {file_path.name}")
        print(f"   Total leads: {len(leads)}")
        
        if leads:
            # Show sample leads
            print("   Sample leads:")
            for i, lead in enumerate(leads[:5]):
                name = lead.get('name') or lead.get('full_name', 'Unknown')
                company = lead.get('company', 'No company')
                scraped_at = lead.get('scraped_at', 'Unknown date')
                print(f"   {i+1}. {name} at {company} (scraped: {scraped_at[:10]})")
            
            # Check dates
            recent_leads = []
            old_leads = []
            
            for lead in leads:
                scraped_at = lead.get('scraped_at', '')
                if '2025-07-31' in scraped_at:  # Today's leads
                    recent_leads.append(lead)
                else:
                    old_leads.append(lead)
            
            print(f"   📅 Recent leads (today): {len(recent_leads)}")
            print(f"   📅 Old leads: {len(old_leads)}")
            
            return {
                'total': len(leads),
                'recent': len(recent_leads),
                'old': len(old_leads),
                'recent_leads': recent_leads,
                'old_leads': old_leads
            }
    
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {str(e)}")
        return None

def main():
    """Main function"""
    shared_dir = Path(__file__).parent / "shared"
    
    lead_files = [
        'raw_leads.json',
        'enriched_leads.json', 
        'custom_enriched_leads.json',
        'scraped_leads.json',
        'processed_leads.json',
        'verified_leads.json'
    ]
    
    print("🔍 Analyzing lead files...")
    
    analysis = {}
    
    for filename in lead_files:
        file_path = shared_dir / filename
        result = analyze_lead_file(file_path)
        if result:
            analysis[filename] = result
    
    # Summary
    print(f"\n📊 SUMMARY:")
    total_all = sum(data['total'] for data in analysis.values())
    total_recent = sum(data['recent'] for data in analysis.values())
    total_old = sum(data['old'] for data in analysis.values())
    
    print(f"   Total leads across all files: {total_all}")
    print(f"   Recent leads (today): {total_recent}")
    print(f"   Old leads: {total_old}")
    
    # Ask if user wants to clean up
    print(f"\n🧹 CLEANUP RECOMMENDATION:")
    if total_old > 0:
        print(f"   You have {total_old} old leads that could be cleaned up")
        print(f"   This would leave you with {total_recent} fresh leads from today")
        
        response = input("\n   Do you want to clean up old leads? (y/n): ")
        if response.lower() == 'y':
            cleanup_old_leads(analysis, shared_dir)
    else:
        print("   No old leads found - system is clean!")

def cleanup_old_leads(analysis, shared_dir):
    """Clean up old leads, keeping only recent ones"""
    print("\n🧹 Cleaning up old leads...")
    
    for filename, data in analysis.items():
        if data['old'] > 0:
            file_path = shared_dir / filename
            
            # Backup original file
            backup_path = shared_dir / f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                # Create backup
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_data = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_data)
                
                # Write only recent leads
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data['recent_leads'], f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ {filename}: {data['total']} → {data['recent']} leads (backup: {backup_path.name})")
                
            except Exception as e:
                print(f"   ❌ Error cleaning {filename}: {str(e)}")
    
    print("\n✅ Cleanup completed!")

if __name__ == "__main__":
    main()