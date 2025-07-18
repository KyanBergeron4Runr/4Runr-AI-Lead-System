# Cron Job Examples for 4Runr Lead System

This file contains examples of cron jobs for the 4Runr Lead System.

## Run the Scraper Every 6 Hours

```bash
0 */6 * * * cd /home/ubuntu/4runr-lead-system && docker-compose run --rm backend npm run scrape >> /home/ubuntu/4runr-lead-system/logs/scraper.log 2>&1
```

## List Leads Every Day

```bash
0 9 * * * cd /home/ubuntu/4runr-lead-system && docker-compose run --rm backend npm run list-leads >> /home/ubuntu/4runr-lead-system/logs/list-leads.log 2>&1
```

## Run Sanity Check Every Day

```bash
0 8 * * * cd /home/ubuntu/4runr-lead-system && docker-compose run --rm backend npm run sanity-check >> /home/ubuntu/4runr-lead-system/logs/sanity-check.log 2>&1
```

## Log Rotation

### Clean Up Logs Older Than 7 Days

```bash
0 0 * * * find /home/ubuntu/4runr-lead-system/logs -type f -name "*.log" -mtime +7 -delete
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