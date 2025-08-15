#!/usr/bin/env python3
"""
Simple Pipeline - Working Version

This script ties together all the working components of the 4Runr system:
1. Database operations
2. Airtable sync
3. AI message generation
4. Basic lead management

This is a simplified, working version that focuses on core functionality.
"""

import sys
import time
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lead_database import LeadDatabase
from simple_sync_manager import SimpleSyncManager
from message_generator.ai_generator import AIMessageGenerator
from shared.data_cleaner import DataCleaner


class SimplePipeline:
    """
    Simple pipeline that ties together working components.
    """
    
    def __init__(self, db_path: str = "data/leads_cache.db"):
        """Initialize the pipeline components."""
        self.db = LeadDatabase(db_path)
        self.sync_manager = SimpleSyncManager(db_path)
        self.message_generator = AIMessageGenerator()
        self.data_cleaner = DataCleaner()
        
        print("🚀 Simple Pipeline initialized")
        print(f"   Database: {db_path}")
        print(f"   Sync Manager: Ready")
        print(f"   AI Generator: Ready")
        print(f"   Data Cleaner: Ready")
    
    def add_lead(self, lead_data: Dict[str, Any]) -> str:
        """
        Add a new lead to the system.
        
        Args:
            lead_data: Lead information
            
        Returns:
            Lead ID
        """
        print(f"\n📝 Adding lead: {lead_data.get('full_name', 'Unknown')}")
        
        # Clean the data
        cleaning_result = self.data_cleaner.clean_and_validate(lead_data, {})
        cleaned_data = cleaning_result.cleaned_data if cleaning_result.success else lead_data
        
        # Add to database
        lead_id = self.db.add_lead(cleaned_data)
        
        if lead_id:
            print(f"   ✅ Added to database: {lead_id}")
            
            # Generate AI message
            try:
                message = self.message_generator.generate_message(cleaned_data)
                if message:
                    # Update lead with generated message
                    self.db.update_lead(lead_id, {
                        'ai_generated_message': message,
                        'message_generated_at': datetime.datetime.now().isoformat()
                    })
                    print(f"   🤖 AI message generated")
                else:
                    print(f"   ⚠️  AI message generation failed")
            except Exception as e:
                print(f"   ⚠️  AI message generation error: {e}")
            
            return lead_id
        else:
            print(f"   ❌ Failed to add lead")
            return None
    
    def sync_to_airtable(self, lead_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync leads to Airtable.
        
        Args:
            lead_ids: Specific lead IDs to sync (if None, sync all pending)
            
        Returns:
            Sync results
        """
        print(f"\n🔄 Syncing to Airtable...")
        
        results = self.sync_manager.sync_to_airtable(lead_ids)
        
        successful = sum(1 for r in results if r.status.value == 'success')
        failed = sum(1 for r in results if r.status.value == 'failed')
        
        print(f"   📊 Results: {successful} successful, {failed} failed")
        
        return {
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            db_stats = self.db.get_database_stats()
            sync_stats = self.sync_manager.get_sync_stats()
            
            return {
                'database': db_stats,
                'sync': sync_stats,
                'timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def run_daily_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete daily pipeline.
        
        Returns:
            Pipeline results
        """
        print("\n🎯 Running Daily Pipeline")
        print("=" * 50)
        
        start_time = time.time()
        results = {
            'start_time': datetime.datetime.now().isoformat(),
            'steps': []
        }
        
        try:
            # Step 1: Get system stats
            print("\n1️⃣  Getting system statistics...")
            stats = self.get_system_stats()
            results['stats'] = stats
            results['steps'].append('stats_retrieved')
            print(f"   📊 Total leads: {stats.get('database', {}).get('total_leads', 0)}")
            
            # Step 2: Sync pending leads
            print("\n2️⃣  Syncing pending leads...")
            sync_results = self.sync_to_airtable()
            results['sync'] = sync_results
            results['steps'].append('sync_completed')
            
            # Step 3: Generate messages for leads without AI messages
            print("\n3️⃣  Generating AI messages...")
            leads_without_messages = self.db.search_leads({'ai_generated_message': None})
            message_count = 0
            
            for lead in leads_without_messages[:5]:  # Limit to 5 for demo
                try:
                    message = self.message_generator.generate_message(lead)
                    if message:
                        self.db.update_lead(lead['id'], {
                            'ai_generated_message': message,
                            'message_generated_at': datetime.datetime.now().isoformat()
                        })
                        message_count += 1
                        print(f"   🤖 Generated message for {lead.get('full_name', 'Unknown')}")
                except Exception as e:
                    print(f"   ⚠️  Failed to generate message for {lead.get('full_name', 'Unknown')}: {e}")
            
            results['messages_generated'] = message_count
            results['steps'].append('messages_generated')
            
            # Step 4: Final sync
            print("\n4️⃣  Final sync...")
            final_sync = self.sync_to_airtable()
            results['final_sync'] = final_sync
            results['steps'].append('final_sync')
            
            # Calculate execution time
            execution_time = time.time() - start_time
            results['execution_time_seconds'] = execution_time
            results['end_time'] = datetime.datetime.now().isoformat()
            results['success'] = True
            
            print(f"\n✅ Pipeline completed in {execution_time:.2f} seconds")
            print(f"   📊 Total leads: {stats.get('database', {}).get('total_leads', 0)}")
            print(f"   🔄 Synced: {sync_results['successful']} leads")
            print(f"   🤖 Messages: {message_count} generated")
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            print(f"\n❌ Pipeline failed: {e}")
            return results


def main():
    """Main function to run the pipeline."""
    print("🚀 4Runr Simple Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = SimplePipeline()
    
    # Run daily pipeline
    results = pipeline.run_daily_pipeline()
    
    # Print summary
    print(f"\n📋 Pipeline Summary:")
    print(f"   Success: {results.get('success', False)}")
    print(f"   Steps completed: {len(results.get('steps', []))}")
    print(f"   Execution time: {results.get('execution_time_seconds', 0):.2f} seconds")
    
    if results.get('error'):
        print(f"   Error: {results['error']}")
    
    return results.get('success', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
