#!/usr/bin/env python3
"""
Daily Batch Processor for Campaign Brain

Automated daily processing with scheduling, error handling, and notifications.
Designed to run as a cron job or scheduled service.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from serve_campaign_brain import CampaignBrainService


class DailyBatchProcessor:
    """Handles automated daily batch processing"""
    
    def __init__(self):
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.service = CampaignBrainService()
        
        # Processing statistics
        self.daily_stats = {
            'start_time': datetime.now(),
            'processed': 0,
            'approved': 0,
            'manual_review': 0,
            'errors': 0,
            'failed_leads': [],
            'successful_leads': [],
            'batch_size': self.config['batch_size']
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load daily processing configuration"""
        return {
            'batch_size': int(os.getenv('DAILY_BATCH_SIZE', '20')),
            'max_retries': int(os.getenv('DAILY_MAX_RETRIES', '3')),
            'retry_delay': int(os.getenv('DAILY_RETRY_DELAY', '300')),  # 5 minutes
            'notification_threshold': int(os.getenv('ERROR_NOTIFICATION_THRESHOLD', '5')),
            'dry_run': os.getenv('DAILY_DRY_RUN', 'false').lower() == 'true',
            'enable_notifications': os.getenv('ENABLE_ERROR_NOTIFICATIONS', 'true').lower() == 'true'
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up daily processing logging"""
        logger = logging.getLogger('daily_batch_processor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = Path("logs/daily")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily log file
        today = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"daily_batch_{today}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    async def run_daily_batch(self) -> Dict[str, Any]:
        """Run the daily batch processing"""
        
        self.logger.info("🚀 Starting daily batch processing")
        self.logger.info(f"Configuration: batch_size={self.config['batch_size']}, "
                        f"dry_run={self.config['dry_run']}")
        
        try:
            # Pre-flight checks
            if not await self._pre_flight_checks():
                return self._create_failure_result("Pre-flight checks failed")
            
            # Process batch with retries
            result = await self._process_with_retries()
            
            # Post-processing
            await self._post_process_results(result)
            
            # Generate daily report
            report = self._generate_daily_report(result)
            
            self.logger.info("✅ Daily batch processing completed successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Daily batch processing failed: {str(e)}")
            return self._create_failure_result(str(e))
    
    async def _pre_flight_checks(self) -> bool:
        """Perform pre-flight checks before processing"""
        
        self.logger.info("🔍 Performing pre-flight checks...")
        
        try:
            # Health check
            health = self.service.health_check()
            if health['status'] != 'healthy':
                self.logger.error(f"Service health check failed: {health.get('issues', [])}")
                return False
            
            self.logger.info("✅ Service health check passed")
            
            # Check available leads
            if self.service.integrated_mode:
                leads = self.service._get_leads_for_brain_processing(1)  # Just check if any exist
                if not leads:
                    self.logger.warning("⚠️  No leads found ready for processing")
                    return True  # Not an error, just nothing to do
                
                self.logger.info(f"✅ Found leads ready for processing")
            
            # Check disk space
            if not self._check_disk_space():
                return False
            
            # Check API connectivity
            if not await self._check_api_connectivity():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-flight check error: {str(e)}")
            return False
    
    def _check_disk_space(self) -> bool:
        """Check available disk space"""
        
        try:
            import shutil
            
            # Check available space (in GB)
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            
            if free_gb < 1:  # Less than 1GB free
                self.logger.error(f"❌ Low disk space: {free_gb}GB free")
                return False
            
            self.logger.info(f"✅ Disk space check passed: {free_gb}GB free")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not check disk space: {str(e)}")
            return True  # Don't fail on this check
    
    async def _check_api_connectivity(self) -> bool:
        """Check API connectivity"""
        
        try:
            # Simple test - this will validate OpenAI key without making expensive calls
            import openai
            
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Test with minimal call
            try:
                models = client.models.list()
                self.logger.info("✅ OpenAI API connectivity verified")
                return True
            except Exception as e:
                self.logger.error(f"❌ OpenAI API connectivity failed: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"API connectivity check error: {str(e)}")
            return False
    
    async def _process_with_retries(self) -> Dict[str, Any]:
        """Process batch with retry logic"""
        
        for attempt in range(self.config['max_retries']):
            try:
                self.logger.info(f"Processing attempt {attempt + 1}/{self.config['max_retries']}")
                
                result = await self.service.process_batch(
                    batch_size=self.config['batch_size'],
                    dry_run=self.config['dry_run']
                )
                
                # Check if we got reasonable results
                if result['processed'] > 0:
                    self.logger.info(f"✅ Batch processed successfully: {result['processed']} leads")
                    return result
                else:
                    self.logger.warning("⚠️  No leads processed in this attempt")
                    if attempt < self.config['max_retries'] - 1:
                        await asyncio.sleep(self.config['retry_delay'])
                        continue
                    else:
                        return result
                        
            except Exception as e:
                self.logger.error(f"Batch processing attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.config['max_retries'] - 1:
                    self.logger.info(f"Retrying in {self.config['retry_delay']} seconds...")
                    await asyncio.sleep(self.config['retry_delay'])
                else:
                    raise e
        
        return {'processed': 0, 'error': 'All retry attempts failed'}
    
    async def _post_process_results(self, result: Dict[str, Any]):
        """Post-process batch results"""
        
        # Update daily statistics
        self.daily_stats.update({
            'end_time': datetime.now(),
            'processed': result.get('processed', 0),
            'duration': (datetime.now() - self.daily_stats['start_time']).total_seconds()
        })
        
        # Process individual results
        if 'results' in result:
            for lead_result in result['results']:
                lead_id = lead_result.get('lead_id', 'unknown')
                status = lead_result.get('final_status', 'unknown')
                
                if status == 'approved':
                    self.daily_stats['approved'] += 1
                    self.daily_stats['successful_leads'].append(lead_id)
                elif status == 'manual_review':
                    self.daily_stats['manual_review'] += 1
                elif status == 'error':
                    self.daily_stats['errors'] += 1
                    self.daily_stats['failed_leads'].append({
                        'lead_id': lead_id,
                        'error': lead_result.get('error', 'Unknown error')
                    })
        
        # Handle error notifications
        if self.daily_stats['errors'] >= self.config['notification_threshold']:
            await self._send_error_notification()
        
        # Save detailed results
        await self._save_daily_results(result)
    
    def _generate_daily_report(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive daily report"""
        
        duration = self.daily_stats.get('duration', 0)
        processed = self.daily_stats['processed']
        
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'execution_time': datetime.now().isoformat(),
            'duration_seconds': duration,
            'duration_minutes': round(duration / 60, 2),
            'configuration': self.config,
            'statistics': {
                'processed': processed,
                'approved': self.daily_stats['approved'],
                'manual_review': self.daily_stats['manual_review'],
                'errors': self.daily_stats['errors'],
                'approval_rate': (self.daily_stats['approved'] / max(1, processed)) * 100,
                'error_rate': (self.daily_stats['errors'] / max(1, processed)) * 100
            },
            'performance': {
                'leads_per_minute': processed / max(1, duration / 60),
                'average_time_per_lead': duration / max(1, processed)
            },
            'failed_leads': self.daily_stats['failed_leads'],
            'successful_leads': self.daily_stats['successful_leads'],
            'service_health': self.service.health_check(),
            'raw_result': result
        }
        
        return report
    
    async def _send_error_notification(self):
        """Send error notification if threshold exceeded"""
        
        if not self.config['enable_notifications']:
            return
        
        error_count = self.daily_stats['errors']
        threshold = self.config['notification_threshold']
        
        self.logger.warning(f"🚨 Error threshold exceeded: {error_count} errors >= {threshold}")
        
        # Create error summary
        error_summary = {
            'timestamp': datetime.now().isoformat(),
            'error_count': error_count,
            'threshold': threshold,
            'failed_leads': self.daily_stats['failed_leads'],
            'total_processed': self.daily_stats['processed']
        }
        
        # Save error notification
        error_dir = Path("logs/errors")
        error_dir.mkdir(parents=True, exist_ok=True)
        
        error_file = error_dir / f"error_notification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(error_file, 'w') as f:
            json.dump(error_summary, f, indent=2)
        
        # Print to console for immediate attention
        print("\n" + "="*60)
        print("🚨 CAMPAIGN BRAIN ERROR NOTIFICATION")
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Errors: {error_count} (threshold: {threshold})")
        print(f"Total Processed: {self.daily_stats['processed']}")
        print("\nFailed Leads:")
        for failed in self.daily_stats['failed_leads'][:5]:  # Show first 5
            print(f"  • {failed['lead_id']}: {failed['error']}")
        if len(self.daily_stats['failed_leads']) > 5:
            print(f"  ... and {len(self.daily_stats['failed_leads']) - 5} more")
        print(f"\nError details saved to: {error_file}")
        print("="*60)
    
    async def _save_daily_results(self, result: Dict[str, Any]):
        """Save detailed daily results"""
        
        results_dir = Path("logs/daily_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime('%Y%m%d')
        results_file = results_dir / f"daily_results_{today}.json"
        
        daily_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'statistics': self.daily_stats,
            'configuration': self.config,
            'batch_result': result,
            'service_stats': self.service.get_stats()
        }
        
        with open(results_file, 'w') as f:
            json.dump(daily_data, f, indent=2, default=str)
        
        self.logger.info(f"Daily results saved to: {results_file}")
    
    def _create_failure_result(self, error_message: str) -> Dict[str, Any]:
        """Create failure result structure"""
        
        return {
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'statistics': self.daily_stats,
            'duration': (datetime.now() - self.daily_stats['start_time']).total_seconds()
        }


