# 🚀 EC2 Deployment Guide for 4Runr Autonomous Organism

## 📦 DEPLOYMENT PACKAGE CONTENTS

**Core Files to Upload to EC2:**
```
autonomous_4runr_organism.py      # The living organism system
ec2_deploy.sh                     # Automated deployment script
final_working_system.py           # Backup system
smart_search_strategy.md          # Strategy documentation
data/unified_leads.db             # Your current database
AUTONOMOUS_ORGANISM_DEPLOYMENT.md # Full documentation
```

## 🔧 EC2 DEPLOYMENT STEPS

### 1. Upload Files to EC2
```bash
# From your local machine, upload to EC2:
scp -i your-key.pem autonomous_4runr_organism.py ubuntu@your-ec2-ip:/home/ubuntu/
scp -i your-key.pem ec2_deploy.sh ubuntu@your-ec2-ip:/home/ubuntu/
scp -i your-key.pem final_working_system.py ubuntu@your-ec2-ip:/home/ubuntu/
scp -i your-key.pem data/unified_leads.db ubuntu@your-ec2-ip:/home/ubuntu/
scp -i your-key.pem *.md ubuntu@your-ec2-ip:/home/ubuntu/
```

### 2. SSH into EC2 and Deploy
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Run the deployment script
chmod +x ec2_deploy.sh
sudo ./ec2_deploy.sh
```

### 3. Start the Autonomous Organism
```bash
# Start the organism as a system service
sudo systemctl start 4runr-organism

# Check if it's running
sudo systemctl status 4runr-organism

# Enable auto-start on boot
sudo systemctl enable 4runr-organism
```

## 📊 MONITORING THE ORGANISM ON EC2

### Real-time Monitoring:
```bash
# Watch the organism live
tail -f /home/ubuntu/4runr-organism/logs/organism-service.log

# Check system service logs
journalctl -u 4runr-organism -f

# Monitor organism health
/home/ubuntu/4runr-organism/monitor_organism.sh
```

### Health Check Commands:
```bash
# Check if organism is alive
sudo systemctl is-active 4runr-organism

# Restart if needed
sudo systemctl restart 4runr-organism

# Stop the organism
sudo systemctl stop 4runr-organism
```

## 🧬 ORGANISM BEHAVIOR ON EC2

### Autonomous Operation:
- **Runs 24/7** without any human intervention
- **Generates 1-3 prospects** every 5 minutes based on need
- **Syncs to Airtable** automatically in real-time
- **Self-monitors health** and adapts behavior
- **Logs everything** for monitoring and debugging
- **Restarts automatically** if it crashes (systemd handles this)

### Production Configuration:
- **Max Cycles**: 10,000 (runs virtually forever)
- **Cycle Interval**: 5 minutes between cycles
- **Auto-restart**: Service restarts if it fails
- **Resource Limits**: 512MB RAM, 50% CPU max
- **Logging**: All activity logged to files

## 🔍 TROUBLESHOOTING ON EC2

### Check Organism Status:
```bash
# Service status
sudo systemctl status 4runr-organism

# Recent logs
tail -n 50 /home/ubuntu/4runr-organism/logs/organism-service.log

# Database status
sqlite3 /home/ubuntu/4runr-organism/data/unified_leads.db "SELECT COUNT(*) FROM leads;"
```

### Common Issues:
1. **Service won't start**: Check logs with `journalctl -u 4runr-organism`
2. **No new prospects**: Check Airtable API connectivity
3. **Database errors**: Ensure database file permissions are correct
4. **Memory issues**: Monitor with `htop` or `free -h`

## 🎯 PRODUCTION READY FEATURES

### Reliability:
- **systemd service** ensures organism stays alive
- **Auto-restart** on failure
- **Resource limits** prevent system overload
- **Comprehensive logging** for debugging

### Monitoring:
- **Health checks** every cycle
- **Performance metrics** tracked
- **Error handling** with graceful recovery
- **Status monitoring** scripts included

### Security:
- **Runs as ubuntu user** (not root)
- **Resource-limited** service
- **Log rotation** to prevent disk overflow

## 🚀 FINAL DEPLOYMENT COMMANDS

### Quick Deploy (All-in-One):
```bash
# On EC2 instance, run this sequence:
sudo ./ec2_deploy.sh
sudo systemctl start 4runr-organism
./monitor_organism.sh
```

### Verify Deployment:
```bash
# Check everything is working:
sudo systemctl status 4runr-organism  # Should show "active (running)"
tail -f logs/organism-service.log      # Should show organism activity
./monitor_organism.sh                  # Should show healthy status
```

## 🧬 ORGANISM LIFECYCLE ON EC2

Once deployed, the organism will:

1. **Start automatically** when EC2 boots
2. **Monitor its health** continuously
3. **Generate quality prospects** based on system needs
4. **Enrich all data** automatically
5. **Sync to Airtable** in real-time
6. **Adapt its behavior** based on performance
7. **Log all activities** for monitoring
8. **Restart itself** if any issues occur
9. **Run forever** until manually stopped

## ✅ DEPLOYMENT CHECKLIST

- [ ] Files uploaded to EC2
- [ ] Deployment script executed
- [ ] Service started and enabled
- [ ] Logs showing activity
- [ ] Database accessible
- [ ] Airtable sync working
- [ ] Monitoring scripts functional
- [ ] Auto-restart configured

## 🎉 SUCCESS CONFIRMATION

**Your organism is successfully deployed when you see:**

```bash
sudo systemctl status 4runr-organism
# Output: ● 4runr-organism.service - 4Runr Autonomous Organism
#         Active: active (running)

tail -f logs/organism-service.log
# Output: Shows organism cycles, prospect generation, Airtable sync

./monitor_organism.sh
# Output: ✅ Service Status: RUNNING
#         Database shows increasing lead count
```

**The organism is now ALIVE on EC2 and working autonomously! 🧬✨**
