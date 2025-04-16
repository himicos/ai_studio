"""
Twitter Agent Router

Manages tracking Twitter users and their tweets, scoring, and keyword extraction.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Query
from pydantic import BaseModel
import asyncio
from ai_studio_package.data.twitter_tracker import TwitterTracker
from ai_studio_package.infra.db_enhanced import (
    get_db_connection, get_twitter_feed, create_memory_node, 
    get_tweet_by_id, get_top_twitter_posts
)
import sqlite3
from transformers import pipeline
import yake

# Import run_twitter_scan_loop
from ai_studio_package.web.routes.twitter import run_twitter_scan_loop

# Import store_memory_node
from ai_studio_package.web.routes.memory import store_memory_node

# Configure logging
logger = logging.getLogger("ai_studio.twitter_agent")

# Create router
router = APIRouter(prefix="/api/twitter-agent", tags=["Twitter Agent"])

# Store the background task reference
# Moved initialization logic to main.py startup event
# twitter_tracker = TwitterTracker() # Remove initialization here

# --- Pydantic Models ---

class UserSearchResponse(BaseModel):
    id: str
    handle: str
    name: str

class UserAddRequest(BaseModel):
    handle: str
    tags: Optional[List[str]] = None

class TrackedUserResponse(BaseModel):
    id: str
    handle: str
    tags: List[str]
    date_added: Optional[str] = None

class TweetResponse(BaseModel):
    id: str
    user_id: str
    handle: Optional[str] = None
    content: Optional[str] = None
    date_posted: Optional[str] = None
    url: Optional[str] = None
    sentiment: Optional[str] = None
    engagement: Dict[str, int]
    keywords: List[str]

class ScoreRequest(BaseModel):
    tweet_ids: List[str]

class ScoreResponse(BaseModel):
    # Define structure for scoring results (e.g., list of scored tweets)
    scored_tweets: List[TweetResponse] # Placeholder

class KeywordsResponse(BaseModel):
    keywords: List[str]

class TrackingStatusResponse(BaseModel):
    is_tracking: bool
    tracked_users_count: int
    tracked_tweets_count: int

class SummarizeRequest(BaseModel):
    tweets: List[TweetResponse] # Or maybe just List[str] containing content?
    focus: Optional[str] = None
    # Add other potential parameters like desired length, focus, etc.

class SummarizeResponse(BaseModel):
    summary: str

class TweetSummaryResponse(BaseModel):
    tweet_id: str
    original_content: Optional[str] = None
    summary: str
    memory_node_id: Optional[str] = None

# --- Endpoints ---

@router.get("/search_users", response_model=List[UserSearchResponse])
async def search_users(query: str, request: Request):
    """Search for Twitter users."""
    logger.info(f"Searching for Twitter user: {query}")
    
    tracker = getattr(request.app.state, 'twitter_scanner', None)
    if not tracker or not hasattr(tracker, 'browser_manager') or not hasattr(tracker.browser_manager, 'search_users'): # Check existence and method
        logger.error("Twitter tracker or browser_manager or search_users method not available.")
        raise HTTPException(status_code=500, detail="Twitter search functionality not available.")
        
    try:
        # Use the tracker's browser manager instance to search for users
        # NOTE: Assuming search_users returns a list of dicts like {'id': ..., 'handle': ..., 'name': ...}
        users_found = await tracker.browser_manager.search_users(query) 
        
        if not users_found:
            logger.info(f"No users found matching query: {query}")
            return []
            
        logger.info(f"Found {len(users_found)} potential users for query: {query}")
        # Map the results to the response model
        return [UserSearchResponse(id=str(user.get('id', '')), handle=user.get('handle', ''), name=user.get('name', '')) 
                for user in users_found]
                
    except AttributeError as ae:
        # Catch if methods don't exist
        logger.error(f"AttributeError during user search: {ae}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search function encountered an internal error.")
    except Exception as e:
        logger.error(f"Error searching users for query '{query}': {e}", exc_info=True)
        # Return empty list on error, or raise HTTPException?
        # Returning empty might be better for UI 
        return []

@router.post("/add_user", response_model=dict)
async def add_user(req: UserAddRequest, request: Request):
    """Add a Twitter user handle directly to the database."""
    handle = req.handle.strip()
    tags = req.tags or []
    
    # Basic handle validation (e.g., remove leading @)
    if handle.startswith('@'):
        handle = handle[1:]
        
    if not handle: # Prevent adding empty handles
        raise HTTPException(status_code=400, detail="User handle cannot be empty.")
        
    logger.info(f"Attempting to add user handle to DB: {handle}")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists (case-insensitive check might be better?)
        cursor.execute("SELECT id FROM tracked_users WHERE handle = ? COLLATE NOCASE", (handle,))
        existing_user = cursor.fetchone()
        if existing_user:
            logger.warning(f"User {handle} already exists in the database (ID: {existing_user[0]}).")
            conn.close()
            return {"message": f"User {handle} is already tracked."}
            
        # Insert the new user, using handle as the ID (since ID is TEXT PRIMARY KEY)
        cursor.execute(
            "INSERT INTO tracked_users (id, handle, tags, added_on) VALUES (?, ?, ?, ?)", 
            (handle, handle, json.dumps(tags), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        logger.info(f"User {handle} added to database.")

        # Optional: Add user to the live tracker instance if needed immediately
        # tracker = getattr(request.app.state, 'twitter_scanner', None)
        # if tracker:
        #     await tracker.add_user(handle) # Might still be useful if tracker doesn't reload users often
        #     logger.info(f"User {handle} added to live tracker instance.")

        return {"message": f"User {handle} added successfully"}
    
    except sqlite3.IntegrityError: # Should be caught by the SELECT check now, but good practice
        logger.warning(f"IntegrityError adding user {handle} (likely already exists).")
        raise HTTPException(status_code=409, detail=f"User {handle} is already tracked (Integrity Error).")
    except Exception as e:
        logger.error(f"Error adding user {handle} to DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding user: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.get("/tracked_users", response_model=List[TrackedUserResponse])
async def get_tracked_users(request: Request):
    """Get the list of currently tracked users from the database."""
    logger.info("Fetching tracked users list from database...")
    conn = None
    try:
        conn = get_db_connection()
        # Use a dictionary cursor for easier mapping to Pydantic model
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Select using correct column name 'added_on', still filter NULL IDs
        cursor.execute("SELECT id, handle, tags, added_on FROM tracked_users WHERE id IS NOT NULL ORDER BY added_on DESC") 
        users = cursor.fetchall()
        conn.close()
        conn = None
        
        logger.info(f"Found {len(users)} tracked users in DB with non-NULL IDs.") # Updated log
        
        # Convert rows to the response model, handling potential JSON parsing errors
        response_users = []
        for user_row in users:
            try:
                tags_list = json.loads(user_row['tags']) if user_row['tags'] else []
            except json.JSONDecodeError:
                logger.warning(f"Could not parse tags JSON for user {user_row['handle']}: {user_row['tags']}")
                tags_list = [] # Default to empty list on error
                
            response_users.append(
                TrackedUserResponse(
                    id=str(user_row['id']), # Ensure ID is string
                    handle=user_row['handle'],
                    tags=tags_list,
                    date_added=user_row['added_on'] or "" # Use correct column name
                )
            )
        return response_users
        
    except Exception as e:
        logger.error(f"Error fetching tracked users: {e}", exc_info=True)
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail="Failed to fetch tracked users")

@router.delete("/remove_user/{user_id}", response_model=dict)
async def remove_user(user_id: str, request: Request):
    """Remove a tracked user from the database and attempt to update the live tracker."""
    logger.info(f"Attempting to remove user with ID: {user_id}")
    
    conn = None
    handle_to_remove = None
    db_deleted = False
    tracker_updated = False

    try:
        # 1. Get handle from DB 
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT handle FROM tracked_users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                logger.warning(f"User with ID {user_id} not found in database for removal.")
                raise HTTPException(status_code=404, detail=f"User not found.")
            handle_to_remove = user_row[0]
            logger.info(f"Found user handle '{handle_to_remove}' for ID {user_id}.")
        except Exception as db_fetch_err:
            logger.error(f"Error fetching handle for user ID {user_id}: {db_fetch_err}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to fetch user details before removal.")
        finally:
            if conn: conn.close(); conn = None # Close connection after fetch

        # 2. Remove from database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracked_users WHERE id = ?", (user_id,))
            conn.commit()
            db_deleted = (cursor.rowcount > 0)
            if not db_deleted:
                 logger.warning(f"DELETE statement affected 0 rows for ID {user_id} (already deleted?).")
            else:
                 logger.info(f"User with ID {user_id} removed from database.")
                 
        except Exception as db_delete_err:
            logger.error(f"Error deleting user ID {user_id} from DB: {db_delete_err}", exc_info=True)
            # Decide if we should still try to remove from tracker? Maybe not.
            raise HTTPException(status_code=500, detail="Failed to remove user from database.")
        finally:
             if conn: conn.close(); conn = None # Close connection after delete
        
        # 3. Attempt to remove from the live tracker instance
        try:
            tracker = getattr(request.app.state, 'twitter_scanner', None)
            if tracker and handle_to_remove:
                normalized_handle = handle_to_remove.lstrip('@').strip()
                if normalized_handle in tracker.tracked_users:
                    await tracker.remove_user(normalized_handle) 
                    logger.info(f"User handle '{normalized_handle}' removed from live tracker instance.")
                    tracker_updated = True
                else:
                     logger.warning(f"User handle '{normalized_handle}' not found in live tracker's list: {tracker.tracked_users}")
            elif not tracker:
                logger.warning("Twitter tracker instance not found in app state.")
        except Exception as tracker_err:
            logger.error(f"Error removing handle '{handle_to_remove}' from tracker instance: {tracker_err}", exc_info=True)
            # Log error but don't fail the whole request if DB delete succeeded
        
        # Return success if DB delete worked, even if tracker update failed
        if db_deleted:
            return {"message": f"User removed successfully"}
        else:
            # If DB delete didn't happen (e.g., already gone), maybe return specific message or 404?
            # For now, let initial fetch handle 404, return success if no DB error
            return {"message": f"User removal process completed (user may have already been removed)."}
        
    except HTTPException as http_exc: # Re-raise HTTPExceptions
        raise http_exc
    except Exception as e: # Catch any unexpected general errors
        logger.error(f"Unexpected error during remove_user for ID {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error removing user: {str(e)}")

@router.get("/feed", response_model=List[TweetResponse])
async def get_feed(
    limit: int = 50,
    offset: int = 0,
    keyword: Optional[str] = None,
    sort_by: str = "date_posted",
    sort_order: str = "desc"
):
    """Get the tweet feed."""
    logger.info(f"Fetching tracked tweets feed (limit={limit}, offset={offset}, keyword={keyword}, sort_by={sort_by}, sort_order={sort_order})")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get tracked users
        cursor.execute("SELECT id, handle FROM tracked_users")
        users = cursor.fetchall()
        logger.info(f"Found {len(users)} tracked users")
        
        # Get tweets
        query = """
            SELECT t.*, u.handle 
            FROM tracked_tweets t
            JOIN tracked_users u ON t.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if keyword:
            query += " AND t.content LIKE ?"
            params.append(f"%{keyword}%")
            
        # Use correct column name for sorting
        sort_column = "date_posted" # Default sort column
        # Add engagement columns to allowed sort columns
        allowed_sort_columns = [
            "date_posted", 
            "content", 
            "score",
            "engagement_likes", 
            "engagement_retweets", 
            "engagement_replies"
        ]
        if sort_by in allowed_sort_columns:
            sort_column = sort_by
        else:
            logger.warning(f"Invalid sort_by column specified: {sort_by}. Defaulting to {sort_column}.")
            sort_column = "date_posted" # Explicitly default back
            
        sort_direction = "DESC" # Default sort direction
        if sort_order.upper() == "ASC":
            sort_direction = "ASC"
            
        # Modify ORDER BY to handle NULLs predictably
        # When DESC, put NULLs last. When ASC, put NULLs first.
        nulls_placement = "NULLS LAST" if sort_direction == "DESC" else "NULLS FIRST"
        query += f" ORDER BY t.{sort_column} {sort_direction} {nulls_placement} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        tweets = cursor.fetchall()
        logger.info(f"Found {len(tweets)} tracked tweets")
        
        if tweets:
            logger.debug("Raw tweet data fetched from DB (first row):")
            # Log all columns for the first row to check content
            # Check indices based on SELECT t.* - sentiment should be index 9
            first_tweet_raw = tweets[0] 
            logger.debug(f"  ID(0): {first_tweet_raw[0]}, UserID(1): {first_tweet_raw[1]}, Content(2): '{str(first_tweet_raw[2])[:50]}...', Date(3): {first_tweet_raw[3]}, Likes(4): {first_tweet_raw[4]}, RTs(5): {first_tweet_raw[5]}, Replies(6): {first_tweet_raw[6]}, URL(7): {first_tweet_raw[7]}, Score(8): {first_tweet_raw[8]}, Sentiment(9): {first_tweet_raw[9]}, Keywords(10): {first_tweet_raw[10]}, AddedAt(11): {first_tweet_raw[11]}, Handle(12): {first_tweet_raw[12]}")
        
        if not tweets:
            logger.info("No tweets found in the database")
            return []
            
        # Construct response using correct indices and handling JSON
        response_tweets = []
        for tweet in tweets:
            try:
                # Construct engagement dict from individual columns
                engagement_dict = {
                    "likes": tweet[4] or 0,
                    "retweets": tweet[5] or 0,
                    "replies": tweet[6] or 0
                }
                # Parse keywords JSON string from the correct column
                keywords_list = json.loads(tweet[10]) if tweet[10] else []

                # Construct the full URL if the path exists
                # TODO: Make base Nitter URL configurable?
                base_nitter_url = "https://nitter.net" 
                partial_url = tweet[7] # URL path is index 7
                full_url = f"{base_nitter_url}{partial_url}" if partial_url and partial_url.startswith('/') else partial_url

                response_tweets.append(TweetResponse(
                    id=tweet[0], # tweet_id
                    user_id=tweet[1], # user_id
                    handle=tweet[12], # handle (from JOIN) is index 12 now
                    content=tweet[2], # content
                    date_posted=str(tweet[3]) if tweet[3] else None, # date_posted
                    url=full_url, # Use the constructed full URL (from index 7)
                    sentiment=tweet[9], # <<< GET Sentiment from DB (index 9) >>>
                    engagement=engagement_dict,
                    keywords=keywords_list # Keywords is index 10 now
                ))
            except Exception as parse_err:
                 logger.error(f"Error parsing tweet row (ID: {tweet[0]}): {parse_err}", exc_info=True)
                 # Skip this tweet if parsing fails
                 continue
                 
        return response_tweets
        
    except Exception as e:
        logger.error(f"Error fetching feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/start_tracking", response_model=dict)
