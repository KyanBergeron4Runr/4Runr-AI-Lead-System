#!/usr/bin/env python3
"""
View All Decision Logs

This script shows all the decision logs and explanations from the 4Runr system
in a comprehensive, easy-to-read format.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n📋 {title}")
    print("-" * 60)

def view_website_scraper_logs():
    """View website scraper decision logs"""
    print_header("WEBSITE SCRAPER DECISION LOGS")
    
    scraper_results_file = Path("shared/website_scraping_test_results.json")
    
    if scraper_results_file.exists():
        with open(scraper_results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        for i, result in enumerate(results, 1):
            print_section(f"Lead {i}: {result.get('name', 'Unknown')} - {result.get('company', 'Unknown')}")
            
            website_data = result.get('website_data', {})
            
            # Basic scraping info
            print(f"🌐 Scrape Timestamp: {website_data.get('scrape_timestamp', 'N/A')}")
            print(f"✅ Successful URLs: {', '.join(website_data.get('successful_urls', []))}")
            print(f"❌ Failed URLs: {', '.join(website_data.get('failed_urls', []))}")
            print(f"📊 Data Quality Score: {website_data.get('data_quality_score', 0)}/100")
            
            # Consolidated data
            consolidated = website_data.get('consolidated_data', {})
            print(f"📝 Company Description: {len(consolidated.get('company_description', ''))} characters")
            print(f"🛠️ Services Found: {len(consolidated.get('top_services', []))}")
            print(f"🎭 Website Tone: {consolidated.get('tone', 'unknown')}")
            print(f"📧 Contact Emails: {len(consolidated.get('contact_emails', []))}")
            
            # Decision log summary
            decision_log = website_data.get('decision_log', [])
            if decision_log:
                print(f"\n🔍 Key Decisions Made ({len(decision_log)} total):")
                key_decisions = [d for d in decision_log if d['decision_type'] in 
                               ['scrape_start', 'base_url_success', 'content_extraction', 'quality_assessment', 'scrape_complete']]
                
                for decision in key_decisions[-5:]:  # Show last 5 key decisions
                    print(f"   • {decision['decision_type'].replace('_', ' ').title()}: {decision['details']}")
    else:
        print("❌ No website scraper logs found")

def view_enrichment_logs():
    """View enrichment decision logs"""
    print_header("ENRICHMENT DECISION LOGS")
    
    enrichment_log_file = Path("shared/enrichment_decisions.json")
    
    if enrichment_log_file.exists():
        with open(enrichment_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        # Group by lead name
        leads = {}
        for log in logs:
            lead_name = log.get('lead_name', 'Unknown')
            if lead_name not in leads:
                leads[lead_name] = []
            leads[lead_name].append(log)
        
        for lead_name, lead_logs in leads.items():
            print_section(f"Lead: {lead_name}")
            
            # Show key decision types
            key_decisions = [
                'enrichment_start', 'website_scraping_success', 'email_enrichment_success',
                'email_confidence_determined', 'engagement_status_determined', 'airtable_sync_success'
            ]
            
            for decision_type in key_decisions:
                matching_logs = [log for log in lead_logs if log['decision_type'] == decision_type]
                for log in matching_logs:
                    timestamp = log['timestamp'][:19].replace('T', ' ')
                    print(f"   🕐 {timestamp} | {decision_type.replace('_', ' ').title()}")
                    print(f"      💬 {log['details']}")
                    
                    # Show additional data if available
                    if log.get('data'):
                        data = log['data']
                        if 'data_quality_score' in data:
                            print(f"      📊 Data Quality: {data['data_quality_score']}/100")
                        if 'email_found' in data:
                            print(f"      📧 Email Found: {data['email_found']}")
                        if 'confidence_level' in data:
                            print(f"      🎯 Confidence: {data['confidence_level']}")
                    print()
    else:
        print("❌ No enrichment logs found")

def view_airtable_logs():
    """View Airtable sync decision logs"""
    print_header("AIRTABLE SYNC DECISION LOGS")
    
    airtable_log_file = Path("shared/airtable_sync_log.json")
    
    if airtable_log_file.exists():
        with open(airtable_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        # Group by lead name
        leads = {}
        for log in logs:
            lead_name = log.get('lead_name', 'Unknown')
            if lead_name not in leads:
                leads[lead_name] = []
            leads[lead_name].append(log)
        
        for lead_name, lead_logs in leads.items():
            print_section(f"Lead: {lead_name}")
            
            # Show sync process
            for log in lead_logs:
                timestamp = log['timestamp'][:19].replace('T', ' ')
                decision_type = log['decision_type'].replace('_', ' ').title()
                
                # Add emoji based on decision type
                emoji = "🔄"
                if "success" in log['decision_type']:
                    emoji = "✅"
                elif "error" in log['decision_type'] or "failed" in log['decision_type']:
                    emoji = "❌"
                elif "start" in log['decision_type']:
                    emoji = "🚀"
                
                print(f"   🕐 {timestamp} | {emoji} {decision_type}")
                print(f"      💬 {log['details']}")
                
                # Show additional data
                if log.get('data'):
                    data = log['data']
                    if 'fields_count' in data:
                        print(f"      📊 Fields Synced: {data['fields_count']}")
                    if 'record_id' in data:
                        print(f"      🆔 Record ID: {data['record_id']}")
                print()
    else:
        print("❌ No Airtable sync logs found")

def view_campaign_brain_logs():
    """View Campaign Brain decision logs"""
    print_header("CAMPAIGN BRAIN DECISION LOGS")
    
    campaigns_dir = Path("../4runr-brain/linkedin_campaigns")
    
    if campaigns_dir.exists():
        campaign_files = list(campaigns_dir.glob("*.json"))
        
        # Show recent campaigns
        recent_campaigns = sorted(campaign_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        
        for campaign_file in recent_campaigns:
            with open(campaign_file, 'r', encoding='utf-8') as f:
                campaign = json.load(f)
            
            lead_data = campaign.get('lead_data', {})
            metadata = campaign.get('campaign_metadata', {})
            
            print_section(f"Campaign: {lead_data.get('name', 'Unknown')} - {lead_data.get('company', 'Unknown')}")
            
            print(f"🕐 Created: {campaign.get('created_at', 'N/A')}")
            print(f"🎯 Traits Detected: {', '.join(metadata.get('traits', []))}")
            print(f"📐 Messaging Angle: {metadata.get('messaging_angle', 'N/A')}")
            print(f"🎭 Campaign Tone: {metadata.get('campaign_tone', 'N/A')}")
            print(f"📊 Quality Score: {metadata.get('overall_quality_score', 0):.1f}/100")
            
            # Show Airtable updates (this contains decision reasoning)
            airtable_updates = campaign.get('airtable_updates', {})
            if 'Extra Info' in airtable_updates:
                print(f"🔍 Decision Summary: {airtable_updates['Extra Info']}")
            
            # Show message preview
            ai_message = airtable_updates.get('AI Message', '')
            if ai_message:
                # Extract just the first message (BOLD_HOOK)
                if 'BOLD_HOOK:' in ai_message:
                    hook_message = ai_message.split('OUTCOME_PROOF:')[0].replace('BOLD_HOOK:', '').strip()
                    print(f"💬 Generated Message Preview:")
                    print(f"   {hook_message[:200]}...")
            print()
    else:
        print("❌ No Campaign Brain logs found")

def view_system_test_results():
    """View system test results"""
    print_header("SYSTEM TEST RESULTS")
    
    test_results_file = Path("shared/enhanced_system_test_summary.json")
    
    if test_results_file.exists():
        with open(test_results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"🕐 Test Timestamp: {results.get('test_timestamp', 'N/A')}")
        
        # Website scraping results
        website_results = results.get('website_scraping', {})
        print_section("Website Scraping Performance")
        print(f"   📊 Leads Tested: {website_results.get('leads_tested', 0)}")
        print(f"   ✅ Successful Scrapes: {website_results.get('successful_scrapes', 0)}")
        print(f"   📈 Average Quality Score: {website_results.get('average_quality_score', 0):.1f}/100")
        print(f"   📝 Leads with Descriptions: {website_results.get('leads_with_descriptions', 0)}")
        print(f"   🛠️ Leads with Services: {website_results.get('leads_with_services', 0)}")
        
        # Airtable sync results
        airtable_results = results.get('airtable_sync', {})
        print_section("Airtable Sync Performance")
        print(f"   📊 Total Leads: {airtable_results.get('total_leads', 0)}")
        print(f"   ✅ Successful Syncs: {airtable_results.get('successful_syncs', 0)}")
        print(f"   ❌ Failed Syncs: {airtable_results.get('failed_syncs', 0)}")
        print(f"   📈 Success Rate: {airtable_results.get('success_rate', 0):.1f}%")
        
        # Overall success
        overall_success = results.get('overall_success', False)
        print_section("Overall System Status")
        print(f"   🎯 System Status: {'✅ OPERATIONAL' if overall_success else '❌ ISSUES DETECTED'}")
    else:
        print("❌ No system test results found")

def main():
    """Main function to display all logs"""
    print("🔍 4Runr System Decision Logs & Analysis")
    print("=" * 80)
    print("This report shows all decision logs and explanations from the 4Runr system")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # View all log types
    view_website_scraper_logs()
    view_enrichment_logs()
    view_airtable_logs()
    view_campaign_brain_logs()
    view_system_test_results()
    
    print_header("SUMMARY")
    print("📊 All decision logs have been displayed above")
    print("🔍 Each system component provides detailed reasoning for its decisions")
    print("📝 Logs are automatically generated and stored for analysis")
    print("🎯 Use these logs to understand exactly how the system processes each lead")
    
    print("\n📁 Log File Locations:")
    print("   • Website Scraper: shared/website_scraping_test_results.json")
    print("   • Enrichment: shared/enrichment_decisions.json")
    print("   • Airtable Sync: shared/airtable_sync_log.json")
    print("   • Campaign Brain: ../4runr-brain/linkedin_campaigns/*.json")
    print("   • System Tests: shared/enhanced_system_test_summary.json")

if __name__ == "__main__":
    main()