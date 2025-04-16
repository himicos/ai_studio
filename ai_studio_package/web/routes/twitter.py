"""
Twitter Router

API endpoints for managing the Twitter scanner (via Nitter).
Handles starting/stopping the scan task and configuring the tracker.
"""

import logging
import asyncio 
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request 
from pydantic import BaseModel, Field
from datetime import datetime

# Import the actual tracker and DB functions
from ai_studio.data.twitter_tracker import TwitterTracker
from ai_studio_package.infra.db_enhanced import (
    get_memory_nodes, search_similar_nodes 
)
# Import Node model for response consistency (assuming it's defined elsewhere or we redefine)
# from ai_studio_package.web.models.memory import Node 

# Configure logging
logger = logging.getLogger("ai_studio.twitter")

# Create router
router = APIRouter()

# Models
class AccountList(BaseModel):
    """List of Twitter accounts to track"""
    accounts: List[str] = Field(..., description="List of Twitter account names")

class KeywordList(BaseModel):
    """List of keywords to track"""
    keywords: List[str] = Field(..., description="List of keywords")

class TwitterStatus(BaseModel):
    """Status of the Twitter scanner"""
    is_running: bool = Field(..., description="Whether the scanner background task is running")
    accounts: List[str] = Field(..., description="List of accounts being tracked")
    keywords: List[str] = Field(..., description="List of keywords being tracked")

class TwitterUser(BaseModel):
    """Twitter user model"""
    id: str
    handle: str
    name: str
    url: str
    metadata: Optional[Dict[str, Any]] = None

# Redefine Tweet response model to align with Node structure from db_enhanced
class TweetPost(BaseModel): 
    """Tweet post model based on Memory Node structure"""
    id: str 
    type: str 
    content: str 
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None 
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Add similarity if needed from search results
    # similarity: Optional[float] = None

# Helper function for the scan loop
async def run_twitter_scan_loop(request: Request, scan_interval: int = 600):
    """Runs the Twitter scan loop in the background."""
    tracker: TwitterTracker = request.app.state.twitter_scanner
    while request.app.state.twitter_scanner_running:
        logger.info("Running Twitter scan loop...")
        try:
            # Scan method is async, but internally uses blocking Selenium calls
            await tracker.scan() 
            logger.info("Twitter scan finished.")
        except asyncio.CancelledError:
            logger.info("Twitter scan loop cancelled.")
            break 
        except Exception as e:
            logger.error(f"Error during Twitter scan: {e}", exc_info=True)
            # Consider adding error handling/stopping logic
        
        # Wait for the next interval
        try:
            await asyncio.sleep(scan_interval)
        except asyncio.CancelledError:
            logger.info("Twitter scan loop sleep cancelled.")
            break 

# Routes
@router.post("/start", response_model=TwitterStatus)
async def start_scanner(request: Request):
    """
    Start the Twitter scanner background task.
    
    Returns:
        TwitterStatus: Current status.
    """
    if request.app.state.twitter_scanner_running:
        logger.warning("Twitter scanner task already running.")
        return await get_status(request)

    tracker: TwitterTracker = request.app.state.twitter_scanner
    if not tracker:
        raise HTTPException(status_code=500, detail="TwitterTracker not initialized.")

    logger.info("Starting Twitter scanner background task.")
    request.app.state.twitter_scanner_running = True
    task = asyncio.create_task(run_twitter_scan_loop(request))
    request.app.state.twitter_scan_task = task
    
    return await get_status(request)

@router.post("/stop", response_model=TwitterStatus)
async def stop_scanner(request: Request):
    """
    Stop the Twitter scanner background task.
    
    Returns:
        TwitterStatus: Current status.
    """
    if not request.app.state.twitter_scanner_running:
        logger.warning("Twitter scanner task not running.")
        return await get_status(request)

    logger.info("Stopping Twitter scanner background task.")
    request.app.state.twitter_scanner_running = False
    task = request.app.state.twitter_scan_task
    if task:
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.CancelledError:
            logger.info("Twitter scan task successfully cancelled.")
        except asyncio.TimeoutError:
            logger.warning("Twitter scan task did not cancel within timeout.")
        except Exception as e:
            logger.error(f"Error during Twitter task cancellation: {e}")
        request.app.state.twitter_scan_task = None
        
    # Consider calling tracker.cleanup() here if browser should be closed immediately
    # Otherwise, it's handled on app shutdown
    
    return await get_status(request)

@router.post("/set-accounts", response_model=TwitterStatus)
async def set_accounts(accounts_list: AccountList, request: Request):
    """
    Update the list of Twitter accounts to track.
    
    Returns:
        TwitterStatus: Current status.
    """
    tracker: TwitterTracker = request.app.state.twitter_scanner
    if not tracker:
        raise HTTPException(status_code=500, detail="TwitterTracker not initialized.")
        
    try:
        tracker.update_accounts(accounts_list.accounts)
        logger.info(f"Updated Twitter accounts: {accounts_list.accounts}")
        return await get_status(request)
    except Exception as e:
        logger.error(f"Error updating Twitter accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-keywords", response_model=TwitterStatus)
