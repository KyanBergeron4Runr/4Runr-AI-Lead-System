#!/usr/bin/env python3
"""
Re-engagement Strategy for 4Runr Outreach System

Handles re-engagement logic for leads who received messages but didn't respond.
Implements timed follow-ups with adjusted messaging and proper tracking.
"""

import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .local_database_manager import LocalDatabaseManager
from shared.airtable_client import AirtableClient
from shared.logging_utils import get_logger


class ReengagementStrategy:
    """
    Manages re-engagement logic for leads who haven't responded to initial outreach.
    
    Handles:
    - Identifying eligible leads for re-engagement
    - Managing follow-up stages and timing
    - Updating lead status and tracking
    - Coordinating with message generation
    """
    
    def __init__(self):
        """Initialize the re-engagement strategy."""
        self.logger = get_logger('reengager')
        self.db_manager = LocalDatabaseManager()
        self.airtable_client = AirtableClient()
        
        # Re-engagement configuration
        self.config = {
            'days_between_followups': 7,  # Wait 7 days between follow-ups
            'max_followup_attempts': 2,   # Maximum 2 follow-up attempts
            'followup_stages': ['Followup_1', 'Followup_2'],
            'eligible_response_statuses': ['No Response', '', None],
            'required_engagement_status': 'Sent'
        }
        
        self.logger.log_module_activity('reengager', 'system', 'success', {
            'message': 'Re-engagement Strategy initialized',
            'config': self.config
        })
    
    def find_eligible_leads(self, days_since_contact: int = 7, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find leads eligible for re-engagement based on criteria.
        
        Args:
            days_since_contact: Minimum days since last contact
            limit: Maximum number of leads to return
            
        Returns:
            List of eligible lead dictionaries
        """
        self.logger.log_module_activity('reengager', 'system', 'info', {
            'message': f'Finding leads eligible for re-engagement',
            'days_since_contact': days_since_contact,
            'limit': limit
        })
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_since_contact)
            cutoff_iso = cutoff_date.isoformat()
            
            # Query database for eligible leads
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query for eligible leads
                query = """
                    SELECT l.*, et.message_sent, et.contacted_at as last_engagement_date
                    FROM leads l
                    LEFT JOIN engagement_tracking et ON l.id = et.lead_id
                    WHERE l.last_contacted IS NOT NULL
                    AND l.last_contacted < ?
                    AND (l.response_status IN ('No Response', '') OR l.response_status IS NULL)
                    AND (l.follow_up_stage IS NULL OR l.follow_up_stage != 'Followup_2')
                    AND l.eligible_for_reengagement = FALSE
                    ORDER BY l.last_contacted ASC
                """
                
                params = [cutoff_iso]
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                eligible_leads = []
                for row in rows:
                    lead_data = {
                        'id': row['id'],
                        'name': row['name'],
                        'email': row['email'],
                        'company': row['company'],
                        'company_website': row['company_website'],
                        'engagement_stage': row['engagement_stage'],
                        'last_contacted': row['last_contacted'],
                        'follow_up_stage': row['follow_up_stage'],
                        'response_status': row['response_status'],
                        'eligible_for_reengagement': bool(row['eligible_for_reengagement']),
                        'last_message': row['message_sent'],
                        'days_since_contact': (datetime.datetime.now() - datetime.datetime.fromisoformat(row['last_contacted'])).days
                    }
                    eligible_leads.append(lead_data)
                
                self.logger.log_module_activity('reengager', 'system', 'success', {
                    'message': f'Found {len(eligible_leads)} eligible leads for re-engagement',
                    'eligible_count': len(eligible_leads)
                })
                
                return eligible_leads
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'find_eligible_leads',
                'days_since_contact': days_since_contact,
                'limit': limit
            })
            return []
    
    def mark_leads_for_reengagement(self, lead_ids: List[str]) -> Dict[str, int]:
        """
        Mark leads as eligible for re-engagement and update their follow-up stage.
        
        Args:
            lead_ids: List of lead IDs to mark for re-engagement
            
        Returns:
            Dictionary with success/failure counts
        """
        self.logger.log_module_activity('reengager', 'system', 'info', {
            'message': f'Marking {len(lead_ids)} leads for re-engagement',
            'lead_count': len(lead_ids)
        })
        
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                for lead_id in lead_ids:
                    try:
                        # Get current follow-up stage
                        cursor.execute("SELECT follow_up_stage FROM leads WHERE id = ?", (lead_id,))
                        row = cursor.fetchone()
                        
                        if not row:
                            results['failed'] += 1
                            results['errors'].append(f"Lead {lead_id} not found")
                            continue
                        
                        current_stage = row['follow_up_stage']
                        
                        # Determine next follow-up stage
                        if not current_stage:
                            next_stage = 'Followup_1'
                        elif current_stage == 'Followup_1':
                            next_stage = 'Followup_2'
                        else:
                            # Already at max follow-ups
                            results['failed'] += 1
                            results['errors'].append(f"Lead {lead_id} already at max follow-ups")
                            continue
                        
                        # Update lead for re-engagement
                        cursor.execute("""
                            UPDATE leads 
                            SET eligible_for_reengagement = TRUE,
                                follow_up_stage = ?,
                                updated_at = ?
                            WHERE id = ?
                        """, (next_stage, datetime.datetime.now().isoformat(), lead_id))
                        
                        if cursor.rowcount > 0:
                            results['success'] += 1
                            self.logger.log_module_activity('reengager', lead_id, 'success', {
                                'message': f'Marked lead for re-engagement',
                                'next_stage': next_stage
                            })
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"Failed to update lead {lead_id}")
                    
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"Error updating lead {lead_id}: {str(e)}")
                        self.logger.log_error(e, {
                            'action': 'mark_lead_for_reengagement',
                            'lead_id': lead_id
                        })
                
                conn.commit()
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'mark_leads_for_reengagement',
                'lead_ids': lead_ids
            })
            results['errors'].append(f"Database error: {str(e)}")
        
        self.logger.log_module_activity('reengager', 'system', 'info', {
            'message': 'Completed marking leads for re-engagement',
            'success': results['success'],
            'failed': results['failed'],
            'errors': len(results['errors'])
        })
        
        return results
    
    def get_reengagement_leads(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get leads that are marked for re-engagement and ready to be processed.
        
        Args:
            limit: Maximum number of leads to return
            
        Returns:
            List of leads ready for re-engagement
        """
        self.logger.log_module_activity('reengager', 'system', 'info', {
            'message': 'Getting leads ready for re-engagement processing',
            'limit': limit
        })
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM leads 
                    WHERE eligible_for_reengagement = TRUE
                    ORDER BY last_contacted ASC
                """
                
                params = []
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                reengagement_leads = []
                for row in rows:
                    lead_data = {
                        'id': row['id'],
                        'name': row['name'],
                        'email': row['email'],
                        'company': row['company'],
                        'company_website': row['company_website'],
                        'engagement_stage': row['engagement_stage'],
                        'last_contacted': row['last_contacted'],
                        'follow_up_stage': row['follow_up_stage'],
                        'response_status': row['response_status'],
                        'eligible_for_reengagement': bool(row['eligible_for_reengagement']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                    reengagement_leads.append(lead_data)
                
                self.logger.log_module_activity('reengager', 'system', 'success', {
                    'message': f'Retrieved {len(reengagement_leads)} leads for re-engagement',
                    'count': len(reengagement_leads)
                })
                
                return reengagement_leads
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'get_reengagement_leads',
                'limit': limit
            })
            return []
    
    def complete_reengagement(self, lead_id: str, success: bool = True, error_message: Optional[str] = None) -> bool:
        """
        Mark a re-engagement attempt as complete and update lead status.
        
        Args:
            lead_id: ID of the lead that was re-engaged
            success: Whether the re-engagement was successful
            error_message: Error message if re-engagement failed
            
        Returns:
            True if update was successful, False otherwise
        """
        self.logger.log_module_activity('reengager', lead_id, 'info', {
            'message': 'Completing re-engagement attempt',
            'success': success,
            'error_message': error_message
        })
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update lead status
                cursor.execute("""
                    UPDATE leads 
                    SET eligible_for_reengagement = FALSE,
                        last_contacted = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    datetime.datetime.now().isoformat(),
                    datetime.datetime.now().isoformat(),
                    lead_id
                ))
                
                # Add engagement tracking record
                cursor.execute("""
                    INSERT INTO engagement_tracking (
                        lead_id, engagement_level, contacted_at, success, error_message
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    'reengagement',
                    datetime.datetime.now().isoformat(),
                    success,
                    error_message
                ))
                
                conn.commit()
                
                self.logger.log_module_activity('reengager', lead_id, 'success', {
                    'message': 'Re-engagement attempt completed',
                    'success': success
                })
                
                return True
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'complete_reengagement',
                'lead_id': lead_id,
                'success': success
            })
            return False
    
    def get_reengagement_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about re-engagement activities.
        
        Returns:
            Dictionary with re-engagement statistics
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total leads eligible for re-engagement
                cursor.execute("SELECT COUNT(*) FROM leads WHERE eligible_for_reengagement = TRUE")
                stats['eligible_for_reengagement'] = cursor.fetchone()[0]
                
                # Leads by follow-up stage
                cursor.execute("""
                    SELECT follow_up_stage, COUNT(*) 
                    FROM leads 
                    WHERE follow_up_stage IS NOT NULL
                    GROUP BY follow_up_stage
                """)
                stats['by_followup_stage'] = dict(cursor.fetchall())
                
                # Leads by response status
                cursor.execute("""
                    SELECT response_status, COUNT(*) 
                    FROM leads 
                    GROUP BY response_status
                """)
                stats['by_response_status'] = dict(cursor.fetchall())
                
                # Recent re-engagement activity (last 7 days)
                cursor.execute("""
                    SELECT COUNT(*) FROM engagement_tracking 
                    WHERE engagement_level = 'reengagement'
                    AND contacted_at >= datetime('now', '-7 days')
                """)
                stats['recent_reengagements'] = cursor.fetchone()[0]
                
                # Re-engagement success rate
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        COUNT(*) as total
                    FROM engagement_tracking
                    WHERE engagement_level = 'reengagement'
                """)
                result = cursor.fetchone()
                if result['total'] > 0:
                    stats['reengagement_success_rate'] = result['successful'] / result['total']
                else:
                    stats['reengagement_success_rate'] = 0.0
                
                return stats
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_reengagement_statistics'})
            return {'error': str(e)}
    
    def cleanup_old_reengagement_flags(self, days_old: int = 30) -> int:
        """
        Clean up old re-engagement flags for leads that haven't been processed.
        
        Args:
            days_old: Number of days after which to clean up flags
            
        Returns:
            Number of flags cleaned up
        """
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
            cutoff_iso = cutoff_date.isoformat()
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE leads 
                    SET eligible_for_reengagement = FALSE
                    WHERE eligible_for_reengagement = TRUE
                    AND updated_at < ?
                """, (cutoff_iso,))
                
                cleaned_count = cursor.rowcount
                conn.commit()
                
                self.logger.log_module_activity('reengager', 'system', 'info', {
                    'message': f'Cleaned up {cleaned_count} old re-engagement flags',
                    'days_old': days_old
                })
                
                return cleaned_count
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'cleanup_old_reengagement_flags',
                'days_old': days_old
            })
            return 0


def find_and_prepare_reengagement_leads(days_since_contact: int = 7, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to find eligible leads and prepare them for re-engagement.
    
    Args:
        days_since_contact: Minimum days since last contact
        limit: Maximum number of leads to process
        
    Returns:
        Dictionary with results and statistics
    """
    strategy = ReengagementStrategy()
    
    # Find eligible leads
    eligible_leads = strategy.find_eligible_leads(days_since_contact, limit)
    
    if not eligible_leads:
        return {
            'eligible_leads': 0,
            'marked_for_reengagement': 0,
            'success': True,
            'message': 'No eligible leads found for re-engagement'
        }
    
    # Mark leads for re-engagement
    lead_ids = [lead['id'] for lead in eligible_leads]
    results = strategy.mark_leads_for_reengagement(lead_ids)
    
    return {
        'eligible_leads': len(eligible_leads),
        'marked_for_reengagement': results['success'],
        'failed': results['failed'],
        'errors': results['errors'],
        'success': results['failed'] == 0,
        'leads': eligible_leads[:5]  # Return first 5 for preview
    }


