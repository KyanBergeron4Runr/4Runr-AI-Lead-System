#!/usr/bin/env python3
"""
Demo script for the Campaign Delivery Service

Demonstrates the complete workflow from campaign generation to delivery queue processing.
"""

import sys
import os
import importlib.util
from datetime import datetime

# Direct imports to avoid dependency issues
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import required modules
simple_generator = import_module_from_path("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
campaign_injector = import_module_from_path("campaign_injector", "campaign_system/campaign_injector.py")

SimpleCampaignGenerator = simple_generator.SimpleCampaignGenerator
CampaignInjector = campaign_injector.CampaignInjector


def demo_complete_workflow():
    """Demonstrate the complete campaign workflow"""
    print("🚀 4Runr Multi-Step Email Campaign Delivery Demo")
    print("=" * 60)
    
    # Initialize components
    generator = SimpleCampaignGenerator()
    injector = CampaignInjector()
    
    # Sample leads for demonstration
    sample_leads = [
        {
            'lead_data': {
                'id': 'demo_001',
                'Name': 'Johannes Reck',
                'Company': 'trivago',
                'Job Title': 'CEO',
                'Email': 'johannes@trivago.com'
            },
            'company_data': {
                'company_description': 'trivago is a global hotel search platform that helps travelers find and compare hotel prices',
                'top_services': 'Hotel price comparison, Travel booking platform, Hotel search engine',
                'tone': 'Professional',
                'traits': ['enterprise', 'multi-language', 'search-based']
            }
        },
        {
            'lead_data': {
                'id': 'demo_002',
                'Name': 'Sarah Johnson',
                'Company': 'CloudTech',
                'Job Title': 'VP of Product',
                'Email': 'sarah@cloudtech.com'
            },
            'company_data': {
                'company_description': 'CloudTech provides SaaS solutions for enterprise workflow management',
                'top_services': 'Software as a Service, API integrations, Cloud platforms',
                'tone': 'Professional',
                'traits': ['enterprise', 'API-based', 'cloud-native']
            }
        }
    ]
    
    print(f"📧 Processing {len(sample_leads)} sample leads...\n")
    
    successful_campaigns = 0
    
    for i, lead_info in enumerate(sample_leads, 1):
        print(f"🎯 Lead {i}: {lead_info['lead_data']['Name']} at {lead_info['lead_data']['Company']}")
        
        # Step 1: Generate campaign
        print("  📝 Generating campaign...")
        campaign_data = generator.generate_campaign(
            lead_info['lead_data'],
            lead_info['company_data']
        )
        
        quality_score = campaign_data.get('overall_quality_score', 0)
        ready_to_send = campaign_data.get('ready_to_send', False)
        
        print(f"  📊 Quality Score: {quality_score}/100")
        print(f"  🎯 Ready to Send: {'✅' if ready_to_send else '❌'}")
        
        if ready_to_send:
            # Step 2: Inject into delivery system
            print("  📥 Injecting into delivery system...")
            
            injection_success = injector.inject_campaign(campaign_data, lead_info['lead_data'])
            
            if injection_success:
                print("  ✅ Campaign injected successfully")
                successful_campaigns += 1
                
                # Show message preview
                messages = campaign_data.get('messages', [])
                for msg in messages:
                    msg_type = msg.get('type', 'unknown').upper()
                    subject = msg.get('subject', 'No subject')
                    print(f"    📨 {msg_type}: {subject}")
            else:
                print("  ❌ Failed to inject campaign")
        else:
            print("  ⚠️  Campaign not ready for delivery")
        
        print()
    
    # Show final statistics
    print("=" * 60)
    print("📊 Campaign Processing Summary")
    print(f"  Total leads processed: {len(sample_leads)}")
    print(f"  Successful campaigns: {successful_campaigns}")
    print(f"  Success rate: {(successful_campaigns/len(sample_leads)*100):.1f}%")
    
    # Get injection statistics
    print("\n📈 Injection Statistics:")
    stats = injector.get_injection_stats()
    
    if 'error' not in stats:
        print(f"  Total campaigns in system: {stats.get('total_campaigns', 0)}")
        
        by_status = stats.get('by_status', {})
        for status, count in by_status.items():
            print(f"  {status.title()}: {count}")
        
        quality_dist = stats.get('quality_distribution', {})
        if quality_dist:
            print(f"\n🏆 Quality Distribution:")
            for tier, count in quality_dist.items():
                print(f"  {tier}: {count}")
    
    return successful_campaigns > 0


def demo_message_examples():
    """Show examples of generated messages"""
    print("\n" + "=" * 60)
    print("📧 Sample Generated Messages")
    print("=" * 60)
    
    generator = SimpleCampaignGenerator()
    
    # Generate a sample campaign
    lead_data = {
        'id': 'sample_001',
        'Name': 'Johannes Reck',
        'Company': 'trivago',
        'Job Title': 'CEO',
        'Email': 'johannes@trivago.com'
    }
    
    company_data = {
        'company_description': 'trivago is a global hotel search platform that helps travelers find and compare hotel prices',
        'top_services': 'Hotel price comparison, Travel booking platform, Hotel search engine',
        'tone': 'Professional',
        'traits': ['enterprise', 'multi-language', 'search-based']
    }
    
    campaign_data = generator.generate_campaign(lead_data, company_data)
    messages = campaign_data.get('messages', [])
    
    for i, message in enumerate(messages):
        msg_type = message.get('type', 'unknown').upper()
        subject = message.get('subject', 'No subject')
        body = message.get('body', 'No body')
        day = [0, 3, 7][i] if i < 3 else i
        
        print(f"\n📨 {msg_type} MESSAGE (Day {day}):")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("-" * 40)


def demo_delivery_queue_status():
    """Show delivery queue status"""
    print("\n" + "=" * 60)
    print("📬 Delivery Queue Status")
    print("=" * 60)
    
    try:
        # Import queue manager
        queue_manager = import_module_from_path("queue_manager", "campaign_system/queue_manager/queue_manager.py")
        MessageQueueManager = queue_manager.MessageQueueManager
        
        queue_mgr = MessageQueueManager()
        
        # Get queue statistics
        stats = queue_mgr.get_queue_stats()
        
        print(f"📊 Queue Overview:")
        print(f"  Total messages: {stats.get('total_messages', 0)}")
        print(f"  Ready for delivery: {stats.get('ready_for_delivery', 0)}")
        
        if stats.get('by_status'):
            print(f"\n📋 Messages by Status:")
            for status, count in stats['by_status'].items():
                print(f"  {status.title()}: {count}")
        
        # Show scheduling info
        earliest = stats.get('earliest_scheduled')
        latest = stats.get('latest_scheduled')
        
        if earliest:
            print(f"\n⏰ Scheduling Info:")
            print(f"  Earliest scheduled: {earliest.strftime('%Y-%m-%d %H:%M:%S')}")
            if latest:
                print(f"  Latest scheduled: {latest.strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"❌ Error getting queue status: {e}")


def main():
    """Run the complete demo"""
    try:
        # Demo 1: Complete workflow
        workflow_success = demo_complete_workflow()
        
        # Demo 2: Message examples
        demo_message_examples()
        
        # Demo 3: Queue status
        demo_delivery_queue_status()
        
        print("\n" + "=" * 60)
        print("🎉 Demo Complete!")
        
        if workflow_success:
            print("\n✅ The delivery system is working correctly!")
            print("\n🚀 Next Steps:")
            print("  1. Run 'python send_from_queue.py --status' to check queue status")
            print("  2. Run 'python send_from_queue.py --dry-run' to simulate delivery")
            print("  3. Run 'python send_from_queue.py' to process actual deliveries")
        else:
            print("\n⚠️  Some issues were encountered during the demo")
        
        return workflow_success
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)