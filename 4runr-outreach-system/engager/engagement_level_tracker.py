"""
Engagement Level Tracker for the 4Runr Email Engager Upgrade.

Manages engagement level progression through Airtable's "Level Engaged" field
and synchronizes with local database for comprehensive tracking.
"""

import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from shared.airtable_client import get_airtable_client
from shared.logging_utils import get_logger
from shared.field_mapping import map_lead_data
from .local_database_manager import LocalDatabaseManager


@dataclass
class EngagementLevelConfig:
    """Configuration for engagement level progression."""
    level_name: str
    display_name: str
    message_tone: str
    next_level: Optional[str]
    skip_if_reached: bool


class EngagementLevelTracker:
    """Manages engagement level progression and database synchronization."""
    
    # Engagement level configuration
    ENGAGEMENT_LEVELS = {
        '1st degree': EngagementLevelConfig(
            level_name='1st degree',
            display_name='First Contact',
            message_tone='insightful_introduction',
            next_level='2nd degree',
            skip_if_reached=False
        ),
        '2nd degree': EngagementLevelConfig(
            level_name='2nd degree',
            display_name='Strategic Follow-up',
            message_tone='strategic_nudge',
            next_level='3rd degree',
            skip_if_reached=False
        ),
        '3rd degree': EngagementLevelConfig(
            level_name='3rd degree',
            display_name='Challenge/Urgency',
            message_tone='challenge_urgency',
            next_level='retry',
            skip_if_reached=False
        ),
        'retry': EngagementLevelConfig(
            level_name='retry',
            display_name='Final Attempt',
            message_tone='bold_last_pitch',
            next_level=None,
            skip_if_reached=True
        )
    }
    
    def __init__(self):
        """Initialize the Engagement Level Tracker."""
        self.airtable_client = get_airtable_client()
        self.db_manager = LocalDatabaseManager()
        self.logger = get_logger('engager')
        
        # Field names in Airtable
        self.level_engaged_field = 'Level Engaged'
        self.last_contacted_field = 'Date Messaged'
        
    def get_current_engagement_level(self, lead: Dict[str, Any]) -> str:
        """
        Get current engagement level from Airtable.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            Current engagement level string
        """
        # Check if Level Engaged field exists and has a value
        level_engaged = lead.get(self.level_engaged_field, '')
        
        # Handle Airtable single-select field format (could be list or string)
        if isinstance(level_engaged, list) and level_engaged:
            level_engaged = level_engaged[0]
        elif not isinstance(level_engaged, str):
            level_engaged = str(level_engaged) if level_engaged else ''
        
        # Default to 1st degree if no level is set
        if not level_engaged or level_engaged not in self.ENGAGEMENT_LEVELS:
            level_engaged = '1st degree'
            
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'info', {
                'message': f'No engagement level found, defaulting to 1st degree',
                'original_value': lead.get(self.level_engaged_field, 'None')
            })
        
        return level_engaged
    
    def should_skip_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Determine if lead should be skipped based on engagement level.
        
        Args:
            lead: Lead data dictionary
            
        Returns:
            True if lead should be skipped, False otherwise
        """
        current_level = self.get_current_engagement_level(lead)
        level_config = self.ENGAGEMENT_LEVELS.get(current_level)
        
        if not level_config:
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                'message': f'Unknown engagement level: {current_level}, allowing engagement'
            })
            return False
        
        if level_config.skip_if_reached:
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'skip', {
                'message': f'Lead at maximum engagement level: {current_level}',
                'level_config': level_config.display_name
            })
            return True
        
        return False
    
    def get_next_engagement_level(self, current_level: str) -> Optional[str]:
        """
        Determine next engagement level in progression.
        
        Args:
            current_level: Current engagement level
            
        Returns:
            Next engagement level or None if at maximum
        """
        level_config = self.ENGAGEMENT_LEVELS.get(current_level)
        
        if not level_config:
            self.logger.log_module_activity('engager', 'system', 'warning', {
                'message': f'Unknown engagement level for progression: {current_level}'
            })
            return None
        
        return level_config.next_level
    
    def update_engagement_level(self, lead_id: str, current_level: str) -> bool:
        """
        Update engagement level to next stage in both Airtable and local DB.
        
        Args:
            lead_id: Airtable record ID
            current_level: Current engagement level
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Determine next level
            next_level = self.get_next_engagement_level(current_level)
            
            if not next_level:
                self.logger.log_module_activity('engager', lead_id, 'info', {
                    'message': f'Lead at final engagement level: {current_level}, no progression needed'
                })
                return True
            
            # Prepare Airtable update fields
            current_timestamp = datetime.datetime.now().isoformat()
            airtable_fields = {
                self.level_engaged_field: next_level,
                self.last_contacted_field: datetime.date.today().isoformat()
            }
            
            # Update Airtable
            airtable_success = self.airtable_client.update_lead_fields(lead_id, airtable_fields)
            
            if airtable_success:
                self.logger.log_module_activity('engager', lead_id, 'success', {
                    'message': f'Updated engagement level: {current_level} → {next_level}',
                    'previous_level': current_level,
                    'new_level': next_level,
                    'timestamp': current_timestamp
                })
                
                # Sync to local database with complete lead data
                engagement_data = {
                    'name': lead.get('Name') or lead.get('Full Name', ''),
                    'email': lead.get('Email', ''),
                    'company': lead.get('Company', ''),
                    'company_website': lead.get('Website', ''),
                    'engagement_stage': next_level,
                    'last_contacted': current_timestamp,
                    'previous_stage': current_level,
                    'success': True,
                    'airtable_synced': True
                }
                
                db_sync_success = self.sync_to_local_database(lead_id, engagement_data)
                if not db_sync_success:
                    self.logger.log_module_activity('engager', lead_id, 'warning', {
                        'message': 'Airtable updated but local database sync failed'
                    })
                
                return True
            else:
                self.logger.log_module_activity('engager', lead_id, 'error', {
                    'message': f'Failed to update Airtable engagement level: {current_level} → {next_level}'
                })
                return False
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'update_engagement_level',
                'lead_id': lead_id,
                'current_level': current_level
            })
            return False
    
    def get_engagement_level_config(self, level: str) -> Optional[EngagementLevelConfig]:
        """
        Get configuration for a specific engagement level.
        
        Args:
            level: Engagement level name
            
        Returns:
            EngagementLevelConfig or None if not found
        """
        return self.ENGAGEMENT_LEVELS.get(level)
    
    def get_message_tone_for_level(self, level: str) -> str:
        """
        Get appropriate message tone for engagement level.
        
        Args:
            level: Engagement level name
            
        Returns:
            Message tone string
        """
        level_config = self.get_engagement_level_config(level)
        return level_config.message_tone if level_config else 'insightful_introduction'
    
    def get_leads_for_enhanced_engagement(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve leads ready for enhanced engagement with level filtering.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of lead records ready for engagement, filtered by level
        """
        try:
            # Get leads that have email addresses - using only existing fields
            # Simplified query to work with current Airtable structure
            formula = "NOT({Email} = '')"
            
            records = self.airtable_client.table.all(
                formula=formula,
                max_records=limit
            )
            
            # Convert generator to list
            records_list = list(records)
            
            leads = []
            for record in records_list:
                # Map Airtable fields to code field names
                lead_data = map_lead_data(record)
                
                # Double-check that lead should not be skipped
                if not self.should_skip_lead(lead_data):
                    leads.append(lead_data)
            
            self.logger.log_module_activity('engager', 'system', 'info', {
                'message': f'Retrieved {len(leads)} leads for enhanced engagement',
                'total_records': len(records_list),
                'filtered_leads': len(leads)
            })
            
            return leads
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_leads_for_enhanced_engagement'})
            return []
    
    def get_engagement_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about engagement levels across all leads.
        
        Returns:
            Dictionary with engagement level statistics
        """
        try:
            # Get all leads with engagement data
            records = self.airtable_client.table.all(
                fields=[self.level_engaged_field, 'Engagement_Status', 'Email_Confidence_Level']
            )
            
            stats = {
                'total_leads': 0,
                'by_level': {level: 0 for level in self.ENGAGEMENT_LEVELS.keys()},
                'no_level_set': 0,
                'ready_for_engagement': 0
            }
            
            for record in records:
                stats['total_leads'] += 1
                
                level_engaged = record['fields'].get(self.level_engaged_field, '')
                if isinstance(level_engaged, list) and level_engaged:
                    level_engaged = level_engaged[0]
                
                if level_engaged in self.ENGAGEMENT_LEVELS:
                    stats['by_level'][level_engaged] += 1
                else:
                    stats['no_level_set'] += 1
                
                # Check if ready for engagement
                engagement_status = record['fields'].get('Engagement_Status', '')
                email_confidence = record['fields'].get('Email_Confidence_Level', '')
                
                if (engagement_status == 'Auto-Send' and 
                    email_confidence in ['Real', 'Pattern'] and
                    not self.should_skip_lead(record['fields'])):
                    stats['ready_for_engagement'] += 1
            
            return stats
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'get_engagement_statistics'})
            return {'error': str(e)}
    
    def sync_to_local_database(self, lead_id: str, engagement_data: Dict[str, Any]) -> bool:
        """
        Update local database with engagement information.
        
        Args:
            lead_id: Lead identifier
            engagement_data: Dictionary with engagement information
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            return self.db_manager.update_engagement_data(lead_id, engagement_data)
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'sync_to_local_database',
                'lead_id': lead_id
            })
            return False
    
    def validate_engagement_level_field(self) -> bool:
        """
        Validate that the Level Engaged field exists in Airtable.
        
        Returns:
            True if field exists and is accessible, False otherwise
        """
        try:
            # Try to get a single record to check field availability
            records = self.airtable_client.table.all(max_records=1)
            
            for record in records:
                fields = record.get('fields', {})
                if self.level_engaged_field in fields:
                    self.logger.log_module_activity('engager', 'system', 'success', {
                        'message': f'Level Engaged field validated successfully'
                    })
                    return True
                else:
                    self.logger.log_module_activity('engager', 'system', 'warning', {
                        'message': f'Level Engaged field not found in Airtable',
                        'available_fields': list(fields.keys())
                    })
                    return False
            
            # No records found, can't validate
            self.logger.log_module_activity('engager', 'system', 'warning', {
                'message': 'No records found to validate Level Engaged field'
            })
            return False
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'validate_engagement_level_field'})
            return False