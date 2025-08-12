#!/usr/bin/env python3
"""
Engagement Defaults Manager

Manages application of default engagement values to Airtable records after
leads are scraped, verified, or enriched.
"""

import os
import time
import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

logger = logging.getLogger('engagement-defaults')

class EngagementDefaultsManager:
    """
    Manages application of default engagement values to Airtable records.
    """
    
    # Default values for engagement fields
    DEFAULT_VALUES = {
        'Engagement_Status': 'Auto-Send',
        'Email_Confidence_Level': 'Pattern',
        'Level Engaged': ''
    }
    
    def __init__(self):
        """Initialize the Engagement Defaults Manager."""
        self.settings = get_settings()
        
        # Airtable configuration
        self.api_key = self.settings.airtable.api_key
        self.base_id = self.settings.airtable.base_id
        self.table_name = self.settings.airtable.table_name
        
        # API endpoints
        from urllib.parse import quote
        encoded_table_name = quote(self.table_name)
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{encoded_table_name}"
        
        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests (5 requests/second)
        
        # Use default values from settings
        self.DEFAULT_VALUES = self.settings.engagement_defaults.default_values.copy()
        
        # Performance tracking
        self.performance_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0
        }
        
        logger.info("🎯 Engagement Defaults Manager initialized")
        logger.info(f"📋 Default values: {self.DEFAULT_VALUES}")
        logger.info(f"⚙️ Enabled: {self.settings.engagement_defaults.enabled}")
    

    
    def apply_defaults_to_lead(self, lead_id: str, airtable_record_id: str) -> Dict[str, Any]:
        """
        Apply default engagement values to a lead in Airtable.
        
        Args:
            lead_id: Local database lead ID (for logging)
            airtable_record_id: Airtable record ID
            
        Returns:
            Dictionary with application results
        """
        with self._performance_timer(f"apply_defaults_lead_{lead_id}"):
            logger.debug(f"🎯 Starting defaults application for lead {lead_id} (Airtable: {airtable_record_id})")
            
            # Log operation start
            self._log_structured_activity('defaults_application', lead_id, 'started', {
                'airtable_record_id': airtable_record_id,
                'default_values_count': len(self.DEFAULT_VALUES)
            })
            
            try:
                # Get current values from Airtable
                logger.debug(f"🔍 Retrieving current values for lead {lead_id}")
                current_values = self._get_current_airtable_values(airtable_record_id)
                
                if current_values is None:
                    error_msg = 'Failed to retrieve current Airtable values'
                    self._log_structured_activity('defaults_application', lead_id, 'error', {
                        'error': error_msg,
                        'airtable_record_id': airtable_record_id
                    })
                    self.performance_stats['failed_operations'] += 1
                    return {
                        'success': False,
                        'fields_updated': [],
                        'error': error_msg
                    }
                
                # Determine which defaults need to be applied
                needed_defaults = self._determine_needed_defaults(current_values)
                
                # Log field analysis
                self._log_field_analysis(lead_id, current_values, needed_defaults)
                
                if not needed_defaults:
                    logger.debug(f"✅ No defaults needed for lead {lead_id} - all fields already have values")
                    self._log_structured_activity('defaults_application', lead_id, 'skipped', {
                        'reason': 'no_defaults_needed',
                        'current_values': current_values
                    })
                    self.performance_stats['successful_operations'] += 1
                    return {
                        'success': True,
                        'fields_updated': [],
                        'message': 'No defaults needed'
                    }
                
                # Apply the defaults
                logger.debug(f"🔧 Applying {len(needed_defaults)} default values to lead {lead_id}")
                success = self._update_airtable_record(airtable_record_id, needed_defaults)
                
                if success:
                    fields_updated = list(needed_defaults.keys())
                    logger.info(f"✅ Applied default engagement values to lead {airtable_record_id}: {fields_updated}")
                    
                    # Log successful application
                    self._log_structured_activity('defaults_application', lead_id, 'success', {
                        'fields_updated': fields_updated,
                        'values_applied': needed_defaults,
                        'airtable_record_id': airtable_record_id
                    })
                    
                    self.performance_stats['successful_operations'] += 1
                    return {
                        'success': True,
                        'fields_updated': fields_updated,
                        'values_applied': needed_defaults
                    }
                else:
                    error_msg = 'Failed to update Airtable record'
                    self._log_structured_activity('defaults_application', lead_id, 'error', {
                        'error': error_msg,
                        'attempted_updates': needed_defaults,
                        'airtable_record_id': airtable_record_id
                    })
                    self.performance_stats['failed_operations'] += 1
                    return {
                        'success': False,
                        'fields_updated': [],
                        'error': error_msg
                    }
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Exception applying defaults to lead {lead_id}: {error_msg}")
                
                # Log exception with context
                self._log_structured_activity('defaults_application', lead_id, 'error', {
                    'error': error_msg,
                    'exception_type': type(e).__name__,
                    'airtable_record_id': airtable_record_id
                })
                
                self.performance_stats['failed_operations'] += 1
                return {
                    'success': False,
                    'fields_updated': [],
                    'error': error_msg
                }
    
    def apply_defaults_to_multiple_leads(self, lead_records: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Apply defaults to multiple leads.
        
        Args:
            lead_records: List of dicts with 'lead_id' and 'airtable_record_id'
            
        Returns:
            Dictionary with batch application results
        """
        batch_start_time = time.time()
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🎯 Starting batch defaults application: {len(lead_records)} leads (batch_id: {batch_id})")
        
        # Log batch start
        self._log_structured_activity('batch_defaults_application', batch_id, 'started', {
            'total_leads': len(lead_records),
            'batch_size': len(lead_records)
        })
        
        results = {
            'success': True,
            'total_leads': len(lead_records),
            'processed_count': 0,
            'updated_count': 0,
            'skipped_count': 0,
            'failed_count': 0,
            'fields_updated': [],
            'errors': [],
            'batch_id': batch_id,
            'processing_time': 0.0
        }
        
        # Track processing times for each lead
        lead_processing_times = []
        
        for i, record in enumerate(lead_records):
            lead_id = record.get('lead_id', 'unknown')
            airtable_record_id = record.get('airtable_record_id')
            
            logger.debug(f"🔄 Processing lead {i+1}/{len(lead_records)}: {lead_id}")
            
            if not airtable_record_id:
                error_msg = f"Lead {lead_id}: No Airtable record ID"
                logger.warning(f"⚠️ {error_msg}")
                
                self._log_structured_activity('batch_lead_processing', lead_id, 'error', {
                    'error': 'missing_airtable_id',
                    'batch_id': batch_id,
                    'position': i+1
                })
                
                results['failed_count'] += 1
                results['errors'].append(error_msg)
                continue
            
            try:
                lead_start_time = time.time()
                result = self.apply_defaults_to_lead(lead_id, airtable_record_id)
                lead_processing_time = time.time() - lead_start_time
                lead_processing_times.append(lead_processing_time)
                
                results['processed_count'] += 1
                
                if result['success']:
                    if result['fields_updated']:
                        results['updated_count'] += 1
                        results['fields_updated'].extend(result['fields_updated'])
                        
                        self._log_structured_activity('batch_lead_processing', lead_id, 'success', {
                            'fields_updated': result['fields_updated'],
                            'processing_time': lead_processing_time,
                            'batch_id': batch_id,
                            'position': i+1
                        })
                    else:
                        results['skipped_count'] += 1
                        
                        self._log_structured_activity('batch_lead_processing', lead_id, 'skipped', {
                            'reason': 'no_defaults_needed',
                            'processing_time': lead_processing_time,
                            'batch_id': batch_id,
                            'position': i+1
                        })
                else:
                    results['failed_count'] += 1
                    error_msg = f"Lead {lead_id}: {result.get('error', 'Unknown error')}"
                    results['errors'].append(error_msg)
                    
                    self._log_structured_activity('batch_lead_processing', lead_id, 'error', {
                        'error': result.get('error', 'Unknown error'),
                        'processing_time': lead_processing_time,
                        'batch_id': batch_id,
                        'position': i+1
                    })
                
                # Rate limiting between requests
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = f"Lead {lead_id}: {str(e)}"
                logger.error(f"❌ Exception processing lead {lead_id}: {str(e)}")
                
                self._log_structured_activity('batch_lead_processing', lead_id, 'error', {
                    'error': str(e),
                    'exception_type': type(e).__name__,
                    'batch_id': batch_id,
                    'position': i+1
                })
                
                results['failed_count'] += 1
                results['errors'].append(error_msg)
        
        # Calculate batch metrics
        batch_processing_time = time.time() - batch_start_time
        results['processing_time'] = batch_processing_time
        
        # Overall success if no failures
        results['success'] = results['failed_count'] == 0
        
        # Remove duplicate field names
        results['fields_updated'] = list(set(results['fields_updated']))
        
        # Calculate performance metrics
        avg_lead_time = sum(lead_processing_times) / len(lead_processing_times) if lead_processing_times else 0
        leads_per_second = len(lead_records) / batch_processing_time if batch_processing_time > 0 else 0
        
        # Log batch completion
        batch_summary = {
            'total_leads': results['total_leads'],
            'updated_count': results['updated_count'],
            'skipped_count': results['skipped_count'],
            'failed_count': results['failed_count'],
            'processing_time': batch_processing_time,
            'avg_lead_processing_time': avg_lead_time,
            'leads_per_second': leads_per_second,
            'success_rate': (results['updated_count'] + results['skipped_count']) / max(1, results['total_leads']) * 100
        }
        
        logger.info(f"📊 Batch defaults application completed (batch_id: {batch_id}): "
                   f"{results['updated_count']} updated, {results['skipped_count']} skipped, "
                   f"{results['failed_count']} failed in {batch_processing_time:.2f}s")
        
        self._log_structured_activity('batch_defaults_application', batch_id, 'completed', batch_summary)
        
        return results
    
    def _get_current_airtable_values(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current field values from Airtable record.
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            Dictionary of current field values or None if failed
        """
        try:
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Get all fields (don't filter - this was causing the 422 error)
            url = f"{self.base_url}/{record_id}"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('fields', {})
            elif response.status_code == 404:
                logger.warning(f"⚠️ Airtable record not found: {record_id}")
                return None
            else:
                logger.error(f"❌ Failed to get Airtable record {record_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception getting Airtable record {record_id}: {str(e)}")
            return None
    
    def _determine_needed_defaults(self, current_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine which default values need to be applied.
        
        Args:
            current_values: Current field values from Airtable
            
        Returns:
            Dictionary of fields that need default values
        """
        needed_defaults = {}
        
        for field_name, default_value in self.DEFAULT_VALUES.items():
            current_value = current_values.get(field_name)
            
            # Check if field is missing or empty
            if self._field_needs_default(current_value, default_value):
                needed_defaults[field_name] = default_value
                logger.debug(f"🎯 Field '{field_name}' needs default: current='{current_value}' -> default='{default_value}'")
        
        return needed_defaults
    
    def _field_needs_default(self, current_value: Any, default_value: Any) -> bool:
        """
        Check if a field needs a default value applied.
        
        Args:
            current_value: Current field value
            default_value: Default value to potentially apply
            
        Returns:
            True if default should be applied
        """
        # Special case: if default is empty string and current is empty, don't apply
        if default_value == '':
            if current_value == '' or current_value == [''] or current_value is None or current_value == []:
                return False
        
        # Handle None/missing values
        if current_value is None:
            return True
        
        # Handle empty strings
        if isinstance(current_value, str) and current_value.strip() == '':
            return True
        
        # Handle empty lists (Airtable single-select can be returned as list)
        if isinstance(current_value, list) and len(current_value) == 0:
            return True
        
        # Handle list with empty string
        if isinstance(current_value, list) and len(current_value) == 1 and current_value[0] == '':
            return True
        
        return False
    
    def _update_airtable_record(self, record_id: str, updates: Dict[str, Any], retry_count: int = 0) -> bool:
        """
        Update Airtable record with new field values.
        
        Args:
            record_id: Airtable record ID
            updates: Dictionary of field updates
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            True if update successful
        """
        max_retries = 2
        
        try:
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Prepare update data
            data = {
                'fields': updates
            }
            
            url = f"{self.base_url}/{record_id}"
            response = requests.patch(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.debug(f"✅ Successfully updated Airtable record {record_id}")
                return True
            elif response.status_code == 429 and retry_count < max_retries:
                # Rate limited - wait and retry
                wait_time = (retry_count + 1) * 2  # Exponential backoff: 2s, 4s
                logger.warning(f"⚠️ Rate limited, waiting {wait_time}s before retry {retry_count + 1}/{max_retries}")
                time.sleep(wait_time)
                return self._update_airtable_record(record_id, updates, retry_count + 1)
            elif response.status_code in [500, 502, 503, 504] and retry_count < max_retries:
                # Server error - retry once
                wait_time = 1
                logger.warning(f"⚠️ Server error {response.status_code}, retrying in {wait_time}s")
                time.sleep(wait_time)
                return self._update_airtable_record(record_id, updates, retry_count + 1)
            else:
                logger.error(f"❌ Failed to update Airtable record {record_id}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout as e:
            if retry_count < max_retries:
                logger.warning(f"⚠️ Request timeout, retrying {retry_count + 1}/{max_retries}")
                time.sleep(1)
                return self._update_airtable_record(record_id, updates, retry_count + 1)
            else:
                logger.error(f"❌ Request timeout updating Airtable record {record_id}: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"❌ Exception updating Airtable record {record_id}: {str(e)}")
            return False
    
    def _apply_rate_limiting(self):
        """Apply rate limiting for Airtable API requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_default_values(self) -> Dict[str, str]:
        """
        Get current default values configuration.
        
        Returns:
            Dictionary of default values
        """
        return self.DEFAULT_VALUES.copy()
    
    def is_enabled(self) -> bool:
        """
        Check if engagement defaults are enabled.
        
        Returns:
            True if enabled
        """
        return self.settings.engagement_defaults.enabled
    
    @contextmanager
    def _performance_timer(self, operation_name: str):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._update_performance_stats(operation_name, duration)
    
    def _update_performance_stats(self, operation_name: str, duration: float):
        """Update performance statistics."""
        self.performance_stats['total_operations'] += 1
        self.performance_stats['total_processing_time'] += duration
        self.performance_stats['average_processing_time'] = (
            self.performance_stats['total_processing_time'] / 
            self.performance_stats['total_operations']
        )
        
        logger.debug(f"⏱️ {operation_name} completed in {duration:.3f}s")
    
    def _log_structured_activity(self, activity_type: str, lead_id: str, status: str, details: Dict[str, Any]):
        """Log structured activity for monitoring and analysis."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'module': 'engagement_defaults',
            'activity_type': activity_type,
            'lead_id': lead_id,
            'status': status,
            'details': details
        }
        
        # Log at appropriate level based on status
        if status == 'success':
            logger.info(f"📊 [ENGAGEMENT_DEFAULTS] {activity_type.upper()} | lead_id={lead_id} | {details}")
        elif status == 'warning':
            logger.warning(f"📊 [ENGAGEMENT_DEFAULTS] {activity_type.upper()} | lead_id={lead_id} | {details}")
        elif status == 'error':
            logger.error(f"📊 [ENGAGEMENT_DEFAULTS] {activity_type.upper()} | lead_id={lead_id} | {details}")
        else:
            logger.debug(f"📊 [ENGAGEMENT_DEFAULTS] {activity_type.upper()} | lead_id={lead_id} | {details}")
    
    def _log_field_analysis(self, lead_id: str, current_values: Dict[str, Any], needed_defaults: Dict[str, Any]):
        """Log detailed field analysis for debugging."""
        analysis = {
            'lead_id': lead_id,
            'current_values': current_values,
            'needed_defaults': needed_defaults,
            'fields_analyzed': list(self.DEFAULT_VALUES.keys())
        }
        
        logger.debug(f"🔍 Field analysis for lead {lead_id}: {analysis}")
        
        # Log each field decision
        for field_name, default_value in self.DEFAULT_VALUES.items():
            current_value = current_values.get(field_name)
            needs_default = field_name in needed_defaults
            
            logger.debug(f"🔍 Field '{field_name}': current='{current_value}' | default='{default_value}' | needs_update={needs_default}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            **self.performance_stats,
            'success_rate': (
                self.performance_stats['successful_operations'] / 
                max(1, self.performance_stats['total_operations'])
            ) * 100,
            'failure_rate': (
                self.performance_stats['failed_operations'] / 
                max(1, self.performance_stats['total_operations'])
            ) * 100
        }
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the engagement defaults configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if Airtable credentials are available
        if not self.api_key:
            errors.append("Airtable API key is missing")
        
        if not self.base_id:
            errors.append("Airtable base ID is missing")
        
        if not self.table_name:
            errors.append("Airtable table name is missing")
        
        # Check if default values are properly configured
        if not self.DEFAULT_VALUES:
            errors.append("No default values configured")
        
        # Check for required engagement fields
        required_fields = ['Engagement_Status', 'Email_Confidence_Level', 'Level Engaged']
        for field in required_fields:
            if field not in self.DEFAULT_VALUES:
                errors.append(f"Missing default value for required field: {field}")
        
        return errors
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            'enabled': self.is_enabled(),
            'default_values': self.get_default_values(),
            'apply_on_scrape': self.settings.engagement_defaults.apply_on_scrape,
            'apply_on_enrich': self.settings.engagement_defaults.apply_on_enrich,
            'apply_on_verify': self.settings.engagement_defaults.apply_on_verify,
            'airtable_configured': bool(self.api_key and self.base_id and self.table_name),
            'validation_errors': self.validate_configuration(),
            'performance_stats': self.get_performance_stats()
        }
    
    def get_monitoring_report(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring report for engagement defaults.
        
        Returns:
            Dictionary with monitoring information
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'configuration': self.get_configuration_summary(),
            'performance': self.get_performance_stats(),
            'system_status': {
                'enabled': self.is_enabled(),
                'airtable_configured': bool(self.api_key and self.base_id and self.table_name),
                'default_values_count': len(self.DEFAULT_VALUES),
                'validation_errors': self.validate_configuration()
            },
            'operational_metrics': {
                'total_operations': self.performance_stats['total_operations'],
                'successful_operations': self.performance_stats['successful_operations'],
                'failed_operations': self.performance_stats['failed_operations'],
                'average_processing_time': self.performance_stats['average_processing_time'],
                'total_processing_time': self.performance_stats['total_processing_time']
            }
        }
    
    def reset_performance_stats(self):
        """Reset performance statistics."""
        self.performance_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0
        }
        logger.info("📊 Performance statistics reset")


# Convenience functions
def apply_defaults_to_lead(lead_id: str, airtable_record_id: str) -> Dict[str, Any]:
    """
    Apply engagement defaults to a single lead (convenience function).
    
    Args:
        lead_id: Local database lead ID
        airtable_record_id: Airtable record ID
        
    Returns:
        Application result dictionary
    """
    manager = EngagementDefaultsManager()
    return manager.apply_defaults_to_lead(lead_id, airtable_record_id)

def apply_defaults_to_multiple_leads(lead_records: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Apply engagement defaults to multiple leads (convenience function).
    
    Args:
        lead_records: List of lead record dictionaries
        
    Returns:
        Batch application result dictionary
    """
    manager = EngagementDefaultsManager()
    return manager.apply_defaults_to_multiple_leads(lead_records)

def is_defaults_enabled() -> bool:
    """
    Check if engagement defaults are enabled (convenience function).
    
    Returns:
        True if enabled
    """
    settings = get_settings()
    return settings.engagement_defaults.enabled


if __name__ == "__main__":
    # Test engagement defaults manager
    print("🧪 Testing Engagement Defaults Manager...")
    
    try:
        manager = EngagementDefaultsManager()
        
        # Test configuration
        print(f"⚙️ Enabled: {manager.is_enabled()}")
        print(f"📋 Default values: {manager.get_default_values()}")
        
        # Validate configuration
        errors = manager.validate_configuration()
        if errors:
            print(f"⚠️ Configuration errors: {errors}")
        else:
            print("✅ Configuration is valid")
        
        # Show configuration summary
        summary = manager.get_configuration_summary()
        print(f"📊 Configuration Summary:")
        for key, value in summary.items():
            print(f"  • {key}: {value}")
        
        # Test field needs default logic
        print("\n🧪 Testing field default logic...")
        test_cases = [
            (None, "Auto-Send", True),
            ("", "Auto-Send", True),
            ([], "Auto-Send", True),
            ([""], "Auto-Send", True),
            ("Existing Value", "Auto-Send", False),
            (["Existing Value"], "Auto-Send", False),
            ("", "", False),  # Empty default for empty value
        ]
        
        for current, default, expected in test_cases:
            result = manager._field_needs_default(current, default)
            status = "✅" if result == expected else "❌"
            print(f"  {status} Current: {current}, Default: {default}, Needs: {result} (Expected: {expected})")
        
        print("\n✅ Engagement defaults manager test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()