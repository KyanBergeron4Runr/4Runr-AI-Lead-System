#!/usr/bin/env python3
"""
Individual Agent Runner

This script allows running individual agents for testing and debugging:
- python run_agent.py scraper
- python run_agent.py verifier  
- python run_agent.py enricher
- python run_agent.py engager
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent-runner')

def run_agent(agent_name: str) -> bool:
    """Run a specific agent"""
    
    # Map agent names to directories
    agent_dirs = {
        'scraper': 'scraper',
        'verifier': 'verifier', 
        'enricher': 'enricher',
        'engager': 'engager'
    }
    
    if agent_name not in agent_dirs:
        logger.error(f"❌ Unknown agent: {agent_name}")
        logger.info(f"Available agents: {', '.join(agent_dirs.keys())}")
        return False
    
    agent_dir = Path(__file__).parent / agent_dirs[agent_name]
    app_file = agent_dir / 'app.py'
    
    if not app_file.exists():
        logger.error(f"❌ Agent app not found: {app_file}")
        return False
    
    logger.info(f"🚀 Running {agent_name} agent...")
    
    try:
        # Set environment variable to run once
        env = os.environ.copy()
        env['RUN_ONCE'] = 'true'
        
        # Run the agent
        result = subprocess.run([
            sys.executable, 'app.py'
        ], cwd=agent_dir, env=env, timeout=600)
        
        if result.returncode == 0:
            logger.info(f"✅ {agent_name} agent completed successfully")
            return True
        else:
            logger.error(f"❌ {agent_name} agent failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {agent_name} agent timed out after 10 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ {agent_name} agent failed with error: {str(e)}")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        logger.error("❌ Usage: python run_agent.py <agent_name>")
        logger.info("Available agents: scraper, verifier, enricher, engager")
        return False
    
    agent_name = sys.argv[1].lower()
    return run_agent(agent_name)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)