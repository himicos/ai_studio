"""
API Routes for Reddit Agent

Provides endpoints for managing and interacting with the RedditTracker.
"""

import logging
import re
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
import json # Ensure json is imported if saving summary to memory nodes
import uuid
import time
import asyncio
import functools

# Import the tracker and DB functions (assuming tracker is instantiated in main app)
from data.reddit_tracker import RedditTracker
from ai_studio_package.infra.db_enhanced import (
    get_db_connection, get_reddit_feed, create_memory_node,
    get_top_reddit_posts, create_memory_from_post
)
from ai_studio_package.infra.models import load_embedding_model
from ai_studio_package.infra.summarizer import SummarizationPipelineSingleton
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss

logger = logging.getLogger("ai_studio.reddit_agent")
router = APIRouter(prefix="/api/reddit/agent", tags=["Reddit Agent"])

# --- Pydantic Models ---
class SubredditAddRequest(BaseModel):
    subreddit_name: str

class SubredditResponse(BaseModel):
    name: str
    is_active: bool
    last_scanned_post_id: Optional[str] = None

class RedditFeedItem(BaseModel):
    id: str
    subreddit: str
    title: str
    author: Optional[str]
    created_utc: str
    score: int
    upvote_ratio: float
    num_comments: int
    permalink: str
    url: str
    selftext: Optional[str]
    is_self: bool
    is_video: bool
    over_18: bool
    spoiler: bool
    stickied: bool
    scraped_at: str

class RedditAgentStatus(BaseModel):
    agent_type: str
    is_running: bool
    scan_interval_seconds: int
    client_initialized: bool

class SummarizeResponse(BaseModel):
    post_id: str
    original_title: Optional[str] = None
    original_selftext: Optional[str] = None
    summary: str
    memory_node_id: Optional[str] = None # If saving to memory

# --- Dependency --- 
# This dependency function retrieves the tracker instance from the FastAPI app state
async def get_reddit_tracker(request: Request) -> RedditTracker:
    if not hasattr(request.app.state, 'reddit_tracker') or request.app.state.reddit_tracker is None:
        logger.error("RedditTracker not found in application state. Ensure it\'s initialized at startup.")
        raise HTTPException(status_code=503, detail="Reddit Agent service is not available.")
    tracker = request.app.state.reddit_tracker
    # Optional: Check if the PRAW client within the tracker is initialized
    if not tracker.reddit:
         logger.warning("RedditTracker exists in state, but PRAW client is not initialized.")
         raise HTTPException(status_code=503, detail="Reddit Agent PRAW client failed to initialize. Check credentials.")
    return tracker

# --- Dependency for summarization components ---
async def get_summarizer_components(request: Request) -> Tuple[Any, Any]:
    """Dependency to get the summarizer pipeline and tokenizer from app state."""
    pipeline = getattr(request.app.state, 'summarizer_pipeline', None)
    tokenizer = getattr(request.app.state, 'summarizer_tokenizer', None)
    if not pipeline or not tokenizer:
        logger.error("Summarization pipeline or tokenizer not found in application state.")
        raise HTTPException(status_code=503, detail="Summarization service is not available.")
    return pipeline, tokenizer

# --- Routes ---