if __name__ == "__main__":
    # Test the re-engagement strategy
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Re-engagement Strategy')
    parser.add_argument('--days', type=int, default=7, help='Days since last contact')
    parser.add_argument('--limit', type=int, help='Limit number of leads')
    parser.add_argument('--stats', action='store_true', help='Show re-engagement statistics')
    parser.add_argument('--cleanup', type=int, help='Clean up old flags (days)')
    
    args = parser.parse_args()
    
    strategy = ReengagementStrategy()
    
    if args.stats:
        print("📊 Re-engagement Statistics:")
        stats = strategy.get_reengagement_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.cleanup:
        print(f"🧹 Cleaning up re-engagement flags older than {args.cleanup} days...")
        cleaned = strategy.cleanup_old_reengagement_flags(args.cleanup)
        print(f"✅ Cleaned up {cleaned} old flags")
    
    else:
        print(f"🔍 Finding leads eligible for re-engagement (>{args.days} days)...")
        results = find_and_prepare_reengagement_leads(args.days, args.limit)
        
        print(f"📋 Results:")
        print(f"  Eligible leads: {results['eligible_leads']}")
        print(f"  Marked for re-engagement: {results['marked_for_reengagement']}")
        print(f"  Failed: {results['failed']}")
        
        if results['errors']:
            print(f"❌ Errors:")
            for error in results['errors'][:3]:
                print(f"  • {error}")