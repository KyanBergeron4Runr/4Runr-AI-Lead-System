#!/usr/bin/env python3
"""
Production Log Viewer

View and analyze production logs suitable for training and system improvement.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def view_production_logs():
    """View all production logs in a structured format"""
    print("🏭 4Runr Production Logs - Training Data Ready")
    print("=" * 80)
    print("These logs are structured for machine learning and system improvement")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    log_dir = Path("production_logs")
    
    if not log_dir.exists():
        print("❌ No production logs directory found")
        print("💡 Production logs will be created automatically when the system runs")
        return
    
    # Check each log type
    log_types = ["website_analysis", "enrichment_decisions", "campaign_generation", 
                "airtable_operations", "email_delivery", "training_data"]
    
    total_logs = 0
    
    for log_type in log_types:
        log_subdir = log_dir / log_type
        if log_subdir.exists():
            log_files = list(log_subdir.glob("*.json"))
            total_logs += len(log_files)
            
            print(f"\n📊 {log_type.replace('_', ' ').title()}")
            print("-" * 60)
            print(f"   📁 Directory: {log_subdir}")
            print(f"   📄 Log Files: {len(log_files)}")
            
            if log_files:
                # Show most recent log
                recent_log = max(log_files, key=lambda x: x.stat().st_mtime)
                try:
                    with open(recent_log, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                    
                    print(f"   🕐 Most Recent: {recent_log.name}")
                    print(f"   📋 Log Type: {log_data.get('log_type', 'unknown')}")
                    print(f"   🆔 Session ID: {log_data.get('session_id', 'unknown')}")
                    
                    # Show training labels if available
                    if 'training_labels' in log_data:
                        labels = log_data['training_labels']
                        print(f"   🏷️ Training Labels: {len(labels)} labels")
                        for key, value in list(labels.items())[:3]:  # Show first 3
                            print(f"      • {key}: {value}")
                    
                    # Show lead identifier if available
                    if 'lead_identifier' in log_data:
                        lead_id = log_data['lead_identifier']
                        print(f"   👤 Lead: {lead_id.get('name', 'Unknown')} - {lead_id.get('company', 'Unknown')}")
                        
                except Exception as e:
                    print(f"   ❌ Error reading recent log: {e}")
            else:
                print("   📭 No log files found")
    
    print(f"\n📈 Summary")
    print("-" * 60)
    print(f"   📊 Total Production Logs: {total_logs}")
    print(f"   🏷️ Training Ready: {'✅ Yes' if total_logs > 0 else '❌ No'}")
    print(f"   📁 Log Directory: {log_dir.absolute()}")
    
    if total_logs > 0:
        print(f"\n🤖 Training Dataset Generation")
        print("-" * 60)
        print("   To create a training dataset from all logs:")
        print("   ```python")
        print("   from shared.production_logger import production_logger")
        print("   dataset_path = production_logger.create_training_dataset()")
        print("   print(f'Training dataset created: {dataset_path}')")
        print("   ```")
    
    print(f"\n📋 Log Structure")
    print("-" * 60)
    print("   Each log contains:")
    print("   • Structured input/output data")
    print("   • Decision reasoning and context")
    print("   • Training labels for ML models")
    print("   • Timestamps and session tracking")
    print("   • Lead identification (anonymizable)")

def create_sample_training_dataset():
    """Create a sample training dataset from existing logs"""
    try:
        from shared.production_logger import production_logger
        dataset_path = production_logger.create_training_dataset()
        print(f"\n✅ Training dataset created: {dataset_path}")
        
        # Show dataset info
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"📊 Dataset Info:")
        print(f"   Records: {dataset['dataset_info']['total_records']}")
        print(f"   Data Types: {len(dataset['dataset_info']['data_types'])}")
        print(f"   Created: {dataset['dataset_info']['created_at']}")
        
        return dataset_path
        
    except Exception as e:
        print(f"❌ Error creating training dataset: {e}")
        return None

if __name__ == "__main__":
    view_production_logs()
    
    # Ask if user wants to create training dataset
    print(f"\n🤖 Would you like to create a training dataset? (y/n)")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            create_sample_training_dataset()
    except:
        pass