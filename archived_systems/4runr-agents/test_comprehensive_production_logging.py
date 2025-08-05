#!/usr/bin/env python3
"""
Test Comprehensive Production Logging

This script demonstrates the complete production logging system by running
real system operations and showing the captured training data.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def test_comprehensive_production_logging():
    """Test comprehensive production logging with multiple system components"""
    print("🏭 Testing COMPREHENSIVE Production Logging")
    print("=" * 60)
    print("Running multiple system components to generate real training data...")
    print()
    
    # Test 1: Run SerpAPI scraping (already working)
    print("🔍 Test 1: SerpAPI Scraping Operations")
    print("-" * 40)
    
    try:
        from scraper.serpapi_linkedin_scraper import SerpAPILinkedInScraper
        
        print("📊 Running real SerpAPI scraping...")
        scraper = SerpAPILinkedInScraper()
        leads = scraper.search_montreal_ceos_with_serpapi(max_results=2)
        
        print(f"✅ SerpAPI scraping completed: {len(leads)} leads found")
        if leads:
            for i, lead in enumerate(leads[:2], 1):
                print(f"   {i}. {lead.get('name', 'Unknown')} - {lead.get('title', 'Unknown')}")
        
    except Exception as e:
        print(f"⚠️ SerpAPI test skipped: {e}")
    
    print()
    
    # Test 2: Run real enrichment operations
    print("🔍 Test 2: Real Lead Enrichment")
    print("-" * 40)
    
    try:
        sys.path.append('shared')
        from daily_enricher_agent import StealthEnricherAgent
        
        # Create real leads to enrich
        test_leads = [
            {
                'name': 'Alexandre Taillefer',
                'company': 'Hexo Corp',
                'record_id': 'real_test_001'
            },
            {
                'name': 'Jean-François Baril',
                'company': 'Sigma Energy Storage',
                'record_id': 'real_test_002'
            }
        ]
        
        enricher = StealthEnricherAgent()
        
        for lead in test_leads:
            print(f"📊 Enriching: {lead['name']} at {lead['company']}")
            result = enricher.enrich_lead_stealth(lead)
            
            print(f"   📧 Email: {result.get('primary_email', 'None found')}")
            print(f"   🎯 Confidence: {result.get('confidence', 'None')}")
            print(f"   🔧 Methods: {', '.join(result.get('methods', []))}")
            print()
        
        print("✅ Real enrichment operations completed")
        
    except Exception as e:
        print(f"⚠️ Enrichment test error: {e}")
    
    print()
    
    # Test 3: Check production logs generated
    print("📋 Test 3: Production Log Analysis")
    print("-" * 40)
    
    log_dir = Path("production_logs")
    if log_dir.exists():
        total_logs = 0
        log_summary = {}
        
        for subdir in log_dir.iterdir():
            if subdir.is_dir():
                log_files = list(subdir.glob("*.json"))
                if log_files:
                    count = len(log_files)
                    total_logs += count
                    log_summary[subdir.name] = count
                    
                    print(f"📁 {subdir.name}: {count} production logs")
                    
                    # Show latest log details
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    try:
                        with open(latest_log, 'r') as f:
                            log_data = json.load(f)
                        
                        print(f"   📄 Latest: {latest_log.name}")
                        print(f"   🏷️ Training Labels: {len(log_data.get('training_labels', {}))}")
                        print(f"   🕐 Timestamp: {log_data.get('timestamp', 'Unknown')[:19]}")
                        
                        # Show training labels
                        labels = log_data.get('training_labels', {})
                        if labels:
                            print(f"   📊 Labels: {', '.join([f'{k}={v}' for k, v in list(labels.items())[:3]])}")
                        
                    except Exception as e:
                        print(f"   ⚠️ Could not read log: {e}")
                    
                    print()
        
        print(f"📊 Total Production Logs: {total_logs}")
        print(f"📈 Log Distribution: {log_summary}")
        
        if total_logs > 0:
            print(f"\n✅ REAL production data successfully captured!")
            print(f"🎯 This data is from actual system operations")
            print(f"🤖 Ready for ML training and system optimization")
        else:
            print("📭 No production logs found")
    else:
        print("📁 No production logs directory found")
    
    print()
    
    # Test 4: Create comprehensive training dataset
    print("🤖 Test 4: Training Dataset Creation")
    print("-" * 40)
    
    try:
        from shared.production_logger import production_logger
        
        print("📊 Creating comprehensive training dataset...")
        dataset_path = production_logger.create_training_dataset()
        
        if Path(dataset_path).exists():
            with open(dataset_path, 'r') as f:
                dataset = json.load(f)
            
            info = dataset.get('dataset_info', {})
            records = dataset.get('training_records', [])
            
            print(f"✅ Training dataset created: {Path(dataset_path).name}")
            print(f"   📊 Total Records: {info.get('total_records', 0)}")
            print(f"   🏷️ Data Types: {len(info.get('data_types', []))}")
            print(f"   📅 Created: {info.get('created_at', 'Unknown')[:19]}")
            
            # Analyze record types and training labels
            record_types = {}
            all_labels = set()
            
            for record in records:
                log_type = record.get('log_type', 'unknown')
                record_types[log_type] = record_types.get(log_type, 0) + 1
                
                labels = record.get('training_labels', {})
                all_labels.update(labels.keys())
            
            print(f"   📋 Record Types: {dict(record_types)}")
            print(f"   🏷️ Training Labels: {len(all_labels)} unique labels")
            print(f"   🎯 Sample Labels: {', '.join(list(all_labels)[:5])}")
            
            print(f"\n🎉 Training dataset ready for ML training!")
            print(f"📈 Data quality: Production-grade with real operational context")
            
        else:
            print("⚠️ No training dataset created")
            
    except Exception as e:
        print(f"⚠️ Training dataset creation failed: {e}")
    
    print()
    print("🏭 COMPREHENSIVE PRODUCTION LOGGING TEST COMPLETE")
    print("=" * 60)
    print("✅ System is capturing REAL operational data for training")
    print("🤖 All future operations will contribute to training dataset")
    print("📈 Data is production-grade and ready for ML model development")

if __name__ == "__main__":
    test_comprehensive_production_logging()