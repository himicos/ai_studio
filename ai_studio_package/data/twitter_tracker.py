from .browser_manager import BrowserManager
import logging
import asyncio
from typing import List, Dict, Optional, Any
import json
from datetime import datetime, timezone
from transformers import pipeline
import functools
import time
import re
from selenium.webdriver.common.by import By
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import the database function
from ai_studio_package.infra.db_enhanced import create_memory_from_post, get_db_connection, get_memory_node, create_memory_node
# Import the FAISS embedding function
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss, create_node_with_embedding
from ai_studio_package.infra.task_manager import create_embedding_task

logger = logging.getLogger(__name__)

class TwitterTracker:
    def __init__(self, browser_manager=None):
        """Initialize the Twitter tracker."""
        # Load configuration from environment variables
        self.twitter_accounts = os.getenv('TWITTER_ACCOUNTS', '').split(',')
        self.twitter_accounts = [a.strip() for a in self.twitter_accounts if a.strip()]
        
        self.keywords = os.getenv('KEYWORDS', '').split(',')
        self.keywords = [k.strip() for k in self.keywords if k.strip()]
        
        # State tracking
        self.last_tweet_ids = {}  # account -> tweet_id
        self.last_check_time = None
        self.is_running = False
        self.scan_task = None
        self._scan_lock = asyncio.Lock()
        self.tracked_users = []
        self.user_id_map = {}  # Map of username to user_id
        
        # Browser manager will be set externally
        self.browser_manager = browser_manager
        
        logger.info(f"Twitter tracker initialized with {len(self.twitter_accounts)} accounts and {len(self.keywords)} keywords")
        
    def set_browser_manager(self, browser_manager: BrowserManager):
        """Set the browser manager instance."""
        self.browser_manager = browser_manager
        logger.info("Browser manager set for Twitter tracker")

    async def scan(self) -> None:
        """Scan Twitter accounts for new tweets."""
        if not self.browser_manager:
            logger.error("Browser manager not initialized. Cannot scan Twitter.")
            raise RuntimeError("Browser manager not initialized")
            
        if self._scan_lock.locked():
            logger.info("Scan already in progress. Skipping concurrent scan request.")
            return
            
        async with self._scan_lock:
            logger.info("Starting Twitter scan cycle...")
            
            # Load users from DB before scanning
            await self.load_users_from_db()
            if not self.tracked_users:
                logger.info("No users to track. Skipping scan.")
                return
                
            logger.info(f"Scanning {len(self.tracked_users)} users: {self.tracked_users}")
            
            # Use asyncio.gather to run user scans concurrently
            scan_tasks = []
            for username in self.tracked_users:
                scan_tasks.append(self._scan_single_user(username))
            
            if scan_tasks:
                await asyncio.gather(*scan_tasks)
                    
            logger.info("Finished Twitter scan cycle.")
            
    async def _scan_single_user(self, username: str):
        """Scans and processes tweets for a single user. Directly awaits the async get_user_tweets."""
        normalized_username = username.lstrip('@').strip().lower()
        logger.info(f"Checking account (normalized/lowercase): {normalized_username}")
        user_db_id = self.user_id_map.get(normalized_username)
        if not user_db_id:
            logger.warning(f"User handle '{normalized_username}' (normalized from '{username}') not found in user_id_map keys: {list(self.user_id_map.keys())}. Skipping.")
            return
            
        # loop = asyncio.get_running_loop() # No longer needed here

        try:
            # --- Directly await the async get_user_tweets method ---
            tweets = await self.browser_manager.get_user_tweets(username)
            # --- End await ---
            
            if tweets:
                logger.info(f"Found {len(tweets)} tweets for {username}. Processing...")
                # Process and store tweets - pass normalized lowercase handle
                await self.process_tweets(tweets) 
            else:
                logger.info(f"No new tweets found for {username}.")
                
        except Exception as e:
            logger.error(f"Error scanning account {username}: {e}", exc_info=True)

    async def process_tweets(self, tweets: List[Dict[str, Any]]) -> None:
        """Process new tweets and store in database with embeddings.
        
        Args:
            tweets (list): List of tweet objects to process
        """
        if not tweets:
            return
            
        try:
            # Get DB connection
            db = get_db_connection()
            cursor = db.cursor()
            
            # Process each tweet
            for tweet in tweets:
                try:
                    # Extract tweet data - handle both old and new tweet structures
                    tweet_id = tweet.get('id') or tweet.get('tweet_id')
                    if not tweet_id:
                        logger.warning(f"Skipping tweet without ID: {tweet}")
                        continue
                        
                    content = tweet.get('content') or tweet.get('tweet_text', '')
                    url = tweet.get('url') or tweet.get('tweet_url', '')
                    
                    # Get author from various possible locations
                    author = (tweet.get('author') or 
                            tweet.get('username') or 
                            tweet.get('metadata', {}).get('author') or
                            tweet.get('user', {}).get('screen_name'))
                            
                    if not author:
                        logger.warning(f"Skipping tweet {tweet_id} without author")
                        continue
                    
                    # Get user ID from tracked_users table using handle
                    cursor.execute(
                        "SELECT id FROM tracked_users WHERE LOWER(handle) = LOWER(?)",
                        (author.lower(),)
                    )
                    result = cursor.fetchone()
                    if not result:
                        logger.warning(f"User {author} not found in tracked_users")
                        continue
                    user_id = result[0]
                    
                    # Get engagement stats
                    stats = tweet.get('stats', {})
                    likes = stats.get('likes', 0)
                    retweets = stats.get('retweets', 0)
                    replies = stats.get('replies', 0)
                    
                    # Create memory node with tweet_ prefix
                    memory_node_id = f"tweet_{tweet_id}"
                    memory_node = {
                        'id': memory_node_id,
                        'type': 'tweet',
                        'content': content,
                        'tags': ['tweet', 'twitter', author.lower()],
                        'created_at': int(time.time() * 1000),
                        'updated_at': int(time.time() * 1000),
                        'source_type': 'twitter',
                        'metadata': {
                            'author': author,
                            'url': url,
                            'tweet_id': tweet_id,
                            'platform': 'twitter',
                            'likes': likes,
                            'retweets': retweets,
                            'replies': replies,
                            'scraped_at': datetime.now().isoformat()
                        }
                    }
                    
                    # Create memory node with async embedding generation
                    node_id = create_node_with_embedding(memory_node, async_embedding=True)
                    if not node_id:
                        logger.error(f"Failed to create memory node for tweet {tweet_id}")
                        continue
                    
                    # Insert into tracked_tweets using raw numeric ID
                    cursor.execute("""
                        INSERT OR REPLACE INTO tracked_tweets 
                        (tweet_id, user_id, content, url, 
                         engagement_likes, engagement_retweets, engagement_replies,
                         date_posted)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        tweet_id,  # Raw numeric ID
                        user_id,   # User ID from tracked_users
                        content,
                        url,
                        likes,
                        retweets,
                        replies
                    ))
                    
                    # Commit after each successful tweet to avoid losing all on one failure
                    db.commit()
                    logger.info(f"Successfully processed tweet {tweet_id} with memory node {node_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing tweet {tweet.get('id', 'unknown')}: {str(e)}", exc_info=True)
                    db.rollback()
                    continue
                    
        except Exception as e:
            logger.error(f"Error in process_tweets: {str(e)}", exc_info=True)
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()

    async def start(self, scan_interval: int = 600):
        """Start the tracking process."""
        if self.is_running:
            logger.warning("Tracker is already running")
            return
            
        self.is_running = True
        self.scan_task = asyncio.create_task(self._scan_loop(scan_interval))
        logger.info("Twitter tracker started")
        
    async def stop(self):
        """Stop the tracking process."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.scan_task:
            self.scan_task.cancel()
            try:
                await self.scan_task
            except asyncio.CancelledError:
                pass
                
        self.browser_manager.cleanup()
        logger.info("Twitter tracker stopped")
        
    async def _scan_loop(self, scan_interval: int):
        """Main scanning loop."""
        while self.is_running:
            try:
                await self.scan()
                await asyncio.sleep(scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying 

    async def load_users_from_db(self):
        """Loads/reloads the list of tracked user handles from the database."""
        logger.info("Loading tracked users from database into tracker instance...")
        conn = None
        new_user_list = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT handle, id FROM tracked_users WHERE id IS NOT NULL") # Fetch handles and IDs
            rows = cursor.fetchall()
            for row in rows:
                handle, user_id = row
                if handle:
                    normalized_handle = handle.lstrip('@').strip()
                    if normalized_handle:
                        new_user_list.append(normalized_handle)
                        self.user_id_map[normalized_handle.lower()] = user_id
                    else:
                        logger.warning(f"Skipping row with invalid handle from DB during load: '{handle}'")
                else:
                    logger.warning("Skipping row with NULL handle from DB during load.")
            
            # Atomically update the list
            self.tracked_users = new_user_list
            logger.info(f"Successfully loaded {len(self.tracked_users)} users into tracker instance: {self.tracked_users}")

        except Exception as e:
            logger.error(f"Failed to load users from database into tracker: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    async def insert_memory_node_async(self, conn, node_data: Dict[str, Any]) -> bool:
        """Helper function to insert a memory node into the database asynchronously."""
        try:
             cursor = conn.cursor()
             cursor.execute('''
                 INSERT INTO memory_nodes (id, title, content, type, created_at, updated_at, has_embedding, tags, metadata)
                 VALUES (:id, :title, :content, :type, :created_at, :updated_at, :has_embedding, :tags, :metadata)
                 ON CONFLICT(id) DO NOTHING 
             ''', node_data) # Use named placeholders
             conn.commit() # Commit after each insert (can be optimized with batching)
             return cursor.rowcount > 0 # Returns 1 if inserted, 0 if conflict/nothing happened
        except Exception as insert_err:
             logger.error(f"Error inserting memory node {node_data.get('id', 'N/A')}: {insert_err}")
             conn.rollback() # Rollback on error
             return False

    def _should_check_account(self, account: str) -> bool:
        """Check if an account should be checked based on rate limiting intervals."""
        now = time.time()
        last_check = self.last_check_time.get(account, 0)
        interval = self.current_intervals.get(account, self.rate_limit_config['min_interval'])
        
        if now - last_check >= interval:
            self.last_check_time[account] = now # Update last check time *before* the check
            return True
        else:
            return False

    def _update_check_interval(self, account: str, activity_count: int):
        """Update the check interval for an account based on recent activity."""
        current_interval = self.current_intervals.get(account, self.rate_limit_config['min_interval'])
        config = self.rate_limit_config
        
        if activity_count >= config['activity_threshold']:
            # High activity, decrease interval
            new_interval = max(config['min_interval'], current_interval * config['recovery_factor'])
        else:
            # Low activity, increase interval
            new_interval = min(config['max_interval'], current_interval * config['backoff_factor'])
            
        self.current_intervals[account] = new_interval
        logger.debug(f"Updated check interval for {account} to {new_interval:.1f}s (activity: {activity_count})")
        
    def cleanup(self):
        # ... (cleanup code remains the same) ...
        pass

    def check_account(self, account: str) -> List[Dict[str, Any]]:
        """Check a Twitter account for new tweets.
        
        Args:
            account (str): Twitter handle to check
            
        Returns:
            list: List of new tweets
        """
        new_tweets = []
        
        try:
            # Get tweets from browser manager
            tweets = self.browser_manager.get_user_tweets(account)
            
            # Process tweets
            for tweet in tweets:
                try:
                    # Check if tweet is pinned
                    pinned = tweet.find_elements(By.CLASS_NAME, "pinned")
                    if pinned:
                        continue
                    
                    # Get tweet ID from permalink
                    permalink = tweet.find_element(By.CLASS_NAME, "tweet-link")
                    tweet_url = permalink.get_attribute("href")
                    tweet_id = tweet_url.split("/")[-1]  # Just the numeric ID
                    
                    # Skip if we've seen this tweet before
                    if account in self.last_tweet_ids and tweet_id == self.last_tweet_ids[account]:
                        break
                    
                    # Get tweet content
                    content_elem = tweet.find_element(By.CLASS_NAME, "tweet-content")
                    tweet_text = content_elem.text
                    
                    # Get tweet timestamp
                    timestamp_elem = tweet.find_element(By.CLASS_NAME, "tweet-date")
                    timestamp_url = timestamp_elem.get_attribute("href")
                    timestamp_text = timestamp_elem.text
                    
                    # Create tweet object with raw numeric ID for tracked_tweets
                    tweet_obj = {
                        'id': tweet_id,  # Store raw numeric ID
                        'source': 'twitter',
                        'author': account,
                        'content': tweet_text,
                        'url': tweet_url,
                        'created_utc': int(datetime.now().timestamp()),  # Approximate
                        'metadata': {
                            'tweet_id': tweet_id,
                            'timestamp_text': timestamp_text,
                            'platform': 'twitter'
                        }
                    }
                    
                    # Add to new tweets
                    new_tweets.append(tweet_obj)
                    
                    # Update last seen tweet ID
                    self.last_tweet_ids[account] = tweet_id
                    
                except Exception as e:
                    logger.error(f"Error processing tweet for {account}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking account {account}: {e}")
            
        return new_tweets

    def _convert_to_twitter_url(self, nitter_url: str, username: str) -> str:
        """Convert a Nitter URL to a Twitter/X.com URL."""
        try:
            # Extract tweet ID from the URL
            tweet_id = nitter_url.split('/')[-1].split('#')[0]
            return f"https://x.com/{username}/status/{tweet_id}"
        except Exception as e:
            logger.error(f"Error converting Nitter URL {nitter_url}: {e}")
            return nitter_url

    def process_tweet(self, tweet: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a tweet to detect patterns.
        
        Args:
            tweet (dict): Tweet data
            
        Returns:
            list: List of detected items
        """
        detected_items = []
        tweet_text = tweet['content']
        tweet_id = tweet['id']  # This is now just the numeric ID
        username = tweet.get('username', tweet.get('author', ''))  # Get username from either field
        
        # Convert URL to Twitter format
        if 'url' in tweet:
            tweet['url'] = self._convert_to_twitter_url(tweet['url'], username)
        
        # Check for contract addresses
        contract_matches = re.findall(self.contract_regex, tweet_text)
        for contract in contract_matches:
            logger.info(f"Found contract in tweet: {contract}")
            
            # Create contract object
            contract_obj = {
                'id': f"contract_{contract}_{int(datetime.now().timestamp())}",
                'address': contract,
                'source': 'twitter',
                'source_id': f"tweet_{tweet_id}",  # Use tweet_ prefix for memory nodes
                'detected_at': int(datetime.now().timestamp()),
                'status': 'detected',
                'metadata': {
                    'tweet_text': tweet_text,
                    'tweet_url': tweet['url'],  # Now using x.com URL
                    'author': username
                }
            }
            
            # Store contract in database
            store_contract(contract_obj)
            
            # Add to detected items
            detected_items.append({
                'type': 'contract',
                'data': contract_obj
            })
        
        # Check for keywords
        for keyword in self.keywords:
            if keyword.lower() in tweet_text.lower():
                logger.info(f"Found keyword '{keyword}' in tweet")
                
                # Add to detected items
                detected_items.append({
                    'type': 'keyword',
                    'data': {
                        'keyword': keyword,
                        'tweet': tweet
                    }
                })
        
        return detected_items

    # ... (rest of the file) ... 