# Cron Job Examples for 4Runr Multi-Agent System

This file contains examples of cron jobs for the 4Runr Multi-Agent System.

## Run the Pipeline Every 6 Hours

```bash
0 */6 * * * cd /home/ubuntu/4runr-agents && docker-compose run --rm pipeline >> /home/ubuntu/4runr-agents/logs/pipeline.log 2>&1
```

## Run Individual Agents

### Run the Scraper Every 4 Hours

```bash
0 */4 * * * docker exec 4runr-scraper python /app/app.py --run-once >> /home/ubuntu/4runr-agents/logs/scraper.log 2>&1
```

### Run the Enricher Every 2 Hours

```bash
0 */2 * * * docker exec 4runr-enricher python /app/app.py --run-once >> /home/ubuntu/4runr-agents/logs/enricher.log 2>&1
```

### Run the Engager Every Hour

```bash
0 * * * * docker exec 4runr-engager python /app/app.py --run-once >> /home/ubuntu/4runr-agents/logs/engager.log 2>&1
```

## Log Rotation

### Clean Up Logs Older Than 7 Days

```bash
0 0 * * * find /home/ubuntu/4runr-agents/logs -type f -name "*.log" -mtime +7 -delete
```

## How to Add Cron Jobs

1. Edit the crontab:

```bash
crontab -e
```

2. Add the desired cron job(s) to the file.

3. Save and exit the editor.

## Checking Cron Jobs

To list all cron jobs:

```bash
crontab -l
```

## Cron Job Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── day of week (0 - 6) (Sunday = 0)
│ │ │ └───── month (1 - 12)
│ │ └─────── day of month (1 - 31)
│ └───────── hour (0 - 23)
└─────────── minute (0 - 59)
```

Common time specifications:
- `*/5 * * * *`: Every 5 minutes
- `0 * * * *`: Every hour at minute 0
- `0 */6 * * *`: Every 6 hours
- `0 0 * * *`: Every day at midnight
- `0 0 * * 0`: Every Sunday at midnight