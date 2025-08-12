#!/usr/bin/env python3
"""
Script to remove old logger calls from lead_database.py and airtable_sync_manager.py
"""

import re

def fix_lead_database():
    """Fix logger calls in lead_database.py"""
    with open('lead_database.py', 'r') as f:
        content = f.read()
    
    # Remove all self.logger.log_module_activity calls
    content = re.sub(
        r'\s*self\.logger\.log_module_activity\([^)]+\)\s*',
        '\n                # Logging handled by decorators\n',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Remove all self.logger.log_error calls
    content = re.sub(
        r'\s*self\.logger\.log_error\([^)]+\)\s*',
        '\n                # Error logging handled by decorators\n',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    with open('lead_database.py', 'w') as f:
        f.write(content)
    
    print("Fixed lead_database.py")

def fix_airtable_sync_manager():
    """Fix logger calls in airtable_sync_manager.py"""
    with open('airtable_sync_manager.py', 'r') as f:
        content = f.read()
    
    # Remove all self.logger.log_module_activity calls
    content = re.sub(
        r'\s*self\.logger\.log_module_activity\([^)]+\)\s*',
        '\n                # Logging handled by decorators\n',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Remove all self.logger.log_error calls
    content = re.sub(
        r'\s*self\.logger\.log_error\([^)]+\)\s*',
        '\n                # Error logging handled by decorators\n',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    with open('airtable_sync_manager.py', 'w') as f:
        f.write(content)
    
    print("Fixed airtable_sync_manager.py")

if __name__ == "__main__":
    fix_lead_database()
    fix_airtable_sync_manager()
    print("All logger calls fixed!")