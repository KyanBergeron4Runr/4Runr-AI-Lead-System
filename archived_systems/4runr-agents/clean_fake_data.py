#!/usr/bin/env python3
"""
Clean Fake Data from Pipeline

Remove leads with fake data indicators to ensure validation-first approach
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data-cleaner')

class DataCleaner:
    def __init__(self):
        self.shared_dir = Path(__file__).parent / 'shared'
        self.backup_dir = self.shared_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # Files to clean
        self.pipeline_files = [
            'raw_leads.json',
            'verified_leads.json', 
            'enriched_leads.json',
            'engaged_leads.json'
        ]
        
        # Fake data indicators
        self.fake_indicators = [
            'pattern_generated',
            'fake',
            'mock',
            'test@example',
            'placeholder',
            'generated',
            'dummy'
        ]
        
        self.cleaning_stats = {
            'files_processed': 0,
            'leads_removed': 0,
            'leads_kept': 0,
            'fake_indicators_found': []
        }
    
    def backup_file(self, file_path):
        """Create backup of file before cleaning"""
        if not file_path.exists():
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"{file_path.stem}_backup_{timestamp}.json"
        
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        logger.info(f"📁 Backup created: {backup_path.name}")
        return backup_path
    
    def has_fake_data(self, lead):
        """Check if a lead contains fake data indicators"""
        fake_found = []
        
        for key, value in lead.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for indicator in self.fake_indicators:
                    if indicator in value_lower:
                        fake_found.append(f"{key}: {indicator}")
        
        return fake_found
    
    def clean_file(self, filename):
        """Clean fake data from a specific file"""
        file_path = self.shared_dir / filename
        
        if not file_path.exists():
            logger.info(f"⚪ {filename}: File not found, skipping")
            return
        
        logger.info(f"🧹 Cleaning {filename}...")
        
        # Backup original file
        backup_path = self.backup_file(file_path)
        
        try:
            # Load data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.warning(f"⚠️ {filename}: Not a list, skipping")
                return
            
            original_count = len(data)
            clean_data = []
            removed_count = 0
            
            # Process each lead
            for lead in data:
                fake_indicators = self.has_fake_data(lead)
                
                if fake_indicators:
                    # Lead has fake data, remove it
                    removed_count += 1
                    self.cleaning_stats['fake_indicators_found'].extend(fake_indicators)
                    
                    lead_name = lead.get('name', lead.get('full_name', 'Unknown'))
                    logger.info(f"   ❌ Removed {lead_name}: {', '.join(fake_indicators)}")
                else:
                    # Lead is clean, keep it
                    clean_data.append(lead)
            
            # Save cleaned data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, indent=2, ensure_ascii=False)
            
            kept_count = len(clean_data)
            
            logger.info(f"✅ {filename}: {original_count} → {kept_count} leads ({removed_count} removed)")
            
            self.cleaning_stats['files_processed'] += 1
            self.cleaning_stats['leads_removed'] += removed_count
            self.cleaning_stats['leads_kept'] += kept_count
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ {filename}: Invalid JSON - {e}")
        except Exception as e:
            logger.error(f"❌ {filename}: Error cleaning - {e}")
    
    def clean_all_files(self):
        """Clean all pipeline files"""
        logger.info("🚀 Starting Data Cleaning Process")
        logger.info("🔒 Validation-First Approach: Removing all fake data")
        
        for filename in self.pipeline_files:
            self.clean_file(filename)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 CLEANING SUMMARY")
        logger.info("="*60)
        
        logger.info(f"Files processed: {self.cleaning_stats['files_processed']}")
        logger.info(f"Leads removed: {self.cleaning_stats['leads_removed']}")
        logger.info(f"Leads kept: {self.cleaning_stats['leads_kept']}")
        
        if self.cleaning_stats['fake_indicators_found']:
            logger.info(f"\n🚨 Fake data indicators found:")
            unique_indicators = list(set(self.cleaning_stats['fake_indicators_found']))
            for indicator in unique_indicators[:10]:  # Show first 10
                logger.info(f"   - {indicator}")
            
            if len(unique_indicators) > 10:
                logger.info(f"   ... and {len(unique_indicators) - 10} more")
        
        logger.info(f"\n💾 Backups saved to: {self.backup_dir}")
        logger.info("="*60)
        
        return self.cleaning_stats

def main():
    """Main entry point"""
    cleaner = DataCleaner()
    stats = cleaner.clean_all_files()
    
    # Return success if we processed files
    if stats['files_processed'] > 0:
        logger.info("✅ Data cleaning completed successfully")
        return True
    else:
        logger.warning("⚠️ No files were processed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)