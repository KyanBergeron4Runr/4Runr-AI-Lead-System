# 🔄 Re-Engagement System: Production Usage Guide

## Overview
The re-engagement system automatically follows up with leads who received messages but didn't respond, using timed follow-ups with adjusted messaging to maximize conversion opportunities.

## 🏗️ Key Modules

| Module | Purpose |
|--------|---------|
| `engager/reengagement_strategy.py` | Business logic for identifying and updating eligible leads |
| `engager/enhanced_engager_agent.py` | Main runner for both initial and follow-up messaging |
| `tools/reengage_leads.py` | CLI utility for scheduled re-engagement campaigns |
| `enricher/fallback_message_generator.py` | Reused for follow-up tone logic |

## 🛠️ Supported CLI Commands

### ➤ Scheduled Daily Re-engagement via CLI
```bash
python tools/reengage_leads.py --days-since-contact 7 --limit 10
```
**What it does:**
- Checks for leads who haven't responded in the past 7+ days
- Updates them for follow-up processing
- **Dry-run mode**: Add `--dry-run` to preview without applying

**Production Example:**
```bash
# Daily cron job at 9 AM
0 9 * * * cd /path/to/4runr-outreach-system && python tools/reengage_leads.py --days-since-contact 7 --limit 10
```

### ➤ Trigger the Engager in Re-engagement Mode
```bash
PYTHONPATH=. python -m engager.enhanced_engager_agent --reengage-only --limit 5
```
**What it does:**
- Picks up `Eligible_For_Reengagement = True` leads
- Sends follow-up message (with adjusted tone)
- Updates follow-up stage and last contacted timestamp

### ➤ Check Current Re-engagement Stats
```bash
python tools/reengage_leads.py --status
```
**What it displays:**
- Total eligible for re-engagement
- Already re-engaged counts
- Skipped leads and reasons
- Success rates and recent activity

## 🧠 Re-engagement Message Flow

| Follow-Up Stage | Message Tone | Trigger Condition |
|----------------|--------------|-------------------|
| **Followup_1** | Light reminder, additional value | `Last_Contacted > 7 days`, no response |
| **Followup_2** | Strategic urgency, final opportunity | `Last_Contacted > 14 days`, no response |

**Auto-skip Conditions:**
- ✅ Converted, Rejected, or Interested leads
- ✅ Leads with 2+ follow-up attempts
- ✅ Low email confidence (not Real/Pattern)

**Message Generation:**
- 🎯 Pulls business traits if available
- 🔄 Falls back to templates if enrichment is incomplete
- 📝 Adjusts tone based on follow-up stage

## 🔐 Safety & Monitoring

| Feature | Description |
|---------|-------------|
| **Auto-backups** | Triggered at engager startup |
| **Dry-run mode** | Simulates entire pipeline without updates |
| **CLI limit** | Prevents mass sends accidentally |
| **Logging** | Full audit trail (logs per lead, per step) |
| **Health validator** | Run `verify_pipeline_health.py` regularly |

### Safety Commands
```bash
# Test without sending real messages
python tools/reengage_leads.py --dry-run --limit 5

# Check system health
python tools/verify_pipeline_health.py --verbose

# Monitor re-engagement statistics
python tools/reengage_leads.py --status
```

## 🧪 Testing Checklist Before Going Live

### Database & Sync Validation
- [ ] Validate `follow_up_stage` and `response_status` fields are syncing to Airtable
- [ ] Ensure no leads are stuck in a follow-up loop (max = 2 attempts)
- [ ] Confirm database backups are being created automatically

### Message Quality Validation
- [ ] Confirm re-engagement messages vary correctly between stages
- [ ] Test fallback templates when AI generation fails
- [ ] Verify message tone progression (helpful → urgent → final)

### System Health Validation
- [ ] Run `verify_pipeline_health.py` to ensure all systems operational
- [ ] Test dry-run mode produces expected results
- [ ] Validate error handling and logging

### Production Readiness
- [ ] Set up scheduled cron jobs for daily re-engagement
- [ ] Configure monitoring alerts for success rates
- [ ] Test with small batch of real leads

## 📊 Production Deployment

### Recommended Cron Schedule
```bash
# Daily re-engagement check at 9 AM
0 9 * * * cd /path/to/4runr-outreach-system && python tools/reengage_leads.py --days-since-contact 7 --limit 10

# Weekly cleanup of old flags at 2 AM Sunday
0 2 * * 0 cd /path/to/4runr-outreach-system && python engager/reengagement_strategy.py --cleanup 30

# Daily health check at 8 AM
0 8 * * * cd /path/to/4runr-outreach-system && python tools/verify_pipeline_health.py --limit 5
```

### Integration with Existing Pipeline
```bash
# Regular outreach (morning)
python -m engager.enhanced_engager_agent --limit 20

# Re-engagement only (afternoon)
python -m engager.enhanced_engager_agent --reengage-only --limit 10

# Combined health monitoring
python tools/verify_pipeline_health.py --limit 5
```

