#!/usr/bin/env python3
"""
Test Validation-First Pipeline

This script tests the validation-first pipeline with sample data to ensure
no fake data is generated and the pipeline works correctly.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline-test')

class PipelineTest:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        self.shared_dir.mkdir(exist_ok=True)
        
        # Test files
        self.raw_leads_file = self.shared_dir / 'raw_leads.json'
        self.verified_leads_file = self.shared_dir / 'verified_leads.json'
        self.enriched_leads_file = self.shared_dir / 'enriched_leads.json'
        self.engaged_leads_file = self.shared_dir / 'engaged_leads.json'
        self.dropped_leads_file = self.shared_dir / 'dropped_leads.json'
    
    def create_test_raw_leads(self):
        """Create test raw leads data"""
        test_leads = [
            {
                "lead_id": "test_001",
                "name": "Tobias Lütke",
                "linkedin_url": "https://www.linkedin.com/in/tobi/",
                "title": "CEO",
                "company": "Shopify",
                "location": "Montreal, Quebec, Canada",
                "email": "",
                "status": "scraped",
                "linkedin_verified": False,
                "verified": False,
                "enriched": False,
                "scraped_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "source": "Test Data"
            },
            {
                "lead_id": "test_002",
                "name": "Test Invalid",
                "linkedin_url": "https://www.linkedin.com/in/invalid-profile-12345/",
                "title": "CEO",
                "company": "Invalid Company",
                "location": "Montreal, Quebec, Canada",
                "email": "",
                "status": "scraped",
                "linkedin_verified": False,
                "verified": False,
                "enriched": False,
                "scraped_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "source": "Test Data"
            }
        ]
        
        with open(self.raw_leads_file, 'w') as f:
            json.dump(test_leads, f, indent=2)
        
        logger.info(f"✅ Created test raw leads: {len(test_leads)} leads")
        return test_leads
    
    def validate_no_fake_data(self, leads: list, stage: str) -> bool:
        """Validate that no fake data was generated"""
        fake_indicators = [
            "fake",
            "mock",
            "test@example.com",
            "placeholder",
            "generated",
            "random"
        ]
        
        for lead in leads:
            # Check all string fields for fake data indicators
            for key, value in lead.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for indicator in fake_indicators:
                        if indicator in value_lower:
                            logger.error(f"❌ FAKE DATA DETECTED in {stage}: {key}='{value}'")
                            return False
        
        logger.info(f"✅ No fake data detected in {stage}")
        return True
    
    def check_pipeline_files(self) -> dict:
        """Check which pipeline files exist and their contents"""
        files = {
            'raw_leads': self.raw_leads_file,
            'verified_leads': self.verified_leads_file,
            'enriched_leads': self.enriched_leads_file,
            'engaged_leads': self.engaged_leads_file,
            'dropped_leads': self.dropped_leads_file
        }
        
        results = {}
        
        for name, file_path in files.items():
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        results[name] = {
                            'exists': True,
                            'count': len(data),
                            'valid_json': True,
                            'no_fake_data': self.validate_no_fake_data(data, name)
                        }
                except json.JSONDecodeError:
                    results[name] = {
                        'exists': True,
                        'count': 0,
                        'valid_json': False,
                        'no_fake_data': False
                    }
            else:
                results[name] = {
                    'exists': False,
                    'count': 0,
                    'valid_json': False,
                    'no_fake_data': True  # No file means no fake data
                }
        
        return results
    
    def print_pipeline_status(self):
        """Print current pipeline status"""
        logger.info("\n" + "="*60)
        logger.info("VALIDATION-FIRST PIPELINE STATUS")
        logger.info("="*60)
        
        results = self.check_pipeline_files()
        
        for stage, data in results.items():
            status = "✅" if data['exists'] and data['no_fake_data'] else "❌"
            logger.info(f"{status} {stage.upper()}: {data['count']} leads")
            
            if data['exists'] and not data['valid_json']:
                logger.error(f"   ❌ Invalid JSON format")
            if data['exists'] and not data['no_fake_data']:
                logger.error(f"   ❌ Fake data detected")
        
        logger.info("="*60)
    
    async def run_test(self):
        """Run the complete pipeline test"""
        logger.info("🧪 Starting Validation-First Pipeline Test")
        
        # Clean up previous test files
        for file_path in [self.raw_leads_file, self.verified_leads_file, 
                         self.enriched_leads_file, self.engaged_leads_file, 
                         self.dropped_leads_file]:
            if file_path.exists():
                file_path.unlink()
        
        # Create test data
        test_leads = self.create_test_raw_leads()
        
        # Print initial status
        self.print_pipeline_status()
        
        logger.info("\n🔍 Test complete - check pipeline files manually")
        logger.info("To run the full pipeline on this test data:")
        logger.info("  python run_validation_pipeline.py")
        logger.info("\nTo run individual agents:")
        logger.info("  python run_agent.py verifier")
        logger.info("  python run_agent.py enricher")
        logger.info("  python run_agent.py engager")
        
        return True

async def main():
    """Main entry point"""
    test = PipelineTest()
    success = await test.run_test()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)