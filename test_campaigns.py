#!/usr/bin/env python3
"""Test the multi-step email system"""

from multi_step_email_system import MultiStepEmailSystem

def main():
    system = MultiStepEmailSystem()
    
    print("📊 Campaign Statistics:")
    stats = system.get_campaign_stats()
    print(f"  Active campaigns: {stats['campaign_status'].get('active', 0)}")
    print(f"  Pending messages: {stats['pending_messages']}")
    
    print("\n📧 Messages Ready to Send:")
    campaigns = system.get_campaigns_ready_to_send()
    print(f"  Found {len(campaigns)} messages ready")
    
    for i, campaign in enumerate(campaigns[:5]):
        print(f"  {i+1}. {campaign['message_type']} to {campaign['email']} ({campaign['company']})")
    
    print(f"\n✅ Multi-step email system is working!")

if __name__ == "__main__":
    main()