async def set_keywords(keywords_list: KeywordList, request: Request):
    """
    Update the list of keywords to track.
    
    Returns:
        TwitterStatus: Current status.
    """
    tracker: TwitterTracker = request.app.state.twitter_scanner
    if not tracker:
        raise HTTPException(status_code=500, detail="TwitterTracker not initialized.")
        
    try:
        tracker.update_keywords(keywords_list.keywords)
        logger.info(f"Updated Twitter keywords: {keywords_list.keywords}")
        return await get_status(request)
    except Exception as e:
        logger.error(f"Error updating Twitter keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=TwitterStatus)
async def get_status(request: Request):
    """
    Get the current status of the Twitter scanner task and configuration.
    
    Returns:
        TwitterStatus: Current status.
    """
    logger.info(f"Accessing /status route. App state keys: {list(request.app.state.__dict__.keys())}") # Log state keys
    tracker: Optional[TwitterTracker] = None
    if hasattr(request.app.state, 'twitter_scanner'):
        tracker = request.app.state.twitter_scanner
        logger.info(f"Found app.state.twitter_scanner: {type(tracker)}")
    else:
        logger.info("app.state.twitter_scanner attribute not found.")

    if not tracker:
        logger.info("Twitter tracker instance is None or not found. Returning default status.")
        # Ensure accounts/keywords are lists even if tracker is None
        return TwitterStatus(is_running=False, accounts=[], keywords=[])
        
    # This part should only run if tracker exists
    try:
        logger.info("Twitter tracker instance found. Getting status from tracker.")
        tracker_config = tracker.get_status() # This method exists
        is_running = False
        if hasattr(request.app.state, 'twitter_scanner_running'):
             is_running = request.app.state.twitter_scanner_running
             logger.info(f"Found app.state.twitter_scanner_running: {is_running}")
        else:
             # If tracker exists but running state doesn't, assume not running
             logger.warning("app.state.twitter_scanner_running attribute not found. Assuming not running.")
        
        logger.info(f"Tracker config: {tracker_config}")

        accounts = tracker_config.get("accounts", [])
        keywords = tracker_config.get("keywords", [])
        
        # Defensive check to ensure accounts/keywords are lists
        accounts = accounts if isinstance(accounts, list) else []
        keywords = keywords if isinstance(keywords, list) else []

        return TwitterStatus(
            is_running=is_running,
            accounts=accounts, 
            keywords=keywords
        )
    except Exception as e:
        logger.error(f"Error getting Twitter status from tracker instance: {e}", exc_info=True) # Log the specific error
        raise HTTPException(status_code=500, detail=f"Internal error getting Twitter status: {str(e)}")

@router.get("/posts", response_model=List[TweetPost])
async def get_posts(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    search_query: Optional[str] = None
):
    """
    Get stored tweets (memory nodes) with optional semantic search.
    
    Returns:
        List[TweetPost]: List of stored tweets.
    """
    try:
        posts_data = []
        if search_query:
            logger.info(f"Performing semantic search for tweets: '{search_query}'")
            posts_data = await search_similar_nodes(
                query_text=search_query,
                node_type="tweet", 
                limit=limit
            )
        else:
            logger.info(f"Fetching latest {limit} tweets (offset {offset})")
            posts_data = await get_memory_nodes(
                node_type="tweet", 
                limit=limit, 
                offset=offset,
                sort_by="created_at", 
                sort_order="desc"
            )
            
        # Convert node data to TweetPost model
        response_posts = []
        for node in posts_data:
             # Handle potential differences if search returns score, etc.
            node_content = node.get('content', '')
            if isinstance(node_content, dict):
                 node_content = node_content.get('text', '') 

            response_posts.append(
                TweetPost(
                    id=node.get('id'),
                    type=node.get('type'),
                    content=node_content,
                    tags=node.get('tags', []),
                    metadata=node.get('metadata'),
                    created_at=node.get('created_at'),
                    updated_at=node.get('updated_at')
                    # similarity=node.get('similarity') 
                )
            )
            
        return response_posts

    except Exception as e:
        logger.error(f"Error getting tweets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting tweets: {str(e)}")

@router.get("/search-users", response_model=List[TwitterUser])
async def search_users(
    request: Request,
    query: str,
    limit: int = 10
):
    """
    Search for Twitter users using Nitter.
    
    Args:
        query (str): Search query
        limit (int): Maximum number of results to return
        
    Returns:
        List[TwitterUser]: List of matching Twitter users
    """
    tracker: TwitterTracker = request.app.state.twitter_scanner
    if not tracker:
        raise HTTPException(status_code=500, detail="TwitterTracker not initialized.")
        
    try:
        users = await tracker.search_users(query=query, limit=limit)
        return users
    except Exception as e:
        logger.error(f"Error searching Twitter users: {e}")
        raise HTTPException(status_code=500, detail=str(e))
