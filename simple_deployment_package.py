#!/usr/bin/env python3
"""
Simple EC2 Deployment Package Creator
"""

import os
import shutil
from datetime import datetime

def create_simple_deployment():
    """Create simple deployment folder for EC2"""
    
    print("Creating EC2 Deployment Package")
    print("=" * 40)
    
    # Create deployment directory
    deploy_dir = "4runr_ec2_deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Essential files
    files_to_copy = [
        "autonomous_4runr_organism.py",
        "final_working_system.py",
        "ec2_deploy.sh",
        "EC2_DEPLOYMENT_GUIDE.md",
        "AUTONOMOUS_ORGANISM_DEPLOYMENT.md"
    ]
    
    copied = 0
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
            print(f"Copied: {file}")
            copied += 1
    
    # Copy database
    if os.path.exists("data/unified_leads.db"):
        os.makedirs(f"{deploy_dir}/data", exist_ok=True)
        shutil.copy2("data/unified_leads.db", f"{deploy_dir}/data/")
        print(f"Copied: data/unified_leads.db")
        copied += 1
    
    # Create simple instructions
    instructions = """4Runr Autonomous Organism - EC2 Deployment

DEPLOYMENT STEPS:

1. Upload this folder to EC2:
   scp -r -i your-key.pem 4runr_ec2_deployment ubuntu@your-ec2-ip:/home/ubuntu/

2. SSH into EC2 and deploy:
   ssh -i your-key.pem ubuntu@your-ec2-ip
   cd 4runr_ec2_deployment
   chmod +x ec2_deploy.sh
   sudo ./ec2_deploy.sh

3. Start the organism:
   sudo systemctl start 4runr-organism
   sudo systemctl status 4runr-organism

4. Monitor:
   tail -f /home/ubuntu/4runr-organism/logs/organism-service.log

The organism will run 24/7 autonomously, generating prospects and syncing to Airtable.
"""
    
    with open(f"{deploy_dir}/DEPLOYMENT_INSTRUCTIONS.txt", "w", encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"Created: DEPLOYMENT_INSTRUCTIONS.txt")
    copied += 1
    
    print(f"\nDEPLOYMENT PACKAGE READY!")
    print(f"Files copied: {copied}")
    print(f"Location: {deploy_dir}/")
    print(f"\nUpload the entire '{deploy_dir}' folder to your EC2 instance")
    
    return deploy_dir

if __name__ == "__main__":
    deploy_dir = create_simple_deployment()
    print(f"\nYour autonomous organism is ready for EC2 deployment!")
    print(f"Upload folder: {deploy_dir}")
