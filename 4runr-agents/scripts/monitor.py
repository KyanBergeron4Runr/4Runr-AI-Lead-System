#!/usr/bin/env python3
"""
4Runr Pipeline Monitor

This script monitors the status of the 4Runr multi-agent pipeline by checking
the shared files and container status.
"""

import os
import json
import subprocess
import time
from datetime import datetime

# Constants
SHARED_DIR = "../shared"
CONTROL_FILE = os.path.join(SHARED_DIR, "control.json")
SCRAPED_FILE = os.path.join(SHARED_DIR, "scraped_leads.json")
ENRICHED_FILE = os.path.join(SHARED_DIR, "enriched_leads.json")
ENGAGED_FILE = os.path.join(SHARED_DIR, "engaged_leads.json")

def get_container_status():
    """Get the status of the Docker containers"""
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        containers = json.loads(result.stdout)
        
        status = {}
        for container in containers:
            name = container.get("Service")
            status[name] = {
                "state": container.get("State"),
                "health": container.get("Health", "N/A"),
                "ports": container.get("Ports", "")
            }
        
        return status
    except Exception as e:
        return {"error": str(e)}

def get_file_info(file_path):
    """Get information about a file"""
    if not os.path.exists(file_path):
        return {"exists": False}
    
    try:
        # Get file stats
        stats = os.stat(file_path)
        
        # Get file content summary
        with open(file_path, 'r') as f:
            content = json.load(f)
            
            if isinstance(content, list):
                summary = {
                    "count": len(content),
                    "sample": content[0] if content else None
                }
            else:
                summary = content
        
        return {
            "exists": True,
            "size": stats.st_size,
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "summary": summary
        }
    except Exception as e:
        return {
            "exists": True,
            "size": stats.st_size if 'stats' in locals() else 0,
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat() if 'stats' in locals() else None,
            "error": str(e)
        }

def main():
    """Main function to monitor the pipeline"""
    print("4Runr Pipeline Monitor")
    print("=====================\n")
    
    # Get container status
    print("Container Status:")
    print("----------------")
    container_status = get_container_status()
    
    if "error" in container_status:
        print(f"Error getting container status: {container_status['error']}")
    else:
        for name, status in container_status.items():
            print(f"{name}: {status['state']} ({status['health']})")
    
    print("\nPipeline Status:")
    print("--------------")
    
    # Check control file
    control_info = get_file_info(CONTROL_FILE)
    if control_info["exists"]:
        print(f"Control file: Last updated {control_info['modified']}")
        print(f"Status: {control_info['summary'].get('status', 'unknown')}")
        print(f"Last operation: {control_info['summary'].get('last_scrape') or control_info['summary'].get('last_enrichment') or control_info['summary'].get('last_engagement')}")
        print(f"Lead count: {control_info['summary'].get('lead_count', 0)}")
    else:
        print("Control file: Not found")
    
    # Check data files
    print("\nData Files:")
    print("-----------")
    
    # Scraped leads
    scraped_info = get_file_info(SCRAPED_FILE)
    if scraped_info["exists"]:
        print(f"Scraped leads: {scraped_info['summary'].get('count', 0)} leads, last updated {scraped_info['modified']}")
    else:
        print("Scraped leads: File not found")
    
    # Enriched leads
    enriched_info = get_file_info(ENRICHED_FILE)
    if enriched_info["exists"]:
        print(f"Enriched leads: {enriched_info['summary'].get('count', 0)} leads, last updated {enriched_info['modified']}")
    else:
        print("Enriched leads: File not found")
    
    # Engaged leads
    engaged_info = get_file_info(ENGAGED_FILE)
    if engaged_info["exists"]:
        print(f"Engaged leads: {engaged_info['summary'].get('count', 0)} leads, last updated {engaged_info['modified']}")
    else:
        print("Engaged leads: File not found")

if __name__ == "__main__":
    main()