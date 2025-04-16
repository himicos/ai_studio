"""
Real-Time Scanner Module for AI Studio

This module coordinates the Twitter and Reddit trackers, including:
- Running both trackers in parallel
- Collecting detected items from both sources
- Passing detected items to the action executor
- Logging scan results and statistics
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Import our modules
from data.twitter_tracker import TwitterTracker
from data.reddit_tracker import RedditTracker
from agents.action_executor import ActionExecutor
from infra.db import log_action

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class RealTimeScanner:
    """
    Real-Time Scanner for AI Studio.
    
    This class coordinates the Twitter and Reddit trackers, collects detected
    items from both sources, and passes them to the action executor.
    """
    
    def __init__(self):
        """
        Initialize the real-time scanner.
        """
        # Initialize trackers
        self.twitter_tracker = TwitterTracker()
        self.reddit_tracker = RedditTracker()
        
        # Initialize action executor
        self.action_executor = ActionExecutor()
        
        # Statistics
        self.scan_count = 0
        self.last_scan_time = None
        self.total_items_detected = 0
        
        logger.info("Real-time scanner initialized")
    
    async def scan(self) -> Dict[str, Any]:
        """
        Run a scan of Twitter and Reddit.
        
        Returns:
            dict: Scan results and statistics
        """
        logger.info("Starting real-time scan")
        self.scan_count += 1
        self.last_scan_time = datetime.now()
        
        start_time = datetime.now()
        
        # Run Twitter and Reddit trackers in parallel
        twitter_task = asyncio.create_task(self.twitter_tracker.scan())
        reddit_task = asyncio.create_task(self.reddit_tracker.scan())
        
        # Wait for both trackers to complete
        twitter_items = await twitter_task
        reddit_items = await reddit_task
        
        # Combine detected items
        all_items = twitter_items + reddit_items
        self.total_items_detected += len(all_items)
        
        # Process detected items
        results = []
        if all_items:
            logger.info(f"Processing {len(all_items)} detected items")
            results = await self.action_executor.process_items(all_items)
        
        # Calculate scan duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log action
        log_action(
            'real_time_scanner', 
            'scan', 
            f"Scan completed in {duration:.2f} seconds, detected {len(all_items)} items"
        )
        
        # Return scan results and statistics
        scan_results = {
            'scan_id': f"scan_{int(start_time.timestamp())}",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'twitter_items_count': len(twitter_items),
            'reddit_items_count': len(reddit_items),
            'total_items_count': len(all_items),
            'items': all_items,
            'results': results
        }
        
        return scan_results
    
    async def start(self):
        """
        Start the real-time scanner.
        
        This method runs continuous scans with intelligent intervals.
        Data collection happens frequently, but processing is batched.
        """
        try:
            logger.info("Starting real-time scanner with intelligent batching")
            
            # Initialize scan interval tracking
            scan_interval = 60  # Start with 1 minute
            min_interval = 30   # Don't go faster than 30 seconds
            max_interval = 300  # Don't go slower than 5 minutes
            activity_threshold = 10  # Number of items that indicate high activity
            
            while True:
                try:
                    # Run a scan
                    scan_results = await self.scan()
                    total_items = scan_results['total_items_count']
                    logger.info(f"Scan completed: detected {total_items} items")
                    
                    # Get batch statistics
                    if hasattr(self.action_executor, 'content_batcher'):
                        stats = self.action_executor.content_batcher.get_stats()
                        logger.info(f"Current batch stats: {stats}")
                    
                    # Adaptive sleep based on activity
                    if total_items > activity_threshold:
                        # High activity - scan more frequently
                        scan_interval = max(min_interval, scan_interval * 0.8)
                        logger.info(f"High activity detected ({total_items} items). Decreasing scan interval to {scan_interval}s")
                    elif total_items == 0:
                        # No activity - reduce scan frequency
                        scan_interval = min(max_interval, scan_interval * 1.2)
                        logger.info(f"No activity detected. Increasing scan interval to {scan_interval}s")
                    else:
                        # Moderate activity - keep current interval
                        logger.info(f"Moderate activity detected ({total_items} items). Keeping scan interval at {scan_interval}s")
                    
                    # Sleep for the calculated interval
                    await asyncio.sleep(scan_interval)
                    
                except Exception as e:
                    logger.error(f"Error in scan iteration: {e}")
                    # On error, use a conservative interval
                    await asyncio.sleep(max_interval)
            
        except Exception as e:
            logger.error(f"Fatal error in real-time scanner: {e}")
            log_action('real_time_scanner', 'start', f"Fatal error: {e}", status='error')
        
        finally:
            # Clean up resources
            self.cleanup()
    
    def cleanup(self):
        """
        Clean up resources.
        """
        try:
            # Clean up Twitter tracker
            if hasattr(self.twitter_tracker, 'cleanup'):
                self.twitter_tracker.cleanup()
            
            logger.info("Real-time scanner resources cleaned up")
        
        except Exception as e:
            logger.error(f"Error cleaning up resources: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scanner statistics.
        
        Returns:
            dict: Scanner statistics
        """
        return {
            'scan_count': self.scan_count,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'total_items_detected': self.total_items_detected
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create real-time scanner
    scanner = RealTimeScanner()
    
    # Run the scanner
    asyncio.run(scanner.start())
