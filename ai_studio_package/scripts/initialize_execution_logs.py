#!/usr/bin/env python3
"""
Script to initialize the execution_logs table for the Self-Improvement Loop

This script should be run once during setup to create the execution_logs table
"""

import os
import sys
import logging
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

# Import our execution logs module
from ai_studio_package.infra.execution_logs import init_execution_logs_table

def main():
    """Initialize the execution logs table"""
    logger.info("Starting execution logs table initialization")
    
    try:
        # Initialize the execution logs table
        init_execution_logs_table()
        logger.info("Execution logs table initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing execution logs table: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 