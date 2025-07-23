#!/usr/bin/env python3
"""
4Runr Log Monitor

This script monitors logs from the 4Runr pipeline in real-time.
"""

import os
import sys
import time
import argparse
import subprocess
import threading
import re
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()

# Define color codes for different log levels
COLORS = {
    'INFO': Fore.BLUE,
    'DEBUG': Fore.WHITE,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.RED + Style.BRIGHT,
    'SUCCESS': Fore.GREEN,
    'SCRAPER': Fore.CYAN,
    'ENRICHER': Fore.MAGENTA,
    'ENGAGER': Fore.YELLOW,
    'PIPELINE': Fore.GREEN,
    'DEFAULT': Fore.WHITE
}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Monitor 4Runr pipeline logs')
    parser.add_argument('--follow', '-f', action='store_true',
                        help='Follow logs in real-time')
    parser.add_argument('--container', '-c', 
                        choices=['all', 'scraper', 'enricher', 'engager', 'pipeline', 'cron'],
                        default='all',
                        help='Container to monitor (default: all)')
    parser.add_argument('--filter', '-F', 
                        help='Filter logs by regex pattern')
    parser.add_argument('--output', '-o',
                        help='Output file to save logs')
    parser.add_argument('--highlight', '-H',
                        help='Highlight regex pattern in logs')
    return parser.parse_args()

def get_container_logs(container, follow=False):
    """Get logs from a container"""
    cmd = ['docker-compose', 'logs']
    
    if follow:
        cmd.append('-f')
    
    if container != 'all':
        cmd.append(container)
    
    try:
        if follow:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            return process
        else:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True
            )
            return result.stdout
    except subprocess.SubprocessError as e:
        print(f"Error getting logs: {e}")
        return None

def parse_log_line(line):
    """Parse a log line to extract container, timestamp, and level"""
    # Extract container name
    container_match = re.match(r'^(\S+)\s+\|', line)
    container = container_match.group(1) if container_match else 'unknown'
    
    # Extract log level
    level_match = re.search(r'(INFO|DEBUG|WARNING|ERROR|CRITICAL)', line)
    level = level_match.group(1) if level_match else 'DEFAULT'
    
    # Determine color based on container and level
    if 'scraper' in container.lower():
        color = COLORS['SCRAPER']
    elif 'enricher' in container.lower():
        color = COLORS['ENRICHER']
    elif 'engager' in container.lower():
        color = COLORS['ENGAGER']
    elif 'pipeline' in container.lower():
        color = COLORS['PIPELINE']
    else:
        color = COLORS.get(level, COLORS['DEFAULT'])
    
    return {
        'container': container,
        'level': level,
        'color': color,
        'line': line
    }

def print_colored_log(log_info, highlight=None):
    """Print a log line with color"""
    line = log_info['line'].rstrip()
    
    # Apply highlighting if specified
    if highlight:
        try:
            pattern = re.compile(highlight, re.IGNORECASE)
            line = pattern.sub(lambda m: Fore.RED + Style.BRIGHT + m.group(0) + Style.RESET_ALL + log_info['color'], line)
        except re.error:
            pass
    
    print(log_info['color'] + line + Style.RESET_ALL)

def save_log(log_info, output_file):
    """Save a log line to a file"""
    with open(output_file, 'a') as f:
        f.write(log_info['line'])

def monitor_logs(container='all', follow=False, filter_pattern=None, output=None, highlight=None):
    """Monitor logs from containers"""
    if follow:
        process = get_container_logs(container, follow=True)
        if not process:
            return
        
        try:
            # Compile filter pattern if specified
            filter_regex = re.compile(filter_pattern, re.IGNORECASE) if filter_pattern else None
            
            # Create output file if specified
            if output:
                os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
                with open(output, 'w') as f:
                    f.write(f"# 4Runr Pipeline Logs\n")
                    f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Container: {container}\n")
                    if filter_pattern:
                        f.write(f"# Filter: {filter_pattern}\n")
                    f.write("\n")
            
            print(f"Monitoring logs from {container}...")
            print(f"Press Ctrl+C to stop")
            print("-" * 80)
            
            for line in process.stdout:
                log_info = parse_log_line(line)
                
                # Apply filter if specified
                if filter_regex and not filter_regex.search(line):
                    continue
                
                # Print and save log
                print_colored_log(log_info, highlight)
                
                if output:
                    save_log(log_info, output)
        
        except KeyboardInterrupt:
            print("\nStopping log monitor...")
        finally:
            process.terminate()
    else:
        logs = get_container_logs(container, follow=False)
        if not logs:
            return
        
        # Compile filter pattern if specified
        filter_regex = re.compile(filter_pattern, re.IGNORECASE) if filter_pattern else None
        
        # Create output file if specified
        if output:
            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
            with open(output, 'w') as f:
                f.write(f"# 4Runr Pipeline Logs\n")
                f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Container: {container}\n")
                if filter_pattern:
                    f.write(f"# Filter: {filter_pattern}\n")
                f.write("\n")
        
        for line in logs.splitlines(True):
            log_info = parse_log_line(line)
            
            # Apply filter if specified
            if filter_regex and not filter_regex.search(line):
                continue
            
            # Print and save log
            print_colored_log(log_info, highlight)
            
            if output:
                save_log(log_info, output)

def main():
    """Main function"""
    args = parse_arguments()
    
    try:
        monitor_logs(args.container, args.follow, args.filter, args.output, args.highlight)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()