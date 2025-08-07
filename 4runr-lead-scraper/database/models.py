#!/usr/bin/env python3
"""
Database Models

Data models and ORM-like functionality for the 4runr-lead-scraper database.
Provides high-level interfaces for lead management operations.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from database.connection import get_database_connection
    from utils.logging import get_logger
    logger = get_logger('database-models')
except ImportError:
    # Create a simple database connection and logger
    import sqlite3
    import logging
    
    def get_database_connection():
        """Simple database connection for fallback"""
        db_path = Path(__file__).parent.parent / "data" / "leads.db"
        return sqlite3.connect(str(db_path))
    
    logger = logging.getLogger('database-models')

@dataclass
class Lead:
    """
    Lead data model representing a potential customer.
    """
    id: str
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_website: Optional[str] = None
    website: Optional[str] = None  # Website discovered via SerpAPI or Google search
    website_search_attempted: bool = False  # Whether Google search was attempted
    website_search_timestamp: Optional[str] = None  # When Google search was performed
    phone: Optional[str] = None
    
    # Scraping metadata
    scraped_at: Optional[str] = None
    scraping_source: str = 'serpapi'
    search_query: Optional[str] = None
    search_context: Optional[str] = None
    
    # Enrichment status
    enriched: bool = False
    enrichment_attempts: int = 0
    enrichment_last_attempt: Optional[str] = None
    enrichment_method: Optional[str] = None
    
    # Lead qualification
    qualified: bool = False
    qualification_date: Optional[str] = None
    qualification_criteria: Optional[str] = None
    lead_score: Optional[int] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    
    # Engagement tracking
    status: str = 'scraped'
    ready_for_outreach: bool = False
    last_contacted: Optional[str] = None
    
    # Sync tracking
    airtable_id: Optional[str] = None
    airtable_synced: Optional[str] = None
    sync_status: str = 'pending'
    
    # Verification
    verified: bool = False
    verification_date: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        """Create Lead instance from dictionary."""
        # Get valid field names from the dataclass
        import inspect
        valid_fields = set(inspect.signature(cls).parameters.keys())
        
        # Handle None values and type conversion
        clean_data = {}
        for key, value in data.items():
            # Skip fields that aren't in the dataclass
            if key not in valid_fields:
                continue
                
            if key in ['enriched', 'qualified', 'ready_for_outreach', 'verified']:
                clean_data[key] = bool(value) if value is not None else False
            elif key in ['enrichment_attempts', 'lead_score']:
                clean_data[key] = int(value) if value is not None else (0 if key == 'enrichment_attempts' else None)
            else:
                clean_data[key] = value
        
        return cls(**clean_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Lead instance to dictionary."""
        return asdict(self)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()


