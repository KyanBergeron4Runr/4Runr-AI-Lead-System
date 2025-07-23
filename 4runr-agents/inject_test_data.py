#!/usr/bin/env python3
"""
4Runr Test Data Injection Tool

This script injects test data into the shared/leads.json file for system testing.
"""

import os
import sys
import json
import argparse
import shutil
from datetime import datetime

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Inject test data into shared/leads.json')
    parser.add_argument('--template', default='test_data_templates/test_lead.json',
                        help='Path to test data template (default: test_data_templates/test_lead.json)')
    parser.add_argument('--output', default='shared/leads.json',
                        help='Path to output file (default: shared/leads.json)')
    parser.add_argument('--backup', action='store_true',
                        help='Create backup of existing file')
    parser.add_argument('--count', type=int, default=1,
                        help='Number of test leads to inject (default: 1)')
    parser.add_argument('--append', action='store_true',
                        help='Append to existing data instead of replacing')
    return parser.parse_args()

def load_template(template_path):
    """Load test data template from file"""
    try:
        with open(template_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Template file not found: {template_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in template file: {template_path}")
        sys.exit(1)

def load_existing_data(output_path):
    """Load existing data from output file"""
    if not os.path.exists(output_path):
        return []
    
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Warning: Existing data is not a list. Converting to list.")
                data = [data]
            return data
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in output file: {output_path}. Creating new file.")
        return []

def create_backup(output_path):
    """Create backup of existing file"""
    if os.path.exists(output_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{output_path}.backup_{timestamp}"
        try:
            shutil.copy2(output_path, backup_path)
            print(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
    return None

def generate_test_leads(template, count):
    """Generate multiple test leads from template"""
    leads = []
    for i in range(count):
        # Create a copy of the template
        lead = template.copy()
        
        # Modify the lead to make it unique if generating multiple leads
        if count > 1:
            lead['name'] = f"{lead['name']} {i+1}"
            if 'linkedin_url' in lead:
                lead['linkedin_url'] = f"{lead['linkedin_url']}{i+1}"
        
        leads.append(lead)
    
    return leads

def inject_test_data(template_path, output_path, backup=True, count=1, append=False):
    """Inject test data into output file"""
    # Load template
    template = load_template(template_path)
    
    # Create backup if requested
    if backup:
        create_backup(output_path)
    
    # Load existing data if appending
    existing_data = load_existing_data(output_path) if append else []
    
    # Generate test leads
    test_leads = generate_test_leads(template, count)
    
    # Combine existing data and test leads
    if append:
        output_data = existing_data + test_leads
    else:
        output_data = test_leads
    
    # Write output data
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Successfully injected {len(test_leads)} test lead(s) into {output_path}")
        print(f"Total leads in file: {len(output_data)}")
    except Exception as e:
        print(f"Error: Failed to write output file: {e}")
        sys.exit(1)

def main():
    """Main function"""
    args = parse_arguments()
    inject_test_data(args.template, args.output, args.backup, args.count, args.append)

if __name__ == "__main__":
    main()