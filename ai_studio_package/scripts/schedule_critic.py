#!/usr/bin/env python3
"""
Scheduler for the Critic Agent

This script sets up a scheduler to run the Critic Agent periodically
to analyze execution logs and generate improvement suggestions.
"""

import os
import sys
import time
import logging
import json
import schedule
from datetime import datetime, timedelta
from pathlib import Path

# Set up the path to include the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our Critic Agent
from ai_studio_package.agents.critic_agent import run_critic

def run_scheduled_critic():
    """Run the Critic Agent on a schedule"""
    logger.info("Running scheduled Critic Agent job")
    
    try:
        # Run critic for all tasks
        all_tasks_result = run_critic(
            task=None,  # All tasks
            limit=100,
            days=1,
            min_entries=5
        )
        logger.info(f"Critic Agent run complete for all tasks: {all_tasks_result['status']}")
        
        # Also run for specific high-priority tasks
        # These would be your most important endpoints/functions
        priority_tasks = [
            "searchMemoryNodes",
            "generateKnowledgeGraph",
            "getMemoryNodes",
            "generateEmbedding",
            "summarizeContent"
        ]
        
        for task in priority_tasks:
            task_result = run_critic(
                task=task,
                limit=50,
                days=1,
                min_entries=3  # Lower threshold for specific tasks
            )
            logger.info(f"Critic Agent run complete for task '{task}': {task_result['status']}")
            
        return True
    except Exception as e:
        logger.error(f"Error in scheduled Critic Agent run: {e}", exc_info=True)
        return False

def setup_schedule(interval_hours=12):
    """Set up the schedule for running the Critic Agent"""
    logger.info(f"Setting up Critic Agent schedule to run every {interval_hours} hours")
    
    # Schedule the Critic Agent to run at the specified interval
    schedule.every(interval_hours).hours.do(run_scheduled_critic)
    
    # Also run at a specific time of day (e.g., 2 AM)
    schedule.every().day.at("02:00").do(run_scheduled_critic)
    
    logger.info("Schedule set up successfully")

def main():
    """Main function to set up and run the scheduler"""
    logger.info("Starting Critic Agent scheduler")
    
    # Set up the schedule
    setup_schedule(interval_hours=12)
    
    # Also run immediately on startup
    logger.info("Running initial Critic Agent job")
    run_scheduled_critic()
    
    # Keep the scheduler running
    logger.info("Entering scheduler loop")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduler loop: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Critic Agent scheduler")
    parser.add_argument("--interval", type=int, default=12, help="Interval in hours between runs")
    parser.add_argument("--run-now", action="store_true", help="Run the critic agent immediately")
    
    args = parser.parse_args()
    
    if args.run_now:
        logger.info("Running Critic Agent job immediately")
        result = run_scheduled_critic()
        print(json.dumps({"status": "success" if result else "error"}, indent=2))
    else:
        # Run the scheduler
        sys.exit(main()) 