async def start_tracking(request: Request, background_tasks: BackgroundTasks):
    """Start the Twitter tracking process using the tracker's internal loop."""
    logger.info("Attempting to start Twitter tracking via tracker.start()...")
    
    tracker = getattr(request.app.state, 'twitter_scanner', None)
    if not tracker:
        logger.error("Twitter tracker not initialized in app state.")
        raise HTTPException(status_code=500, detail="Twitter tracker not initialized.")

    # Check if tracker thinks it's already running
    if tracker.is_running and tracker.scan_task and not tracker.scan_task.done():
        logger.warning("Tracker is already running according to its state.")
        # Ensure app.state reflects this, just in case
        request.app.state.twitter_scanner_running = True
        request.app.state.twitter_scan_task = tracker.scan_task
        return {"message": "Twitter tracking is already running."}

    try:
        # Reload users before starting (Good practice)
        try:
            await tracker.load_users_from_db()
            logger.info(f"Tracker instance reloaded with users: {tracker.tracked_users}")
        except Exception as load_err:
            logger.error(f"Error loading users into tracker before start: {load_err}", exc_info=True)
            # Don't necessarily fail the start if loading fails, but log it.

        # Call the tracker's start method (which creates the background task)
        logger.info("Calling tracker.start()...")
        scan_interval = 600 # TODO: Make configurable (e.g., via settings API/DB)
        await tracker.start(scan_interval=scan_interval)
        logger.info(f"tracker.start() completed. Tracker running: {tracker.is_running}")

        # Update app.state to reflect the tracker's state
        request.app.state.twitter_scanner_running = tracker.is_running
        request.app.state.twitter_scan_task = tracker.scan_task # Store the task managed by the tracker
        
        if tracker.is_running:
            logger.info("Twitter tracking background task started successfully via tracker.")
            return {"message": f"Twitter tracking started (interval: {scan_interval}s)"}
        else:
            logger.error("tracker.start() was called but tracker.is_running is still false.")
            raise HTTPException(status_code=500, detail="Failed to confirm tracking start status.")
            
    except Exception as e:
        logger.error(f"Error calling tracker.start(): {e}", exc_info=True)
        # Ensure state reflects failure
        request.app.state.twitter_scanner_running = False 
        if hasattr(request.app.state, 'twitter_scan_task'):
             del request.app.state.twitter_scan_task 
        raise HTTPException(status_code=500, detail=f"Error starting tracking task: {str(e)}")

