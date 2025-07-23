#!/usr/bin/env python3
"""
4Runr Pipeline Test Runner

This script runs the 4Runr pipeline and monitors its execution.
"""

import os
import sys
import time
import json
import argparse
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline-test-runner')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run 4Runr pipeline test')
    parser.add_argument('--timeout', type=int, default=300,
                        help='Timeout in seconds (default: 300)')
    parser.add_argument('--output-dir', default='test_results',
                        help='Directory to store test results (default: test_results)')
    parser.add_argument('--docker', action='store_true',
                        help='Run in Docker environment')
    return parser.parse_args()

def check_docker():
    """Check if Docker is running"""
    try:
        subprocess.run(['docker', 'info'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def check_docker_compose():
    """Check if docker-compose is available"""
    try:
        subprocess.run(['docker-compose', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def check_containers():
    """Check if required containers are running"""
    try:
        result = subprocess.run(['docker-compose', 'ps'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        output = result.stdout
        
        required_containers = ['scraper', 'enricher', 'engager', 'pipeline', 'cron']
        missing_containers = []
        
        for container in required_containers:
            if container not in output:
                missing_containers.append(container)
        
        if missing_containers:
            logger.warning(f"Missing containers: {', '.join(missing_containers)}")
            return False
        
        return True
    except subprocess.SubprocessError:
        return False

def run_pipeline(docker=False, timeout=300):
    """Run the pipeline"""
    logger.info("Starting pipeline execution...")
    
    start_time = time.time()
    
    try:
        if docker:
            # Run in Docker environment
            logger.info("Running pipeline in Docker environment...")
            result = subprocess.run(
                ['docker-compose', 'exec', '-T', '4runr-pipeline', 'python', 'run_pipeline.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=timeout
            )
        else:
            # Run locally
            logger.info("Running pipeline locally...")
            result = subprocess.run(
                [sys.executable, 'run_pipeline.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=timeout
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Pipeline execution completed in {duration:.2f} seconds")
        
        return {
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': duration
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Pipeline execution timed out after {timeout} seconds")
        return {
            'success': False,
            'error': 'timeout',
            'duration': timeout
        }
    except subprocess.SubprocessError as e:
        end_time = time.time()
        duration = end_time - start_time
        
        logger.error(f"Pipeline execution failed: {e}")
        
        return {
            'success': False,
            'error': str(e),
            'stdout': getattr(e, 'stdout', ''),
            'stderr': getattr(e, 'stderr', ''),
            'duration': duration
        }

def collect_logs(docker=False, output_dir='test_results'):
    """Collect logs from all containers"""
    logger.info("Collecting logs...")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(output_dir, f"container_logs_{timestamp}.log")
    
    try:
        if docker:
            # Collect logs from Docker containers
            with open(log_file, 'w') as f:
                subprocess.run(
                    ['docker-compose', 'logs', '--no-color'],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    check=True
                )
        else:
            # In local environment, just note that logs are not available
            with open(log_file, 'w') as f:
                f.write("Logs not available in local environment\n")
        
        logger.info(f"Logs collected and saved to {log_file}")
        return log_file
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to collect logs: {e}")
        return None

def analyze_logs(log_file):
    """Analyze logs for errors and component status"""
    if not log_file or not os.path.exists(log_file):
        logger.error("Log file not found")
        return {
            'enricher_status': False,
            'engager_status': False,
            'errors': ['Log file not found']
        }
    
    try:
        with open(log_file, 'r') as f:
            logs = f.read()
        
        # Check if enricher processed the test lead
        enricher_status = 'Enriching lead' in logs and 'Successfully enriched lead' in logs
        
        # Check if engager processed the test lead
        engager_status = 'Engaging with lead' in logs and 'Message sent to' in logs
        
        # Extract errors
        error_lines = []
        for line in logs.split('\n'):
            if any(error_term in line for error_term in ['Error', 'ERROR', 'Exception', 'Failed', 'Crash']):
                error_lines.append(line)
        
        return {
            'enricher_status': enricher_status,
            'engager_status': engager_status,
            'errors': error_lines
        }
    except Exception as e:
        logger.error(f"Failed to analyze logs: {e}")
        return {
            'enricher_status': False,
            'engager_status': False,
            'errors': [f"Failed to analyze logs: {e}"]
        }

def generate_report(pipeline_result, log_analysis, output_dir='test_results'):
    """Generate test report"""
    logger.info("Generating test report...")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"test_report_{timestamp}.md")
    
    # Determine overall status
    overall_status = "PASS" if (
        pipeline_result.get('success', False) and
        log_analysis.get('enricher_status', False) and
        log_analysis.get('engager_status', False) and
        not log_analysis.get('errors', [])
    ) else "FAIL"
    
    try:
        with open(report_file, 'w') as f:
            f.write(f"# 4Runr AI Lead Scraper System Test Results\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Test ID:** {timestamp}\n\n")
            
            f.write(f"## Test Summary\n\n")
            f.write(f"**Status:** {'✅ ' if overall_status == 'PASS' else '❌ '}{overall_status}\n")
            f.write(f"**Duration:** {pipeline_result.get('duration', 0):.2f} seconds\n\n")
            
            f.write(f"## Component Results\n\n")
            
            f.write(f"### Enricher\n")
            f.write(f"**Status:** {'✅ PASS' if log_analysis.get('enricher_status', False) else '❌ FAIL'}\n")
            f.write(f"**Details:** {('Successfully enriched test lead' if log_analysis.get('enricher_status', False) else 'Failed to enrich test lead')}\n\n")
            
            f.write(f"### Engager\n")
            f.write(f"**Status:** {'✅ PASS' if log_analysis.get('engager_status', False) else '❌ FAIL'}\n")
            f.write(f"**Details:** {('Successfully processed test lead for outreach' if log_analysis.get('engager_status', False) else 'Failed to process test lead for outreach')}\n\n")
            
            f.write(f"### System Health\n")
            f.write(f"**Status:** {'✅ PASS' if not log_analysis.get('errors', []) else '❌ FAIL'}\n")
            error_count = len(log_analysis.get('errors', []))
            f.write(f"**Details:** {('No errors detected' if not error_count else f'{error_count} errors detected')}\n\n")
            
            f.write(f"## Log Files\n\n")
            f.write(f"- Full logs: {os.path.basename(report_file).replace('test_report_', 'container_logs_')}\n\n")
            
            if log_analysis.get('errors', []):
                f.write(f"## Error Details\n\n")
                f.write("```\n")
                for error in log_analysis.get('errors', [])[:20]:  # Limit to 20 errors
                    f.write(f"{error}\n")
                if len(log_analysis.get('errors', [])) > 20:
                    f.write(f"... {len(log_analysis.get('errors', [])) - 20} more errors ...\n")
                f.write("```\n")
        
        logger.info(f"Test report generated and saved to {report_file}")
        return report_file
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return None

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Check Docker if running in Docker environment
    if args.docker:
        if not check_docker():
            logger.error("Docker is not running. Please start Docker and try again.")
            sys.exit(1)
        
        if not check_docker_compose():
            logger.error("docker-compose is not available. Please install it and try again.")
            sys.exit(1)
        
        if not check_containers():
            logger.error("Some required containers are not running. Please start them with 'docker-compose up -d'.")
            sys.exit(1)
    
    # Run pipeline
    pipeline_result = run_pipeline(args.docker, args.timeout)
    
    # Collect logs
    log_file = collect_logs(args.docker, args.output_dir)
    
    # Analyze logs
    log_analysis = analyze_logs(log_file)
    
    # Generate report
    report_file = generate_report(pipeline_result, log_analysis, args.output_dir)
    
    # Print summary
    if pipeline_result.get('success', False):
        logger.info("Pipeline execution completed successfully.")
    else:
        logger.error(f"Pipeline execution failed: {pipeline_result.get('error', 'Unknown error')}")
    
    if report_file:
        logger.info(f"Test report: {report_file}")
    
    # Exit with appropriate status code
    sys.exit(0 if pipeline_result.get('success', False) else 1)

if __name__ == "__main__":
    main()