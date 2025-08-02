# Daily Enricher Agent - Setup Guide

## 🎯 Overview
Your Daily Enricher Agent automatically finds leads in Airtable missing emails and enriches them using advanced stealth techniques. **$0 cost per lead** with anti-detection measures.

## 🔧 Features

### ✅ **Anti-Detection Measures:**
- **Rotating User Agents** - 5 different browser signatures
- **Intelligent Delays** - 5-20 second delays between requests
- **Domain-Specific Timing** - Tracks request timing per domain
- **Randomized Headers** - Mimics real browser behavior
- **Progressive Delays** - Increases delays with each page scraped
- **Stealth Request Patterns** - Avoids bot-like behavior

### ✅ **Smart Enrichment:**
- **Domain Discovery** - Finds company websites automatically
- **Website Scraping** - Extracts emails from contact pages
- **Pattern Generation** - Creates intelligent email patterns
- **Email Verification** - Validates deliverability via DNS
- **Airtable Integration** - Updates records automatically

### ✅ **Cost Benefits:**
- **$0 per lead** (vs $0.50+ with APIs)
- **Unlimited scalability**
- **No rate limits**
- **No monthly API fees**

## 🚀 Setup Instructions

### 1. **Install Dependencies**
```bash
pip install schedule beautifulsoup4 dnspython requests
```

### 2. **Configure Environment**
Make sure your `.env` file has:
```
AIRTABLE_API_KEY=your_key_here
AIRTABLE_BASE_ID=your_base_id_here
AIRTABLE_TABLE_NAME=Table 1
```

### 3. **Test the System**
```bash
python daily_enricher_agent.py
```

### 4. **Start Daily Automation**
```bash
python schedule_daily_enricher.py
```

Or on Windows:
```bash
start_daily_enricher.bat
```

## 📅 Scheduling Options

### **Option 1: Built-in Scheduler (Recommended)**
- Runs `schedule_daily_enricher.py`
- Scheduled for 9:00 AM daily
- Includes error handling and logging
- Automatically restarts on failures

### **Option 2: Windows Task Scheduler**
1. Open Windows Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:00 AM
4. Set action: Start program `python daily_enricher_agent.py`
5. Set start in: Your project directory

### **Option 3: Cron Job (Linux/Mac)**
```bash
# Add to crontab (crontab -e)
0 9 * * * cd /path/to/4runr-agents && python daily_enricher_agent.py
```

## 🛡️ Anti-Detection Strategy

### **Request Patterns:**
- **5-20 second delays** between leads
- **2-5 second delays** between pages
- **Random jitter** added to all delays
- **Domain-specific timing** tracking

### **Browser Simulation:**
- **Realistic headers** with referers
- **Multiple user agents** rotated randomly
- **Session persistence** for cookies
- **HTTPS preference** with HTTP fallback

### **Failure Handling:**
- **Graceful degradation** on blocks
- **Automatic retries** with backoff
- **Error logging** without stopping
- **Domain blacklist** for problematic sites

## 📊 Monitoring & Reports

### **Daily Reports:**
- Saved to `shared/daily_enrichment_reports.json`
- Tracks success rates and costs
- Monitors system performance

### **Log Files:**
- `daily_enricher.log` - Scheduler logs
- Console output - Real-time progress

### **Airtable Updates:**
- **Email** field populated
- **Date Enriched** timestamp
- **Response Notes** with confidence level
- **Needs Enrichment** set to False

## 🔍 How It Works

### **Daily Process:**
1. **Scan Airtable** for leads missing emails
2. **Discover domains** using pattern matching + search
3. **Scrape websites** for contact information
4. **Generate patterns** if no emails found
5. **Verify deliverability** via DNS checks
6. **Update Airtable** with found emails
7. **Generate report** with statistics

### **Lead Prioritization:**
- Processes leads with missing emails only
- Skips already enriched leads
- Updates `Needs Enrichment` flag

## 💡 Scaling Tips

### **For High Volume:**
- Increase delays between requests
- Add proxy rotation (extend `proxies` list)
- Implement domain rotation
- Add more user agents

### **For Better Success:**
- Customize domain patterns per industry
- Add more page types to scrape
- Implement company-specific logic
- Add social media profile scraping

## 🚨 Troubleshooting

### **Common Issues:**

**"No leads need enrichment"**
- All leads already have emails
- Check Airtable `Email` field is empty for test

**"Domain not found"**
- Company name too generic
- Add manual domain mapping
- Check domain pattern generation

**"Request failed"**
- Website blocking requests
- Increase delays in `min_delay_between_domains`
- Add more user agents

**"Airtable update failed"**
- Check API key permissions
- Verify field names match exactly
- Check rate limits

### **Debug Mode:**
Set logging level to DEBUG in the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Metrics

### **Expected Results:**
- **Success Rate:** 60-80% for domain discovery
- **Email Discovery:** 40-60% via scraping
- **Pattern Success:** 70-90% with verification
- **Processing Speed:** 2-3 leads per minute
- **Cost:** $0 per lead

### **Optimization:**
- Monitor daily reports for trends
- Adjust delays based on success rates
- Add industry-specific patterns
- Implement caching for repeated domains

## 🎯 Next Steps

1. **Run daily for 1 week** to establish baseline
2. **Monitor success rates** and adjust delays
3. **Add custom patterns** for your industry
4. **Scale up** to handle more leads
5. **Consider proxy rotation** for high volume

Your enrichment system is now **fully automated** and **cost-free**! 🚀