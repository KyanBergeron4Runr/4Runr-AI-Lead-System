#!/usr/bin/env python3
"""
Create EC2 Deployment Package for 4Runr Autonomous Organism
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_ec2_deployment_package():
    """Create a complete deployment package for EC2"""
    
    print("📦 CREATING EC2 DEPLOYMENT PACKAGE")
    print("=" * 50)
    
    # Create deployment directory
    deploy_dir = "4runr_ec2_deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Essential files to include
    essential_files = [
        "autonomous_4runr_organism.py",
        "final_working_system.py", 
        "ec2_deploy.sh",
        "EC2_DEPLOYMENT_GUIDE.md",
        "AUTONOMOUS_ORGANISM_DEPLOYMENT.md",
        "smart_search_strategy.md"
    ]
    
    # Copy essential files
    copied_count = 0
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
            print(f"✅ Copied: {file}")
            copied_count += 1
        else:
            print(f"⚠️ Missing: {file}")
    
    # Copy database if it exists
    if os.path.exists("data/unified_leads.db"):
        os.makedirs(f"{deploy_dir}/data", exist_ok=True)
        shutil.copy2("data/unified_leads.db", f"{deploy_dir}/data/")
        print(f"✅ Copied: data/unified_leads.db")
        copied_count += 1
    else:
        print(f"⚠️ Database not found - will be created on EC2")
    
    # Create deployment instructions
    instructions = f"""
# 🚀 4Runr Autonomous Organism - EC2 Deployment Package
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 DEPLOYMENT STEPS:

1. **Upload this entire folder to your EC2 instance:**
   ```bash
   scp -r -i your-key.pem 4runr_ec2_deployment ubuntu@your-ec2-ip:/home/ubuntu/
   ```

2. **SSH into EC2 and deploy:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   cd 4runr_ec2_deployment
   chmod +x ec2_deploy.sh
   sudo ./ec2_deploy.sh
   ```

3. **Start the autonomous organism:**
   ```bash
   sudo systemctl start 4runr-organism
   sudo systemctl status 4runr-organism
   ```

4. **Monitor the organism:**
   ```bash
   /home/ubuntu/4runr-organism/monitor_organism.sh
   tail -f /home/ubuntu/4runr-organism/logs/organism-service.log
   ```

## 🧬 WHAT THE ORGANISM DOES:

- Runs 24/7 autonomously on EC2
- Generates 1-3 quality SMB prospects every 5 minutes
- Enriches all data automatically 
- Syncs to Airtable in real-time
- Self-monitors health and adapts behavior
- Logs all activities for monitoring
- Restarts automatically if issues occur

## ✅ SUCCESS INDICATORS:

- Service shows "active (running)" status
- Logs show organism cycles and prospect generation
- Airtable receives new leads automatically
- Database lead count increases over time

## 📊 FILES INCLUDED:

- autonomous_4runr_organism.py (The living organism)
- ec2_deploy.sh (Automated deployment script)
- EC2_DEPLOYMENT_GUIDE.md (Complete deployment guide)
- Database with existing leads
- Documentation and strategy files

**The organism is ready to come alive on EC2! 🧬✨**
"""
    
    with open(f"{deploy_dir}/DEPLOYMENT_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    print(f"✅ Created: DEPLOYMENT_INSTRUCTIONS.md")
    copied_count += 1
    
    # Create zip package
    package_name = f"4runr_autonomous_organism_ec2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arc_name)
    
    print(f"✅ Created zip package: {package_name}")
    
    # Summary
    print(f"\n📊 DEPLOYMENT PACKAGE SUMMARY:")
    print(f"✅ Files included: {copied_count}")
    print(f"📁 Folder: {deploy_dir}/")
    print(f"📦 Zip package: {package_name}")
    print(f"💾 Total size: {os.path.getsize(package_name) / 1024:.1f} KB")
    
    print(f"\n🚀 READY FOR EC2 DEPLOYMENT!")
    print(f"Upload '{package_name}' to your EC2 instance and follow the instructions.")
    
    return package_name

if __name__ == "__main__":
    package = create_ec2_deployment_package()
    print(f"\n🧬 Your autonomous organism is packaged and ready for EC2! 🚀")
