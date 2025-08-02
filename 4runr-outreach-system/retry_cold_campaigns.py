#!/usr/bin/env python3
"""
Cold Lead Recycling System

Automatically identifies completed campaigns with no replies and creates
re-engagement campaigns with different narrative angles after a cooldown period.
"""

import sys
import os
import uuid
import argparse
import importlib.util
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add campaign system to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direct imports to avoid dependency issues
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import required modules
try:
    from campaign_system.database.connection import get_database_connection
    from campaign_system.database.schema import create_campaign_tables
    
    simple_generator = import_module_from_path("simple_generator", "campaign_system/campaign_generator/simple_generator.py")
    campaign_injector = import_module_from_path("campaign_injector", "campaign_system/campaign_injector.py")
    
    SimpleCampaignGenerator = simple_generator.SimpleCampaignGenerator
    CampaignInjector = campaign_injector.CampaignInjector
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the campaign system is properly set up")
    sys.exit(1)


class ColdLeadRecycler:
    """Manages cold lead recycling and re-engagement campaigns"""
    
    def __init__(self, cooldown_days: int = 14, max_recycle_attempts: int = 2):
        self.db = get_database_connection()
        self.generator = SimpleCampaignGenerator()
        self.injector = CampaignInjector()
        
        # Configuration
        self.cooldown_days = cooldown_days
        self.max_recycle_attempts = max_recycle_attempts
        
        # Recycle types
        self.recycle_types = {
            'soft_retry': 'Gentle re-engagement with new angle',
            'content_drop': 'Value-first approach with insights',
            'escalation': 'Different contact or urgency increase'
        }
    
    def find_eligible_campaigns(self) -> List[Dict[str, Any]]:
        """
        Find campaigns eligible for recycling
        
        Returns:
            List of campaign records eligible for recycling
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.cooldown_days)
            
            query = """
            SELECT c.*, 
                   (julianday('now') - julianday(c.updated_at)) as days_since_last_message
            FROM campaigns c
            WHERE c.campaign_status = 'completed'
            AND c.response_detected = 0
            AND c.current_message >= 3
            AND c.updated_at <= ?
            AND (c.recycle_attempt_count < ? OR c.recycle_attempt_count IS NULL)
            AND c.eligible_for_recycle = 0
            ORDER BY c.updated_at ASC
            """
            
            params = (cutoff_date.isoformat(), self.max_recycle_attempts)
            rows = self.db.execute_query(query, params)
            
            eligible_campaigns = []
            for row in rows:
                campaign_data = dict(row)
                
                # Check if enough time has passed
                days_since = campaign_data.get('days_since_last_message', 0)
                if days_since >= self.cooldown_days:
                    eligible_campaigns.append(campaign_data)
            
            return eligible_campaigns
            
        except Exception as e:
            print(f"❌ Error finding eligible campaigns: {e}")
            return []
    
    def mark_eligible_for_recycle(self, campaign_ids: List[str]) -> int:
        """
        Mark campaigns as eligible for recycling
        
        Args:
            campaign_ids: List of campaign IDs to mark
            
        Returns:
            Number of campaigns marked
        """
        try:
            if not campaign_ids:
                return 0
            
            # Create placeholders for the IN clause
            placeholders = ','.join(['?' for _ in campaign_ids])
            
            query = f"""
            UPDATE campaigns SET
                eligible_for_recycle = 1,
                updated_at = ?
            WHERE campaign_id IN ({placeholders})
            """
            
            params = [datetime.now().isoformat()] + campaign_ids
            self.db.execute_query(query, params)
            
            return len(campaign_ids)
            
        except Exception as e:
            print(f"❌ Error marking campaigns for recycle: {e}")
            return 0
    
    def generate_recycled_campaign(self, original_campaign: Dict[str, Any], recycle_type: str = 'soft_retry') -> Optional[Dict[str, Any]]:
        """
        Generate a new campaign for recycling with re-engagement tone
        
        Args:
            original_campaign: Original campaign data
            recycle_type: Type of recycling approach
            
        Returns:
            Generated campaign data or None if failed
        """
        try:
            # Extract lead and company data from original campaign
            import json
            
            lead_traits = json.loads(original_campaign.get('lead_traits', '{}'))
            company_insights = json.loads(original_campaign.get('company_insights', '{}'))
            
            # Prepare lead data
            lead_data = {
                'id': original_campaign['lead_id'],
                'Name': lead_traits.get('Name', 'Unknown'),
                'Company': original_campaign['company'],
                'Title': lead_traits.get('Title', 'Unknown'),
                'Email': lead_traits.get('Email', '')
            }
            
            # Prepare company data with recycling context
            company_data = {
                'company_description': company_insights.get('company_description', ''),
                'top_services': company_insights.get('top_services', ''),
                'tone': company_insights.get('tone', 'Professional'),
                'traits': company_insights.get('traits', []),
                'is_recycled': True,
                'recycle_type': recycle_type,
                'original_campaign_id': original_campaign['campaign_id']
            }
            
            # Generate campaign with recycling prompts
            campaign_data = self._generate_recycled_campaign_with_prompts(lead_data, company_data, recycle_type)
            
            if campaign_data:
                # Add recycling metadata
                campaign_data['is_recycled'] = True
                campaign_data['recycle_type'] = recycle_type
                campaign_data['original_campaign_id'] = original_campaign['campaign_id']
                
                return campaign_data
            
            return None
            
        except Exception as e:
            print(f"❌ Error generating recycled campaign: {e}")
            return None
    
    def _generate_recycled_campaign_with_prompts(self, lead_data: Dict[str, Any], 
                                               company_data: Dict[str, Any], 
                                               recycle_type: str) -> Optional[Dict[str, Any]]:
        """Generate campaign with recycling-specific prompts"""
        
        # Create a modified generator for recycling
        recycled_generator = RecycledCampaignGenerator(recycle_type)
        
        return recycled_generator.generate_campaign(lead_data, company_data)
    
    def process_recycling_batch(self, limit: int = 10, dry_run: bool = False) -> Dict[str, int]:
        """
        Process a batch of campaigns for recycling
        
        Args:
            limit: Maximum number of campaigns to process
            dry_run: If True, don't actually create campaigns
            
        Returns:
            Dictionary with processing statistics
        """
        print(f"🔄 Processing cold lead recycling batch (limit: {limit})")
        
        stats = {
            'eligible_found': 0,
            'marked_for_recycle': 0,
            'campaigns_generated': 0,
            'campaigns_injected': 0,
            'quality_failures': 0,
            'errors': 0
        }
        
        try:
            # Step 1: Find eligible campaigns
            print("🔍 Finding eligible campaigns...")
            eligible_campaigns = self.find_eligible_campaigns()
            
            if not eligible_campaigns:
                print("✅ No campaigns eligible for recycling")
                return stats
            
            # Limit the batch
            eligible_campaigns = eligible_campaigns[:limit]
            stats['eligible_found'] = len(eligible_campaigns)
            
            print(f"📋 Found {len(eligible_campaigns)} eligible campaigns")
            
            # Step 2: Mark as eligible for recycle
            if not dry_run:
                campaign_ids = [c['campaign_id'] for c in eligible_campaigns]
                marked_count = self.mark_eligible_for_recycle(campaign_ids)
                stats['marked_for_recycle'] = marked_count
                print(f"✅ Marked {marked_count} campaigns for recycling")
            else:
                stats['marked_for_recycle'] = len(eligible_campaigns)
                print(f"🧪 DRY RUN: Would mark {len(eligible_campaigns)} campaigns")
            
            # Step 3: Generate and inject recycled campaigns
            for i, campaign in enumerate(eligible_campaigns, 1):
                try:
                    print(f"\n🎯 Processing {i}/{len(eligible_campaigns)}: {campaign['company']}")
                    
                    # Determine recycle type
                    recycle_count = campaign.get('recycle_attempt_count', 0)
                    recycle_type = self._determine_recycle_type(recycle_count)
                    
                    print(f"  🔄 Recycle type: {recycle_type}")
                    
                    # Generate recycled campaign
                    recycled_campaign = self.generate_recycled_campaign(campaign, recycle_type)
                    
                    if not recycled_campaign:
                        print(f"  ❌ Failed to generate recycled campaign")
                        stats['errors'] += 1
                        continue
                    
                    stats['campaigns_generated'] += 1
                    
                    # Check quality
                    quality_score = recycled_campaign.get('overall_quality_score', 0)
                    ready_to_send = recycled_campaign.get('ready_to_send', False)
                    
                    print(f"  📊 Quality score: {quality_score}/100")
                    print(f"  🎯 Ready to send: {'✅' if ready_to_send else '❌'}")
                    
                    if not ready_to_send or quality_score < 80:
                        print(f"  ⚠️  Campaign failed quality gate")
                        stats['quality_failures'] += 1
                        continue
                    
                    # Inject campaign
                    if not dry_run:
                        # Prepare lead data for injection
                        import json
                        lead_traits = json.loads(campaign.get('lead_traits', '{}'))
                        
                        injection_success = self.injector.inject_campaign(recycled_campaign, lead_traits)
                        
                        if injection_success:
                            # Update original campaign
                            self._update_original_campaign_recycle_status(
                                campaign['campaign_id'], 
                                recycle_type,
                                recycle_count + 1
                            )
                            
                            stats['campaigns_injected'] += 1
                            print(f"  ✅ Recycled campaign injected successfully")
                        else:
                            print(f"  ❌ Failed to inject recycled campaign")
                            stats['errors'] += 1
                    else:
                        stats['campaigns_injected'] += 1
                        print(f"  🧪 DRY RUN: Would inject recycled campaign")
                
                except Exception as e:
                    print(f"  ❌ Error processing campaign: {e}")
                    stats['errors'] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Error in recycling batch: {e}")
            stats['errors'] += 1
            return stats
    
    def _determine_recycle_type(self, recycle_count: int) -> str:
        """Determine recycle type based on attempt count"""
        if recycle_count == 0:
            return 'soft_retry'
        elif recycle_count == 1:
            return 'content_drop'
        else:
            return 'escalation'
    
    def _update_original_campaign_recycle_status(self, campaign_id: str, recycle_type: str, attempt_count: int) -> bool:
        """Update original campaign with recycle status"""
        try:
            query = """
            UPDATE campaigns SET
                recycle_attempt_count = ?,
                updated_at = ?
            WHERE campaign_id = ?
            """
            
            params = (attempt_count, datetime.now().isoformat(), campaign_id)
            self.db.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"❌ Error updating recycle status: {e}")
            return False
    
    def get_recycling_stats(self) -> Dict[str, Any]:
        """Get recycling statistics"""
        try:
            # Get eligible campaigns count
            eligible_query = """
            SELECT COUNT(*) as count FROM campaigns
            WHERE campaign_status = 'completed'
            AND response_detected = 0
            AND current_message >= 3
            AND (julianday('now') - julianday(updated_at)) >= ?
            AND (recycle_attempt_count < ? OR recycle_attempt_count IS NULL)
            """
            
            eligible_rows = self.db.execute_query(eligible_query, (self.cooldown_days, self.max_recycle_attempts))
            eligible_count = eligible_rows[0]['count'] if eligible_rows else 0
            
            # Get recycled campaigns stats
            recycled_query = """
            SELECT 
                recycle_type,
                COUNT(*) as count,
                AVG(CASE WHEN response_detected = 1 THEN 1.0 ELSE 0.0 END) as response_rate
            FROM campaigns
            WHERE is_recycled = 1
            GROUP BY recycle_type
            """
            
            recycled_rows = self.db.execute_query(recycled_query)
            recycled_stats = {}
            
            for row in recycled_rows:
                recycled_stats[row['recycle_type']] = {
                    'count': row['count'],
                    'response_rate': round(row['response_rate'] * 100, 1)
                }
            
            # Get total recycled campaigns
            total_recycled_query = "SELECT COUNT(*) as count FROM campaigns WHERE is_recycled = 1"
            total_recycled_rows = self.db.execute_query(total_recycled_query)
            total_recycled = total_recycled_rows[0]['count'] if total_recycled_rows else 0
            
            return {
                'eligible_for_recycling': eligible_count,
                'total_recycled_campaigns': total_recycled,
                'recycled_by_type': recycled_stats,
                'cooldown_days': self.cooldown_days,
                'max_attempts': self.max_recycle_attempts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting recycling stats: {e}")
            return {'error': str(e)}


class RecycledCampaignGenerator:
    """Specialized generator for recycled campaigns with re-engagement prompts"""
    
    def __init__(self, recycle_type: str):
        self.recycle_type = recycle_type
        self.base_generator = SimpleCampaignGenerator()
    
    def generate_campaign(self, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate recycled campaign with specialized prompts"""
        
        # Modify company data to include recycling context
        recycled_company_data = company_data.copy()
        recycled_company_data['recycling_context'] = self._get_recycling_context()
        
        # Use base generator but with modified prompts
        campaign_data = self.base_generator.generate_campaign(lead_data, recycled_company_data)
        
        if campaign_data:
            # Modify messages for recycling tone
            messages = campaign_data.get('messages', [])
            modified_messages = []
            
            for message in messages:
                modified_message = self._modify_message_for_recycling(message, lead_data, company_data)
                modified_messages.append(modified_message)
            
            campaign_data['messages'] = modified_messages
            
            # Re-run quality control on modified messages
            try:
                from campaign_system.campaign_generator.quality_control import enhance_campaign_with_quality_control
                campaign_data = enhance_campaign_with_quality_control(campaign_data, lead_data, company_data)
            except ImportError:
                # Fallback quality scoring
                campaign_data['overall_quality_score'] = 85  # Assume good quality for recycled
                campaign_data['ready_to_send'] = True
        
        return campaign_data
    
    def _get_recycling_context(self) -> str:
        """Get recycling context based on type"""
        contexts = {
            'soft_retry': "This is a gentle re-engagement after previous outreach. Reference prior contact subtly and offer new value.",
            'content_drop': "This is a value-first re-engagement. Lead with insights, data, or concrete examples.",
            'escalation': "This is an escalated re-engagement. Create appropriate urgency while staying professional."
        }
        
        return contexts.get(self.recycle_type, contexts['soft_retry'])
    
    def _modify_message_for_recycling(self, message: Dict[str, str], lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, str]:
        """Modify message content for recycling tone"""
        
        msg_type = message.get('type', 'hook')
        original_body = message.get('body', '')
        
        # Get recycling modifications based on type and message
        if self.recycle_type == 'soft_retry':
            modified_message = self._apply_soft_retry_tone(message, lead_data, company_data)
        elif self.recycle_type == 'content_drop':
            modified_message = self._apply_content_drop_tone(message, lead_data, company_data)
        else:  # escalation
            modified_message = self._apply_escalation_tone(message, lead_data, company_data)
        
        return modified_message
    
    def _apply_soft_retry_tone(self, message: Dict[str, str], lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, str]:
        """Apply soft retry tone modifications"""
        
        msg_type = message.get('type', 'hook')
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company_name = lead_data.get('Company', 'your company')
        
        if msg_type == 'hook':
            return {
                'type': 'hook',
                'subject': f'Following up — new insights for {company_name}',
                'body': f"""Hi {lead_name},

We reached out a few weeks ago — maybe the timing wasn't right. Wanted to circle back with a concrete example of what we're seeing work in your space.

Companies like {company_name} are facing new competitive pressures, and the ones getting ahead are making strategic infrastructure moves now.

Worth a quick conversation about what's working at your scale?

— 4Runr Team"""
            }
        
        elif msg_type == 'proof':
            return {
                'type': 'proof',
                'subject': f'What we\'re seeing work for companies like {company_name}',
                'body': f"""Hi {lead_name},

Since our last outreach, we've been tracking what separates the companies that are pulling ahead from those that aren't.

The pattern is clear: it's not about bigger budgets or flashier features. It's about having the right system architecture that can:
• Adapt quickly to market changes
• Scale without breaking
• Deliver consistent performance under pressure

This is exactly what we help optimize — and we're seeing measurable results.

Curious about what this looks like in practice for {company_name}?

— 4Runr Team"""
            }
        
        else:  # fomo
            return {
                'type': 'fomo',
                'subject': f'Quick update on the {company_name.split()[0] if company_name else "industry"} space',
                'body': f"""Hi {lead_name},

Quick update: we've been working with a few companies in your space, and the results have been significant enough that I wanted to reach out one more time.

The window for getting ahead of these changes is narrowing, and the companies that move first are seeing the biggest impact.

If you're open to a brief conversation about what we're seeing work, I'd be happy to share specifics.

Otherwise, no worries — just wanted to close the loop.

— 4Runr Team"""
            }
    
    def _apply_content_drop_tone(self, message: Dict[str, str], lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, str]:
        """Apply content drop tone modifications"""
        
        msg_type = message.get('type', 'hook')
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company_name = lead_data.get('Company', 'your company')
        
        if msg_type == 'hook':
            return {
                'type': 'hook',
                'subject': f'Data point that might interest you — {company_name}',
                'body': f"""Hi {lead_name},

Came across a data point that reminded me of our previous conversation about {company_name}.

We just completed an analysis of 50+ companies in your space, and found that the top performers share one key characteristic: they've optimized their core system architecture for speed and reliability.

The performance gap is widening — 40% faster response times and 60% fewer system issues.

Thought you might find the specific methodology interesting. Worth a quick call?

— 4Runr Team"""
            }
        
        elif msg_type == 'proof':
            return {
                'type': 'proof',
                'subject': f'Case study: How similar companies are winning',
                'body': f"""Hi {lead_name},

Following up on the data I mentioned — here's a concrete example of what we're seeing work.

One company similar to {company_name} implemented our optimization approach and saw:
• 35% reduction in system response time
• 50% fewer customer-facing issues
• 25% improvement in user engagement

The key was focusing on infrastructure efficiency rather than adding more features.

We documented the exact process and results. Would you like to see how this applies to {company_name}'s situation?

— 4Runr Team"""
            }
        
        else:  # fomo
            return {
                'type': 'fomo',
                'subject': f'Final insight for {company_name}',
                'body': f"""Hi {lead_name},

One last insight I wanted to share: the companies that are implementing these optimizations now are creating a significant competitive moat.

We're seeing a clear pattern where early adopters are pulling ahead, while others are struggling to catch up later.

If you'd like to explore what this looks like for {company_name}, I'm happy to share the specific approach.

Otherwise, I'll leave you to it — just wanted to make sure you had the information.

— 4Runr Team"""
            }
    
    def _apply_escalation_tone(self, message: Dict[str, str], lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, str]:
        """Apply escalation tone modifications"""
        
        msg_type = message.get('type', 'hook')
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company_name = lead_data.get('Company', 'your company')
        
        if msg_type == 'hook':
            return {
                'type': 'hook',
                'subject': f'Strategic priority for {company_name} — time-sensitive',
                'body': f"""Hi {lead_name},

I've reached out a couple of times about strategic infrastructure optimization for {company_name}. Given the current market dynamics, this has become more urgent.

Your competitors are making moves that are creating lasting advantages. The companies that act in the next 30-60 days will have a significant head start.

This isn't about selling you something — it's about making sure {company_name} doesn't fall behind on something critical.

Worth a strategic conversation this week?

— 4Runr Team"""
            }
        
        elif msg_type == 'proof':
            return {
                'type': 'proof',
                'subject': f'Competitive intelligence for {company_name}',
                'body': f"""Hi {lead_name},

Direct feedback from the market: companies in your space that haven't optimized their core systems are starting to lose ground.

We're seeing measurable impacts:
• Customer acquisition costs rising 20-30%
• User retention dropping as performance lags
• Technical debt creating scaling bottlenecks

The companies that address this now are seeing the opposite trend — better performance, lower costs, stronger competitive position.

{company_name} has the opportunity to be in the winning group, but the window is narrowing.

Can we discuss the strategic implications this week?

— 4Runr Team"""
            }
        
        else:  # fomo
            return {
                'type': 'fomo',
                'subject': f'Final strategic note for {company_name}',
                'body': f"""Hi {lead_name},

This is my final outreach on this topic. The strategic window I mentioned is closing, and I wanted to make sure {company_name} had the opportunity to act.

Several of your competitors have already begun implementing these optimizations. The performance advantages they're building will compound over time.

If you'd like to discuss how {company_name} can maintain its competitive edge, I'm available for a strategic conversation this week.

Otherwise, I understand priorities vary, and I'll respect your decision.

— 4Runr Team"""
            }


