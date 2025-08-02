#!/usr/bin/env python3
"""
Main pipeline orchestration script for the 4Runr Autonomous Outreach System.

This script coordinates the execution of all four modules in sequence or
allows running individual modules independently.
"""

import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shared.logging_utils import get_logger
from shared.config import config


def run_website_scraper():
    """Run the Website Scraper Agent."""
    logger = get_logger('pipeline')
    logger.log_module_activity('pipeline', 'system', 'info', {'message': 'Starting Website Scraper Agent'})
    
    try:
        from website_scraper.app import main as scraper_main
        scraper_main()
        logger.log_module_activity('pipeline', 'system', 'success', {'message': 'Website Scraper completed'})
        return True
    except Exception as e:
        logger.log_error(e, {'action': 'run_website_scraper', 'lead_id': 'system'})
        return False


def run_message_generator():
    """Run the Message Generator Agent."""
    logger = get_logger('pipeline')
    logger.log_module_activity('pipeline', 'system', 'info', {'message': 'Starting Message Generator Agent'})
    
    try:
        from message_generator.app import main as generator_main
        generator_main()
        logger.log_module_activity('pipeline', 'system', 'success', {'message': 'Message Generator completed'})
        return True
    except Exception as e:
        logger.log_error(e, {'action': 'run_message_generator', 'lead_id': 'system'})
        return False


def run_email_validator():
    """Run the Email Validation Upgrade."""
    logger = get_logger('pipeline')
    logger.log_module_activity('pipeline', 'system', 'info', {'message': 'Starting Email Validator'})
    
    try:
        from email_validator.app import main as validator_main
        validator_main()
        logger.log_module_activity('pipeline', 'system', 'success', {'message': 'Email Validator completed'})
        return True
    except Exception as e:
        logger.log_error(e, {'action': 'run_email_validator', 'lead_id': 'system'})
        return False


def run_engager():
    """Run the Engager Agent."""
    logger = get_logger('pipeline')
    logger.log_module_activity('pipeline', 'system', 'info', {'message': 'Starting Engager Agent'})
    
    try:
        from engager.app import main as engager_main
        engager_main()
        logger.log_module_activity('pipeline', 'system', 'success', {'message': 'Engager completed'})
        return True
    except Exception as e:
        logger.log_error(e, {'action': 'run_engager', 'lead_id': 'system'})
        return False


def run_full_pipeline():
    """Run the complete autonomous outreach pipeline."""
    logger = get_logger('pipeline')
    logger.log_module_activity('pipeline', 'system', 'info', {'message': 'Starting full autonomous outreach pipeline'})
    
    modules = [
        ('Website Scraper', run_website_scraper),
        ('Message Generator', run_message_generator),
        ('Email Validator', run_email_validator),
        ('Engager', run_engager)
    ]
    
    results = {}
    
    for module_name, module_func in modules:
        logger.log_module_activity('pipeline', 'system', 'info', {'message': f'Running {module_name}'})
        success = module_func()
        results[module_name] = success
        
        if not success:
            logger.log_module_activity('pipeline', 'system', 'error', 
                                     {'message': f'{module_name} failed, continuing with next module'})
    
    # Log final results
    successful = sum(results.values())
    total = len(results)
    
    logger.log_module_activity('pipeline', 'system', 'complete', {
        'message': f'Pipeline completed: {successful}/{total} modules successful',
        'results': results
    })
    
    return successful == total


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='4Runr Autonomous Outreach System Pipeline')
    parser.add_argument('--module', choices=['website_scraper', 'message_generator', 'email_validator', 'engager'],
                       help='Run a specific module only')
    parser.add_argument('--config-check', action='store_true',
                       help='Check configuration and exit')
    
    args = parser.parse_args()
    
    logger = get_logger('pipeline')
    
    # Configuration check
    if args.config_check:
        try:
            airtable_config = config.get_airtable_config()
            ai_config = config.get_ai_config()
            logger.log_module_activity('pipeline', 'system', 'info', {
                'message': 'Configuration check passed',
                'airtable_configured': bool(airtable_config['api_key']),
                'ai_configured': bool(ai_config['api_key'])
            })
            return True
        except Exception as e:
            logger.log_error(e, {'action': 'config_check', 'lead_id': 'system'})
            return False
    
    # Run specific module
    if args.module:
        module_functions = {
            'website_scraper': run_website_scraper,
            'message_generator': run_message_generator,
            'email_validator': run_email_validator,
            'engager': run_engager
        }
        
        return module_functions[args.module]()
    
    # Run full pipeline
    return run_full_pipeline()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)