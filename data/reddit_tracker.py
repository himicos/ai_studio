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
import prawcore # Import prawcore for exceptions
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

# Import shared modules
# Assuming db_enhanced will have these functions after modification
from ai_studio_package.infra.db_enhanced import (
    get_db_connection,
    add_tracked_subreddit,
    remove_tracked_subreddit,
    get_tracked_subreddits_with_state,
    update_subreddit_scan_state,
    insert_reddit_posts
)

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class RedditTracker:
    """
    Manages tracking of Reddit subreddits using PRAW.
    """
    
    def __init__(self, db_path: str = "memory/memory.sqlite"):
        """
        Initialize the Reddit tracker.
        Loads credentials, initializes PRAW, and sets up initial state.
        """
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT")
        self.db_path = db_path
        self.reddit = None
        self.running_task = None
        self.scan_interval_seconds = 600  # Default: 10 minutes

        if not all([self.client_id, self.client_secret, self.user_agent]):
            logger.error("Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT) not found in .env")
            # Consider raising an error or handling this state appropriately
            return

        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                # Add username/password if using script credentials that require them
                # username=os.getenv("REDDIT_USERNAME"),
                # password=os.getenv("REDDIT_PASSWORD"),
                check_for_async=False # Important if running in async context later
            )
            # Test connection (optional, PRAW is lazy)
            # self.reddit.user.me() # This might raise exception if auth fails but requires user context
            logger.info(f"PRAW initialized successfully for user agent: {self.user_agent}")
        except Exception as e:
            logger.error(f"Failed to initialize PRAW: {e}", exc_info=True)
            self.reddit = None

    async def get_tracked_subreddits(self) -> List[Dict[str, Any]]:
        """Fetches the list of currently tracked subreddits from the DB."""
        if not self.reddit:
            logger.warning("Reddit client not initialized.")
            return []
        conn = get_db_connection()
        try:
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
        """Adds a subreddit to the tracking list in the DB."""
        if not self.reddit:
            logger.warning("Reddit client not initialized.")
            return False
        # Basic validation
        if not subreddit_name or not re.match(r"^[a-zA-Z0-9_]+$", subreddit_name):
             logger.error(f"Invalid subreddit name format: {subreddit_name}")
             return False

        conn = None
        try:
            # Check subreddit existence using lambda in to_thread
            logger.debug(f"Checking existence of r/{subreddit_name} on Reddit...")
            await asyncio.to_thread(lambda: self.reddit.subreddit(subreddit_name).id)
            logger.debug(f"Subreddit r/{subreddit_name} exists on Reddit.")

            # Proceed with DB add
            conn = get_db_connection()
            add_tracked_subreddit(conn, subreddit_name)
            conn.commit()
            logger.info(f"Successfully added subreddit r/{subreddit_name} to tracking list.")
            return True

        # Catch specific prawcore exception
        except prawcore.exceptions.NotFound:
             logger.error(f"Subreddit r/{subreddit_name} not found or is invalid on Reddit (prawcore.exceptions.NotFound).")
             return False
        # Optionally catch Redirect if needed, often handled similarly to NotFound by PRAW
        # except prawcore.exceptions.Redirect:
        #      logger.error(f"Subreddit r/{subreddit_name} caused a redirect.")
        #      return False
        except Exception as e:
            logger.error(f"Error adding subreddit r/{subreddit_name}: {e}", exc_info=True)
            if conn: conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    async def remove_subreddit(self, subreddit_name: str) -> bool:
        """Removes a subreddit from the tracking list in the DB."""
        if not self.reddit:
            logger.warning("Reddit client not initialized.")
            return False
        conn = get_db_connection()
        try:
            remove_tracked_subreddit(conn, subreddit_name)
            conn.commit()
            logger.info(f"Successfully removed subreddit r/{subreddit_name} from tracking list.")
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
        Processes a list of PRAW Submission objects into a format for DB storage.
        Returns a list of post dictionaries and the ID of the newest post processed.
        """
        processed_posts = []
        newest_post_id = None
        latest_creation_time = 0

        for post in posts:
             # Convert created_utc timestamp to ISO 8601 format string
            created_dt = datetime.utcfromtimestamp(post.created_utc)
            created_iso = created_dt.isoformat() + "Z" # Add Z for UTC

            post_data = {
                "id": post.id,
                "subreddit": subreddit_name.lower(), # Store lowercased for consistency
                "title": post.title,
                "author": getattr(post.author, 'name', '[deleted]'),
                "created_utc": created_iso,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "permalink": f"https://www.reddit.com{post.permalink}",
                "url": post.url,
                "selftext": post.selftext[:4000], # Truncate long selftext if needed (adjust limit)
                "is_self": post.is_self,
                "is_video": post.is_video,
                "over_18": post.over_18,
                "spoiler": post.spoiler,
                "stickied": post.stickied,
                "scraped_at": datetime.utcnow().isoformat() + "Z" # Add Z for UTC
                # Add other fields if needed, e.g., flair, domain, etc.
            }
            processed_posts.append(post_data)

            # Track the newest post based on creation time
            if post.created_utc > latest_creation_time:
                latest_creation_time = post.created_utc
                newest_post_id = post.id

        logger.debug(f"Processed {len(processed_posts)} posts for r/{subreddit_name}. Newest ID: {newest_post_id}")
        return processed_posts, newest_post_id


    async def scan_subreddit(self, subreddit_name: str, last_scanned_id: Optional[str] = None, limit: int = 25) -> int:
        """
        Scans a specific subreddit for new posts since the last scan.
        
        Args:
            subreddit_name: The name of the subreddit to scan.
            last_scanned_id: The ID of the newest post from the previous scan (to fetch only newer posts).
            limit: The maximum number of posts to fetch per scan.
            
        Returns:
            The number of new posts found and stored.
        """
        if not self.reddit:
            logger.warning("Reddit client not initialized, cannot scan.")
            return 0

        logger.info(f"Scanning r/{subreddit_name} for posts newer than ID: {last_scanned_id}")
        new_posts_count = 0
        newest_post_id_in_scan = None

        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            # PRAW's .new() returns a generator. Fetch posts newer than last_scanned_id.
            # `params` allows passing extra query params like `before` (which expects fullname t3_<id>)
            params = {"limit": limit}
            if last_scanned_id:
                # PRAW expects the "fullname" (t3_ + id) for before/after
                params["before"] = f"t3_{last_scanned_id}"

            # Run PRAW network calls in a separate thread to avoid blocking asyncio loop
            posts_generator = await asyncio.to_thread(
                subreddit.new,
                params=params
            )
            # Convert generator to list within the thread execution if needed,
            # or iterate carefully if memory is a concern.
            fetched_posts = await asyncio.to_thread(list, posts_generator)

            if not fetched_posts:
                logger.info(f"No new posts found in r/{subreddit_name} since {last_scanned_id}.")
                # Update the scan time even if no new posts, maybe useful later
                # update_subreddit_scan_state(conn, subreddit_name, last_scanned_id, update_time=True)
                return 0

            processed_posts, newest_post_id_in_scan = self._process_posts(fetched_posts, subreddit_name)

            if processed_posts:
                conn = get_db_connection()
                try:
                    insert_reddit_posts(conn, processed_posts)
                    conn.commit()
                    new_posts_count = len(processed_posts)
                    logger.info(f"Stored {new_posts_count} new posts from r/{subreddit_name}.")

                    # Update the last scanned ID for this subreddit in the DB
                    # Ensure newest_post_id_in_scan actually corresponds to the latest *processed* post
                    if newest_post_id_in_scan:
                         update_subreddit_scan_state(conn, subreddit_name, newest_post_id_in_scan)
                         conn.commit()
                         logger.info(f"Updated last scanned ID for r/{subreddit_name} to {newest_post_id_in_scan}")
                except Exception as e:
                    pass
                    logger.error(f"Database error storing posts for r/{subreddit_name}: {e}", exc_info=True)
                    if conn: conn.rollback()
                finally:
                    if conn:
                        conn.close()

        except (prawcore.exceptions.NotFound, prawcore.exceptions.Redirect):
             logger.error(f"Subreddit r/{subreddit_name} not found or invalid during scan.")
        except praw.exceptions.PRAWException as e:
            logger.error(f"PRAW error scanning r/{subreddit_name}: {e}", exc_info=True)
            # Handle specific errors like rate limits if needed
        except Exception as e:
            logger.error(f"Unexpected error scanning r/{subreddit_name}: {e}", exc_info=True)

        return new_posts_count

    async def scan(self) -> None:
        """Performs a scan of all tracked subreddits."""
        if not self.reddit:
            logger.warning("Reddit client not initialized, skipping scan.")
            return

        logger.info("Starting scheduled Reddit scan...")
        tracked_subreddits = await self.get_tracked_subreddits()
        total_new_posts = 0

        for sub_info in tracked_subreddits:
            # Check if tracking is active for this sub (assuming db function provides this)
            if sub_info.get('is_active', True):
                subreddit_name = sub_info['name']
                # Get the last scanned post ID from the state stored in DB
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
                await asyncio.sleep(self.scan_interval_seconds)
            except asyncio.CancelledError:
                logger.info("Reddit tracking loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in Reddit tracking loop: {e}", exc_info=True)
                # Avoid tight loop on persistent errors
                await asyncio.sleep(self.scan_interval_seconds)


    async def start_tracking(self, interval_seconds: Optional[int] = None):
        """Starts the background scanning task."""
        if self.running_task and not self.running_task.done():
            logger.warning("Reddit tracking is already running.")
            return False

        if not self.reddit:
            logger.error("Cannot start tracking, Reddit client not initialized.")
            return False

        if interval_seconds is not None:
             self.scan_interval_seconds = interval_seconds

        logger.info(f"Starting Reddit background tracking. Scan interval: {self.scan_interval_seconds}s")
        # Use asyncio.create_task for background execution
        self.running_task = asyncio.create_task(self._tracking_loop())
        return True

    async def stop_tracking(self):
        """Stops the background scanning task."""
        stopped = False
        if self.running_task and not self.running_task.done():
            self.running_task.cancel()
            logger.info("Attempting to stop Reddit tracking loop...")
            try:
                await self.running_task # Wait for cancellation
            except asyncio.CancelledError:
                logger.info("Reddit tracking loop successfully stopped.")
                stopped = True
            except Exception as e:
                 logger.error(f"Error during tracking task cancellation: {e}", exc_info=True)
                 # Task might be stopped despite error
                 stopped = True # Assume stopped

            self.running_task = None
        else:
            logger.info("Reddit tracking is not currently running.")
            stopped = True # It wasn't running, so it's effectively stopped
        return stopped

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the tracker."""
        is_running = self.running_task is not None and not self.running_task.done()
        status = {
            "agent_type": "reddit",
            "is_running": is_running,
            "scan_interval_seconds": self.scan_interval_seconds,
            "client_initialized": self.reddit is not None,
            # Add more status info like tracked subreddit count later if needed
        }
        logger.debug(f"RedditTracker status: {status}")
        return status

    def cleanup(self):
         """Clean up resources (e.g., stop tracking task)."""
         # This needs to be called in an async context or run the async stop function
         # For now, just log.
         logger.info("RedditTracker cleanup called. Ensure stop_tracking is called if running.")
         # if self.running_task:
             # asyncio.run(self.stop_tracking())

# Example usage block (inactive by default)
async def _test_main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    tracker = RedditTracker()
    if tracker.reddit:
        print("Tracker initialized")
        # Ensure DB schema exists before running tests
        # Example calls:
        # await tracker.add_subreddit("python")
        # await tracker.add_subreddit("programming")
        # print(await tracker.get_tracked_subreddits())
        # await tracker.scan()
        # print(await tracker.get_tracked_subreddits()) # Check updated scan state
        # await tracker.remove_subreddit("programming")
        # print(await tracker.get_tracked_subreddits())
        # await tracker.start_tracking(30)
        # await asyncio.sleep(65)
        # await tracker.stop_tracking()
        pass

if __name__ == "__main__":
     # To run tests: Ensure DB is initialized, uncomment below
     # asyncio.run(_test_main())
     pass