class LeadDatabase:
    """
    High-level database interface for lead management operations.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize lead database.
        
        Args:
            db_path: Optional database path
        """
        self.db = get_database_connection(db_path)
        logger.info("Lead database initialized")
    
    def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """
        Create a new lead in the database.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            str: Lead ID
        """
        # Generate ID if not provided
        if 'id' not in lead_data or not lead_data['id']:
            lead_data['id'] = str(uuid.uuid4())
        
        # Set timestamps
        now = datetime.now().isoformat()
        lead_data.setdefault('created_at', now)
        lead_data['updated_at'] = now
        
        # Create Lead instance for validation
        lead = Lead.from_dict(lead_data)
        
        try:
            # Insert into database
            query = """
                INSERT INTO leads (
                    id, name, email, company, title, linkedin_url, company_website, website, 
                    website_search_attempted, website_search_timestamp, phone,
                    scraped_at, scraping_source, search_query, search_context,
                    enriched, enrichment_attempts, enrichment_last_attempt, enrichment_method,
                    qualified, qualification_date, qualification_criteria, lead_score, 
                    company_size, industry, location,
                    status, ready_for_outreach, last_contacted,
                    airtable_id, airtable_synced, sync_status,
                    verified, verification_date,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?
                )
            """
            
            params = (
                lead.id, lead.name, lead.email, lead.company, lead.title, 
                lead.linkedin_url, lead.company_website, lead.website, 
                lead.website_search_attempted, lead.website_search_timestamp, lead.phone,
                lead.scraped_at, lead.scraping_source, lead.search_query, lead.search_context,
                lead.enriched, lead.enrichment_attempts, lead.enrichment_last_attempt, lead.enrichment_method,
                lead.qualified, lead.qualification_date, lead.qualification_criteria, lead.lead_score,
                lead.company_size, lead.industry, lead.location,
                lead.status, lead.ready_for_outreach, lead.last_contacted,
                lead.airtable_id, lead.airtable_synced, lead.sync_status,
                lead.verified, lead.verification_date,
                lead.created_at, lead.updated_at
            )
            
            self.db.execute_update(query, params)
            
            logger.info(f"Created lead: {lead.name} ({lead.id})")
            return lead.id
            
        except Exception as e:
            logger.error(f"Failed to create lead: {e}")
            raise
    
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by ID.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Lead instance or None if not found
        """
        try:
            cursor = self.db.execute_query("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            
            if row:
                return Lead.from_dict(dict(row))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            return None
    
    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a lead with new data.
        
        Args:
            lead_id: Lead ID
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if update successful
        """
        try:
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            params.append(lead_id)  # For WHERE clause
            
            query = f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?"
            
            rows_affected = self.db.execute_update(query, tuple(params))
            
            if rows_affected > 0:
                logger.info(f"Updated lead {lead_id}: {list(updates.keys())}")
                return True
            else:
                logger.warning(f"No lead found with ID {lead_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update lead {lead_id}: {e}")
            return False
    
    def search_leads(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Lead]:
        """
        Search for leads based on filters.
        
        Args:
            filters: Dictionary of search criteria
            limit: Optional limit on results
            
        Returns:
            List of Lead instances
        """
        try:
            # Build dynamic WHERE clause
            where_clauses = []
            params = []
            
            for key, value in filters.items():
                if value is not None:
                    if isinstance(value, bool):
                        where_clauses.append(f"{key} = ?")
                        params.append(value)
                    elif isinstance(value, str):
                        where_clauses.append(f"{key} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        where_clauses.append(f"{key} = ?")
                        params.append(value)
            
            # Build query
            query = "SELECT * FROM leads"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = self.db.execute_query(query, tuple(params))
            rows = cursor.fetchall()
            
            leads = [Lead.from_dict(dict(row)) for row in rows]
            
            logger.info(f"Found {len(leads)} leads matching filters")
            return leads
            
        except Exception as e:
            logger.error(f"Failed to search leads: {e}")
            return []
    
    def get_leads_needing_enrichment(self, limit: Optional[int] = None) -> List[Lead]:
        """
        Get leads that need enrichment.
        
        Args:
            limit: Optional limit on results
            
        Returns:
            List of Lead instances
        """
        return self.search_leads({'enriched': False}, limit=limit)
    
    def get_leads_ready_for_outreach(self, limit: Optional[int] = None) -> List[Lead]:
        """
        Get leads ready for outreach.
        
        Args:
            limit: Optional limit on results
            
        Returns:
            List of Lead instances
        """
        return self.search_leads({'ready_for_outreach': True}, limit=limit)
    
    def mark_lead_enriched(self, lead_id: str, enrichment_data: Dict[str, Any]) -> bool:
        """
        Mark a lead as enriched with additional data.
        
        Args:
            lead_id: Lead ID
            enrichment_data: Enrichment data to add
            
        Returns:
            bool: True if successful
        """
        updates = {
            'enriched': True,
            'enrichment_last_attempt': datetime.now().isoformat(),
            **enrichment_data
        }
        
        return self.update_lead(lead_id, updates)
    
    def get_lead_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {}
            
            # Total counts
            cursor = self.db.execute_query("SELECT COUNT(*) FROM leads")
            stats['total_leads'] = cursor.fetchone()[0]
            
            # Status breakdown
            cursor = self.db.execute_query("""
                SELECT status, COUNT(*) 
                FROM leads 
                GROUP BY status
            """)
            stats['by_status'] = dict(cursor.fetchall())
            
            # Enrichment stats
            cursor = self.db.execute_query("SELECT COUNT(*) FROM leads WHERE enriched = 1")
            stats['enriched_leads'] = cursor.fetchone()[0]
            
            cursor = self.db.execute_query("SELECT COUNT(*) FROM leads WHERE ready_for_outreach = 1")
            stats['ready_for_outreach'] = cursor.fetchone()[0]
            
            # Recent activity
            cursor = self.db.execute_query("""
                SELECT COUNT(*) FROM leads 
                WHERE scraped_at >= datetime('now', '-7 days')
            """)
            stats['scraped_last_7_days'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead from the database.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            bool: True if deletion successful
        """
        try:
            rows_affected = self.db.execute_update("DELETE FROM leads WHERE id = ?", (lead_id,))
            
            if rows_affected > 0:
                logger.info(f"Deleted lead {lead_id}")
                return True
            else:
                logger.warning(f"No lead found with ID {lead_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete lead {lead_id}: {e}")
            return False
    
    def bulk_insert_leads(self, leads_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple leads efficiently.
        
        Args:
            leads_data: List of lead data dictionaries
            
        Returns:
            int: Number of leads inserted
        """
        try:
            # Prepare data
            prepared_leads = []
            now = datetime.now().isoformat()
            
            for lead_data in leads_data:
                # Generate ID if not provided
                if 'id' not in lead_data or not lead_data['id']:
                    lead_data['id'] = str(uuid.uuid4())
                
                # Set timestamps
                lead_data.setdefault('created_at', now)
                lead_data['updated_at'] = now
                
                # Create Lead instance for validation
                lead = Lead.from_dict(lead_data)
                prepared_leads.append(lead)
            
            # Bulk insert
            query = """
                INSERT OR IGNORE INTO leads (
                    id, name, email, company, title, linkedin_url, company_website, website, 
                    website_search_attempted, website_search_timestamp, phone,
                    scraped_at, scraping_source, search_query, search_context,
                    enriched, enrichment_attempts, enrichment_last_attempt, enrichment_method,
                    qualified, qualification_date, qualification_criteria, lead_score, 
                    company_size, industry, location,
                    status, ready_for_outreach, last_contacted,
                    airtable_id, airtable_synced, sync_status,
                    verified, verification_date,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?
                )
            """
            
            params_list = []
            for lead in prepared_leads:
                params = (
                    lead.id, lead.name, lead.email, lead.company, lead.title, 
                    lead.linkedin_url, lead.company_website, lead.website, 
                    lead.website_search_attempted, lead.website_search_timestamp, lead.phone,
                    lead.scraped_at, lead.scraping_source, lead.search_query, lead.search_context,
                    lead.enriched, lead.enrichment_attempts, lead.enrichment_last_attempt, lead.enrichment_method,
                    lead.qualified, lead.qualification_date, lead.qualification_criteria, lead.lead_score,
                    lead.company_size, lead.industry, lead.location,
                    lead.status, lead.ready_for_outreach, lead.last_contacted,
                    lead.airtable_id, lead.airtable_synced, lead.sync_status,
                    lead.verified, lead.verification_date,
                    lead.created_at, lead.updated_at
                )
                params_list.append(params)
            
            rows_affected = self.db.execute_many(query, params_list)
            
            logger.info(f"Bulk inserted {rows_affected} leads")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Failed to bulk insert leads: {e}")
            return 0


# Convenience function to get database instance
def get_lead_database(db_path: Optional[str] = None) -> LeadDatabase:
    """
    Get LeadDatabase instance.
    
    Args:
        db_path: Optional database path
        
    Returns:
        LeadDatabase instance
    """
    return LeadDatabase(db_path)


if __name__ == "__main__":
    # Test the database models
    db = get_lead_database()
    
    print("🧪 Testing Database Models...")
    
    # Test lead creation
    test_lead_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'company': 'Test Company',
        'title': 'CEO',
        'linkedin_url': 'https://linkedin.com/in/testuser'
    }
    
    lead_id = db.create_lead(test_lead_data)
    print(f"Created test lead: {lead_id}")
    
    # Test lead retrieval
    lead = db.get_lead(lead_id)
    if lead:
        print(f"Retrieved lead: {lead.name}")
    
    # Test statistics
    stats = db.get_lead_statistics()
    print(f"Database stats: {stats}")
    
    # Clean up
    db.delete_lead(lead_id)
    print("✅ Database models test completed")