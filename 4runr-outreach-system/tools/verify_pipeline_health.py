#!/usr/bin/env python3
"""
Pipeline Health Validator for 4Runr Enhanced Engagement System

Performs comprehensive end-to-end validation of the entire pipeline without
sending real emails or making permanent changes. Provides detailed diagnostics
and health reports for production readiness verification.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import system components
try:
    from engager.enhanced_engager_agent import EnhancedEngagerAgent
    from engager.website_scraper_service import WebsiteScraperService
    from engager.local_database_manager import LocalDatabaseManager
    from shared.airtable_client import AirtableClient
    # Use standard logging for the health validator
    import logging
    from shared.config import Config
    
    # Import fallback message generator from lead scraper
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4runr-lead-scraper"))
    from enricher.fallback_message_generator import FallbackMessageGenerator, should_use_fallback_messaging
    
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    import_error = str(e)

@dataclass
class LeadHealthStatus:
    """Health status for a single lead."""
    lead_id: str
    full_name: str
    email: str
    status: str  # 'enriched', 'fallback', 'skipped', 'error'
    has_website: bool
    has_business_type: bool
    has_response_notes: bool
    email_confidence: str
    action_taken: str
    error_message: Optional[str] = None
    fallback_reason: Optional[str] = None

@dataclass
class PipelineHealthReport:
    """Complete pipeline health report."""
    pipeline_ok: bool
    tested: int
    enriched: int
    fallback_used: int
    skipped: int
    errors: int
    error_details: List[str]
    missing_fields_summary: Dict[str, int]
    component_status: Dict[str, bool]
    execution_time: float
    timestamp: str
    lead_details: List[Dict[str, Any]]

class PipelineHealthValidator:
    """
    Comprehensive pipeline health validator for the 4Runr system.
    
    Performs dry-run validation of the entire engagement pipeline without
    making permanent changes or sending real emails.
    """
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize the pipeline health validator.
        
        Args:
            dry_run: If True, prevents any permanent changes or email sending
        """
        self.dry_run = dry_run
        self.logger = logging.getLogger('pipeline-health-validator')
        
        # Initialize components
        self.components_status = {}
        self.airtable_client = None
        self.enhanced_engager = None
        self.website_scraper = None
        self.fallback_generator = None
        self.db_manager = None
        
        # Health tracking
        self.lead_statuses: List[LeadHealthStatus] = []
        self.missing_fields = {
            'Website': 0,
            'Business_Type': 0,
            'Response Notes': 0,
            'Full Name': 0,
            'Email': 0
        }
        
        self.logger.info("🏥 Pipeline Health Validator initialized")
        self.logger.info(f"🔒 Dry run mode: {'ENABLED' if self.dry_run else 'DISABLED'}")
    
    def validate_components(self) -> bool:
        """
        Validate that all required components are available and functional.
        
        Returns:
            bool: True if all components are healthy
        """
        self.logger.info("🔧 Validating system components...")
        
        if not COMPONENTS_AVAILABLE:
            self.logger.error(f"❌ Component import failed: {import_error}")
            self.components_status['imports'] = False
            return False
        
        self.components_status['imports'] = True
        
        # Test Airtable connection
        try:
            self.airtable_client = AirtableClient()
            # Test connection with a simple query
            test_leads = self.airtable_client.get_leads_for_outreach(limit=1)
            self.components_status['airtable'] = True
            self.logger.info("✅ Airtable connection: OK")
        except Exception as e:
            self.logger.error(f"❌ Airtable connection failed: {str(e)}")
            self.components_status['airtable'] = False
        
        # Test Enhanced Engager Agent
        try:
            self.enhanced_engager = EnhancedEngagerAgent()
            self.components_status['enhanced_engager'] = True
            self.logger.info("✅ Enhanced Engager Agent: OK")
        except Exception as e:
            self.logger.error(f"❌ Enhanced Engager Agent failed: {str(e)}")
            self.components_status['enhanced_engager'] = False
        
        # Test Website Scraper Service
        try:
            self.website_scraper = WebsiteScraperService()
            self.components_status['website_scraper'] = True
            self.logger.info("✅ Website Scraper Service: OK")
        except Exception as e:
            self.logger.error(f"❌ Website Scraper Service failed: {str(e)}")
            self.components_status['website_scraper'] = False
        
        # Test Fallback Message Generator
        try:
            self.fallback_generator = FallbackMessageGenerator(use_ai=False)  # Use template mode for reliability
            self.components_status['fallback_generator'] = True
            self.logger.info("✅ Fallback Message Generator: OK")
        except Exception as e:
            self.logger.error(f"❌ Fallback Message Generator failed: {str(e)}")
            self.components_status['fallback_generator'] = False
        
        # Test Database Manager
        try:
            self.db_manager = LocalDatabaseManager()
            self.components_status['database'] = True
            self.logger.info("✅ Database Manager: OK")
        except Exception as e:
            self.logger.error(f"❌ Database Manager failed: {str(e)}")
            self.components_status['database'] = False
        
        # Overall component health
        all_healthy = all(self.components_status.values())
        
        if all_healthy:
            self.logger.info("🎉 All components are healthy!")
        else:
            failed_components = [name for name, status in self.components_status.items() if not status]
            self.logger.warning(f"⚠️ Failed components: {', '.join(failed_components)}")
        
        return all_healthy
    
    def get_test_leads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get test leads from Airtable for validation.
        
        Args:
            limit: Maximum number of leads to retrieve
            
        Returns:
            List of lead dictionaries
        """
        self.logger.info(f"📋 Retrieving {limit} test leads from Airtable...")
        
        if not self.airtable_client:
            self.logger.error("❌ Airtable client not available")
            return []
        
        try:
            # Get leads for testing (use the available method)
            leads = self.airtable_client.get_leads_for_outreach(limit=limit)
            
            self.logger.info(f"✅ Retrieved {len(leads)} test leads")
            return leads
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve test leads: {str(e)}")
            return []
    
    def validate_lead_fields(self, lead: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that a lead has required fields.
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Tuple of (is_valid, missing_fields_list)
        """
        required_fields = ['Full Name', 'Email']
        optional_fields = ['Website', 'Business_Type', 'Response Notes']
        
        missing_required = []
        missing_optional = []
        
        # Check required fields
        for field in required_fields:
            if not lead.get(field) or lead.get(field) == '':
                missing_required.append(field)
                self.missing_fields[field] += 1
        
        # Check optional fields (for reporting)
        for field in optional_fields:
            if not lead.get(field) or lead.get(field) == '':
                missing_optional.append(field)
                if field in self.missing_fields:
                    self.missing_fields[field] += 1
        
        is_valid = len(missing_required) == 0
        all_missing = missing_required + missing_optional
        
        return is_valid, all_missing
    
    def simulate_lead_processing(self, lead: Dict[str, Any]) -> LeadHealthStatus:
        """
        Simulate processing a single lead through the entire pipeline.
        
        Args:
            lead: Lead dictionary from Airtable
            
        Returns:
            LeadHealthStatus with processing results
        """
        lead_id = lead.get('id', 'unknown')
        full_name = lead.get('Full Name', '')
        email = lead.get('Email', '')
        
        self.logger.info(f"🧪 Simulating processing for: {full_name} ({email})")
        
        # Initialize status
        status = LeadHealthStatus(
            lead_id=lead_id,
            full_name=full_name,
            email=email,
            status='unknown',
            has_website=bool(lead.get('Website')),
            has_business_type=bool(lead.get('Business_Type') and lead.get('Business_Type') != 'Unknown'),
            has_response_notes=bool(lead.get('Response Notes')),
            email_confidence=lead.get('Email_Confidence_Level', ''),
            action_taken='none'
        )
        
        try:
            # Step 1: Validate lead fields
            is_valid, missing_fields = self.validate_lead_fields(lead)
            
            if not is_valid:
                status.status = 'error'
                status.error_message = f"Missing required fields: {', '.join([f for f in missing_fields if f in ['Full Name', 'Email']])}"
                status.action_taken = 'skipped_invalid'
                return status
            
            # Step 2: Check email confidence
            email_confidence = lead.get('Email_Confidence_Level', '').lower()
            if email_confidence not in ['real', 'pattern']:
                status.status = 'skipped'
                status.action_taken = 'skipped_low_confidence'
                return status
            
            # Step 3: Determine processing path
            has_enrichment_data = (
                status.has_business_type and 
                status.has_response_notes and 
                status.has_website
            )
            
            if has_enrichment_data:
                # Full enrichment path
                status.status = 'enriched'
                status.action_taken = 'full_enrichment'
                
                # Simulate message generation with full data
                if self.dry_run:
                    self.logger.info(f"   🎯 Would generate enriched message for {full_name}")
                else:
                    # In non-dry-run mode, we could actually generate the message
                    pass
                    
            else:
                # Check if fallback should be used
                fallback_decision = should_use_fallback_messaging(lead)
                
                if fallback_decision.get('should_use_fallback', False):
                    # Fallback message path
                    status.status = 'fallback'
                    status.action_taken = 'fallback_message'
                    status.fallback_reason = '; '.join(fallback_decision.get('reasons', [])[:2])
                    
                    # Simulate fallback message generation
                    if self.dry_run:
                        self.logger.info(f"   🔄 Would generate fallback message for {full_name}")
                        self.logger.info(f"      Reason: {status.fallback_reason}")
                    else:
                        # In non-dry-run mode, we could actually generate the fallback message
                        pass
                else:
                    # Skip lead
                    status.status = 'skipped'
                    status.action_taken = 'skipped_no_fallback'
                    status.error_message = '; '.join(fallback_decision.get('reasons', [])[:2])
            
            self.logger.info(f"   ✅ Simulation complete: {status.status} ({status.action_taken})")
            
        except Exception as e:
            status.status = 'error'
            status.error_message = str(e)
            status.action_taken = 'error_processing'
            self.logger.error(f"   ❌ Simulation failed: {str(e)}")
        
        return status
    
    def run_health_check(self, limit: int = 10) -> PipelineHealthReport:
        """
        Run comprehensive pipeline health check.
        
        Args:
            limit: Number of leads to test
            
        Returns:
            PipelineHealthReport with complete results
        """
        start_time = datetime.now()
        self.logger.info("🏥 Starting comprehensive pipeline health check...")
        
        # Step 1: Validate components
        components_healthy = self.validate_components()
        
        # Step 2: Get test leads
        test_leads = self.get_test_leads(limit) if components_healthy else []
        
        # Step 3: Process each lead
        if test_leads:
            self.logger.info(f"🔄 Processing {len(test_leads)} test leads...")
            
            for i, lead in enumerate(test_leads, 1):
                self.logger.info(f"📋 Processing lead {i}/{len(test_leads)}")
                lead_status = self.simulate_lead_processing(lead)
                self.lead_statuses.append(lead_status)
        
        # Step 4: Generate report
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        enriched_count = len([s for s in self.lead_statuses if s.status == 'enriched'])
        fallback_count = len([s for s in self.lead_statuses if s.status == 'fallback'])
        skipped_count = len([s for s in self.lead_statuses if s.status == 'skipped'])
        error_count = len([s for s in self.lead_statuses if s.status == 'error'])
        
        # Collect error details
        error_details = [
            f"{s.full_name}: {s.error_message}" 
            for s in self.lead_statuses 
            if s.error_message
        ]
        
        # Overall pipeline health
        pipeline_ok = (
            components_healthy and 
            len(test_leads) > 0 and 
            error_count < len(test_leads) * 0.5  # Less than 50% errors
        )
        
        report = PipelineHealthReport(
            pipeline_ok=pipeline_ok,
            tested=len(self.lead_statuses),
            enriched=enriched_count,
            fallback_used=fallback_count,
            skipped=skipped_count,
            errors=error_count,
            error_details=error_details,
            missing_fields_summary=dict(self.missing_fields),
            component_status=self.components_status,
            execution_time=execution_time,
            timestamp=start_time.isoformat(),
            lead_details=[asdict(status) for status in self.lead_statuses]
        )
        
        self.logger.info("📊 Health check complete!")
        self._log_report_summary(report)
        
        return report
    
    def _log_report_summary(self, report: PipelineHealthReport) -> None:
        """Log a summary of the health report."""
        self.logger.info("=" * 60)
        self.logger.info("📊 PIPELINE HEALTH REPORT SUMMARY")
        self.logger.info("=" * 60)
        
        status_emoji = "✅" if report.pipeline_ok else "❌"
        self.logger.info(f"{status_emoji} Overall Pipeline Status: {'HEALTHY' if report.pipeline_ok else 'UNHEALTHY'}")
        
        self.logger.info(f"📋 Leads Tested: {report.tested}")
        self.logger.info(f"🎯 Enriched: {report.enriched}")
        self.logger.info(f"🔄 Fallback Used: {report.fallback_used}")
        self.logger.info(f"⏭️ Skipped: {report.skipped}")
        self.logger.info(f"❌ Errors: {report.errors}")
        
        if report.missing_fields_summary:
            self.logger.info("📋 Missing Fields Summary:")
            for field, count in report.missing_fields_summary.items():
                if count > 0:
                    self.logger.info(f"   • {field}: {count} leads")
        
        if report.error_details:
            self.logger.info("❌ Error Details:")
            for error in report.error_details[:5]:  # Show first 5 errors
                self.logger.info(f"   • {error}")
            if len(report.error_details) > 5:
                self.logger.info(f"   ... and {len(report.error_details) - 5} more errors")
        
        self.logger.info(f"⏱️ Execution Time: {report.execution_time:.2f} seconds")
        self.logger.info("=" * 60)
    
    def save_report(self, report: PipelineHealthReport, output_path: str = None) -> str:
        """
        Save the health report to a JSON file.
        
        Args:
            report: PipelineHealthReport to save
            output_path: Optional custom output path
            
        Returns:
            Path to the saved report file
        """
        if output_path is None:
            # Create logs directory if it doesn't exist
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            output_path = logs_dir / "pipeline_health_report.json"
        
        try:
            with open(output_path, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            
            self.logger.info(f"💾 Health report saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save report: {str(e)}")
            return ""

def main():
    """Main function for running the pipeline health validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Pipeline Health Validator')
    parser.add_argument('--limit', type=int, default=10, help='Number of leads to test (default: 10)')
    parser.add_argument('--output', type=str, help='Output file path for the report')
    parser.add_argument('--no-dry-run', action='store_true', help='Disable dry run mode (DANGEROUS)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize validator
    dry_run = not args.no_dry_run
    validator = PipelineHealthValidator(dry_run=dry_run)
    
    if not dry_run:
        print("⚠️ WARNING: Dry run mode is DISABLED. This may make permanent changes!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    # Run health check
    try:
        report = validator.run_health_check(limit=args.limit)
        
        # Save report
        output_path = validator.save_report(report, args.output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 PIPELINE HEALTH CHECK COMPLETE")
        print("=" * 60)
        print(f"Status: {'✅ HEALTHY' if report.pipeline_ok else '❌ UNHEALTHY'}")
        print(f"Tested: {report.tested} leads")
        print(f"Enriched: {report.enriched}")
        print(f"Fallback: {report.fallback_used}")
        print(f"Skipped: {report.skipped}")
        print(f"Errors: {report.errors}")
        print(f"Report saved to: {output_path}")
        print("=" * 60)
        
        # Exit with appropriate code
        sys.exit(0 if report.pipeline_ok else 1)
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()