#!/usr/bin/env python3
"""
Main API service for the 4Runr Autonomous Outreach System.

Provides a lightweight web service with health checks and runs the
outreach pipeline in a background thread to prevent blocking.
"""

import sys
import threading
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Ensure the project root is in the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from outreach.shared.logging_utils import get_logger
from outreach.shared.config import config


# Initialize FastAPI app
app = FastAPI(
    title="4Runr Outreach System",
    description="Autonomous outreach system with AI-powered message generation",
    version="2.0.0"
)

# Global state
pipeline_status = {
    "running": False,
    "last_run": None,
    "last_error": None,
    "total_runs": 0,
    "successful_runs": 0
}

logger = get_logger('api')


@app.get("/health")
def health_check():
    """
    Lightweight health check endpoint that doesn't depend on pipeline state.
    Returns 200 OK as long as the web service is running.
    """
    return {
        "status": "ok",
        "service": "outreach-system",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.get("/pipeline/status")
def pipeline_status_check():
    """
    Detailed pipeline status endpoint with background process information.
    """
    return {
        "pipeline": pipeline_status,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    }


@app.get("/system/info")
def system_info():
    """
    System information endpoint for debugging and monitoring.
    """
    try:
        # Test key system components
        system_checks = {}
        
        # Test Airtable connection
        try:
            from outreach.shared.configurable_airtable_client import get_configurable_airtable_client
            airtable_client = get_configurable_airtable_client()
            airtable_ok = airtable_client.test_connection()
            system_checks["airtable"] = "ok" if airtable_ok else "error"
        except Exception as e:
            system_checks["airtable"] = f"error: {str(e)}"
        
        # Test OpenAI configuration
        try:
            ai_config = config.get_ai_config()
            system_checks["openai"] = "configured" if ai_config.get('api_key') else "not_configured"
        except Exception as e:
            system_checks["openai"] = f"error: {str(e)}"
        
        return {
            "system_checks": system_checks,
            "pipeline_status": pipeline_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System info check failed: {e}")
        raise HTTPException(status_code=500, detail=f"System check failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize the application and start background pipeline."""
    app.state.start_time = time.time()
    
    logger.log_module_activity('api', 'system', 'info', {
        'message': '4Runr Outreach System API starting up'
    })
    
    # Start the background pipeline
    start_background_pipeline()
    
    logger.log_module_activity('api', 'system', 'success', {
        'message': 'API startup completed, background pipeline started'
    })


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of the application."""
    logger.log_module_activity('api', 'system', 'info', {
        'message': '4Runr Outreach System API shutting down'
    })


def run_pipeline_background():
    """
    Run the outreach pipeline in a continuous loop.
    This runs in a background thread and doesn't block the web service.
    """
    global pipeline_status
    
    logger.log_module_activity('api', 'system', 'info', {
        'message': 'Background pipeline thread started'
    })
    
    while True:
        try:
            pipeline_status["running"] = True
            pipeline_status["last_error"] = None
            
            # Run the pipeline modules in sequence
            success = run_pipeline_cycle()
            
            pipeline_status["last_run"] = datetime.now().isoformat()
            pipeline_status["total_runs"] += 1
            
            if success:
                pipeline_status["successful_runs"] += 1
                logger.log_module_activity('api', 'system', 'success', {
                    'message': 'Pipeline cycle completed successfully'
                })
            else:
                logger.log_module_activity('api', 'system', 'warning', {
                    'message': 'Pipeline cycle completed with some errors'
                })
            
        except Exception as e:
            pipeline_status["last_error"] = str(e)
            logger.log_module_activity('api', 'system', 'error', {
                'message': f'Pipeline cycle failed: {str(e)}'
            })
        
        finally:
            pipeline_status["running"] = False
        
        # Wait before next cycle (configurable delay)
        cycle_delay = int(config.get('PIPELINE_CYCLE_DELAY', '300'))  # 5 minutes default
        logger.log_module_activity('api', 'system', 'info', {
            'message': f'Pipeline sleeping for {cycle_delay} seconds'
        })
        time.sleep(cycle_delay)


def run_pipeline_cycle() -> bool:
    """
    Run a single cycle of the outreach pipeline.
    
    Returns:
        True if cycle completed successfully, False if there were errors
    """
    success = True
    
    try:
        # Import modules here to avoid blocking startup
        from outreach.website_scraper.app import WebsiteScraperAgent
        from outreach.message_generator.app import MessageGeneratorAgent
        from outreach.email_validator.app import EmailValidatorAgent
        from outreach.engager.app import EngagerAgent
        
        # Get batch size from config
        batch_size = config.get_system_config().get('batch_size', 10)
        
        logger.log_module_activity('api', 'system', 'info', {
            'message': f'Starting pipeline cycle with batch size {batch_size}'
        })
        
        # Step 1: Website Scraper
        try:
            scraper = WebsiteScraperAgent()
            scraper_results = asyncio.run(scraper.process_leads(limit=batch_size))
            logger.log_module_activity('api', 'system', 'info', {
                'message': f'Website scraper processed {scraper_results.get("processed", 0)} leads'
            })
        except Exception as e:
            logger.log_module_activity('api', 'system', 'warning', {
                'message': f'Website scraper failed: {str(e)}'
            })
            success = False
        
        # Step 2: Email Validator
        try:
            validator = EmailValidatorAgent()
            validator_results = validator.process_leads(limit=batch_size)
            logger.log_module_activity('api', 'system', 'info', {
                'message': f'Email validator processed {validator_results.get("processed", 0)} leads'
            })
        except Exception as e:
            logger.log_module_activity('api', 'system', 'warning', {
                'message': f'Email validator failed: {str(e)}'
            })
            success = False
        
        # Step 3: Message Generator
        try:
            generator = MessageGeneratorAgent()
            generator_results = generator.process_leads(limit=batch_size)
            logger.log_module_activity('api', 'system', 'info', {
                'message': f'Message generator processed {generator_results.get("processed", 0)} leads'
            })
        except Exception as e:
            logger.log_module_activity('api', 'system', 'warning', {
                'message': f'Message generator failed: {str(e)}'
            })
            success = False
        
        # Step 4: Engager
        try:
            engager = EngagerAgent()
            engager_results = engager.process_leads(limit=batch_size)
            logger.log_module_activity('api', 'system', 'info', {
                'message': f'Engager processed {engager_results.get("processed", 0)} leads, sent {engager_results.get("successful", 0)}'
            })
        except Exception as e:
            logger.log_module_activity('api', 'system', 'warning', {
                'message': f'Engager failed: {str(e)}'
            })
            success = False
        
        return success
        
    except Exception as e:
        logger.log_module_activity('api', 'system', 'error', {
            'message': f'Pipeline cycle failed with critical error: {str(e)}'
        })
        return False


def start_background_pipeline():
    """Start the pipeline in a background daemon thread."""
    pipeline_thread = threading.Thread(
        target=run_pipeline_background,
        daemon=True,
        name="outreach-pipeline"
    )
    pipeline_thread.start()
    
    logger.log_module_activity('api', 'system', 'info', {
        'message': 'Background pipeline thread started successfully'
    })


def main():
    """Main entry point for the API service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='4Runr Outreach System API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--log-level', default='info', help='Log level')
    
    args = parser.parse_args()
    
    logger.log_module_activity('api', 'system', 'info', {
        'message': f'Starting 4Runr Outreach System API on {args.host}:{args.port}'
    })
    
    # Start the web service
    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == '__main__':
    main()