@router.get("/status", response_model=RedditAgentStatus)
async def get_tracker_status(tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Get the current status of the Reddit background tracker."""
    try:
        status = tracker.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting Reddit tracker status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching status")

@router.get("/tracked", response_model=List[SubredditResponse])
async def list_tracked_subreddits(tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Get the list of subreddits currently being tracked."""
    try:
        tracked_subreddits = await tracker.get_tracked_subreddits()
        return tracked_subreddits
    except Exception as e:
        logger.error(f"Error listing tracked subreddits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve tracked subreddits")

@router.post("/tracked", status_code=201)
async def add_tracked_subreddit_route(request: SubredditAddRequest, tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Add a new subreddit to the tracking list."""
    subreddit_name = request.subreddit_name.strip()
    if not subreddit_name:
        raise HTTPException(status_code=400, detail="Subreddit name cannot be empty")

    try:
        success = await tracker.add_subreddit(subreddit_name)
        if success:
            return {"message": f"Subreddit r/{subreddit_name} added successfully."}
        else:
            if not tracker.reddit:
                 raise HTTPException(status_code=503, detail="Reddit client not initialized. Check credentials.")
            raise HTTPException(status_code=404, detail=f"Failed to add subreddit r/{subreddit_name}. It might be invalid, private, or does not exist.")
    except Exception as e:
        logger.error(f"Error adding subreddit r/{subreddit_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error adding subreddit.")

@router.delete("/tracked/{subreddit_name}", status_code=200)
async def remove_tracked_subreddit_route(subreddit_name: str, tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Remove a subreddit from the tracking list."""
    if not subreddit_name:
        raise HTTPException(status_code=400, detail="Subreddit name cannot be empty")

    try:
        success = await tracker.remove_subreddit(subreddit_name)
        if success:
            return {"message": f"Subreddit r/{subreddit_name} removed successfully."}
        else:
            # Removal might fail silently if subreddit wasn't tracked
            return {"message": f"Subreddit r/{subreddit_name} was not found in the tracked list or could not be removed."}
    except Exception as e:
        logger.error(f"Error removing subreddit r/{subreddit_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error removing subreddit.")

@router.post("/scan", status_code=200)
async def trigger_scan_route(tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Manually trigger a scan of all tracked subreddits."""
    try:
        # Run scan in background? For now, run synchronously and wait
        await tracker.scan()
        return {"message": "Reddit scan initiated successfully."}
    except Exception as e:
        logger.error(f"Error triggering Reddit scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger Reddit scan.")

@router.post("/start_tracking", status_code=200)
async def start_tracking_route(interval_seconds: Optional[int] = None, tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Start the background Reddit tracking process."""
    try:
        success = await tracker.start_tracking(interval_seconds=interval_seconds)
        if success:
             return {"message": f"Reddit background tracking started with interval {tracker.scan_interval_seconds}s."}
        else:
             # Check status to provide more specific feedback
             status = tracker.get_status()
             if status['is_running']:
                  raise HTTPException(status_code=409, detail="Tracking is already running.")
             elif not status['client_initialized']:
                 raise HTTPException(status_code=503, detail="Cannot start tracking, Reddit client not initialized.")
             else:
                 raise HTTPException(status_code=500, detail="Failed to start tracking for an unknown reason.")
    except Exception as e:
        logger.error(f"Error starting Reddit tracking: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error starting tracking.")

@router.post("/stop_tracking", status_code=200)
async def stop_tracking_route(tracker: RedditTracker = Depends(get_reddit_tracker)):
    """Stop the background Reddit tracking process."""
    try:
        success = await tracker.stop_tracking()
        if success:
            return {"message": "Reddit background tracking stopped successfully."}
        else:
             # It might already be stopped
             status = tracker.get_status()
             if not status['is_running']:
                 return {"message": "Reddit background tracking was already stopped."}
             else:
                 raise HTTPException(status_code=500, detail="Failed to stop tracking cleanly.")
    except Exception as e:
        logger.error(f"Error stopping Reddit tracking: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error stopping tracking.")

@router.get("/feed", response_model=List[RedditFeedItem])
async def get_reddit_posts_feed(
    subreddit: Optional[str] = Query(None, description="Filter by specific subreddit (case-insensitive)"),
    limit: int = Query(50, ge=1, le=200, description="Number of posts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query('created_utc', description="Sort column: created_utc, score, num_comments, author, subreddit"),
    sort_order: str = Query('desc', description="Sort order: asc or desc"),
    search: Optional[str] = Query(None, description="Search term for post title or selftext")
):
    """Retrieve stored Reddit posts with filtering and sorting."""
    conn = None
    try:
        conn = get_db_connection()
        feed_data = get_reddit_feed(
            conn=conn,
            subreddit=subreddit,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            search_term=search
        )
        return feed_data
    except Exception as e:
        logger.error(f"Error retrieving Reddit feed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve Reddit feed from database.")
    finally:
        if conn:
            conn.close() 

# --- NEW Route: Summarize Individual Post ---
@router.post("/summarize_post/{post_id}", response_model=SummarizeResponse)
async def summarize_reddit_post(
    post_id: str,
    summarizer_components: Tuple[Any, Any] = Depends(get_summarizer_components)
):
    """Generate a summary for a specific Reddit post using its ID."""
    summarizer, tokenizer = summarizer_components
    conn = None
    
    logger.info(f"Summarization requested for Reddit post ID: {post_id}")

    try:
        # 1. Fetch post content from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title, selftext, subreddit FROM reddit_posts WHERE id = ?", (post_id,))
        post_data = cursor.fetchone()
        conn.close()
        conn = None # Mark as closed

        if not post_data:
            raise HTTPException(status_code=404, detail=f"Reddit post with ID {post_id} not found.")

        # Safely extract title and selftext using indexing instead of attribute access
        title = post_data[0] if post_data[0] else ""  # title is first column
        selftext = post_data[1] if post_data[1] else ""  # selftext is second column
        
        # Combine title and selftext for summarization input
        text_to_summarize = f"{title}\n\n{selftext}".strip()
        
        if not text_to_summarize:
             logger.warning(f"Post {post_id} has no title or selftext to summarize.")
             # Return empty summary or specific message?
             return SummarizeResponse(post_id=post_id, original_title=title, original_selftext=selftext, summary="Post has no text content to summarize.")

        # 2. Truncate input based on tokenizer limits (similar to Twitter agent)
        # Use tokenizer max_length or a reasonable default (e.g., 1024 for distilbart)
        max_input_length = getattr(tokenizer, 'model_max_length', 1024)
        # Use slightly less to be safe
        safe_max_length = max_input_length - 10 
        
        inputs = tokenizer(text_to_summarize, return_tensors='pt', max_length=safe_max_length, truncation=True)
        truncated_text = tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
        
        if len(truncated_text) < len(text_to_summarize):
             logger.warning(f"Summarization input for post {post_id} was truncated from {len(text_to_summarize)} to {len(truncated_text)} characters.")

        # 3. Generate Summary
        # Adjust summarization parameters as needed (min_length, max_length)
        summary_result = summarizer(truncated_text, max_length=150, min_length=30, do_sample=False)
        summary_text = summary_result[0]['summary_text']
        logger.info(f"Generated summary for post {post_id}. Length: {len(summary_text)}")
        
        # 4. (Optional) Store summary in memory_nodes
        memory_node_id = None
        try:
            memory_node = {
                'id': f'reddit_summary_{post_id}', # Unique ID for the summary node
                'type': 'reddit_summary',
                'content': summary_text,
                'tags': ['summary', 'reddit', post_data[2] if len(post_data) > 2 else 'unknown'],
                'source_id': post_id,
                'source_type': 'reddit_post',
                'metadata': {
                    'original_post_id': post_id,
                    'original_title': title,
                     # Avoid storing full original text in metadata if too long
                    'original_selftext_preview': selftext[:200] + '...' if len(selftext) > 200 else selftext,
                    'model_used': getattr(summarizer.model, 'name_or_path', 'unknown')
                }
            }
            conn = get_db_connection()
            memory_node_id = create_memory_node(memory_node)
            if memory_node_id:
                logger.info(f"Saved Reddit post summary to memory node: {memory_node_id}")
            else:
                 logger.error(f"Failed to save Reddit post summary to memory for post {post_id}")
            conn.commit() # Commit after create_memory_node call

            # --- Trigger Background Embedding --- 
            logger.info(f"Triggering background embedding generation for Reddit node: {memory_node_id}")
            loop = asyncio.get_running_loop()
            loop.run_in_executor(
                None, # Use default ThreadPoolExecutor
                functools.partial(generate_embedding_for_node_faiss, memory_node_id)
            ) # No need to await the executor task here
            # ------------------------------------ 
            
        except Exception as mem_e:
            logger.error(f"Error saving summary to memory for post {post_id}: {mem_e}", exc_info=True)
            if conn: conn.rollback()
        finally:
             if conn:
                 conn.close()
                 conn = None

        # 5. Return response
        return SummarizeResponse(
            post_id=post_id,
            original_title=title,
            original_selftext=selftext, # Consider not returning full text if very long
            summary=summary_text,
            memory_node_id=memory_node_id
        )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.error(f"Error summarizing Reddit post {post_id}: {e}", exc_info=True)
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to summarize Reddit post: {str(e)}")
    finally:
        # Ensure connection is closed if an error occurred before explicit close
        if conn:
            conn.close() 

# --- NEW Route: Get Top Reddit Posts ---
@router.get("/top_posts", response_model=List[RedditFeedItem])
async def get_top_posts(
    limit: int = Query(10, ge=1, le=50, description="Number of top posts to return"),
    metric: str = Query('score', description="Metric to sort by: score, num_comments, created_utc")
):
    """Retrieve the top N Reddit posts based on a specified metric."""
    conn = None
    try:
        conn = get_db_connection()
        # Input validation for metric is handled within get_top_reddit_posts
        top_posts_data = get_top_reddit_posts(conn, limit=limit, metric=metric)
        return top_posts_data
    except Exception as e:
        logger.error(f"Error retrieving top Reddit posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve top Reddit posts from database.")
    finally:
        if conn:
            conn.close() 

def store_reddit_summary(
    post: Dict[str, Any],
    summary: str,
    summarizer_model_name: str
):
    """Stores a Reddit post and its summary as a memory node and triggers embedding."""
    
    # Prepare data for memory node creation
    # Use permalink or another stable identifier for source_id
    # Ensure uniqueness for the primary key `id`
    node_id = f"reddit_{post.get('id', str(uuid.uuid4()))}"
    source_id = post.get('permalink', node_id) # Use permalink if available
    tags = ['reddit', 'summary', post.get('subreddit')]
    metadata = {
        'source_id': post.get('id'),
        'source_type': 'reddit',
        'subreddit': post.get('subreddit'),
        'title': post.get('title', ''),
        'author': post.get('author'),
        'upvotes': post.get('score'),
        'num_comments': post.get('num_comments'),
        'url': post.get('url'), # Direct link to post
        'permalink': post.get('permalink'), # Reddit permalink
        'model_used': summarizer_model_name, 
        'fetched_at': int(time.time()),
        'created_utc': int(post.get('created_utc', 0))
    }
    
    memory_node_data = {
        "id": node_id,
        "type": "reddit_summary",
        "content": summary, # The generated summary
        "tags": json.dumps([t for t in tags if t]), # Ensure no None tags
        "created_at": int(post.get('created_utc', int(time.time()))), # Use post creation time
        "updated_at": int(time.time()), # Use current time for update
        "source_id": source_id,
        "source_type": "reddit",
        "metadata": json.dumps(metadata),
        "has_embedding": 0 # Initially false
    }
    
    try:
        # Call the function to insert/update the memory node
        inserted_or_updated = create_memory_from_post(memory_node_data)

        if inserted_or_updated:
            logger.info(f"Successfully stored or updated memory node for Reddit post: {node_id}")
            
            # --- Trigger Background Embedding --- 
            logger.info(f"Triggering background embedding generation for Reddit node: {node_id}")
            loop = asyncio.get_running_loop()
            loop.run_in_executor(
                None, # Use default ThreadPoolExecutor
                functools.partial(generate_embedding_for_node_faiss, node_id)
            ) # No need to await the executor task here
            # ------------------------------------ 
            
        else:
            # This case might occur if ON CONFLICT DO NOTHING happens and no update was made
            logger.info(f"Memory node for Reddit post {node_id} already exists and was not updated.")

    except Exception as e:
        logger.error(f"Error storing Reddit summary memory node {node_id}: {e}", exc_info=True)