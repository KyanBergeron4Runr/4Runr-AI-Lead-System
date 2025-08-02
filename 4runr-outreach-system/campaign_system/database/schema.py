"""
Database schema for the Multi-Step Email Campaign System
"""

from .connection import get_database_connection


def create_campaign_tables():
    """Create all campaign system database tables"""
    db = get_database_connection()
    
    # Campaigns table
    campaigns_table = """
    CREATE TABLE IF NOT EXISTS campaigns (
        campaign_id TEXT PRIMARY KEY,
        lead_id TEXT NOT NULL,
        company TEXT NOT NULL,
        campaign_type TEXT DEFAULT 'standard',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        campaign_status TEXT DEFAULT 'active',
        current_message INTEGER DEFAULT 1,
        response_detected BOOLEAN DEFAULT FALSE,
        response_date TIMESTAMP,
        response_type TEXT,
        total_opens INTEGER DEFAULT 0,
        total_clicks INTEGER DEFAULT 0,
        conversion_rate REAL DEFAULT 0.0,
        engagement_score REAL DEFAULT 0.0,
        airtable_record_id TEXT,
        lead_traits TEXT,  -- JSON string
        company_insights TEXT,  -- JSON string
        is_recycled BOOLEAN DEFAULT FALSE,
        original_campaign_id TEXT,
        recycle_type TEXT,
        recycle_attempt_count INTEGER DEFAULT 0,
        eligible_for_recycle BOOLEAN DEFAULT FALSE,
        last_message_sent_type TEXT,
        days_since_last_message INTEGER DEFAULT 0
    );
    """
    
    # Campaign messages table
    messages_table = """
    CREATE TABLE IF NOT EXISTS campaign_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id TEXT NOT NULL,
        message_number INTEGER NOT NULL,
        message_type TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        scheduled_date TIMESTAMP NOT NULL,
        sent_date TIMESTAMP,
        status TEXT DEFAULT 'scheduled',
        delivery_id TEXT,
        opens INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        bounced BOOLEAN DEFAULT FALSE,
        replied BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id),
        UNIQUE(campaign_id, message_number)
    );
    """
    
    # Message queue table
    queue_table = """
    CREATE TABLE IF NOT EXISTS message_queue (
        queue_id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        message_number INTEGER NOT NULL,
        lead_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        scheduled_for TIMESTAMP NOT NULL,
        priority INTEGER DEFAULT 5,
        attempts INTEGER DEFAULT 0,
        status TEXT DEFAULT 'queued',
        last_attempt TIMESTAMP,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        max_attempts INTEGER DEFAULT 3,
        FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id)
    );
    """
    
    # Campaign analytics table
    analytics_table = """
    CREATE TABLE IF NOT EXISTS campaign_analytics (
        analytics_id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        date DATE NOT NULL,
        hook_opens INTEGER DEFAULT 0,
        hook_clicks INTEGER DEFAULT 0,
        hook_sent BOOLEAN DEFAULT FALSE,
        proof_opens INTEGER DEFAULT 0,
        proof_clicks INTEGER DEFAULT 0,
        proof_sent BOOLEAN DEFAULT FALSE,
        fomo_opens INTEGER DEFAULT 0,
        fomo_clicks INTEGER DEFAULT 0,
        fomo_sent BOOLEAN DEFAULT FALSE,
        responded BOOLEAN DEFAULT FALSE,
        response_message INTEGER,
        response_time_hours INTEGER,
        campaign_completed BOOLEAN DEFAULT FALSE,
        industry TEXT,
        company_size TEXT,
        lead_role TEXT,
        email_confidence TEXT,
        engagement_rate REAL DEFAULT 0.0,
        conversion_rate REAL DEFAULT 0.0,
        progression_rate REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns (campaign_id),
        UNIQUE(campaign_id, date)
    );
    """
    
    # Create indexes for better performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_campaigns_lead_id ON campaigns (lead_id);",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns (campaign_status);",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns (created_at);",
        "CREATE INDEX IF NOT EXISTS idx_messages_campaign_id ON campaign_messages (campaign_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_scheduled_date ON campaign_messages (scheduled_date);",
        "CREATE INDEX IF NOT EXISTS idx_queue_scheduled_for ON message_queue (scheduled_for);",
        "CREATE INDEX IF NOT EXISTS idx_queue_status ON message_queue (status);",
        "CREATE INDEX IF NOT EXISTS idx_analytics_campaign_id ON campaign_analytics (campaign_id);",
        "CREATE INDEX IF NOT EXISTS idx_analytics_date ON campaign_analytics (date);"
    ]
    
    # Execute table creation
    tables = [campaigns_table, messages_table, queue_table, analytics_table]
    
    for table_sql in tables:
        db.execute_query(table_sql)
    
    # Create indexes
    for index_sql in indexes:
        db.execute_query(index_sql)
    
    print("Campaign system database tables created successfully")


def drop_campaign_tables():
    """Drop all campaign system database tables (use with caution)"""
    db = get_database_connection()
    
    tables = [
        "DROP TABLE IF EXISTS campaign_analytics;",
        "DROP TABLE IF EXISTS message_queue;",
        "DROP TABLE IF EXISTS campaign_messages;",
        "DROP TABLE IF EXISTS campaigns;"
    ]
    
    for table_sql in tables:
        db.execute_query(table_sql)
    
    print("Campaign system database tables dropped successfully")


def migrate_database():
    """Run database migrations"""
    # For now, just create tables
    # In the future, this would handle schema updates
    create_campaign_tables()


if __name__ == "__main__":
    # Allow running this script directly to create tables
    create_campaign_tables()