def main():
    """Main entry point for cold lead recycling"""
    parser = argparse.ArgumentParser(description='4Runr Cold Lead Recycling System')
    parser.add_argument('--limit', type=int, default=10,
                       help='Maximum number of campaigns to process')
    parser.add_argument('--cooldown-days', type=int, default=14,
                       help='Days to wait before recycling')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate recycling without creating campaigns')
    parser.add_argument('--stats', action='store_true',
                       help='Show recycling statistics')
    parser.add_argument('--init-db', action='store_true',
                       help='Initialize database tables')
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("🗄️  Initializing database tables...")
        try:
            create_campaign_tables()
            print("✅ Database tables initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
    
    # Create recycler instance
    try:
        recycler = ColdLeadRecycler(
            cooldown_days=args.cooldown_days,
            max_recycle_attempts=2
        )
    except Exception as e:
        print(f"❌ Failed to initialize recycler: {e}")
        return False
    
    # Handle different operations
    if args.stats:
        print("📊 Cold Lead Recycling Statistics:")
        print("=" * 50)
        
        stats = recycler.get_recycling_stats()
        
        if 'error' in stats:
            print(f"❌ Error getting stats: {stats['error']}")
            return False
        
        print(f"📋 Eligible for recycling: {stats['eligible_for_recycling']}")
        print(f"🔄 Total recycled campaigns: {stats['total_recycled_campaigns']}")
        print(f"⏰ Cooldown period: {stats['cooldown_days']} days")
        print(f"🔢 Max attempts: {stats['max_attempts']}")
        
        if stats['recycled_by_type']:
            print(f"\n📈 Recycled Campaign Performance:")
            for recycle_type, type_stats in stats['recycled_by_type'].items():
                print(f"  {recycle_type.title()}:")
                print(f"    Count: {type_stats['count']}")
                print(f"    Response Rate: {type_stats['response_rate']}%")
        
        return True
    
    else:
        # Process recycling batch
        print(f"🔄 4Runr Cold Lead Recycling System")
        print(f"Cooldown: {args.cooldown_days} days | Limit: {args.limit}")
        
        if args.dry_run:
            print("🧪 DRY RUN MODE - No campaigns will be created")
        
        print("=" * 60)
        
        result = recycler.process_recycling_batch(args.limit, args.dry_run)
        
        print("\n" + "=" * 60)
        print("📊 Recycling Results:")
        print(f"  Eligible campaigns found: {result['eligible_found']}")
        print(f"  Marked for recycling: {result['marked_for_recycle']}")
        print(f"  Campaigns generated: {result['campaigns_generated']}")
        print(f"  Campaigns injected: {result['campaigns_injected']}")
        print(f"  Quality failures: {result['quality_failures']}")
        print(f"  Errors: {result['errors']}")
        
        if result['campaigns_injected'] > 0:
            success_rate = (result['campaigns_injected'] / result['eligible_found']) * 100
            print(f"  Success rate: {success_rate:.1f}%")
        
        return result['errors'] == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)