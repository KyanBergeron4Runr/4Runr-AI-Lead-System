#!/usr/bin/env python3
"""
Pipeline CLI - Command Line Interface for Validation-First Pipeline

This script provides easy commands for managing the validation-first pipeline:
- Run full pipeline or individual agents
- Check pipeline health
- View pipeline status
- Clean pipeline data
- Run tests
"""

import os
import sys
import json
import argparse
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline-cli')

class PipelineCLI:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.shared_dir = self.root_dir / 'shared'
        self.logs_dir = self.root_dir / 'logs'
        
        # Ensure directories exist
        self.shared_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def run_command(self, command: list, timeout: int = 600) -> bool:
        """Run a command and return success status"""
        try:
            logger.info(f"🚀 Running: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=self.root_dir,
                timeout=timeout,
                capture_output=False  # Show output in real-time
            )
            
            if result.returncode == 0:
                logger.info("✅ Command completed successfully")
                return True
            else:
                logger.error(f"❌ Command failed with return code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Command timed out after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"❌ Command failed with error: {str(e)}")
            return False
    
    def run_pipeline(self) -> bool:
        """Run the full validation-first pipeline"""
        logger.info("🔄 Starting Full Validation-First Pipeline")
        return self.run_command([sys.executable, 'run_validation_pipeline.py'])
    
    def run_agent(self, agent_name: str) -> bool:
        """Run a specific agent"""
        valid_agents = ['scraper', 'verifier', 'enricher', 'engager']
        
        if agent_name not in valid_agents:
            logger.error(f"❌ Invalid agent: {agent_name}")
            logger.info(f"Valid agents: {', '.join(valid_agents)}")
            return False
        
        logger.info(f"🤖 Running {agent_name} agent")
        return self.run_command([sys.executable, 'run_agent.py', agent_name])
    
    def check_health(self) -> bool:
        """Check pipeline health"""
        logger.info("🏥 Checking Pipeline Health")
        return self.run_command([sys.executable, 'verify_pipeline_health.py'])
    
    def run_test(self) -> bool:
        """Run pipeline tests"""
        logger.info("🧪 Running Pipeline Tests")
        return self.run_command([sys.executable, 'test_validation_pipeline.py'])
    
    def show_status(self):
        """Show current pipeline status"""
        logger.info("📊 Pipeline Status")
        
        # Check file existence and sizes
        pipeline_files = {
            'raw_leads.json': 'Raw leads from scraper',
            'verified_leads.json': 'Verified LinkedIn profiles',
            'enriched_leads.json': 'Enriched leads with contact info',
            'engaged_leads.json': 'Leads that were contacted',
            'dropped_leads.json': 'Leads dropped during validation'
        }
        
        print("\n" + "="*60)
        print("📁 PIPELINE FILES STATUS")
        print("="*60)
        
        for filename, description in pipeline_files.items():
            file_path = self.shared_dir / filename
            
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        count = len(data)
                        size = file_path.stat().st_size
                        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        print(f"✅ {filename}")
                        print(f"   {description}")
                        print(f"   Count: {count} leads")
                        print(f"   Size: {size} bytes")
                        print(f"   Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
                        print()
                        
                except json.JSONDecodeError:
                    print(f"❌ {filename} - Invalid JSON")
                    print(f"   {description}")
                    print()
                except Exception as e:
                    print(f"❌ {filename} - Error: {str(e)}")
                    print(f"   {description}")
                    print()
            else:
                print(f"⚪ {filename} - Not found")
                print(f"   {description}")
                print()
        
        # Check logs
        print("📋 RECENT LOGS")
        print("="*60)
        
        if self.logs_dir.exists():
            log_files = list(self.logs_dir.glob('*.log'))
            if log_files:
                for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                    size = log_file.stat().st_size
                    print(f"📄 {log_file.name}")
                    print(f"   Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   Size: {size} bytes")
                    print()
            else:
                print("No log files found")
        else:
            print("Logs directory not found")
        
        print("="*60)
    
    def clean_data(self, confirm: bool = False):
        """Clean pipeline data files"""
        if not confirm:
            print("⚠️  This will delete all pipeline data files!")
            print("Files that will be deleted:")
            
            files_to_delete = []
            for file_path in self.shared_dir.glob('*.json'):
                if file_path.name != 'control.json':  # Keep control file
                    files_to_delete.append(file_path)
                    print(f"   - {file_path.name}")
            
            if not files_to_delete:
                print("No data files to delete")
                return
            
            response = input("\nAre you sure you want to delete these files? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Cancelled")
                return
        
        # Delete data files
        deleted_count = 0
        for file_path in self.shared_dir.glob('*.json'):
            if file_path.name != 'control.json':  # Keep control file
                try:
                    file_path.unlink()
                    logger.info(f"🗑️  Deleted {file_path.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to delete {file_path.name}: {str(e)}")
        
        logger.info(f"✅ Cleaned {deleted_count} data files")
    
    def docker_build(self) -> bool:
        """Build Docker image"""
        logger.info("🐳 Building Docker image")
        return self.run_command(['docker', 'build', '-f', 'Dockerfile.pipeline', '-t', '4runr-pipeline', '.'])
    
    def docker_run(self, service: str = 'pipeline') -> bool:
        """Run Docker service"""
        logger.info(f"🐳 Running Docker service: {service}")
        return self.run_command(['docker-compose', '-f', 'docker-compose.pipeline.yml', 'run', '--rm', service])
    
    def show_help(self):
        """Show help information"""
        help_text = """
🔒 Validation-First Pipeline CLI

BASIC COMMANDS:
  pipeline          Run the full validation-first pipeline
  scraper           Run only the scraper agent
  verifier          Run only the verifier agent  
  enricher          Run only the enricher agent
  engager           Run only the engager agent
  
MONITORING:
  status            Show current pipeline status
  health            Check pipeline health and data quality
  test              Run pipeline tests
  
MAINTENANCE:
  clean             Clean all pipeline data files
  clean --force     Clean without confirmation
  
DOCKER:
  docker-build      Build Docker image
  docker-run        Run full pipeline in Docker
  docker-scraper    Run scraper in Docker
  docker-verifier   Run verifier in Docker
  docker-enricher   Run enricher in Docker
  docker-engager    Run engager in Docker
  
EXAMPLES:
  python pipeline_cli.py pipeline     # Run full pipeline
  python pipeline_cli.py scraper      # Run just scraper
  python pipeline_cli.py status       # Check status
  python pipeline_cli.py health       # Health check
  python pipeline_cli.py clean        # Clean data files
  
PIPELINE FLOW:
  SCRAPER → raw_leads.json → VERIFIER → verified_leads.json → 
  ENRICHER → enriched_leads.json → ENGAGER → Airtable
  
🚫 NO FAKE DATA GENERATED AT ANY STAGE
✅ ONLY REAL, VERIFIED LEADS PROCESSED
        """
        print(help_text)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Validation-First Pipeline CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default='help',
        help='Command to run (pipeline, scraper, verifier, enricher, engager, status, health, test, clean, docker-build, docker-run, help)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force action without confirmation (for clean command)'
    )
    
    args = parser.parse_args()
    
    cli = PipelineCLI()
    
    # Handle commands
    if args.command == 'pipeline':
        success = cli.run_pipeline()
    elif args.command in ['scraper', 'verifier', 'enricher', 'engager']:
        success = cli.run_agent(args.command)
    elif args.command == 'health':
        success = cli.check_health()
    elif args.command == 'test':
        success = cli.run_test()
    elif args.command == 'status':
        cli.show_status()
        success = True
    elif args.command == 'clean':
        cli.clean_data(confirm=args.force)
        success = True
    elif args.command == 'docker-build':
        success = cli.docker_build()
    elif args.command == 'docker-run':
        success = cli.docker_run('pipeline')
    elif args.command.startswith('docker-'):
        service = args.command.replace('docker-', '')
        success = cli.docker_run(service)
    elif args.command == 'help':
        cli.show_help()
        success = True
    else:
        logger.error(f"❌ Unknown command: {args.command}")
        cli.show_help()
        success = False
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)