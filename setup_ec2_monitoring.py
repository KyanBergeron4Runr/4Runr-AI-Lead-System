#!/usr/bin/env python3
"""
Setup EC2 Monitoring - Configure local monitoring for EC2 pipeline
"""

import os
import shutil

def setup_monitoring():
    """Set up EC2 monitoring configuration"""
    print("🔧 Setting up EC2 Pipeline Monitoring")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        shutil.copy('.env.ec2', '.env')
        print("✅ .env file created")
    else:
        print("ℹ️  .env file already exists")
    
    print("\n🔑 EC2 Configuration Required:")
    print("Please update your .env file with:")
    print("1. EC2_HOST=ubuntu@your-ec2-instance.amazonaws.com")
    print("2. EC2_KEY_PATH=~/.ssh/your-key.pem")
    print("3. Ensure your SSH key has correct permissions: chmod 600 ~/.ssh/your-key.pem")
    
    print("\n🚀 Available Commands:")
    print("• python pipeline_dashboard.py          - Interactive dashboard")
    print("• python ec2_pipeline_monitor.py status - Quick status check")
    print("• python ec2_pipeline_monitor.py watch  - Continuous monitoring")
    print("• python ec2_pipeline_monitor.py logs   - View pipeline logs")
    
    print("\n📊 Test Connection:")
    print("Run: python ec2_pipeline_monitor.py status")
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    print("\n✅ Setup complete!")

if __name__ == "__main__":
    setup_monitoring()