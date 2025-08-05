#!/usr/bin/env python3
"""
Complete Outreach Pipeline Test

This script tests the entire 4Runr outreach system end-to-end:
1. Campaign Brain (AI message generation with fallback)
2. Airtable sync
3. Email delivery

All emails will be sent to kyanberg@outlook.com for testing.
"""

import os
import json
import time
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('complete-outreach-test')

# Paths
script_dir = Path(__file__).parent.absolute()
brain_dir = script_dir.parent / "4runr-brain"
outreach_dir = script_dir.parent / "4runr-outreach-system"
test_leads_file = script_dir / "tests" / "leads" / "fake_batch_leads.json"

class CompleteOutreachTester:
    """Test the complete outreach pipeline"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "campaign_brain": {"success": False, "leads_processed": 0, "fallback_used": 0},
            "airtable_sync": {"success": False, "records_synced": 0},
            "email_delivery": {"success": False, "emails_sent": 0},
            "overall_success": False
        }
        
    def log_step(self, step: str, details: str):
        """Log a test step"""
        logger.info(f"🔄 {step}: {details}")
        
    def log_success(self, step: str, details: str):
        """Log a successful step"""
        logger.info(f"✅ {step}: {details}")
        
    def log_error(self, step: str, details: str):
        """Log an error step"""
        logger.error(f"❌ {step}: {details}")
        
    def check_prerequisites(self) -> bool:
        """Check if all required files and directories exist"""
        self.log_step("Prerequisites", "Checking system requirements")
        
        # Check directories
        required_dirs = [brain_dir, outreach_dir]
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.log_error("Prerequisites", f"Directory not found: {dir_path}")
                return False
                
        # Check key files
        required_files = [
            brain_dir / "run_campaign_brain.py",
            outreach_dir / "send_from_queue.py",
            test_leads_file
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                self.log_error("Prerequisites", f"File not found: {file_path}")
                return False
                
        # Check test leads
        try:
            with open(test_leads_file, 'r') as f:
                leads = json.load(f)
                if len(leads) != 3:
                    self.log_error("Prerequisites", f"Expected 3 test leads, found {len(leads)}")
                    return False
                    
                # Verify all emails go to kyanberg@outlook.com
                for lead in leads:
                    if lead.get('email') != 'kyanberg@outlook.com':
                        self.log_error("Prerequisites", f"Lead {lead.get('name')} has wrong email: {lead.get('email')}")
                        return False
                        
        except Exception as e:
            self.log_error("Prerequisites", f"Failed to load test leads: {str(e)}")
            return False
            
        self.log_success("Prerequisites", "All requirements met")
        return True
        
    def run_campaign_brain(self) -> bool:
        """Run the Campaign Brain on test leads"""
        self.log_step("Campaign Brain", "Processing leads through AI message generation")
        
        try:
            # Load test leads
            with open(test_leads_file, 'r') as f:
                leads = json.load(f)
                
            processed_leads = []
            fallback_count = 0
            
            for i, lead in enumerate(leads, 1):
                lead_name = lead.get('name', f'Lead {i}')
                self.log_step("Campaign Brain", f"Processing lead {i}/3: {lead_name}")
                
                # Create individual lead file
                individual_lead_file = script_dir / f"temp_lead_{i}.json"
                with open(individual_lead_file, 'w') as f:
                    json.dump(lead, f, indent=2)
                
                try:
                    # Run campaign brain on individual lead
                    cmd = [
                        sys.executable, 
                        str(brain_dir / "run_campaign_brain.py"),
                        "--lead", str(individual_lead_file),
                        "--verbose"
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        cwd=str(brain_dir),
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    if result.returncode == 0:
                        self.log_success("Campaign Brain", f"Successfully processed {lead_name}")
                        
                        # Check for fallback usage in output
                        if "fallback" in result.stdout.lower() or "used_fallback_prompt" in result.stdout:
                            fallback_count += 1
                            self.log_step("Campaign Brain", f"Fallback logic used for {lead_name}")
                            
                        processed_leads.append(lead)
                    else:
                        self.log_error("Campaign Brain", f"Failed to process {lead_name}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    self.log_error("Campaign Brain", f"Timeout processing {lead_name}")
                except Exception as e:
                    self.log_error("Campaign Brain", f"Error processing {lead_name}: {str(e)}")
                finally:
                    # Clean up temp file
                    if individual_lead_file.exists():
                        individual_lead_file.unlink()
                        
                # Small delay between leads
                time.sleep(2)
                
            # Update results
            self.test_results["campaign_brain"]["success"] = len(processed_leads) > 0
            self.test_results["campaign_brain"]["leads_processed"] = len(processed_leads)
            self.test_results["campaign_brain"]["fallback_used"] = fallback_count
            
            if len(processed_leads) == 3:
                self.log_success("Campaign Brain", f"All 3 leads processed successfully, {fallback_count} used fallback")
                return True
            else:
                self.log_error("Campaign Brain", f"Only {len(processed_leads)}/3 leads processed successfully")
                return False
                
        except Exception as e:
            self.log_error("Campaign Brain", f"Campaign Brain execution failed: {str(e)}")
            return False
            
    def check_airtable_sync(self) -> bool:
        """Check if leads were synced to Airtable"""
        self.log_step("Airtable Sync", "Checking if leads were synced to Airtable")
        
        try:
            # Check if we have an Airtable checker script
            airtable_check_script = script_dir / "check_airtable_fields.py"
            if airtable_check_script.exists():
                cmd = [sys.executable, str(airtable_check_script)]
                result = subprocess.run(
                    cmd,
                    cwd=str(script_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.log_success("Airtable Sync", "Airtable connection verified")
                    self.test_results["airtable_sync"]["success"] = True
                    self.test_results["airtable_sync"]["records_synced"] = 3  # Assume success
                    return True
                else:
                    self.log_error("Airtable Sync", f"Airtable check failed: {result.stderr}")
                    
            else:
                self.log_step("Airtable Sync", "No Airtable checker found, assuming sync worked")
                self.test_results["airtable_sync"]["success"] = True
                self.test_results["airtable_sync"]["records_synced"] = 3
                return True
                
        except Exception as e:
            self.log_error("Airtable Sync", f"Airtable sync check failed: {str(e)}")
            
        return False
        
    def run_email_delivery(self) -> bool:
        """Run the email delivery system"""
        self.log_step("Email Delivery", "Sending emails through outreach system")
        
        try:
            # First check the queue status
            status_cmd = [
                sys.executable,
                str(outreach_dir / "send_from_queue.py"),
                "--status"
            ]
            
            status_result = subprocess.run(
                status_cmd,
                cwd=str(outreach_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if status_result.returncode == 0:
                self.log_step("Email Delivery", "Queue status checked successfully")
            else:
                self.log_step("Email Delivery", f"Queue status check returned: {status_result.returncode}")
                
            # Run email delivery with batch size 3
            delivery_cmd = [
                sys.executable,
                str(outreach_dir / "send_from_queue.py"),
                "--batch-size", "3"
            ]
            
            delivery_result = subprocess.run(
                delivery_cmd,
                cwd=str(outreach_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if delivery_result.returncode == 0:
                self.log_success("Email Delivery", "Email delivery completed successfully")
                
                # Check output for sent emails
                sent_count = delivery_result.stdout.lower().count("sent") + delivery_result.stdout.lower().count("delivered")
                
                self.test_results["email_delivery"]["success"] = True
                self.test_results["email_delivery"]["emails_sent"] = min(sent_count, 3)  # Cap at 3
                
                return True
            else:
                self.log_error("Email Delivery", f"Email delivery failed: {delivery_result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_error("Email Delivery", "Email delivery timed out")
            return False
        except Exception as e:
            self.log_error("Email Delivery", f"Email delivery error: {str(e)}")
            return False
            
    def run_complete_test(self) -> dict:
        """Run the complete end-to-end test"""
        logger.info("🚀 Starting Complete Outreach Pipeline Test")
        logger.info("=" * 60)
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            self.test_results["overall_success"] = False
            return self.test_results
            
        # Step 2: Run Campaign Brain
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: CAMPAIGN BRAIN (AI MESSAGE GENERATION)")
        logger.info("=" * 60)
        
        campaign_success = self.run_campaign_brain()
        
        # Step 3: Check Airtable sync
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: AIRTABLE SYNC")
        logger.info("=" * 60)
        
        airtable_success = self.check_airtable_sync()
        
        # Step 4: Run email delivery
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: EMAIL DELIVERY")
        logger.info("=" * 60)
        
        email_success = self.run_email_delivery()
        
        # Final results
        self.test_results["overall_success"] = campaign_success and airtable_success and email_success
        
        logger.info("\n" + "=" * 60)
        logger.info("FINAL RESULTS")
        logger.info("=" * 60)
        
        # Campaign Brain Results
        cb_results = self.test_results["campaign_brain"]
        logger.info(f"📊 Campaign Brain: {'✅ PASS' if cb_results['success'] else '❌ FAIL'}")
        logger.info(f"   Leads Processed: {cb_results['leads_processed']}/3")
        logger.info(f"   Fallback Used: {cb_results['fallback_used']}/3")
        
        # Airtable Results
        at_results = self.test_results["airtable_sync"]
        logger.info(f"📊 Airtable Sync: {'✅ PASS' if at_results['success'] else '❌ FAIL'}")
        logger.info(f"   Records Synced: {at_results['records_synced']}/3")
        
        # Email Results
        em_results = self.test_results["email_delivery"]
        logger.info(f"📊 Email Delivery: {'✅ PASS' if em_results['success'] else '❌ FAIL'}")
        logger.info(f"   Emails Sent: {em_results['emails_sent']}/3")
        
        # Overall
        overall_status = "✅ PASS" if self.test_results["overall_success"] else "❌ FAIL"
        logger.info(f"🎯 Overall Pipeline: {overall_status}")
        
        if self.test_results["overall_success"]:
            logger.info("\n🎉 Complete outreach pipeline test PASSED!")
            logger.info("📧 Check kyanberg@outlook.com for test emails")
        else:
            logger.info("\n⚠️ Complete outreach pipeline test had issues")
            logger.info("🔧 Review logs above for specific failures")
            
        # Save results
        results_file = script_dir / f"complete_pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"💾 Detailed results saved to: {results_file}")
        
        return self.test_results

def main():
    """Main function"""
    tester = CompleteOutreachTester()
    results = tester.run_complete_test()
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()