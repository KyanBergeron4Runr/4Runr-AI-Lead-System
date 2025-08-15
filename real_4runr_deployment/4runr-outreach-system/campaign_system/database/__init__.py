"""
Database management for the Multi-Step Email Campaign System
"""

from .schema import create_campaign_tables, drop_campaign_tables
from .connection import get_database_connection, init_database

__all__ = ['create_campaign_tables', 'drop_campaign_tables', 'get_database_connection', 'init_database']