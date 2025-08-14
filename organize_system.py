#!/usr/bin/env python3
"""
4Runr AI Lead System - Master Organization Script
Comprehensive system organization and cleanup
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import logging

# Import our organization modules
from database_consolidation import DatabaseConsolidator
from code_organization import CodeOrganizer

class SystemOrganizer:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.organization_dir = self.root_dir / "system_organization"
        self.backup_dir = self.root_dir / "backups" / f"system_organization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.root_dir / "logs" / "system_organization.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log(self, message: str, level: str = "info"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if level == "error":
            self.logger.error(formatted_message)
        elif level == "warning":
            self.logger.warning(formatted_message)
        else:
            self.logger.info(formatted_message)
            
    def create_backup(self):
        """Create comprehensive backup before organization"""
        self.log("🔄 Creating comprehensive system backup...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup key directories
        key_dirs = [
            "4runr-brain",
            "4runr-lead-scraper", 
            "4runr-outreach-system",
            "data",
            "logs"
        ]
        
        for dir_name in key_dirs:
            dir_path = self.root_dir / dir_name
            if dir_path.exists():
                backup_path = self.backup_dir / dir_name
                if dir_path.is_dir():
                    self.copy_directory(dir_path, backup_path)
                else:
                    import shutil
                    shutil.copy2(dir_path, backup_path)
                self.log(f"   ✅ Backed up {dir_name}")
                
        # Create backup manifest
        manifest = {
            "backup_date": datetime.now().isoformat(),
            "backup_location": str(self.backup_dir),
            "directories_backed_up": key_dirs,
            "organization_phase": "pre_organization"
        }
        
        with open(self.backup_dir / "backup_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
            
        self.log(f"✅ System backup complete: {self.backup_dir}")
        
    def copy_directory(self, src: Path, dst: Path):
        """Copy directory recursively"""
        import shutil
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        
    def run_database_consolidation(self):
        """Run database consolidation"""
        self.log("🗄️ Starting database consolidation...")
        
        try:
            consolidator = DatabaseConsolidator()
            success = consolidator.run_consolidation()
            
            if success:
                self.log("✅ Database consolidation completed successfully")
                return True
            else:
                self.log("❌ Database consolidation failed", "error")
                return False
                
        except Exception as e:
            self.log(f"❌ Database consolidation error: {str(e)}", "error")
            return False
            
    def run_code_organization(self):
        """Run code organization analysis"""
        self.log("📁 Starting code organization analysis...")
        
        try:
            organizer = CodeOrganizer()
            success = organizer.run_organization_analysis()
            
            if success:
                self.log("✅ Code organization analysis completed successfully")
                return True
            else:
                self.log("❌ Code organization analysis failed", "error")
                return False
                
        except Exception as e:
            self.log(f"❌ Code organization error: {str(e)}", "error")
            return False
            
    def create_unified_configuration(self):
        """Create unified configuration system"""
        self.log("⚙️ Creating unified configuration system...")
        
        try:
            # Create unified config directory
            config_dir = self.root_dir / "config"
            config_dir.mkdir(exist_ok=True)
            
            # Create main configuration file
            config_file = config_dir / "config.py"
            config_content = '''"""
