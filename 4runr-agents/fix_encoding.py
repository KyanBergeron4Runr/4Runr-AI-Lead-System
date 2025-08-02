#!/usr/bin/env python3
"""
Standalone script to fix encoding issues in all lead files
Can be run manually or as part of the pipeline
"""

import sys
import os
from pathlib import Path

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

def main():
    """Main function to fix encoding issues"""
    try:
        from shared.encoding_fixer import EncodingFixer
        import logging
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger = logging.getLogger('encoding-fix')
        logger.info("🔧 Starting encoding fix process...")
        
        # Initialize the fixer
        fixer = EncodingFixer()
        
        # Fix all lead files in the shared directory
        shared_dir = Path(__file__).parent / "shared"
        success = fixer.fix_all_lead_files(shared_dir)
        
        if success:
            logger.info("✅ Encoding fix process completed successfully")
            return 0
        else:
            logger.error("❌ Encoding fix process failed")
            return 1
            
    except ImportError as e:
        print(f"❌ Error importing encoding fixer: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())