#!/usr/bin/env python3
"""
AI Studio - Main Entry Point

This is the main entry point for the AI Studio system. It provides a command-line
interface for starting the real-time scanner and processing schizoprompts.
"""

import os
import sys
import argparse
import logging
import asyncio
from datetime import datetime

# Import our modules
from agents.real_time_scanner import RealTimeScanner
from agents.prompt_router import PromptRouter
from infra.db import init_db, get_db_connection
from infra.scheduler import Scheduler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("memory", "logs", f"ai_studio_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup():
    """Initialize the system."""
    # Create necessary directories if they don't exist
    os.makedirs(os.path.join("memory", "logs"), exist_ok=True)
    os.makedirs(os.path.join("memory", "prompt_outputs"), exist_ok=True)
    
    # Initialize the database
    init_db()
    
    logger.info("AI Studio initialized")

async def run_scanner():
    """Run the real-time scanner."""
    logger.info("Starting real-time scanner")
    
    # Initialize the scanner
    scanner = RealTimeScanner()
    
    # Start the scanner
    await scanner.start()

async def process_prompt(prompt):
    """Process a schizoprompt."""
    logger.info(f"Processing prompt: {prompt}")
    
    # Initialize the prompt router
    router = PromptRouter()
    
    # Process the prompt
    result = await router.process(prompt)
    
    logger.info(f"Prompt processed: {result}")
    return result

def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI Studio - A modular, agentic operating system for real-time web tracking and prompt-driven automation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true", help="Start the real-time scanner")
    group.add_argument("--prompt", type=str, help="Process a schizoprompt")
    group.add_argument("--schedule", action="store_true", help="Start the scheduler")
    args = parser.parse_args()
    
    # Initialize the system
    setup()
    
    # Process the command
    if args.scan:
        # Run the scanner
        asyncio.run(run_scanner())
    elif args.prompt:
        # Process the prompt
        asyncio.run(process_prompt(args.prompt))
    elif args.schedule:
        # Start the scheduler
        scheduler = Scheduler()
        scheduler.start()

if __name__ == "__main__":
    main()
