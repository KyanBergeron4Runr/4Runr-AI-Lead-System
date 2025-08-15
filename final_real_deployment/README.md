# FINAL REAL 4Runr Autonomous Organism

## 🎯 REAL DATA ONLY
This organism uses REAL SerpAPI searches to find REAL LinkedIn professionals.
NO MORE FAKE DATA!

## 🚀 Deployment

1. Copy this package to your EC2 instance
2. Set environment variables (SERPAPI_KEY, AIRTABLE_API_KEY)
3. Run: `chmod +x deploy_real.sh && sudo ./deploy_real.sh`
4. Start: `sudo systemctl start 4runr-real-organism`

## 📊 Rate Limiting
- 7 real leads per day
- 1 lead every ~3.4 hours
- Sustainable for long-term operation

## 🔍 What It Does
1. Searches LinkedIn via SerpAPI for real professionals
2. Validates LinkedIn URLs are working
3. Enriches with email guesses and AI messages
4. Saves to local SQLite database
5. Syncs to Airtable with all fields

## 📋 Monitoring
```bash
# Check if running
sudo systemctl status 4runr-real-organism

# Watch live logs
tail -f logs/organism-service.log

# Check systemd logs
journalctl -u 4runr-real-organism -f
```

## ⚠️ Environment Variables Required
- `SERPAPI_KEY`: Your SerpAPI key
- `AIRTABLE_API_KEY`: Your Airtable API key

## 🏆 Success Metrics
- REAL LinkedIn URLs that work
- REAL professional names and companies
- Valid email address patterns
- Complete Airtable field population
- No duplicate leads
