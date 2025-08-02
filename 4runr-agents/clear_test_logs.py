#!/usr/bin/env python3
"""
Clear Test Logs - Prepare for Production Logging

This script clears any test logs to ensure only real production data is captured.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def clear_test_logs():
    """Clear test logs and prepare for production logging"""
    print("🧹 Clearing Test Logs - Preparing for Production Data Collection")
    print("=" * 70)
    
    # Clear production logs directory
    log_dir = Path("production_logs")
    if log_dir.exists():
        print(f"📁 Found existing logs directory: {log_dir}")
        
        # Count existing files
        total_files = 0
        for subdir in log_dir.iterdir():
            if subdir.is_dir():
                files = list(subdir.glob("*.json"))
                if files:
                    print(f"   📄 {subdir.name}: {len(files)} files")
                    total_files += len(files)
        
        if total_files > 0:
            print(f"\\n🗑️ Removing {total_files} test log files...")
            
            # Remove all JSON files but keep directory structure
            for subdir in log_dir.iterdir():
                if subdir.is_dir():
                    for json_file in subdir.glob("*.json"):
                        json_file.unlink()
                        print(f"   ❌ Removed: {json_file.name}")
            
            print(f"✅ Test logs cleared successfully")
        else:
            print("✅ No test logs found - directory is clean")
    else:
        print("📁 No logs directory found - will be created on first production run")
    
    # Create fresh README for production
    if log_dir.exists():
        readme_content = f"""# 4Runr Production Logs - Real Training Data

This directory contains **REAL PRODUCTION LOGS** from the 4Runr system.
All data here is from actual system operations and is suitable for ML training.

## Production Data Collection Started
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Purpose**: Collect real operational data for training and optimization
- **Data Type**: Production-grade decision logs with training labels

## What Gets Logged
- **Website Analysis**: Real scraping decisions and results
- **Enrichment Operations**: Actual email finding and validation
- **Campaign Generation**: Real AI message creation decisions  
- **Airtable Sync**: Live data synchronization operations
- **System Performance**: Real performance metrics and outcomes

## Training Dataset Creation
Use the production logger to create training datasets:
```python
from shared.production_logger import production_logger
dataset_path = production_logger.create_training_dataset()
```

## Data Quality
✅ **Real Production Data**: All logs from actual system operations
✅ **Structured Format**: Ready for ML training pipelines
✅ **Training Labels**: Automatic quality and success labeling
✅ **Decision Context**: Full reasoning and decision explanations

**Note**: This data is from real production operations, not test data.
"""
        
        readme_file = log_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"📚 Updated README for production logging")
    
    print(f"\n🏭 Production Logging Ready!")
    print(f"🎯 Next Steps:")
    print(f"1. Run any 4Runr production component:")
    print(f"   • python daily_enricher_agent.py")
    print(f"   • python run_production_pipeline.py")
    print(f"   • python scraper/montreal_ceo_scraper_enhanced.py")
    print(f"2. Real production data will be automatically logged")
    print(f"3. Use view_production_logs.py to monitor data collection")
    print(f"4. Create training datasets with create_training_dataset.py")
    
    print(f"\n✨ All future logs will be REAL PRODUCTION DATA for training!")

if __name__ == "__main__":
    clear_test_logs()