# Lead Cache Database Location

## Database File
The lead cache database will be created at:
```
4runr-agents/data/leads_cache.db
```

## What's in the Database
- **leads table**: All your lead data from Airtable
- **cache_meta table**: Sync timestamps and metadata  
- **pending_sync table**: Changes waiting to sync back to Airtable

## File Size
- Typical size: 1-10MB for thousands of leads
- SQLite format: Single file, easy to backup

## Deployment Locations
- **Local development**: `4runr-agents/data/leads_cache.db`
- **Docker**: Mount volume to persist at `/app/data/leads_cache.db`
- **EC2/Server**: Set `LEAD_CACHE_DB_PATH` environment variable

## Backup
The database file can be copied for backup:
```bash
cp data/leads_cache.db data/backups/leads_cache_backup_$(date +%Y%m%d).db
```