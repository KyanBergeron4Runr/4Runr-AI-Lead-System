#!/usr/bin/env python3
"""
Deploy Real 4Runr System
========================
1. Clean fake leads from database and Airtable
2. Stop fake organism on EC2
3. Deploy real organism with all integrated systems
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime

# Add paths for Airtable client
sys.path.append('4runr-outreach-system')
from shared.airtable_client import AirtableClient

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/real_system_deploy.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('deploy_real')

def clean_fake_leads_from_database():
    """Remove all fake leads from local database"""
    logger = logging.getLogger('deploy_real')
    logger.info("🗑️ Cleaning fake leads from local database...")
    
    db_paths = [
        'data/unified_leads.db',
        '4runr-outreach-system/data/unified_leads.db',
        '4runr-lead-scraper/data/unified_leads.db'
    ]
    
    total_removed = 0
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get count before cleaning
            cursor.execute("SELECT COUNT(*) FROM leads")
            before_count = cursor.fetchone()[0]
            
            # Remove fake leads (those with generic names from our fake lists)
            fake_names = [
                'Alex Miller', 'Jordan Smith', 'Taylor Wilson', 'Morgan Johnson',
                'Casey Williams', 'Riley Brown', 'Avery Davis', 'Cameron Miller',
                'Alex Davis', 'Taylor Brown', 'Riley Miller', 'Cameron Brown',
                'Jordan Williams', 'Morgan Davis', 'Casey Miller', 'Avery Johnson',
                'Alex Wilson', 'Riley Smith', 'Cameron Davis', 'Taylor Smith'
            ]
            
            # Also remove by source if it's our fake organism
            cursor.execute("""
                DELETE FROM leads 
                WHERE full_name IN ({}) 
                OR source = 'Mock'
                OR company LIKE '%Systems'
                OR company LIKE '%Labs'
                OR company LIKE '%Solutions'
                OR company LIKE '%Tech'
                OR company LIKE '%Works'
                OR company LIKE '%Group'
                OR company LIKE '%Ventures'
                OR company LIKE '%Partners'
            """.format(','.join(['?' for _ in fake_names])), fake_names)
            
            removed_count = cursor.rowcount
            total_removed += removed_count
            
            # Get count after cleaning
            cursor.execute("SELECT COUNT(*) FROM leads")
            after_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Cleaned {db_path}: {removed_count} fake leads removed ({before_count} -> {after_count})")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning {db_path}: {e}")
            
    logger.info(f"🗑️ Total fake leads removed from databases: {total_removed}")
    return total_removed

def clean_fake_leads_from_airtable():
    """Remove fake leads from Airtable"""
    logger = logging.getLogger('deploy_real')
    logger.info("🗑️ Cleaning fake leads from Airtable...")
    
    try:
        airtable = AirtableClient()
        all_leads = airtable.get_all_leads()
        
        fake_names = [
            'Alex Miller', 'Jordan Smith', 'Taylor Wilson', 'Morgan Johnson',
            'Casey Williams', 'Riley Brown', 'Avery Davis', 'Cameron Miller',
            'Alex Davis', 'Taylor Brown', 'Riley Miller', 'Cameron Brown',
            'Jordan Williams', 'Morgan Davis', 'Casey Miller', 'Avery Johnson',
            'Alex Wilson', 'Riley Smith', 'Cameron Davis', 'Taylor Smith'
        ]
        
        removed_count = 0
        
        for lead in all_leads:
            full_name = lead.get('fields', {}).get('Full Name', '')
            
            # Check if this is a fake lead
            if (full_name in fake_names or 
                'SmartLabs' in lead.get('fields', {}).get('Company', '') or
                'NextSolutions' in lead.get('fields', {}).get('Company', '') or
                'CoreSystems' in lead.get('fields', {}).get('Company', '') or
                'PrimeTech' in lead.get('fields', {}).get('Company', '')):
                
                try:
                    airtable.delete_record(lead['id'])
                    removed_count += 1
                    logger.info(f"🗑️ Removed fake lead from Airtable: {full_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to remove {full_name}: {e}")
                    
        logger.info(f"🗑️ Removed {removed_count} fake leads from Airtable")
        return removed_count
        
    except Exception as e:
        logger.error(f"❌ Error cleaning Airtable: {e}")
        return 0

def create_deployment_package():
    """Create deployment package for EC2"""
    logger = logging.getLogger('deploy_real')
    logger.info("📦 Creating real system deployment package...")
    
    # Create deployment directory
    deploy_dir = "real_4runr_deployment"
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Copy essential files
    import shutil
    
    files_to_copy = [
        'real_autonomous_organism.py',
        'clean_data.py',
        'requirements.txt'
    ]
    
    dirs_to_copy = [
        '4runr-lead-scraper',
        '4runr-outreach-system', 
        '4runr-brain'
    ]
    
    # Copy files
    for file_path in files_to_copy:
        if os.path.exists(file_path):
            shutil.copy2(file_path, deploy_dir)
            logger.info(f"✅ Copied {file_path}")
        else:
            logger.warning(f"⚠️ File not found: {file_path}")
            
    # Copy directories
    for dir_path in dirs_to_copy:
        if os.path.exists(dir_path):
            dest_path = os.path.join(deploy_dir, dir_path)
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(dir_path, dest_path)
            logger.info(f"✅ Copied {dir_path}")
        else:
            logger.warning(f"⚠️ Directory not found: {dir_path}")
            
    # Create systemd service file for real organism
    service_content = """[Unit]