4Runr AI Lead System - Unified Configuration
Centralized configuration management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Unified configuration for 4Runr AI Lead System"""
    
    # Database Configuration
    DATABASE_PATH = os.getenv('LEAD_DATABASE_PATH', 'data/unified_leads.db')
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
    SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
    
    # Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # System Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_LEADS_PER_RUN = int(os.getenv('MAX_LEADS_PER_RUN', '5'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
    
    # Automation Configuration
    DAILY_SYNC_TIME = os.getenv('DAILY_SYNC_TIME', '06:00')
    AUTOMATION_ENABLED = os.getenv('AUTOMATION_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_keys = [
            'OPENAI_API_KEY',
            'AIRTABLE_API_KEY',
            'AIRTABLE_BASE_ID',
            'AIRTABLE_TABLE_NAME'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
                
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
            
        return True

# Global config instance
config = Config()
'''
            
            with open(config_file, 'w') as f:
                f.write(config_content)
                
            # Create .env template
            env_template = config_dir / ".env.template"
            env_content = '''# 4Runr AI Lead System - Environment Configuration Template

# Database Configuration
LEAD_DATABASE_PATH=data/unified_leads.db

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=your_airtable_table_name_here
SERPAPI_API_KEY=your_serpapi_key_here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_app_password_here

# System Configuration
LOG_LEVEL=INFO
MAX_LEADS_PER_RUN=5
BATCH_SIZE=10

# Automation Configuration
DAILY_SYNC_TIME=06:00
AUTOMATION_ENABLED=true
'''
            
            with open(env_template, 'w') as f:
                f.write(env_content)
                
            self.log("✅ Unified configuration created")
            return True
            
        except Exception as e:
            self.log(f"❌ Configuration creation error: {str(e)}", "error")
            return False
            
    def create_system_summary(self):
        """Create comprehensive system summary"""
        self.log("📊 Creating system summary...")
        
        summary = {
            "organization_date": datetime.now().isoformat(),
            "system_name": "4Runr AI Lead System",
            "organization_status": "completed",
            "components": {
                "brain": "AI learning and decision making system",
                "scraper": "Lead discovery and data collection",
                "outreach": "Outreach automation and messaging",
                "unified_database": "Consolidated lead management database",
                "unified_config": "Centralized configuration management"
            },
            "architecture": {
                "database": "Unified SQLite database with comprehensive schema",
                "configuration": "Centralized config with environment variable support",
                "modules": "Organized into logical functional modules",
                "services": "Background services for automation and monitoring"
            },
            "key_features": [
                "Automated lead discovery and scraping",
                "AI-powered message generation",
                "Email outreach automation",
                "Airtable integration",
                "Data enrichment and validation",
                "Campaign management",
                "System monitoring and health checks"
            ],
            "deployment": {
                "platform": "Ubuntu/Linux (EC2 recommended)",
                "requirements": "Python 3.8+, SQLite, required API keys",
                "automation": "Cron-based daily sync and monitoring"
            }
        }
        
        summary_file = self.root_dir / "SYSTEM_SUMMARY.md"
        with open(summary_file, 'w') as f:
            f.write("# 4Runr AI Lead System - Organization Summary\n\n")
            f.write(f"**Organization Date:** {summary['organization_date']}\n\n")
            f.write("## System Overview\n\n")
            f.write("The 4Runr AI Lead System is a comprehensive, autonomous lead generation and outreach platform.\n\n")
            
            f.write("## Components\n\n")
            for component, description in summary['components'].items():
                f.write(f"- **{component.title()}**: {description}\n")
            f.write("\n")
            
            f.write("## Architecture\n\n")
            for aspect, description in summary['architecture'].items():
                f.write(f"- **{aspect.title()}**: {description}\n")
            f.write("\n")
            
            f.write("## Key Features\n\n")
            for feature in summary['key_features']:
                f.write(f"- {feature}\n")
            f.write("\n")
            
            f.write("## Deployment\n\n")
            for key, value in summary['deployment'].items():
                f.write(f"- **{key.title()}**: {value}\n")
            f.write("\n")
            
        self.log(f"✅ System summary created: {summary_file}")
        return summary
        
    def create_quick_start_guide(self):
        """Create quick start guide for the organized system"""
        self.log("📖 Creating quick start guide...")
        
        guide_content = '''# 4Runr AI Lead System - Quick Start Guide

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- Ubuntu/Linux server (EC2 recommended)
- Required API keys (OpenAI, Airtable, SerpAPI)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd 4Runr-AI-Lead-System

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp config/.env.template .env
# Edit .env with your API keys and configuration
```

### 3. Database Setup

```bash
# Run database consolidation (if not already done)
python database_consolidation.py

# Verify database
python -c "import sqlite3; conn = sqlite3.connect('data/unified_leads.db'); print('Database ready')"
```

### 4. System Testing

```bash
# Test system health
python system_controller.py

# Test individual components
python -c "from config.config import config; config.validate(); print('Configuration valid')"
```

### 5. Start Services

```bash
# Start automation (if configured)
sudo systemctl start 4runr-ai-system

# Start monitoring dashboard
python monitoring_dashboard.py
```

## 📊 System Components

### Core Modules
- **Brain**: AI learning and decision making
- **Scraper**: Lead discovery and data collection  
- **Outreach**: Outreach automation and messaging
- **Enrichment**: Data enrichment and validation

### Services
- **Automation**: Automated processes and scheduling
- **Monitoring**: System monitoring and health checks
- **Backup**: Backup and recovery services

## 🔧 Configuration

Key configuration files:
- `config/config.py`: Main configuration
- `.env`: Environment variables
- `data/unified_leads.db`: Unified database

## 📈 Monitoring

- System dashboard: `python monitoring_dashboard.py`
- Logs: `logs/` directory
- Health checks: Built into system controller

## 🆘 Support

For issues and questions:
1. Check logs in `logs/` directory
2. Review system status: `python system_controller.py`
3. Verify configuration: `python -c "from config.config import config; config.validate()"`

---

**System Status**: ✅ Organized and Ready
'''
        
        guide_file = self.root_dir / "QUICK_START_GUIDE.md"
        with open(guide_file, 'w') as f:
            f.write(guide_content)
            
        self.log(f"✅ Quick start guide created: {guide_file}")
        
    def run_complete_organization(self):
        """Run the complete system organization process"""
        self.log("🚀 Starting complete system organization...")
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Database consolidation
            db_success = self.run_database_consolidation()
            if not db_success:
                self.log("❌ Database consolidation failed, stopping organization", "error")
                return False
                
            # Step 3: Code organization analysis
            code_success = self.run_code_organization()
            if not code_success:
                self.log("❌ Code organization failed, stopping organization", "error")
                return False
                
            # Step 4: Create unified configuration
            config_success = self.create_unified_configuration()
            if not config_success:
                self.log("❌ Configuration creation failed, stopping organization", "error")
                return False
                
            # Step 5: Create system summary
            self.create_system_summary()
            
            # Step 6: Create quick start guide
            self.create_quick_start_guide()
            
            self.log("🎉 Complete system organization finished successfully!")
            self.log("📋 Organization Summary:")
            self.log("   ✅ Database consolidated into unified structure")
            self.log("   ✅ Code organization analysis completed")
            self.log("   ✅ Unified configuration system created")
            self.log("   ✅ System documentation updated")
            self.log("   ✅ Quick start guide created")
            
            return True
            
        except Exception as e:
            self.log(f"❌ System organization failed: {str(e)}", "error")
            return False

def main():
    """Main function to run complete system organization"""
    organizer = SystemOrganizer()
    success = organizer.run_complete_organization()
    
    if success:
        print("\n🎉 4Runr AI Lead System organization completed successfully!")
        print("\n📋 What was accomplished:")
        print("   🗄️ Database consolidation - Unified all scattered databases")
        print("   📁 Code organization - Analyzed and categorized all code")
        print("   ⚙️ Configuration management - Created unified config system")
        print("   📖 Documentation - Updated system documentation")
        print("\n📋 Next steps:")
        print("   1. Review the organization reports")
        print("   2. Test the unified database")
        print("   3. Update any hardcoded paths in your code")
        print("   4. Follow the QUICK_START_GUIDE.md for setup")
        print("   5. Consider implementing the code organization recommendations")
        print("\n📊 Files created:")
        print("   - SYSTEM_ORGANIZATION_PLAN.md (organization plan)")
        print("   - database_consolidation.py (database consolidation script)")
        print("   - code_organization.py (code organization script)")
        print("   - organize_system.py (master organization script)")
        print("   - SYSTEM_SUMMARY.md (system overview)")
        print("   - QUICK_START_GUIDE.md (setup guide)")
        print("   - config/config.py (unified configuration)")
        print("   - data/unified_leads.db (unified database)")
    else:
        print("\n❌ System organization failed. Check logs for details.")

if __name__ == "__main__":
    main()