@router.post("/stop_tracking", response_model=dict)
async def stop_tracking(request: Request, background_tasks: BackgroundTasks):
    """Stop the Twitter tracking process using the tracker's internal method."""
    logger.info("Attempting to stop Twitter tracking via tracker.stop()...")
    
    tracker = getattr(request.app.state, 'twitter_scanner', None)
    if not tracker:
        logger.warning("Twitter tracker not found in app state during stop request.")
        # If tracker doesn't exist, ensure app state is clean
        request.app.state.twitter_scanner_running = False 
        if hasattr(request.app.state, 'twitter_scan_task'):
             del request.app.state.twitter_scan_task 
        return {"message": "Twitter tracker not initialized, cannot stop."}

    # Check if tracker thinks it's running
    if not tracker.is_running:
        logger.warning("Tracker is not running according to its state.")
        # Ensure app.state reflects this
        request.app.state.twitter_scanner_running = False
        if hasattr(request.app.state, 'twitter_scan_task'):
             del request.app.state.twitter_scan_task
        return {"message": "Twitter tracking was not running."}

    try:
        logger.info("Calling tracker.stop()...")
        await tracker.stop()
        logger.info(f"tracker.stop() completed. Tracker running: {tracker.is_running}")

        # Update app.state based on tracker state AFTER stopping
        request.app.state.twitter_scanner_running = tracker.is_running
        # Task should be cleaned up by tracker.stop(), remove from app.state too
        if hasattr(request.app.state, 'twitter_scan_task'):
             del request.app.state.twitter_scan_task 

        if not tracker.is_running:
            logger.info("Twitter tracking stopped successfully via tracker.")
            return {"message": "Twitter tracking stopped"}
        else:
            logger.error("tracker.stop() was called but tracker.is_running is still true.")
            # Force state to false for UI consistency
            request.app.state.twitter_scanner_running = False
            raise HTTPException(status_code=500, detail="Failed to confirm tracking stop status.")

    except Exception as e:
        logger.error(f"Error calling tracker.stop(): {e}", exc_info=True)
        # If stopping fails, the state is uncertain. Force false for UI consistency.
        request.app.state.twitter_scanner_running = False 
        if hasattr(request.app.state, 'twitter_scan_task'):
            del request.app.state.twitter_scan_task # Attempt cleanup
        raise HTTPException(status_code=500, detail=f"Error stopping tracking task: {str(e)}")

