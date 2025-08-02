#!/usr/bin/env python3
"""
Validation-First Pipeline Orchestrator

This script runs the complete validation-first pipeline:
1. Scraper Agent → raw_leads.json
2. Verifier Agent → verified_leads.json  
3. Enricher Agent → enriched_leads.json
4. Engager Agent → Airtable updates

No fake data is generated at any stage.
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('validation-pipeline')

class ValidationPipeline:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        self.shared_dir.mkdir(exist_ok=True)
        
        # Pipeline files
        self.raw_leads_file = self.shared_dir / 'raw_leads.json'
        self.verified_leads_file = self.shared_dir / 'verified_leads.json'
        self.enriched_leads_file = self.shared_dir / 'enriched_leads.json'
        self.dropped_leads_file = self.shared_dir / 'dropped_leads.json'
        
        # Agent directories
        self.scraper_dir = Path(__file__).parent / 'scraper'
        self.verifier_dir = Path(__file__).parent / 'verifier'
        self.enricher_dir = Path(__file__).parent / 'enricher'
        self.engager_dir = Path(__file__).parent / 'engager'
    
    def log_pipeline_status(self, stage: str, status: str, details: dict = None):
        """Log pipeline status with details"""
        logger.info(f"🔄 PIPELINE [{stage.upper()}]: {status}")
        if details:
            for key, value in details.items():
                logger.info(f"   {key}: {value}")
    
    def get_file_stats(self, file_path: Path) -> dict:
        """Get statistics about a pipeline file"""
        if not file_path.exists():
            return {"exists": False, "count": 0}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {"exists": True, "count": len(data)}
        except:
            return {"exists": True, "count": 0, "error": "Could not parse JSON"}
    
    async def run_scraper(self) -> bool:
        """Run the scraper agent to generate raw_leads.json"""
        try:
            self.log_pipeline_status("scraper", "Starting LinkedIn scraper")
            
            # Run scraper
            result = subprocess.run([
                sys.executable, 'app.py'
            ], cwd=self.scraper_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"❌ Scraper failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return False
            
            # Check if raw leads were generated
            stats = self.get_file_stats(self.raw_leads_file)
            
            if not stats["exists"] or stats["count"] == 0:
                logger.error("❌ Scraper completed but no raw leads were generated")
                logger.error("❌ This means no real LinkedIn profiles were found")
                return False
            
            self.log_pipeline_status("scraper", "Completed successfully", {
                "raw_leads_generated": stats["count"],
                "output_file": "raw_leads.json"
            })
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Scraper timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Scraper failed with error: {str(e)}")
            return False
    
    async def run_verifier(self) -> bool:
        """Run the verifier agent to validate LinkedIn URLs"""
        try:
            self.log_pipeline_status("verifier", "Starting LinkedIn URL verification")
            
            # Check if raw leads exist
            raw_stats = self.get_file_stats(self.raw_leads_file)
            if not raw_stats["exists"] or raw_stats["count"] == 0:
                logger.error("❌ No raw leads found to verify")
                return False
            
            # Run verifier
            result = subprocess.run([
                sys.executable, 'app.py'
            ], cwd=self.verifier_dir, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"❌ Verifier failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return False
            
            # Check verification results
            verified_stats = self.get_file_stats(self.verified_leads_file)
            dropped_stats = self.get_file_stats(self.dropped_leads_file)
            
            verification_rate = 0
            if raw_stats["count"] > 0:
                verification_rate = (verified_stats.get("count", 0) / raw_stats["count"]) * 100
            
            self.log_pipeline_status("verifier", "Completed successfully", {
                "raw_leads_processed": raw_stats["count"],
                "verified_leads": verified_stats.get("count", 0),
                "dropped_leads": dropped_stats.get("count", 0),
                "verification_rate": f"{verification_rate:.1f}%"
            })
            
            if verified_stats.get("count", 0) == 0:
                logger.warning("⚠️ No leads passed verification - pipeline cannot continue")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Verifier timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Verifier failed with error: {str(e)}")
            return False
    
    async def run_enricher(self) -> bool:
        """Run the enricher agent to add contact information"""
        try:
            self.log_pipeline_status("enricher", "Starting lead enrichment")
            
            # Check if verified leads exist
            verified_stats = self.get_file_stats(self.verified_leads_file)
            if not verified_stats["exists"] or verified_stats["count"] == 0:
                logger.error("❌ No verified leads found to enrich")
                return False
            
            # Run enricher
            result = subprocess.run([
                sys.executable, 'app.py'
            ], cwd=self.enricher_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"❌ Enricher failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return False
            
            # Check enrichment results
            enriched_stats = self.get_file_stats(self.enriched_leads_file)
            
            # Calculate enrichment success rate
            enrichment_rate = 0
            if verified_stats["count"] > 0:
                enrichment_rate = (enriched_stats.get("count", 0) / verified_stats["count"]) * 100
            
            self.log_pipeline_status("enricher", "Completed successfully", {
                "verified_leads_processed": verified_stats["count"],
                "enriched_leads": enriched_stats.get("count", 0),
                "enrichment_rate": f"{enrichment_rate:.1f}%"
            })
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Enricher timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Enricher failed with error: {str(e)}")
            return False
    
    async def run_engager(self) -> bool:
        """Run the engager agent to contact leads"""
        try:
            self.log_pipeline_status("engager", "Starting lead engagement")
            
            # Check if enriched leads exist
            enriched_stats = self.get_file_stats(self.enriched_leads_file)
            if not enriched_stats["exists"] or enriched_stats["count"] == 0:
                logger.error("❌ No enriched leads found to engage")
                return False
            
            # Run engager
            result = subprocess.run([
                sys.executable, 'app.py'
            ], cwd=self.engager_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"❌ Engager failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return False
            
            self.log_pipeline_status("engager", "Completed successfully", {
                "enriched_leads_processed": enriched_stats["count"],
                "engagement_status": "Check Airtable for results"
            })
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Engager timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Engager failed with error: {str(e)}")
            return False
    
    async def run_full_pipeline(self) -> bool:
        """Run the complete validation-first pipeline"""
        logger.info("🚀 Starting Validation-First Lead Generation Pipeline")
        logger.info("🔒 No fake data will be generated at any stage")
        
        pipeline_start = datetime.now()
        
        # Stage 1: Scraper
        logger.info("\n" + "="*60)
        logger.info("STAGE 1: LINKEDIN SCRAPER")
        logger.info("="*60)
        
        if not await self.run_scraper():
            logger.error("❌ Pipeline failed at scraper stage")
            return False
        
        # Stage 2: Verifier
        logger.info("\n" + "="*60)
        logger.info("STAGE 2: LINKEDIN URL VERIFIER")
        logger.info("="*60)
        
        if not await self.run_verifier():
            logger.error("❌ Pipeline failed at verifier stage")
            return False
        
        # Stage 3: Enricher
        logger.info("\n" + "="*60)
        logger.info("STAGE 3: LEAD ENRICHER")
        logger.info("="*60)
        
        if not await self.run_enricher():
            logger.error("❌ Pipeline failed at enricher stage")
            return False
        
        # Stage 4: Engager
        logger.info("\n" + "="*60)
        logger.info("STAGE 4: LEAD ENGAGER")
        logger.info("="*60)
        
        if not await self.run_engager():
            logger.error("❌ Pipeline failed at engager stage")
            return False
        
        # Pipeline completed successfully
        pipeline_end = datetime.now()
        duration = pipeline_end - pipeline_start
        
        logger.info("\n" + "="*60)
        logger.info("🎉 VALIDATION-FIRST PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        # Final statistics
        raw_stats = self.get_file_stats(self.raw_leads_file)
        verified_stats = self.get_file_stats(self.verified_leads_file)
        enriched_stats = self.get_file_stats(self.enriched_leads_file)
        dropped_stats = self.get_file_stats(self.dropped_leads_file)
        
        logger.info(f"📊 FINAL PIPELINE STATISTICS:")
        logger.info(f"   Raw leads scraped: {raw_stats.get('count', 0)}")
        logger.info(f"   Verified leads: {verified_stats.get('count', 0)}")
        logger.info(f"   Enriched leads: {enriched_stats.get('count', 0)}")
        logger.info(f"   Dropped leads: {dropped_stats.get('count', 0)}")
        logger.info(f"   Total duration: {duration}")
        logger.info(f"   No fake data generated: ✅")
        
        return True

async def main():
    """Main entry point"""
    pipeline = ValidationPipeline()
    
    # Check if we should run individual stages or full pipeline
    if len(sys.argv) > 1:
        stage = sys.argv[1].lower()
        
        if stage == "scraper":
            success = await pipeline.run_scraper()
        elif stage == "verifier":
            success = await pipeline.run_verifier()
        elif stage == "enricher":
            success = await pipeline.run_enricher()
        elif stage == "engager":
            success = await pipeline.run_engager()
        else:
            logger.error(f"❌ Unknown stage: {stage}")
            logger.info("Available stages: scraper, verifier, enricher, engager")
            return False
    else:
        # Run full pipeline
        success = await pipeline.run_full_pipeline()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)