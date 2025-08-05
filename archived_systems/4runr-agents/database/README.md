# Lead Database Module

This module provides a robust SQLite database system for managing lead data in the 4Runr lead generation system.

## Features

- **Thread-safe operations** with connection pooling
- **Automatic schema initialization** with proper indexes
- **Data integrity** with foreign key constraints
- **Performance optimization** with strategic indexing
- **Health monitoring** and database statistics
- **Backup and restore** capabilities

## Database Schema

### Tables

1. **leads** - Main lead data storage
   - Primary key: `id` (UUID)
   - Unique constraints on `linkedin_url` and `email`
   - Comprehensive lead information including sync status

2. **sync_status** - Airtable synchronization tracking
   - Tracks sync operations and their status
   - Foreign key relationship to leads table

3. **migration_log** - Data migration history
   - Records migration operations from JSON files
   - Tracks success/failure statistics

### Indexes

Performance indexes are automatically created for:
- LinkedIn URL lookups
- Email searches
- Name and company searches
- Sync status filtering
- Date-based queries

## Usage

### Basic Database Operations

```python
from database.connection import get_database_connection

# Get database connection
db_conn = get_database_connection()

# Insert a lead
lead_id = str(uuid.uuid4())
insert_query = """
    INSERT INTO leads (id, uuid, full_name, email, company)
    VALUES (?, ?, ?, ?, ?)
"""
db_conn.execute_update(insert_query, (lead_id, uuid.uuid4(), "John Doe", "john@example.com", "Example Corp"))

# Query leads
cursor = db_conn.execute_query("SELECT * FROM leads WHERE company = ?", ("Example Corp",))
leads = cursor.fetchall()

# Update a lead
db_conn.execute_update("UPDATE leads SET enriched = ? WHERE id = ?", (True, lead_id))
```

### Database Initialization

```bash
# Initialize database with schema
python database/init_database.py

# Verify schema
python database/init_database.py --verify

# Show database info
python database/init_database.py --info

# Create backup
python database/init_database.py --backup
```

### Health Monitoring

```python
# Check database health
health = db_conn.health_check()
print(f"Status: {health['status']}")
print(f"Response time: {health['response_time_seconds']}s")

# Get database statistics
info = db_conn.get_database_info()
print(f"Total leads: {info['leads_count']}")
print(f"Database size: {info['database_size_mb']} MB")
```

## Configuration

Database configuration is managed through environment variables:

```bash
# Database file location (default: data/leads.db)
LEAD_DATABASE_PATH=data/leads.db

# Backup settings
DATABASE_BACKUP_ENABLED=true
DATABASE_BACKUP_RETENTION_DAYS=30
```

## File Structure

```
database/
├── __init__.py              # Package initialization
├── schema.sql               # Database schema definition
├── connection.py            # Connection management and operations
├── init_database.py         # Database initialization script
├── test_connection.py       # Connection testing
└── README.md               # This documentation
```

## Error Handling

The database module includes comprehensive error handling:

- **Connection failures**: Automatic retry with exponential backoff
- **Lock timeouts**: Graceful handling with retry logic
- **Transaction failures**: Automatic rollback
- **Schema validation**: Verification of table structure

## Performance Considerations

- **Connection pooling**: Thread-local connections for concurrent access
- **WAL mode**: Write-Ahead Logging for better concurrent performance
- **Strategic indexing**: Optimized for common query patterns
- **Prepared statements**: Protection against SQL injection

## Testing

Run the test suite to verify database functionality:

```bash
python database/test_connection.py
```

The test suite covers:
- Basic CRUD operations
- Foreign key relationships
- Transaction handling
- Health checks
- Data cleanup

## Backup and Recovery

### Automatic Backups

Backups can be created automatically:

```python
from database.init_database import create_backup

backup_path = create_backup()
print(f"Backup created: {backup_path}")
```

### Manual Backup

```bash
# Create timestamped backup
python database/init_database.py --backup
```

### Recovery

To restore from backup:

1. Stop all agents using the database
2. Replace the database file with backup
3. Restart agents
4. Verify data integrity

## Migration Support

The database system supports migration from existing JSON files:

- Automatic detection of JSON lead files
- Duplicate prevention during migration
- Preservation of all existing data
- Migration logging and reporting

## Thread Safety

All database operations are thread-safe:

- Thread-local connections prevent conflicts
- Proper transaction isolation
- Lock handling with timeouts
- Connection pooling for performance

## Monitoring and Logging

Database operations are logged with:

- Operation timestamps
- Performance metrics
- Error details with stack traces
- Health check results
- Migration statistics

## Troubleshooting

### Common Issues

1. **Database locked**: Usually resolves automatically with retry logic
2. **Schema mismatch**: Run `--verify` to check schema integrity
3. **Performance issues**: Check index usage and query patterns
4. **Connection errors**: Verify file permissions and disk space

### Debug Mode

Enable debug logging for detailed operation traces:

```python
import logging
logging.getLogger('database.connection').setLevel(logging.DEBUG)
```

## Integration

This database module integrates with:

- **Airtable sync system**: Bidirectional synchronization
- **Lead generation agents**: Safe concurrent access
- **Migration tools**: JSON to database conversion
- **Monitoring systems**: Health checks and statistics