@router.get("/keywords", response_model=KeywordsResponse)
async def get_trending_keywords(limit: int = 10, days_back: int = 2):
    """Extract trending keywords from recent tweets using YAKE."""
    logger.info(f"Extracting top {limit} keywords from tweets in the last {days_back} days.")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_iso = cutoff_date.isoformat()
        
        # Fetch recent tweet content
        # Assuming 'date_posted' is stored in ISO format or compatible
        cursor.execute(
            "SELECT content FROM tracked_tweets WHERE date_posted >= ? AND content IS NOT NULL", 
            (cutoff_iso,)
        )
        tweets = cursor.fetchall()
        
        if not tweets:
            logger.info(f"No tweets found in the last {days_back} days to extract keywords from.")
            return KeywordsResponse(keywords=[])
            
        # Combine content
        combined_text = " ".join([row[0] for row in tweets])
        logger.info(f"Processing {len(tweets)} tweets ({len(combined_text)} chars) for keyword extraction.")
        
        # <<< ADD DEBUG LOG for combined text >>>
        logger.debug(f"Combined text for YAKE: {combined_text}") 
        # <<< END DEBUG LOG >>>

        if not combined_text.strip():
             logger.warning("Combined text for keyword extraction is empty.")
             return KeywordsResponse(keywords=[])
             
        # Extract keywords using YAKE!
        # You can customize language, max ngram size, etc.
        kw_extractor = yake.KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=limit, features=None)
        keywords_with_scores = kw_extractor.extract_keywords(combined_text)
        
        # YAKE returns list of (keyword, score), lower score is better.
        # We just want the keywords.
        extracted_keywords = [kw for kw, score in keywords_with_scores]
        
        logger.info(f"Extracted keywords: {extracted_keywords}")
        return KeywordsResponse(keywords=extracted_keywords)
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extract keywords")
    finally:
        if conn:
            conn.close()

