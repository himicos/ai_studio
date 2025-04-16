"""
Reddit Tracker Module for AI Studio

Handles Reddit monitoring using the PRAW library:
- Tracks specified subreddits for new posts.
- Fetches post details (title, author, score, comments, text, etc.).
- Stores data in the application's database.
- Optionally runs background scans.
"""

import os
import re
import logging
import asyncio
import praw
import prawcore
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv
import json
import time
import functools

# Import shared modules - ensure these functions exist in db_enhanced
from ai_studio_package.infra.db_enhanced import (
    get_db_connection,
    add_tracked_subreddit,
    remove_tracked_subreddit,
    get_tracked_subreddits_with_state, # Expects name, last_scanned_post_id, is_active
    update_subreddit_scan_state,
    insert_reddit_posts,
    create_memory_node
)
from ai_studio_package.infra.summarizer import SummarizationPipelineSingleton
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class RedditTracker:
    """
    Manages tracking of Reddit subreddits using PRAW.
    Mirrors the structure of TwitterTracker but uses Reddit API.
    """

    def __init__(self, sentiment_pipeline=None, ner_pipeline=None, db_path: str = "memory/memory.sqlite"):
        """
        Initialize the Reddit tracker.
        Loads credentials, initializes PRAW, stores pipelines, and sets up initial state.
        
        Args:
            sentiment_pipeline: Pre-loaded sentiment analysis pipeline.
            ner_pipeline: Pre-loaded Named Entity Recognition pipeline.
            db_path: Path to the SQLite database file.
        """
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT")
        self.db_path = db_path
        self.reddit: Optional[praw.Reddit] = None
        self.running_task: Optional[asyncio.Task] = None
        self.scan_interval_seconds: int = 600
        
        # Store passed-in pipelines
        self.sentiment_pipeline = sentiment_pipeline
        self.ner_pipeline = ner_pipeline

        if not all([self.client_id, self.client_secret, self.user_agent]):
            logger.error("Reddit API credentials missing in .env (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)")
            return
            
        if not self.sentiment_pipeline:
            logger.warning("Sentiment analysis pipeline not provided to RedditTracker during initialization.")
        if not self.ner_pipeline:
             logger.warning("NER pipeline not provided to RedditTracker during initialization.")

        try:
            # Use check_for_async=False for compatibility with asyncio.to_thread
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                check_for_async=False
            )
            # Basic check (PRAW is lazy, this might not catch all auth errors)
            # Attempting to read a property forces initialization
            _ = self.reddit.config.kinds 
            logger.info(f"PRAW initialized successfully for user agent: {self.user_agent}")
        except Exception as e:
            logger.error(f"Failed to initialize PRAW: {e}", exc_info=True)
            self.reddit = None

        self._initialize_summarizer()

    async def get_tracked_subreddits(self) -> List[Dict[str, Any]]:
        """Fetches the list of currently tracked subreddits from the DB."""
        if not self.reddit:
            logger.warning("Reddit client not initialized.")
            return []
        conn = None
        try:
            conn = get_db_connection() # Use db_path if needed by your implementation
            # Assuming get_tracked_subreddits_with_state returns List[Dict]
            tracked = get_tracked_subreddits_with_state(conn)
            logger.info(f"Retrieved {len(tracked)} tracked subreddits.")
            return tracked
        except Exception as e:
            logger.error(f"Error fetching tracked subreddits: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()

    async def add_subreddit(self, subreddit_name: str) -> bool:
        """Adds a subreddit to the tracking list in the DB after validation."""
        if not self.reddit:
            logger.warning("Reddit client not initialized. Cannot add subreddit.")
            return False
        
        # Basic validation
        if not subreddit_name or not re.match(r"^[a-zA-Z0-9_]+$", subreddit_name) or len(subreddit_name) > 21:
             logger.error(f"Invalid subreddit name format or length: {subreddit_name}")
             return False

        conn = None
        try:
            # Check subreddit existence using PRAW in a thread
            logger.debug(f"Checking existence of r/{subreddit_name} on Reddit...")
            # Accessing any attribute will raise NotFound if it doesn't exist
            await asyncio.to_thread(lambda: self.reddit.subreddit(subreddit_name).id)
            logger.debug(f"Subreddit r/{subreddit_name} exists.")

            # Proceed with DB add
            conn = get_db_connection()
            add_tracked_subreddit(conn, subreddit_name)
            conn.commit()
            logger.info(f"Successfully added subreddit r/{subreddit_name} to tracking.")
            return True

        except prawcore.exceptions.NotFound:
             logger.error(f"Subreddit r/{subreddit_name} not found or is invalid on Reddit.")
             return False
        except prawcore.exceptions.Redirect:
             logger.error(f"Subreddit r/{subreddit_name} caused a redirect, likely invalid.")
             return False
        except Exception as e:
            # Handle DB errors or other unexpected issues
            logger.error(f"Error adding subreddit r/{subreddit_name}: {e}", exc_info=True)
            if conn: conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    async def remove_subreddit(self, subreddit_name: str) -> bool:
        """Removes a subreddit from the tracking list in the DB."""
        # No PRAW check needed, just remove from DB
        conn = None
        try:
            conn = get_db_connection()
            remove_tracked_subreddit(conn, subreddit_name)
            conn.commit()
            logger.info(f"Successfully removed subreddit r/{subreddit_name} from tracking.")
            return True
        except Exception as e:
            logger.error(f"Error removing subreddit r/{subreddit_name}: {e}", exc_info=True)
            if conn: conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def _process_posts(self, posts: List[praw.models.Submission], subreddit_name: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Processes a list of PRAW Submission objects, adds AI enrichments, 
        and returns a format for DB storage.
        Returns a list of post dictionaries and the ID of the newest post processed.
        """
        processed_posts_data = []
        newest_post_id = None
        latest_creation_unix = 0

        # Prepare combined texts for potentially faster batch processing (if pipelines support it)
        # Use title and selftext for analysis
        texts_to_analyze = []
        for post in posts:
            text_content = f"{post.title}\n\n{post.selftext or ''}" # Combine title and body
            texts_to_analyze.append(text_content[:1024]) # Truncate long inputs if necessary for models

        # --- Run Sentiment Analysis --- 
        sentiments = []
        sentiment_scores = []
        if self.sentiment_pipeline and texts_to_analyze:
            try:
                # Assuming pipeline returns list of dicts like [{'label': 'Positive', 'score': 0.9...}]
                results = self.sentiment_pipeline(texts_to_analyze, truncation=True) 
                for result in results:
                    label = result.get('label', 'Neutral').upper() # Default to Neutral
                    score = result.get('score', 0.5)
                    sentiments.append(label)
                    # Convert label to score (-1.0, 0.0, 1.0)
                    if label == 'POSITIVE':
                        sentiment_scores.append(1.0)
                    elif label == 'NEGATIVE':
                        sentiment_scores.append(-1.0)
                    else: # Neutral or other labels
                         sentiment_scores.append(0.0)
            except Exception as e:
                 logger.error(f"Error during sentiment analysis for r/{subreddit_name}: {e}", exc_info=True)
                 sentiments = ['ERROR'] * len(posts)
                 sentiment_scores = [0.0] * len(posts)
        else:
             sentiments = [None] * len(posts)
             sentiment_scores = [None] * len(posts)

        # --- Run NER (Keyword Extraction) --- 
        all_keywords_list = [] # List of lists
        if self.ner_pipeline and texts_to_analyze:
            try:
                # Assuming pipeline with grouped_entities=True, returns list of lists of dicts
                # [[{'entity_group': 'ORG', 'word': 'Google'...}], [...]]
                ner_results_batched = self.ner_pipeline(texts_to_analyze)
                for ner_results in ner_results_batched:
                    extracted_keywords = set() # Use set for deduplication
                    for entity in ner_results:
                        keyword = entity.get('word')
                        # Apply filtering similar to Twitter agent
                        if keyword and len(keyword) >= 3 and not keyword.startswith( ('#', '@') ) and any(c.isalpha() for c in keyword):
                            extracted_keywords.add(keyword.strip('.,!?;:"()[]{}<>')) 
                    # Sort for consistent DB storage, convert back to list
                    all_keywords_list.append(sorted(list(extracted_keywords), key=str.lower))
            except Exception as e:
                 logger.error(f"Error during NER processing for r/{subreddit_name}: {e}", exc_info=True)
                 all_keywords_list = [[]] * len(posts)
        else:
             all_keywords_list = [None] * len(posts)


        # --- Combine data for each post --- 
        for i, post in enumerate(posts):
            created_dt = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
            created_iso = created_dt.isoformat()

            post_data = {
                "id": post.id,
                "subreddit": subreddit_name.lower(),
                "title": post.title,
                "author": getattr(post.author, 'name', '[deleted]'),
                "created_utc": created_iso,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "permalink": f"https://www.reddit.com{post.permalink}",
                "url": post.url,
                "selftext": post.selftext[:4000] if post.selftext else None,
                "is_self": post.is_self,
                "is_video": post.is_video,
                "over_18": post.over_18,
                "spoiler": post.spoiler,
                "stickied": post.stickied,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                # Add AI fields
                "sentiment": sentiments[i],
                "sentiment_score": sentiment_scores[i], # Assuming column name is sentiment_score
                "keywords": json.dumps(all_keywords_list[i]) if all_keywords_list[i] is not None else None # Store keywords as JSON string
            }
            processed_posts_data.append(post_data)

            if post.created_utc > latest_creation_unix:
                latest_creation_unix = post.created_utc
                newest_post_id = post.id

        logger.debug(f"Processed {len(processed_posts_data)} posts with AI enrichments for r/{subreddit_name}. Newest ID: {newest_post_id}")
        return processed_posts_data, newest_post_id

    async def scan_subreddit(self, subreddit_name: str, last_scanned_id: Optional[str] = None) -> int:
        """
        Scans a specific subreddit for new posts since the last scan.
        
        Args:
            subreddit_name: The name of the subreddit to scan.
            last_scanned_id: The ID of the last scanned post.
            
        Returns:
            The number of new posts found and stored.
        """
        if not self.reddit:
            logger.warning("Reddit client not initialized, cannot scan.")
            return 0

        logger.info(f"Scanning r/{subreddit_name} for posts newer than ID: {last_scanned_id}")
        new_posts_count = 0
        newest_post_id_in_scan = last_scanned_id # Start with the last known ID
        conn = None

        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # PRAW's .new() fetches posts. Use 'params' for `before`.
            # PRAW expects the "fullname" (t3_ + id) for before/after
            params = {"limit": 25}
            if last_scanned_id:
                params["before"] = f"t3_{last_scanned_id}"

            # Run PRAW network calls in a separate thread
            def fetch_new_posts(): 
                return list(subreddit.new(params=params))
                
            fetched_posts = await asyncio.to_thread(fetch_new_posts)

            if not fetched_posts:
                logger.info(f"No new posts found in r/{subreddit_name} since {last_scanned_id}.")
                # Optionally update timestamp even if no new posts?
                # conn = get_db_connection()
                # update_subreddit_scan_state(conn, subreddit_name, last_scanned_id, update_time=True)
                # conn.commit()
                return 0

            processed_posts, newest_id_local = self._process_posts(fetched_posts, subreddit_name)
            
            if newest_id_local:
                newest_post_id_in_scan = newest_id_local
            else:
                logger.warning(f"No newest ID found in fetched posts for r/{subreddit_name}, keeping last known ID: {last_scanned_id}")

            if processed_posts:
                conn = get_db_connection()
                insert_reddit_posts(conn, processed_posts)
                conn.commit()
                new_posts_count = len(processed_posts)
                logger.info(f"Stored {new_posts_count} new posts from r/{subreddit_name}.")

            # Update the last scanned ID for this subreddit in the DB
            # Only update if we found a newer post ID
            if newest_post_id_in_scan and newest_post_id_in_scan != last_scanned_id:
                if not conn: # Get connection if not already open
                     conn = get_db_connection()
                update_subreddit_scan_state(conn, subreddit_name, newest_post_id_in_scan)
                conn.commit()
                logger.info(f"Updated last scanned ID for r/{subreddit_name} to {newest_post_id_in_scan}")
            else:
                 logger.info(f"Last scanned ID for r/{subreddit_name} remains {last_scanned_id}")

        except (prawcore.exceptions.NotFound, prawcore.exceptions.Redirect):
             logger.error(f"Subreddit r/{subreddit_name} not found or invalid during scan.")
        except praw.exceptions.PRAWException as e:
            logger.error(f"PRAW error scanning r/{subreddit_name}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error scanning r/{subreddit_name}: {e}", exc_info=True)
            if conn: conn.rollback()
        finally:
             if conn:
                 conn.close()

        return new_posts_count

    async def scan(self) -> None:
        """Performs a scan of all active tracked subreddits."""
        if not self.reddit:
            logger.warning("Reddit client not initialized, skipping scan.")
            return

        logger.info("Starting scheduled Reddit scan...")
        tracked_subreddits = await self.get_tracked_subreddits()
        total_new_posts = 0

        active_subreddits = [sub for sub in tracked_subreddits if sub.get('is_active', 1)]
        logger.info(f"Found {len(active_subreddits)} active subreddits to scan.")

        for sub_info in active_subreddits:
             subreddit_name = sub_info['name']
             last_scanned_id = sub_info.get('last_scanned_post_id')
             logger.debug(f"Preparing to scan r/{subreddit_name}, last ID: {last_scanned_id}")
             try:
                 count = await self.scan_subreddit(subreddit_name, last_scanned_id)
                 total_new_posts += count
                 # Add a small delay between subreddits to be polite to Reddit API
                 await asyncio.sleep(2)
             except Exception as e:
                 logger.error(f"Error during scan loop for r/{subreddit_name}: {e}", exc_info=True)

        logger.info(f"Reddit scan finished. Found {total_new_posts} new posts across tracked subreddits.")

    async def _tracking_loop(self):
        """The main background loop for periodic scanning."""
        logger.info(f"Starting Reddit tracking loop with interval: {self.scan_interval_seconds}s")
        while True:
            try:
                await self.scan()
                logger.debug(f"Tracking loop finished scan, sleeping for {self.scan_interval_seconds}s...")
                await asyncio.sleep(self.scan_interval_seconds)
            except asyncio.CancelledError:
                logger.info("Reddit tracking loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in Reddit tracking loop: {e}", exc_info=True)
                logger.info(f"Waiting {self.scan_interval_seconds}s before retrying after error.")
                await asyncio.sleep(self.scan_interval_seconds)

    async def start_tracking(self, interval_seconds: Optional[int] = None) -> bool:
        """Starts the background scanning task."""
        if self.running_task and not self.running_task.done():
            logger.warning("Reddit tracking is already running.")
            return False

        if not self.reddit:
            logger.error("Cannot start tracking, Reddit client not initialized.")
            return False

        if interval_seconds is not None and interval_seconds > 0:
             self.scan_interval_seconds = interval_seconds

        logger.info(f"Starting Reddit background tracking. Scan interval: {self.scan_interval_seconds}s")
        self.running_task = asyncio.create_task(self._tracking_loop())
        # Optional: Add callback to handle task completion/errors
        # self.running_task.add_done_callback(self._handle_task_completion)
        return True

    async def stop_tracking(self) -> bool:
        """Stops the background scanning task."""
        if not self.running_task or self.running_task.done():
            logger.info("Reddit tracking is not currently running or already stopped.")
            return True # Effectively stopped

        logger.info("Attempting to stop Reddit tracking loop...")
        self.running_task.cancel()
        try:
            await self.running_task # Wait for the task to acknowledge cancellation
            logger.info("Reddit tracking loop successfully stopped.")
        except asyncio.CancelledError:
            logger.info("Reddit tracking loop caught cancellation signal.")
        except Exception as e:
             logger.error(f"Error encountered while waiting for tracking task cancellation: {e}", exc_info=True)
             # Task might be stopped despite error, but log it
        finally:
            self.running_task = None
        return True

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the tracker."""
        is_running = self.running_task is not None and not self.running_task.done()
        status = {
            "agent_type": "reddit",
            "is_running": is_running,
            "scan_interval_seconds": self.scan_interval_seconds,
            "client_initialized": self.reddit is not None,
        }
        logger.debug(f"RedditTracker status: {status}")
        return status

    # Optional: Callback for task completion
    # def _handle_task_completion(self, task: asyncio.Task):
    #     try:
    #         task.result() # Raise exception if task failed
    #         logger.info("Reddit tracking task completed normally.")
    #     except asyncio.CancelledError:
    #         logger.info("Reddit tracking task was cancelled.")
    #     except Exception as e:
    #         logger.error(f"Reddit tracking task failed with exception: {e}", exc_info=True)
    #     finally:
    #          # Ensure task is marked as None even if callback has issues
    #          if self.running_task is task:
    #              self.running_task = None

    def _initialize_summarizer(self):
        """Helper to initialize summarizer, called from init."""
        try:
            logger.info("Initializing summarizer pipeline for RedditTracker...")
            # Access the singleton instance
            self.summarizer_pipeline = SummarizationPipelineSingleton.get_pipeline()
            self.summarizer_tokenizer = SummarizationPipelineSingleton.get_tokenizer()
            if not self.summarizer_pipeline or not self.summarizer_tokenizer:
                logger.error("Failed to get summarization pipeline or tokenizer from Singleton.")
                self.summarizer_pipeline = None
                self.summarizer_tokenizer = None
            else:
                logger.info("Summarizer pipeline obtained successfully.")
        except Exception as e:
            logger.error(f"Error initializing summarizer pipeline: {e}", exc_info=True)
            self.summarizer_pipeline = None
            self.summarizer_tokenizer = None

    async def _scan_single_subreddit(self, subreddit_name: str):
        # ... (logic to get PRAW subreddit object) ...
        last_scanned_id = None # Fetch this from DB for the subreddit
        conn_state = None
        try:
            # Fetch state before fetching posts
            conn_state = get_db_connection()
            # Assuming get_tracked_subreddits_with_state filters by name or you fetch one
            sub_state = next((s for s in get_tracked_subreddits_with_state(conn_state) if s['name'] == subreddit_name), None)
            if sub_state:
                last_scanned_id = sub_state.get('last_scanned_post_id')
            logger.info(f"Scanning r/{subreddit_name} for posts newer than ID: {last_scanned_id}")
        except Exception as state_err:
            logger.error(f"Error fetching scan state for r/{subreddit_name}: {state_err}")
            # Optionally proceed without last_scanned_id or return
        finally:
            if conn_state: conn_state.close()

        new_submissions = []
        newest_post_id_in_scan = last_scanned_id
        # --- ADD PRINT 1 --- 
        print(f"DEBUG PRINT 1: Entering main try block for r/{subreddit_name}")
        # --- END PRINT 1 ---
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            params = {"limit": 100} # Fetch more posts
            if last_scanned_id:
                params["before"] = f"t3_{last_scanned_id}"

            def fetch_new_posts_sync(): 
                return list(subreddit.new(params=params))
            
            fetched_submissions = await asyncio.to_thread(fetch_new_posts_sync)
            
            if not fetched_submissions:
                logger.info(f"No new posts found in r/{subreddit_name} since {last_scanned_id}.")
                return

            # Find the actual newest ID from the fetched batch
            local_newest_id = None
            max_created = 0
            for sub in fetched_submissions:
                if sub.created_utc > max_created:
                    max_created = sub.created_utc
                    local_newest_id = sub.id
            
            if local_newest_id: # Update overall newest ID if a newer one was found
                newest_post_id_in_scan = local_newest_id

            logger.info(f"Found {len(fetched_submissions)} new posts in r/{subreddit_name}. Processing...")
            conn = None
            # --- ADD PRINT 2 --- 
            print(f"DEBUG PRINT 2: Immediately before DB transaction try block for r/{subreddit_name}")
            # --- END PRINT 2 ---
            try:
                # --- Add logging --- 
                logger.info(f"--> Getting DB connection for r/{subreddit_name} processing...")
                conn = get_db_connection()
                logger.info(f"--> DB connection obtained for r/{subreddit_name}. Starting transaction...")
                conn.execute("BEGIN") # Start transaction
                logger.info(f"--> Transaction BEGUN for r/{subreddit_name}.")
                # --- End logging ---

                # Step 1: Store raw posts (using the implemented helper)
                logger.info(f"--> Calling _store_raw_posts for r/{subreddit_name}...") # Log before call
                raw_insert_count = self._store_raw_posts(conn, subreddit_name, fetched_submissions)
                logger.info(f"--> _store_raw_posts finished for r/{subreddit_name}. Inserted count: {raw_insert_count}") # Log after call

                # --- Add specific checkpoint log --- 
                logger.info(f"--> CHECKPOINT: Immediately before calling summarize/embed for r/{subreddit_name}.")
                # --- End checkpoint log ---

                # --- Add logging before and after summarization call ---
                logger.info(f"--->>> Attempting to summarize and embed {len(fetched_submissions)} posts for r/{subreddit_name}...")
                # Step 2: Summarize and embed (passing the same connection)
                await self._summarize_and_embed_posts(conn, subreddit_name, fetched_submissions)
                logger.info(f"--->>> Finished call to _summarize_and_embed_posts for r/{subreddit_name}.")
                # --- End logging addition ---
                
                # Step 3: Commit transaction after all processing for this sub
                conn.commit()
                logger.info(f"Committed DB changes for r/{subreddit_name}.")

            except Exception as processing_err:
                logger.error(f"Error during DB operations for r/{subreddit_name}: {processing_err}", exc_info=True)
                if conn: 
                    logger.warning(f"Rolling back transaction for r/{subreddit_name}")
                    conn.rollback()
            finally:
                if conn:
                    conn.close()
            
            # Step 4: Update scan state *after* successful commit
            if newest_post_id_in_scan and newest_post_id_in_scan != last_scanned_id:
                conn_update = None
                try:
                    conn_update = get_db_connection()
                    update_subreddit_scan_state(conn_update, subreddit_name, newest_post_id_in_scan)
                    conn_update.commit()
                    logger.info(f"Updated last scanned ID for r/{subreddit_name} to {newest_post_id_in_scan}")
                except Exception as update_err:
                     logger.error(f"Failed to update scan state for r/{subreddit_name}: {update_err}")
                     if conn_update: conn_update.rollback()
                finally: 
                     if conn_update: conn_update.close()
            else:
                 logger.info(f"Last scanned ID for r/{subreddit_name} remains {last_scanned_id} (no newer posts processed or commit failed).")

        except (prawcore.exceptions.NotFound, prawcore.exceptions.Redirect) as praw_err:
             logger.error(f"Subreddit r/{subreddit_name} not found or invalid during scan: {praw_err}")
             # Consider marking as inactive in DB?
        except Exception as e:
            logger.error(f"Error scanning subreddit r/{subreddit_name}: {e}", exc_info=True)

    # --- Implement the raw post storage logic --- 
    def _store_raw_posts(self, conn, subreddit_name: str, new_submissions: List[Any]) -> int:
        """Stores raw post data into the reddit_posts table using the provided connection."""
        posts_to_insert = []
        logger.debug(f"[_store_raw_posts] Preparing raw post data for r/{subreddit_name}...") # Log entry
        for submission in new_submissions:
            try:
                created_dt = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                post_data = {
                    "id": submission.id,
                    "subreddit": subreddit_name.lower(),
                    "title": submission.title,
                    "author": getattr(submission.author, 'name', '[deleted]'),
                    "created_utc": created_dt.isoformat(), # Store as ISO string
                    "score": submission.score,
                    "upvote_ratio": submission.upvote_ratio,
                    "num_comments": submission.num_comments,
                    "permalink": f"https://www.reddit.com{submission.permalink}",
                    "url": submission.url,
                    "selftext": submission.selftext[:4000] if submission.selftext else None, # Limit length
                    "is_self": submission.is_self,
                    "is_video": submission.is_video,
                    "over_18": submission.over_18,
                    "spoiler": submission.spoiler,
                    "stickied": submission.stickied,
                    "scraped_at": datetime.now(timezone.utc).isoformat()
                }
                posts_to_insert.append(post_data)
            except Exception as prep_err:
                logger.warning(f"Could not prepare raw post data for {submission.id}: {prep_err}")
        
        if not posts_to_insert:
            logger.info(f"[_store_raw_posts] No valid posts prepared for insertion for r/{subreddit_name}.")
            return 0
        logger.info(f"[_store_raw_posts] Prepared {len(posts_to_insert)} posts for insertion for r/{subreddit_name}.")

        try:
            logger.info(f"[_store_raw_posts] Attempting batch insert via insert_reddit_posts for r/{subreddit_name}...")
            inserted_count = insert_reddit_posts(conn, posts_to_insert)
            # The commit is handled by the caller (_scan_single_subreddit)
            logger.info(f"[_store_raw_posts] insert_reddit_posts call completed for r/{subreddit_name}. DB reported count: {inserted_count}")
            return inserted_count
        except Exception as insert_err:
            logger.error(f"[_store_raw_posts] Error during insert_reddit_posts call for r/{subreddit_name}: {insert_err}", exc_info=True) # Log full exception
            # Rollback is handled by the caller
            return 0

    async def _summarize_and_embed_posts(self, conn, subreddit_name: str, new_submissions: List[Any]):
        """Generates summaries, stores them as memory nodes, and triggers embedding."""
        if not self.summarizer_pipeline or not self.summarizer_tokenizer:
            logger.error("Summarizer not available, cannot process posts for embedding.")
            return

        loop = asyncio.get_running_loop()
        processed_count = 0
        failed_count = 0
        # Keep track of node IDs inserted in this batch within the transaction
        inserted_node_ids_in_batch = [] 

        for submission in new_submissions:
            try:
                post_id = submission.id
                title = submission.title
                selftext = submission.selftext
                text_to_summarize = f"{title}\n\n{selftext}".strip()

                if not text_to_summarize:
                    logger.info(f"Skipping summary for post {post_id} (no text content)." )
                    continue

                # --- Run Summarization in Executor --- 
                try:
                    summary_text = await loop.run_in_executor(
                        None, # Default ThreadPoolExecutor
                        functools.partial(self._run_summarization_sync, text_to_summarize)
                    )
                    if not summary_text:
                        logger.warning(f"Summarization returned empty for post {post_id}. Skipping node creation.")
                        failed_count += 1
                        continue 
                except Exception as summ_err:
                    logger.error(f"Error during summarization for post {post_id}: {summ_err}")
                    failed_count += 1
                    continue # Skip this post if summarization fails
                # --- End Summarization --- 
                
                # --- Prepare Summary Memory Node Data --- 
                node_id = f"reddit_summary_{post_id}"
                tags = ['reddit', 'summary', subreddit_name]
                metadata = {
                    'original_post_id': post_id,
                    'source_type': 'reddit',
                    'subreddit': subreddit_name,
                    'title': title,
                    'author': str(submission.author) if submission.author else None,
                    'upvotes': submission.score,
                    'num_comments': submission.num_comments,
                    'url': submission.url,
                    'permalink': submission.permalink,
                    'model_used': SummarizationPipelineSingleton.get_model_name(), 
                    'fetched_at': int(time.time()),
                    'created_utc': int(submission.created_utc)
                }
                
                memory_node_data = {
                    "id": node_id,
                    "type": "reddit_summary",
                    "content": summary_text, # Use the generated summary
                    "tags": json.dumps([t for t in tags if t]),
                    "created_at": int(submission.created_utc),
                    "updated_at": int(time.time()),
                    "source_id": submission.permalink, # Use permalink as source_id maybe?
                    "source_type": "reddit",
                    "metadata": json.dumps(metadata),
                    "has_embedding": 0
                }
                # --- End Prepare Data --- 

                # --- Insert Summary Node (using helper) --- 
                # Pass the connection
                inserted = await self.insert_memory_node_async(conn, memory_node_data)
                # --- End Insert --- 
                
                if inserted:
                    processed_count += 1
                    # Add the ID to list for embedding *after* commit
                    inserted_node_ids_in_batch.append(memory_node_data["id"])
                else:
                    failed_count += 1

            except Exception as post_proc_err:
                logger.error(f"Error processing post {submission.id} for summary/embedding: {post_proc_err}", exc_info=True)
                failed_count += 1
        
        # -- Commit is handled by the CALLER (_scan_single_subreddit) --
        # -- We don't commit or rollback here inside the loop --
        
        # --- Trigger Embedding AFTER successful commit (done in caller) --- 
        # We return the list of IDs that should be embedded
        logger.info(f"Finished preparing summaries for r/{subreddit_name}. Successful: {processed_count}, Failed/Skipped: {failed_count}")
        # --- Return list of node IDs that were successfully prepared and inserted --- 
        # Embedding trigger will happen in the caller after commit
        # return inserted_node_ids_in_batch <<-- Modify _scan_single_subreddit to handle this return

        # --- Revised Approach: Trigger Embedding Here --- 
        # If insert_memory_node_async succeeded (returned True), trigger embedding
        # This assumes insert_memory_node_async doesn't rely on an external commit 
        # (which it shouldn't if using ON CONFLICT DO NOTHING or similar)
        if inserted_node_ids_in_batch:
            logger.info(f"Triggering background embedding for {len(inserted_node_ids_in_batch)} summary nodes from r/{subreddit_name}...")
            for node_id in inserted_node_ids_in_batch:
                 loop.run_in_executor(
                    None, 
                    functools.partial(generate_embedding_for_node_faiss, node_id)
                 )
        # --- End Trigger Embedding --- 

    def _run_summarization_sync(self, text: str) -> Optional[str]:
        """Synchronous helper to run the summarization pipeline."""
        if not self.summarizer_pipeline or not self.summarizer_tokenizer:
            return None
        try:
            # Truncate input based on tokenizer limits
            max_input_length = getattr(self.summarizer_tokenizer, 'model_max_length', 1024)
            safe_max_length = max_input_length - 10 
            inputs = self.summarizer_tokenizer(text, return_tensors='pt', max_length=safe_max_length, truncation=True)
            truncated_text = self.summarizer_tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)

            if len(truncated_text) < 5: # Basic check if input is too short after truncation
                 return None
                 
            # Adjust summarization parameters as needed
            summary_result = self.summarizer_pipeline(truncated_text, max_length=150, min_length=20, do_sample=False)
            return summary_result[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarization pipeline error: {e}")
            return None

    # --- Add the async DB insert helper if it doesn't exist --- 
    async def insert_memory_node_async(self, conn, node_data: Dict[str, Any]) -> bool:
        """Helper function to insert a memory node into the database.
           Uses the passed connection.
        """
        cursor = None
        try:
            cursor = conn.cursor()
            # Use INSERT OR IGNORE or ON CONFLICT DO NOTHING to handle duplicates gracefully
            cursor.execute("""
                INSERT INTO memory_nodes (id, type, content, tags, created_at, updated_at, source_id, source_type, metadata, has_embedding)
                VALUES (:id, :type, :content, :tags, :created_at, :updated_at, :source_id, :source_type, :metadata, :has_embedding)
                ON CONFLICT(id) DO NOTHING
            """, node_data)
            # commit happens in the calling function (_scan_single_subreddit) after all processing
            # conn.commit() # DO NOT commit here if batching or called within transaction
            # Return True if insert happened (rowcount > 0), False otherwise (conflict or error)
            return cursor.rowcount > 0
        except Exception as insert_err:
            logger.error(f"DB Error inserting memory node {node_data.get('id', 'N/A')}: {insert_err}")
            # Rollback might be handled by the caller if part of a larger transaction
            # conn.rollback()
            return False
        # finally:
            # Cursor is managed by the connection passed in
            # if cursor: cursor.close()

# Example usage block (inactive by default)
async def _test_main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("--- Starting RedditTracker Test --- ")
    tracker = RedditTracker()
    if tracker.reddit:
        print("Tracker initialized.")
        # Add test calls here, e.g.:
        # await tracker.add_subreddit("learnpython")
        # print(await tracker.get_tracked_subreddits())
        # await tracker.scan()
        # await tracker.start_tracking(15) # Short interval for testing
        # await asyncio.sleep(35)
        # await tracker.stop_tracking()
    else:
        print("Tracker failed to initialize.")
    logger.info("--- Finished RedditTracker Test --- ")


if __name__ == "__main__":
     # To run tests: Ensure DB is initialized (e.g., run main.py once)
     # and uncomment the line below.
     # asyncio.run(_test_main())
     pass