## 🔍 Monitoring & Troubleshooting

### Key Metrics to Monitor
- **Eligible Leads**: Number of leads ready for re-engagement
- **Success Rate**: Percentage of successful re-engagement attempts
- **Stage Distribution**: Breakdown of Followup_1 vs Followup_2
- **Response Status**: Tracking of No Response, Converted, etc.

### Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **No eligible leads found** | `Eligible for Re-engagement: 0` | Check if leads have `Engagement_Status = 'Sent'` and proper timing |
| **Messages not sending** | High error count in results | Check email configuration and API keys |
| **Leads stuck in loop** | Same leads processed repeatedly | Verify completion tracking and database updates |
| **Poor message quality** | Generic or inappropriate messages | Review AI prompts and fallback templates |

### Debug Commands
```bash
# Verbose logging for troubleshooting
python tools/reengage_leads.py --verbose --dry-run

# Check specific lead status
python engager/reengagement_strategy.py --stats

# Test message generation
python engager/message_generator_enhanced.py --test
```

## 📈 Performance Optimization

### Recommended Limits
- **Daily Re-engagement**: 10-20 leads max to avoid overwhelming recipients
- **Batch Processing**: Process in small batches (5-10) for better monitoring
- **Timing**: Space out initial and re-engagement campaigns by several hours

### Scaling Considerations
- Monitor database performance with large lead volumes
- Consider rate limiting for email sending
- Implement queue-based processing for high volumes

## 🧭 Next Optional Upgrades

### Immediate Enhancements
- **⏳ Lead Decay Logic**: Auto-expire leads after 3 follow-up failures
- **📈 Email Tracking**: Track open/click rates to improve logic
- **🤖 Response Detection**: Automated response detection to update `response_status` via GPT

### Advanced Features
- **A/B Testing**: Test different message variations for optimal conversion
- **Industry Segmentation**: Industry-specific re-engagement strategies
- **CRM Integration**: Sync re-engagement data with external systems
- **Predictive Scoring**: ML-based lead scoring for re-engagement priority

## 🚨 Emergency Procedures

### If Re-engagement System Fails
1. **Stop Scheduled Jobs**: Comment out cron jobs immediately
2. **Check Logs**: Review recent logs for error patterns
3. **Run Health Check**: `python tools/verify_pipeline_health.py`
4. **Fallback to Manual**: Process critical leads manually
5. **Database Restore**: Use automatic backups if needed

### Rollback Procedure
```bash
# Stop all re-engagement processes
# Comment out cron jobs

# Restore from backup if needed
python engager/local_database_manager.py --restore backup_filename.db

# Reset re-engagement flags
UPDATE leads SET eligible_for_reengagement = FALSE WHERE eligible_for_reengagement = TRUE;
```

## 📋 Maintenance Checklist

### Daily
- [ ] Check re-engagement campaign results
- [ ] Monitor error logs for issues
- [ ] Verify database backups are created

### Weekly
- [ ] Review re-engagement success rates
- [ ] Clean up old re-engagement flags
- [ ] Analyze message quality and feedback

### Monthly
- [ ] Review and optimize re-engagement timing
- [ ] Update message templates based on performance
- [ ] Audit database for data quality issues
- [ ] Plan capacity for growing lead volumes

## 🎯 Success Metrics

### Key Performance Indicators
- **Re-engagement Rate**: % of eligible leads that get re-engaged
- **Response Rate**: % of re-engaged leads that respond
- **Conversion Rate**: % of re-engaged leads that convert
- **System Uptime**: % of successful re-engagement campaigns

### Target Benchmarks
- Re-engagement Rate: >90%
- Response Rate: >5% (industry standard for follow-ups)
- Conversion Rate: >2% (from re-engagement to interested)
- System Uptime: >99%

## 📞 Support & Documentation

### Internal Resources
- **System Architecture**: See `RE_ENGAGEMENT_SYSTEM_SUMMARY.md`
- **API Documentation**: See individual module docstrings
- **Database Schema**: See `local_database_manager.py`
- **Message Templates**: See `message_generator_enhanced.py`

### External Dependencies
- OpenAI API for message generation
- Airtable API for lead data sync
- SMTP/Email service for message delivery
- SQLite for local data storage

---

## 🎉 Quick Start for New Team Members

1. **Understand the Flow**: Read this guide and the system summary
2. **Test in Dry-Run**: `python tools/reengage_leads.py --dry-run --limit 3`
3. **Check System Health**: `python tools/verify_pipeline_health.py`
4. **Monitor a Campaign**: `python tools/reengage_leads.py --status`
5. **Review Logs**: Check recent re-engagement attempts and results

**The re-engagement system is production-ready and actively maintaining lead engagement to maximize conversion opportunities while respecting recipient preferences and maintaining 4Runr's professional brand standards.**