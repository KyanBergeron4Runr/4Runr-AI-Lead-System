#!/usr/bin/env python3
"""
Verify that the 4Runr system is completely clean of mock/fake data
"""

import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('clean-system-verifier')

def verify_clean_system():
    """Verify the system contains no mock or fake data"""
    
    shared_dir = Path(__file__).parent / "shared"
    
    # Check for pipeline data files
    pipeline_files = [
        "raw_leads.json",
        "verified_leads.json", 
        "enriched_leads.json",
        "engaged_leads.json",
        "dropped_leads.json"
    ]
    
    logger.info("🧹 Verifying system is clean of mock/fake data...")
    
    all_clean = True
    
    for file_name in pipeline_files:
        file_path = shared_dir / file_name
        if file_path.exists():
            logger.warning(f"⚠️ Found pipeline file: {file_name}")
            all_clean = False
        else:
            logger.info(f"✅ Clean: {file_name} - Not found")
    
    # Check control.json
    control_file = shared_dir / "control.json"
    if control_file.exists():
        with open(control_file, 'r') as f:
            control_data = json.load(f)
        
        if control_data.get("lead_count", 0) == 0 and control_data.get("status") == "ready":
            logger.info("✅ Clean: control.json - Reset to clean state")
        else:
            logger.warning(f"⚠️ control.json contains data: {control_data}")
            all_clean = False
    
    # Check for test files with mock data
    test_files_to_check = [
        "test_mock_scraper.py",
        "inject_test_data.py", 
        "test_verifier.py",
        "test_data_templates/test_lead.json"
    ]
    
    for test_file in test_files_to_check:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            logger.warning(f"⚠️ Found test file with potential mock data: {test_file}")
            all_clean = False
        else:
            logger.info(f"✅ Clean: {test_file} - Removed")
    
    if all_clean:
        logger.info("🎉 SYSTEM IS COMPLETELY CLEAN!")
        logger.info("✅ No mock or fake data found")
        logger.info("✅ All pipeline files cleared")
        logger.info("✅ Test files with mock data removed")
        logger.info("✅ Ready for real LinkedIn lead generation")
        return True
    else:
        logger.error("❌ System still contains mock/fake data")
        return False

if __name__ == "__main__":
    verify_clean_system()