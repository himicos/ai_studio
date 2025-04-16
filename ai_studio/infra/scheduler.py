"""
Scheduler Module for AI Studio

This module handles scheduling of periodic tasks for AI Studio, including:
- Running the real-time scanner at regular intervals
- Executing scheduled prompts
- Managing background tasks
"""

import os
import logging
import time
from datetime import datetime
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Import our modules
from agents.real_time_scanner import RealTimeScanner
from infra.db import log_action

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class Scheduler:
    """
    Scheduler for AI Studio.
    
    This class manages periodic tasks for AI Studio, such as running the
    real-time scanner at regular intervals.
    """
    
    def __init__(self):
        """
        Initialize the scheduler.
        """
        self.scheduler = BackgroundScheduler()
        self.scanner = RealTimeScanner()
        self.scan_interval = int(os.getenv('SCAN_INTERVAL', '60'))
        logger.info(f"Scheduler initialized with scan interval: {self.scan_interval} seconds")
    
    def start(self):
        """
        Start the scheduler.
        """
        # Add jobs
        self.add_jobs()
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Scheduler started")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
    
    def stop(self):
        """
        Stop the scheduler.
        """
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def add_jobs(self):
        """
        Add jobs to the scheduler.
        """
        # Add real-time scanner job
        self.scheduler.add_job(
            self.run_scanner,
            IntervalTrigger(seconds=self.scan_interval),
            id='real_time_scanner',
            replace_existing=True
        )
        logger.info(f"Added real-time scanner job (every {self.scan_interval} seconds)")
        
        # Add daily database cleanup job (runs at 3 AM)
        self.scheduler.add_job(
            self.cleanup_database,
            CronTrigger(hour=3, minute=0),
            id='database_cleanup',
            replace_existing=True
        )
        logger.info("Added database cleanup job (daily at 3 AM)")
    
    async def run_scanner_async(self):
        """
        Run the real-time scanner asynchronously.
        """
        try:
            await self.scanner.scan()
            log_action('scheduler', 'run_scanner', 'Real-time scanner executed successfully')
        except Exception as e:
            logger.error(f"Error running scanner: {e}")
            log_action('scheduler', 'run_scanner', f"Error: {e}", status='error')
    
    def run_scanner(self):
        """
        Run the real-time scanner.
        """
        logger.info("Running real-time scanner")
        asyncio.run(self.run_scanner_async())
    
    def cleanup_database(self):
        """
        Clean up the database.
        """
        logger.info("Cleaning up database")
        try:
            # Implement database cleanup logic here
            # For example, removing old logs, compacting the database, etc.
            log_action('scheduler', 'cleanup_database', 'Database cleanup executed successfully')
        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")
            log_action('scheduler', 'cleanup_database', f"Error: {e}", status='error')

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start the scheduler
    scheduler = Scheduler()
    scheduler.start()
