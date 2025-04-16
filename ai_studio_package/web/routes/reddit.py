"""
Reddit Router

This module provides API endpoints for managing the Reddit scanner.
Handles starting/stopping the scanner and managing subreddit tracking using
the global RedditTracker instance managed by the main app.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from datetime import datetime
import traceback

# Import the actual tracker and DB functions
from ai_studio.data.reddit_tracker import RedditTracker
from ai_studio_package.infra.db_enhanced import (
    get_memory_nodes, search_similar_nodes
)

# Configure logging
logger = logging.getLogger("ai_studio.reddit")

# Create router
router = APIRouter()

# Models
class SubredditList(BaseModel):
    """List of subreddits to track"""
    subreddits: List[str] = Field(..., description="List of subreddit names to track")

class RedditStatus(BaseModel):
    """Status of the Reddit scanner"""
    is_running: bool = Field(..., description="Whether the scanner background task is currently running")
    subreddits: List[str] = Field(..., description="List of subreddits being tracked by the scanner instance")
    keywords: List[str] = Field(..., description="List of keywords being tracked by the scanner instance")
    # Removed scan_interval as it's not directly managed here

class RedditPost(BaseModel):
    """Reddit post model (aligned with memory node structure)"""
    id: str # Node ID (e.g., reddit_post_abcdef)
    type: str # Should be 'reddit'
    content: str # Post title or selftext
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None # Contains original post details
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Add other fields if needed, mapping from get_memory_nodes result

# Helper function for the scan loop
async def run_reddit_scan_loop(request: Request, scan_interval: int = 300):
    """Runs the Reddit scan loop in the background."""
    tracker: RedditTracker = request.app.state.reddit_scanner
    while request.app.state.reddit_scanner_running:
        logger.info("Running Reddit scan loop...")
        try:
            await tracker.scan() # Call the scan method of the tracker
            logger.info("Reddit scan finished.")
        except asyncio.CancelledError:
            logger.info("Reddit scan loop cancelled.")
            break # Exit loop if cancelled
        except Exception as e:
            logger.error(f"Error during Reddit scan: {e}", exc_info=True)
            # Optional: Add a mechanism to stop the loop after too many errors
        
        # Wait for the next interval
        try:
            await asyncio.sleep(scan_interval)
        except asyncio.CancelledError:
            logger.info("Reddit scan loop sleep cancelled.")
            break # Exit loop if cancelled during sleep

# Routes
@router.post("/start", response_model=RedditStatus)
async def start_scanner(request: Request):
    """
    Start the Reddit scanner background task.
    
    Returns:
        RedditStatus: Current status of the Reddit scanner.
    """
    if request.app.state.reddit_scanner_running:
        logger.warning("Reddit scanner background task is already running.")
        return await get_status(request) # Return current status

    tracker: RedditTracker = request.app.state.reddit_scanner
    if not tracker:
        raise HTTPException(status_code=500, detail="RedditTracker not initialized in app state.")

    logger.info("Starting Reddit scanner background task.")
    request.app.state.reddit_scanner_running = True
    # Use asyncio.create_task for background execution
    task = asyncio.create_task(run_reddit_scan_loop(request))
    request.app.state.reddit_scan_task = task
    
    return await get_status(request)

@router.post("/stop", response_model=RedditStatus)
async def stop_scanner(request: Request):
    """
    Stop the Reddit scanner background task.
    
    Returns:
        RedditStatus: Current status of the Reddit scanner.
    """
    if not request.app.state.reddit_scanner_running:
        logger.warning("Reddit scanner background task is not running.")
        return await get_status(request)

    logger.info("Stopping Reddit scanner background task.")
    request.app.state.reddit_scanner_running = False
    task = request.app.state.reddit_scan_task
    if task:
        task.cancel()
        try:
            # Wait briefly for the task to acknowledge cancellation
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.CancelledError:
            logger.info("Reddit scan task successfully cancelled.")
        except asyncio.TimeoutError:
            logger.warning("Reddit scan task did not cancel within timeout.")
        except Exception as e:
            # Log other potential exceptions during task waiting/cancellation
            logger.error(f"Error waiting for Reddit task cancellation: {e}")
        request.app.state.reddit_scan_task = None
        
    return await get_status(request)

@router.post("/set-subreddits", response_model=RedditStatus)
async def set_subreddits(
    subreddit_list: SubredditList,
    request: Request
):
    """
    Update the list of subreddits the tracker monitors.
    
    Args:
        subreddit_list: List of subreddits to track.
        request: The request object.
        
    Returns:
        RedditStatus: Current status of the Reddit scanner.
    """
    tracker: RedditTracker = request.app.state.reddit_scanner
    if not tracker:
        raise HTTPException(status_code=500, detail="RedditTracker not initialized in app state.")
        
    try:
        tracker.update_subreddits(subreddit_list.subreddits)
        logger.info(f"Updated subreddit list for tracker: {subreddit_list.subreddits}")
        return await get_status(request)
    except Exception as e:
        logger.error(f"Error updating subreddits in tracker: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating subreddits: {str(e)}")

@router.get("/status", response_model=RedditStatus)
async def get_status(request: Request):
    """
    Get the current status of the Reddit scanner task and tracker config.
    
    Returns:
        RedditStatus: Current status of the Reddit scanner.
    """
    tracker: RedditTracker = request.app.state.reddit_scanner
    if not tracker:
         # Return a default status if tracker somehow not initialized
         return RedditStatus(is_running=False, subreddits=[], keywords=[])
        
    try:
        tracker_config = tracker.get_status() # Get subreddits/keywords from tracker
        is_running = request.app.state.reddit_scanner_running
        return RedditStatus(
            is_running=is_running,
            subreddits=tracker_config.get("subreddits", []),
            keywords=tracker_config.get("keywords", [])
        )
    except Exception as e:
        logger.error(f"Error getting Reddit scanner status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting Reddit scanner status: {str(e)}")

@router.get("/posts", response_model=List[RedditPost])
async def get_posts(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    search_query: Optional[str] = None
):
    """
    Get Reddit posts from memory nodes, with optional semantic search.
    
    Args:
        request: The request object.
        limit: Maximum number of posts to return.
        offset: Number of posts to skip (for non-search).
        search_query: Optional semantic search query.
        
    Returns:
        List[RedditPost]: List of Reddit posts retrieved from memory.
    """
    try:
        posts_data = []
        if search_query:
            # Perform semantic search using db_enhanced function
            logger.info(f"Performing semantic search for Reddit posts: '{search_query}'")
            # Assuming node_type for reddit posts stored by tracker is 'reddit'
            posts_data = await search_similar_nodes(
                query_text=search_query,
                node_type="reddit", 
                limit=limit
                # Note: search_similar_nodes might not support offset directly
                # It returns nodes with similarity scores
            )
        else:
            # Get latest posts using db_enhanced function
            logger.info(f"Fetching latest {limit} Reddit posts (offset {offset})")
            posts_data = await get_memory_nodes(
                node_type="reddit", 
                limit=limit, 
                offset=offset,
                sort_by="created_at", # Ensure db_enhanced supports this sort key
                sort_order="desc"
            )
            
        # Convert raw node data to RedditPost model
        # This assumes get_memory_nodes/search_similar_nodes return dicts
        # matching the fields in the Node model from db_enhanced
        response_posts = []
        for node in posts_data:
            # Handle potential differences if search returns score, etc.
            node_content = node.get('content', '')
            if isinstance(node_content, dict):
                 # If content itself is a dict (e.g., from search results), extract relevant text
                 node_content = node_content.get('text', '') 
            
            response_posts.append(
                RedditPost(
                    id=node.get('id'),
                    type=node.get('type'),
                    content=node_content, # Use extracted content
                    tags=node.get('tags', []),
                    metadata=node.get('metadata'),
                    created_at=node.get('created_at'),
                    updated_at=node.get('updated_at')
                    # Add similarity score if present from search
                    # similarity=node.get('similarity') 
                )
            )
            
        return response_posts

    except Exception as e:
        logger.error(f"Error getting Reddit posts: {e}", exc_info=True)
        print(f"DEBUG: Error in get_posts: {str(e)}")
        print("DEBUG: Full traceback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting Reddit posts: {str(e)}")