@router.get("/tracking_status", response_model=TrackingStatusResponse)
async def get_tracking_status(request: Request):
    """Get the current tracking status."""
    logger.info("Fetching Twitter tracking status")
    
    # Primarily use app state for running status
    is_running = getattr(request.app.state, 'twitter_scanner_running', False)
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM tracked_users")
        users_row = cursor.fetchone()
        users_count = users_row[0] if users_row else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM tracked_tweets")
        tweets_row = cursor.fetchone()
        tweets_count = tweets_row[0] if tweets_row else 0
                
        logger.info(f"Tracking status from app state: is_running={is_running}, users={users_count}, tweets={tweets_count}")
        return TrackingStatusResponse(
            is_tracking=is_running,
            tracked_users_count=users_count,
            tracked_tweets_count=tweets_count
        )
    except Exception as e:
        logger.error(f"Error fetching DB counts for tracking status: {e}", exc_info=True)
        # Return status based on app state even if DB fails
        return TrackingStatusResponse(
            is_tracking=is_running, 
            tracked_users_count=0, 
            tracked_tweets_count=0
        )
    finally:
        if conn:
            conn.close()

@router.post("/run_scan", response_model=dict)
async def run_scan_now(request: Request):
    """Triggers a manual scan cycle if the tracker is initialized."""
    logger.info("Manual scan requested via API.")
    tracker = getattr(request.app.state, 'twitter_scanner', None)
    if not tracker:
        logger.error("Cannot run manual scan: Twitter tracker not initialized.")
        raise HTTPException(status_code=500, detail="Twitter tracker not initialized.")
        
    # Check if tracker thinks it's running (optional, scan can run even if loop isn't)
    # is_loop_running = getattr(request.app.state, 'twitter_scanner_running', False)
    # logger.info(f"Manual scan requested. Loop running state: {is_loop_running}")

    try:
        # Explicitly load users before manual scan too, just in case
        try:
            await tracker.load_users_from_db() 
            logger.info(f"Tracker instance reloaded with users before manual scan: {tracker.tracked_users}")
        except Exception as load_err:
             logger.error(f"Error loading users into tracker before manual scan (proceeding anyway): {load_err}", exc_info=True)

        # === ADD Try/Except around scan ===
        scan_success = False
        try:
            logger.info("Calling tracker.scan() manually...")
            await tracker.scan()
            scan_success = True # Assume success if no exception
            logger.info("Manual tracker.scan() completed.")
            return {"message": "Manual scan cycle completed successfully."}
        except Exception as scan_err:
            logger.error(f"Error during tracker.scan() execution: {scan_err}", exc_info=True)
            # Return a specific error message to the frontend
            raise HTTPException(status_code=500, detail=f"Error during scan execution: {str(scan_err)}")
        # === END Try/Except ===

    except HTTPException as http_exc: # Re-raise HTTPExceptions
        raise http_exc
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error during manual scan endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error during manual scan: {str(e)}")

