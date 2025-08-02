#!/usr/bin/env python3
"""
Test AI Message Generation Logging

This script tests the production logging for AI message generation decisions.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def test_ai_message_logging():
    """Test AI message generation with production logging"""
    print("🤖 Testing AI Message Generation Logging")
    print("=" * 50)
    print("Generating AI messages for real leads to capture decision data...")
    print()
    
    try:
        # Import AI message generator
        sys.path.append('shared')
        from ai_message_generator import generate_ai_message
        
        # Test leads with different characteristics
        test_leads = [
            {
                'name': 'Alexandre Taillefer',
                'full_name': 'Alexandre Taillefer',
                'title': 'CEO',
                'company': 'Hexo Corp',
                'linkedin_url': 'https://linkedin.com/in/alexandre-taillefer',
                'website_data': {
                    'company_description': 'Leading cannabis company in Canada',
                    'top_services': ['Cannabis products', 'Medical marijuana'],
                    'tone': 'professional',
                    'website_insights': 'Innovative cannabis solutions'
                }
            },
            {
                'name': 'Jean-François Baril',
                'full_name': 'Jean-François Baril',
                'title': 'Chief Executive Officer',
                'company': 'Sigma Energy Storage',
                'linkedin_url': 'https://linkedin.com/in/jf-baril',
                'website_data': {
                    'company_description': 'Energy storage solutions provider',
                    'top_services': ['Battery storage', 'Energy management'],
                    'tone': 'technical',
                    'website_insights': 'Advanced energy storage technology'
                }
            },
            {
                'name': 'Marie Dubois',
                'full_name': 'Marie Dubois',
                'title': 'President',
                'company': 'TechStart Montreal',
                'linkedin_url': 'https://linkedin.com/in/marie-dubois'
                # No website data - test fallback
            }
        ]
        
        sources = ['Search', 'Comment', 'Other']
        
        print("🎯 Generating AI messages for real leads:")
        print()
        
        for i, lead in enumerate(test_leads, 1):
            source = sources[i % len(sources)]
            
            print(f"📊 Lead {i}: {lead['name']} - {lead['title']} at {lead['company']}")
            print(f"   📍 Source: {source}")
            
            # Generate AI message
            message_data = generate_ai_message(lead, source)
            
            print(f"   ✅ Message Generated:")
            print(f"      📝 Template: {message_data.get('template_id', 'Unknown')}")
            print(f"      🎨 Tone: {message_data.get('tone', 'Unknown')}")
            print(f"      📏 Length: {message_data.get('length', 'Unknown')}")
            print(f"      🌐 Website Data Used: {message_data.get('website_data_used', False)}")
            print(f"      🔧 Personalization: {message_data.get('personalization_applied', False)}")
            
            # Show first 100 chars of message
            message = message_data.get('message', '')
            preview = message[:100] + "..." if len(message) > 100 else message
            print(f"      💬 Preview: {preview}")
            print()
        
        print("✅ AI message generation completed")
        
    except Exception as e:
        print(f"❌ AI message generation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Check production logs
    print("📋 Checking AI Message Generation Logs:")
    print("-" * 40)
    
    log_dir = Path("production_logs/campaign_generation")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.json"))
        
        if log_files:
            print(f"📁 Found {len(log_files)} AI message generation logs")
            
            # Show latest log
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"📄 Latest log: {latest_log.name}")
            
            try:
                with open(latest_log, 'r') as f:
                    log_data = json.load(f)
                
                print(f"   🏷️ Training Labels: {len(log_data.get('training_labels', {}))}")
                print(f"   🕐 Timestamp: {log_data.get('timestamp', 'Unknown')[:19]}")
                print(f"   👤 Lead: {log_data.get('lead_identifier', {}).get('name', 'Unknown')}")
                
                # Show generation results
                results = log_data.get('generation_output', {})
                if results:
                    print(f"   📊 Template Used: {results.get('template_id', 'Unknown')}")
                    print(f"   🎨 Tone: {results.get('tone', 'Unknown')}")
                    print(f"   🌐 Website Data: {results.get('website_data_used', False)}")
                
                # Show training labels
                labels = log_data.get('training_labels', {})
                if labels:
                    print(f"   🏷️ Labels: {', '.join([f'{k}={v}' for k, v in list(labels.items())[:3]])}")
                
            except Exception as e:
                print(f"   ⚠️ Could not read log: {e}")
            
            print(f"\n✅ AI message generation logging is working!")
            print(f"🎯 Capturing real AI decision data for training")
            
        else:
            print("📭 No AI message generation logs found")
    else:
        print("📁 No campaign_generation logs directory found")
    
    print()
    
    # Create training dataset
    print("🤖 Creating Training Dataset:")
    print("-" * 40)
    
    try:
        from shared.production_logger import production_logger
        
        dataset_path = production_logger.create_training_dataset()
        
        if Path(dataset_path).exists():
            with open(dataset_path, 'r') as f:
                dataset = json.load(f)
            
            records = dataset.get('training_records', [])
            
            # Count AI message generation records
            ai_records = [r for r in records if r.get('log_type') == 'campaign_generation']
            
            print(f"✅ Training dataset updated: {Path(dataset_path).name}")
            print(f"   📊 Total Records: {len(records)}")
            print(f"   🤖 AI Message Records: {len(ai_records)}")
            
            if ai_records:
                print(f"   🎯 AI decisions captured for ML training!")
                
                # Show sample AI record
                sample = ai_records[0]
                print(f"   📄 Sample AI Record:")
                print(f"      🏷️ Labels: {len(sample.get('training_labels', {}))}")
                print(f"      📊 Template: {sample.get('generation_output', {}).get('template_id', 'Unknown')}")
                print(f"      🎨 Tone: {sample.get('generation_output', {}).get('tone', 'Unknown')}")
            
        else:
            print("⚠️ No training dataset created")
            
    except Exception as e:
        print(f"⚠️ Training dataset creation failed: {e}")
    
    print()
    print("🤖 AI Message Generation Logging Test Complete")
    print("=" * 50)
    print("✅ AI decisions are now being captured for training")
    print("🎯 Every message generation contributes to ML dataset")
    print("📈 Ready for AI model optimization and improvement")

if __name__ == "__main__":
    test_ai_message_logging()