Description=Real 4Runr Autonomous Organism - Complete Lead Generation System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/real-4runr-system
ExecStart=/usr/bin/python3 real_autonomous_organism.py --cycles 10000 --interval 10800
Restart=always
RestartSec=30
StandardOutput=append:/home/ubuntu/real-4runr-system/logs/real-organism-service.log
StandardError=append:/home/ubuntu/real-4runr-system/logs/real-organism-error.log
MemoryMax=512M
TimeoutStartSec=30
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open(os.path.join(deploy_dir, 'real-4runr-organism.service'), 'w') as f:
        f.write(service_content)
        
    # Create deployment script
    deploy_script = """#!/bin/bash
# Real 4Runr System Deployment Script

echo "🧬 DEPLOYING REAL 4RUNR AUTONOMOUS ORGANISM"
echo "=========================================="

# Create directories
mkdir -p /home/ubuntu/real-4runr-system
mkdir -p /home/ubuntu/real-4runr-system/logs

# Copy files
cp -r * /home/ubuntu/real-4runr-system/

# Set permissions
chmod +x /home/ubuntu/real-4runr-system/real_autonomous_organism.py

# Install Python dependencies
cd /home/ubuntu/real-4runr-system
echo "📦 Installing dependencies..."
pip3 install --user -r requirements.txt

# Setup systemd service
echo "🔧 Setting up systemd service..."
sudo cp real-4runr-organism.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable real-4runr-organism

echo "✅ REAL 4RUNR SYSTEM DEPLOYED!"
echo ""
echo "🚀 To start the real organism:"
echo "sudo systemctl start real-4runr-organism"
echo ""
echo "📊 To monitor:"
echo "sudo systemctl status real-4runr-organism"
echo "tail -f /home/ubuntu/real-4runr-system/logs/real-organism-service.log"
"""
    
    with open(os.path.join(deploy_dir, 'deploy_real.sh'), 'w') as f:
        f.write(deploy_script)
        
    # Make script executable
    os.chmod(os.path.join(deploy_dir, 'deploy_real.sh'), 0o755)
    
    logger.info(f"📦 Real system deployment package created: {deploy_dir}")
    return deploy_dir

def main():
    logger = setup_logging()
    logger.info("🚀 DEPLOYING REAL 4RUNR SYSTEM")
    logger.info("=" * 50)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    print("⚠️  This will clean ALL fake leads and deploy the REAL system!")
    print("This includes:")
    print("- Removing fake leads from local databases")
    print("- Removing fake leads from Airtable")
    print("- Creating real system deployment package")
    print()
    
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Deployment cancelled")
        return
        
    try:
        # 1. Clean fake data
        logger.info("🗑️ Step 1: Cleaning fake data...")
        db_removed = clean_fake_leads_from_database()
        airtable_removed = clean_fake_leads_from_airtable()
        
        logger.info(f"✅ Cleanup complete: {db_removed} from DB, {airtable_removed} from Airtable")
        
        # 2. Create deployment package
        logger.info("📦 Step 2: Creating deployment package...")
        deploy_dir = create_deployment_package()
        
        logger.info("✅ REAL SYSTEM DEPLOYMENT COMPLETE!")
        logger.info("=" * 50)
        logger.info(f"📁 Deployment package: {deploy_dir}")
        logger.info("")
        logger.info("🚀 NEXT STEPS:")
        logger.info("1. Stop the fake organism on EC2:")
        logger.info("   sudo systemctl stop 4runr-organism")
        logger.info("")
        logger.info("2. Upload deployment package to EC2:")
        logger.info(f"   scp -r {deploy_dir} ubuntu@your-ec2:/home/ubuntu/")
        logger.info("")
        logger.info("3. Deploy on EC2:")
        logger.info("   cd /home/ubuntu/real_4runr_deployment")
        logger.info("   chmod +x deploy_real.sh")
        logger.info("   sudo ./deploy_real.sh")
        logger.info("")
        logger.info("4. Start the REAL organism:")
        logger.info("   sudo systemctl start real-4runr-organism")
        logger.info("")
        logger.info("🧬 Your REAL autonomous organism will then:")
        logger.info("✅ Scrape actual LinkedIn leads with SerpAPI")
        logger.info("✅ Enrich with real company data")
        logger.info("✅ Generate AI messages with the brain")
        logger.info("✅ Sync real prospects to Airtable")
        logger.info("✅ Operate autonomously 24/7")
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise

if __name__ == "__main__":
    main()