async def main():
    """Main entry point for daily batch processing"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily Batch Processor for Campaign Brain")
    parser.add_argument('--batch-size', type=int, help='Override batch size')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--force', action='store_true', help='Force run even if already ran today')
    parser.add_argument('--report-only', action='store_true', help='Generate report from existing data')
    
    args = parser.parse_args()
    
    # Override config with command line args
    if args.batch_size:
        os.environ['DAILY_BATCH_SIZE'] = str(args.batch_size)
    if args.dry_run:
        os.environ['DAILY_DRY_RUN'] = 'true'
    
    try:
        processor = DailyBatchProcessor()
        
        if args.report_only:
            # Generate report from existing data
            print("📊 Generating daily report from existing data...")
            # Implementation for report-only mode
            return True
        
        # Check if already ran today (unless forced)
        if not args.force:
            today = datetime.now().strftime('%Y%m%d')
            results_file = Path(f"logs/daily_results/daily_results_{today}.json")
            
            if results_file.exists():
                print(f"⚠️  Daily batch already ran today. Use --force to run again.")
                print(f"Existing results: {results_file}")
                return True
        
        # Run daily batch
        result = await processor.run_daily_batch()
        
        # Print summary
        if result.get('success', True):
            stats = result.get('statistics', {})
            print(f"\n✅ Daily Batch Completed Successfully")
            print(f"Processed: {stats.get('processed', 0)} leads")
            print(f"Approved: {stats.get('approved', 0)} campaigns")
            print(f"Manual Review: {stats.get('manual_review', 0)} campaigns")
            print(f"Errors: {stats.get('errors', 0)}")
            print(f"Approval Rate: {stats.get('approval_rate', 0):.1f}%")
            return True
        else:
            print(f"\n❌ Daily Batch Failed: {result.get('error', 'Unknown error')}")
            return False
            
    except KeyboardInterrupt:
        print("\n\nDaily batch processing interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ Daily batch processing error: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)