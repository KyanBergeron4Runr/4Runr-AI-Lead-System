# 4Runr AI Lead System - Automation Setup Guide

## 🎯 Current Status
- ✅ Database consolidated: 26 leads
- ✅ AI messages fixed: 96.2% complete
- ✅ Enrichment fixed: 96.2% complete
- ✅ Unicode encoding issues resolved
- ✅ Database configuration fixed

## 🚀 Automation Setup

### For Linux/EC2 (Recommended)

1. **Set up cron jobs:**
   ```bash
   chmod +x setup_cron.sh
   bash setup_cron.sh
   ```

2. **Set up systemd service (optional):**
   ```bash
   sudo cp 4runr-ai-system.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable 4runr-ai-system
   sudo systemctl start 4runr-ai-system
   ```

### For Windows

1. **Set up Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Name: '4Runr Daily Sync'
   - Trigger: Daily at 6:00 AM
   - Action: Start a program
   - Program: cmd.exe
   - Arguments: /c "C:\path\to\4Runr-AI-Lead-System\daily_sync.bat"

## 📊 Expected Results

After automation is set up:
- **Daily scraping**: 5 new leads every day at 6 AM
- **Daily enrichment**: All new leads enriched automatically
- **Daily messaging**: AI messages generated for all leads
- **Daily sync**: All data synced to Airtable

## 🔧 Monitoring

### Check Daily Sync Logs
```bash
# Linux
tail -f logs/daily_sync_$(date +%Y%m%d).log

# Windows
type logs\daily_sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log
```

### Check System Health
```bash
python system_controller.py --health
```

### Check Database Status
```bash
python check_database_status.py
```

## 🆘 Troubleshooting

### If automation stops working:
1. Check cron jobs: `crontab -l`
2. Check systemd service: `sudo systemctl status 4runr-ai-system`
3. Check logs: `tail -f logs/daily_sync_*.log`
4. Restart services: `sudo systemctl restart 4runr-ai-system`

### If components fail:
1. Test individually: `python system_controller.py --health`
2. Check API keys: Ensure all required keys are configured
3. Check database: `python check_database_status.py`

## 📈 Success Metrics

- ✅ All leads have AI messages
- ✅ All leads are enriched
- ✅ Daily automation running
- ✅ 5 new leads scraped daily
- ✅ Airtable sync working
- ✅ System health checks passing

## 🎯 Next Steps

1. **Deploy to EC2** (if not already done)
2. **Set up monitoring** and alerts
3. **Optimize performance** based on usage
4. **Scale up** as lead volume increases

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Run diagnostic scripts
3. Review this guide
4. Contact system administrator
