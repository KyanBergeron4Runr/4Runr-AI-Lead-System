# 🤖 4Runr AI Lead System - Autonomous Operation Setup

## 🎯 **COMPLETE SYSTEM ARCHITECTURE**

Your system has 4 main components that should work together autonomously:

### 1. **4runr-lead-scraper** - Lead Generation
- Scrapes Google/SerpAPI for new leads
- Enriches lead data with contact information
- Stores leads in primary database

### 2. **4runr-brain** - AI Campaign Management  
- Daily batch processing with automation
- AI-powered campaign generation
- Quality control and approval workflows

### 3. **4runr-outreach-system** - Website Analysis & Email
- Website scraping and company analysis
- AI message generation
- Email delivery via Microsoft Graph

### 4. **system_controller.py** - Master Orchestrator
- Health monitoring
- Database synchronization
- Complete pipeline coordination

---

## 🚀 **AUTONOMOUS OPERATION COMMANDS**

### **Complete System Startup (EC2)**
```bash
cd ~/4Runr-AI-Lead-System
source .venv/bin/activate

# Run complete autonomous system
python system_controller.py --deploy
```

### **Daily Automated Processing**
```bash
# Set up cron job for daily automation
crontab -e

# Add these lines:
# Daily lead generation at 6 AM
0 6 * * * cd ~/4Runr-AI-Lead-System && source .venv/bin/activate && python 4runr-lead-scraper/simple_cli.py scrape --limit 50

# Daily brain processing at 8 AM  
0 8 * * * cd ~/4Runr-AI-Lead-System && source .venv/bin/activate && python 4runr-brain/daily_batch_processor.py --batch-size 20

# Daily outreach processing at 10 AM
0 10 * * * cd ~/4Runr-AI-Lead-System/4runr-outreach-system && source ../venv/bin/activate && python website_scraper/app.py --limit 20 && python message_generator/app.py --limit 20

# Health check every hour
0 * * * * cd ~/4Runr-AI-Lead-System && source .venv/bin/activate && python system_controller.py --health-check
```

### **Manual Full Pipeline Test**
```bash
# Test complete pipeline end-to-end
python system_controller.py --test-pipeline
```

---

## 🔧 **IMMEDIATE SETUP COMMANDS FOR EC2**

### **1. Test Lead Scraper**
```bash
cd ~/4Runr-AI-Lead-System/4runr-lead-scraper
source ../venv/bin/activate
python simple_cli.py stats
```

### **2. Test Brain Service**
```bash
cd ~/4Runr-AI-Lead-System/4runr-brain
source ../venv/bin/activate
python daily_batch_processor.py --batch-size 5 --dry-run
```

### **3. Set Up System Controller**
```bash
cd ~/4Runr-AI-Lead-System
source .venv/bin/activate
python system_controller.py --health
```

### **4. Create Autonomous Service**
```bash
# Create systemd service for autonomous operation
sudo tee /etc/systemd/system/4runr-ai-system.service > /dev/null <<EOF
[Unit]
Description=4Runr AI Lead System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/4Runr-AI-Lead-System
Environment=PATH=/home/ubuntu/4Runr-AI-Lead-System/.venv/bin
ExecStart=/home/ubuntu/4Runr-AI-Lead-System/.venv/bin/python system_controller.py --autonomous
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl enable 4runr-ai-system
sudo systemctl start 4runr-ai-system
```

---

## 🎯 **NEXT STEPS TO MAKE IT AUTONOMOUS**

1. **Test each component individually**
2. **Set up the system controller with autonomous mode**
3. **Configure cron jobs for daily processing**
4. **Add monitoring and alerting**
5. **Create systemd service for 24/7 operation**

---