@router.post("/summarize_feed", response_model=SummarizeResponse)
async def summarize_feed(req: SummarizeRequest, request: Request):
    """Generates a summary for the provided tweets, optionally focusing on a specific topic."""
    logger.info(f"Received request to summarize {len(req.tweets)} tweets. Focus: {req.focus}")
    
    if not req.tweets:
        return SummarizeResponse(summary="No tweets provided to summarize.")

    try:
        # 1. Get the pre-loaded pipeline AND tokenizer from app state
        summarizer = getattr(request.app.state, 'summarizer_pipeline', None)
        tokenizer = getattr(request.app.state, 'summarizer_tokenizer', None)
        
        # 2. Check if pipeline and tokenizer are available
        if not summarizer or not tokenizer:
            logger.error("Summarization pipeline or tokenizer not available in app state.")
            raise HTTPException(status_code=500, detail="Summarization components unavailable. Check server startup logs.")

        # --- ADD FOCUS FILTERING --- 
        tweets_to_process = req.tweets
        if req.focus:
            logger.info(f"Applying focus filter: '{req.focus}'")
            # Placeholder keyword map (could be loaded from config/DB later)
            FOCUS_KEYWORDS = {
                "efficiency": ["optimize", "speed", "performance", "refactor", "scale", "benchmark", "fast", "slow"],
                "development": ["code", "feature", "implement", "build", "test", "debug", "release", "bug", "fix"],
                "finance": ["money", "finance", "financial", "stock", "market", "economy", "business", "cost", "price", "funding", "investment", "revenue", "profit", "crypto", "bitcoin", "eth", "$", "€", "£"]
                # Add more focus areas here
            }
            focus_keywords = FOCUS_KEYWORDS.get(req.focus.lower(), [])
            
            if not focus_keywords:
                logger.warning(f"Unknown focus area: '{req.focus}'. No keywords defined. Proceeding without filtering.")
            else:
                logger.debug(f"Filtering for keywords: {focus_keywords}")
                filtered_tweets = []
                for tweet in req.tweets:
                    if tweet.content and any(keyword.lower() in tweet.content.lower() for keyword in focus_keywords):
                        filtered_tweets.append(tweet)
                
                logger.info(f"Filtered tweets from {len(req.tweets)} down to {len(filtered_tweets)} based on focus '{req.focus}'.")
                tweets_to_process = filtered_tweets
                
                if not tweets_to_process:
                    return SummarizeResponse(summary=f"No tweets found matching the focus: '{req.focus}'.")
        # --- END FOCUS FILTERING ---
        
        # 3. Concatenate tweet content (using filtered tweets)
        text_to_summarize = "\n---\n".join([tweet.content for tweet in tweets_to_process if tweet.content])
        
        if not text_to_summarize.strip():
             return SummarizeResponse(summary="No content found in provided tweets to summarize.")
             
        # 4. Tokenize and Truncate based on model's max length
        # Get max length from tokenizer/model config (usually 1024 for distilbart)
        # Add buffer for special tokens ([CLS], [SEP]) if needed, but truncate handles this often
        max_length = tokenizer.model_max_length 
        logger.debug(f"Tokenizing and truncating text to max model length: {max_length} tokens.")
        
        # Tokenize the text, truncating to max_length, return PyTorch tensors
        tokenized_input = tokenizer(
            text_to_summarize, 
            max_length=max_length, 
            truncation=True, 
            return_tensors="pt" 
        )
        
        # Move tokenized input to the same device as the model
        device = next(summarizer.model.parameters()).device
        input_ids = tokenized_input['input_ids'].to(device)
        attention_mask = tokenized_input.get('attention_mask', None)
        if attention_mask is not None:
            attention_mask = attention_mask.to(device)
        
        num_tokens = input_ids.shape[1]
        logger.info(f"Input text tokenized to {num_tokens} tokens (truncated to {max_length} if needed). Generating summary...")

        # 5. Pass the PRE-TOKENIZED and TRUNCATED input_ids to the pipeline
        # Call the summarizer with the token IDs directly
        summary_ids = summarizer.model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=150, # Max length of the generated summary
            min_length=30,  # Min length of the generated summary
            num_beams=4,    # Beam search parameter (optional, adjust for quality/speed)
            early_stopping=True
        )
        
        # Decode the generated token IDs back into text
        generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        logger.info("Summary generated successfully.")

        # 6. Save the summary to memory 
        try:
            summarized_tweet_ids = [tweet.id for tweet in tweets_to_process if tweet.id] # Use tweets_to_process
            metadata = {
                "source": "twitter_feed_summary",
                "summarized_tweet_ids": summarized_tweet_ids,
                "model_used": tokenizer.name_or_path, # Get model name from tokenizer
                "original_char_count": len(text_to_summarize),
                "input_token_count": num_tokens # Store actual token count used
            }
            tags = ["summary", "twitter"]
            
            logger.info(f"Attempting to save summary to memory node...")
            memory_node = await store_memory_node(
                content=generated_summary,
                node_type="twitter_summary",
                tags=tags,
                metadata=metadata
            )
            logger.info(f"Summary saved to memory node with ID: {memory_node.get('id')}")
        except Exception as mem_err:
            logger.error(f"Failed to save generated summary to memory: {mem_err}", exc_info=True)
            # Do not re-raise, just log the error. We still want to return the summary.

        # 7. Return the summary
        return SummarizeResponse(summary=generated_summary)

    except Exception as e:
        logger.error(f"Error during summarization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.post("/summarize_tweet/{tweet_id}", response_model=TweetSummaryResponse)
async def summarize_single_tweet(tweet_id: str, request: Request):
    """Generates and saves a summary for a single specified tweet."""
    logger.info(f"Received request to summarize tweet ID: {tweet_id}")

    # 1. Get pipeline and tokenizer from app state
    summarizer = getattr(request.app.state, 'summarizer_pipeline', None)
    tokenizer = getattr(request.app.state, 'summarizer_tokenizer', None)
    if not summarizer or not tokenizer:
        logger.error("Summarization components unavailable.")
        raise HTTPException(status_code=500, detail="Summarization components unavailable.")

    # 2. Fetch tweet content from DB
    conn = None
    original_content = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM tracked_tweets WHERE tweet_id = ?", (tweet_id,))
        tweet_row = cursor.fetchone()
        if not tweet_row or not tweet_row[0]:
            raise HTTPException(status_code=404, detail=f"Tweet ID {tweet_id} not found or has no content.")
        original_content = tweet_row[0]
    except Exception as db_err:
        logger.error(f"Error fetching tweet {tweet_id} from DB: {db_err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error fetching tweet.")
    finally:
        if conn: conn.close()
        
    # 3. Summarize (consider minimum length)
    min_length_for_summary = 50 # Configurable minimum characters
    if len(original_content) < min_length_for_summary:
        logger.info(f"Tweet {tweet_id} content too short ({len(original_content)} chars), skipping summarization. Returning original content.")
        # Decide: return original or specific message?
        # Returning original in summary field for now
        return TweetSummaryResponse(tweet_id=tweet_id, original_content=original_content, summary=original_content, memory_node_id=None)
        
    try:
        # Tokenize/Truncate (shouldn't be needed for single tweets, but safe)
        max_length = tokenizer.model_max_length
        tokenized_input = tokenizer(original_content, max_length=max_length, truncation=True, return_tensors="pt")
        
        # Move tokenized input to the same device as the model
        device = next(summarizer.model.parameters()).device
        input_ids = tokenized_input['input_ids'].to(device)
        
        num_tokens = input_ids.shape[1]
        logger.info(f"Summarizing tweet {tweet_id} ({num_tokens} tokens)...")
        
        # Generate summary
        summary_ids = summarizer.model.generate(
            input_ids, max_length=80, min_length=15, num_beams=4, early_stopping=True # Shorter summary for single tweet
        )
        generated_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        logger.info(f"Generated summary for tweet {tweet_id}: {generated_summary}")
        
        # 4. Save summary to memory
        memory_node_id = None
        try:
            metadata = {
                "source": "single_tweet_summary",
                "original_tweet_id": tweet_id,
                "model_used": tokenizer.name_or_path,
                "original_char_count": len(original_content),
                "input_token_count": num_tokens
            }
            tags = ["summary", "tweet", f"tweet_id:{tweet_id}"] # Add tweet ID tag
            
            memory_node = await store_memory_node(
                content=generated_summary,
                node_type="tweet_summary",
                tags=tags,
                metadata=metadata
            )
            memory_node_id = memory_node.get('id')
            logger.info(f"Individual tweet summary saved to memory node ID: {memory_node_id}")
        except Exception as mem_err:
            logger.error(f"Failed to save individual tweet summary to memory: {mem_err}", exc_info=True)

        # 5. Return result
        return TweetSummaryResponse(
            tweet_id=tweet_id,
            original_content=original_content,
            summary=generated_summary,
            memory_node_id=memory_node_id
        )

    except Exception as e:
        logger.error(f"Error during single tweet summarization (ID: {tweet_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate summary for tweet {tweet_id}")

# --- NEW Route: Get Top Tweets ---
@router.get("/top_posts", response_model=List[TweetResponse])
async def get_top_tweets(
    limit: int = Query(10, ge=1, le=50, description="Number of top tweets to return"),
    metric: str = Query('retweet_count', description="Metric to sort by: retweet_count, like_count, reply_count, score, created_at")
):
    """Retrieve the top N tweets based on a specified metric."""
    conn = None
    try:
        conn = get_db_connection()
        # Input validation for metric is handled within get_top_twitter_posts
        top_tweets_data = get_top_twitter_posts(conn, limit=limit, metric=metric)
        return top_tweets_data
    except Exception as e:
        logger.error(f"Error retrieving top tweets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve top tweets from database.")
    finally:
        if conn:
            conn.close()

# TODO: Define the background agent (twitter_tracker_agent.py)
