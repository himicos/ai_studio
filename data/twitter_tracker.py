"""
Twitter Tracker Module for AI Studio

This module handles Twitter monitoring via nitter.net for AI Studio, including:
- Monitoring Twitter accounts for keywords and contract addresses
- Using Selenium to scrape nitter.net instances
- Detecting patterns in tweets using regex
- Sending detected items to the action executor
"""

import os
import re
import time
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import random

# Import our modules
from ai_studio_package.infra.db_enhanced import create_memory_node, get_db_connection, create_memory_edge, get_memory_node
from tools.burner_manager import BurnerManager

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# --- Configuration Constants ---
MIN_REPLIES_FOR_COMMENT_FETCH = 10
MIN_LIKES_FOR_COMMENT_FETCH = 25
# Add other thresholds if needed (retweets?)
# TODO: Consider moving these to .env or a config file

class TwitterTracker:
    """
    Twitter Tracker for AI Studio.
    
    This class monitors Twitter accounts via nitter.net instances using Selenium.
    It detects patterns in tweets using regex and sends detected items to the
    action executor.
    """
    
    def __init__(self):
        """
        Initialize the Twitter tracker.
        """
        # Thresholds for fetching replies
        self.min_replies_for_comment_fetch = MIN_REPLIES_FOR_COMMENT_FETCH
        self.min_likes_for_comment_fetch = MIN_LIKES_FOR_COMMENT_FETCH

        # Load configuration from environment variables
        self.twitter_accounts = os.getenv('TWITTER_ACCOUNTS', '').split(',')
        self.twitter_accounts = [a.strip() for a in self.twitter_accounts if a.strip()]
        
        self.keywords = os.getenv('KEYWORDS', '').split(',')
        self.keywords = [k.strip() for k in self.keywords if k.strip()]
        
        # Nitter instances
        self.instances = [
            "https://nitter.net",
            "https://nitter.poast.org",
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks"
        ]
        self.current_instance = 0
        
        # Regex patterns
        self.contract_regex = r"0x[a-fA-F0-9]{40}"
        
        # State tracking
        self.last_tweet_ids = {}  # account -> tweet_id
        self.driver = None
        self.last_check_time = None
        
        # Rate limiting
        self.rate_limit_config = {
            'min_interval': 60,  # Minimum seconds between checks (1 minute)
            'max_interval': 300,  # Maximum seconds between checks (5 minutes)
            'activity_threshold': 5,  # Number of tweets that indicate high activity
            'backoff_factor': 1.5,  # How much to increase interval when no activity
            'recovery_factor': 0.8,  # How much to decrease interval when activity detected
        }
        self.last_check_times = {}  # account -> last check timestamp
        self.current_intervals = {}  # account -> current check interval
        
        # Initialize browser
        self.setup_browser()
        
        # Initialize burner manager
        self.burner_manager = BurnerManager()
        
        self.running_task = None
        
        logger.info(f"Twitter tracker initialized with {len(self.twitter_accounts)} accounts and {len(self.keywords)} keywords")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current configuration/status of the tracker.

        Returns:
            dict: Tracker status including accounts and keywords.
        """
        logger.info(f"Executing TwitterTracker.get_status. Current state: accounts={self.twitter_accounts}, keywords={self.keywords}")
        return {
            "accounts": self.twitter_accounts,
            "keywords": self.keywords,
            # Add other relevant status info here if needed
        }

    def setup_browser(self):
        """
        Initialize Chrome in headless mode with specific options.
        """
        try:
            chrome_options = Options()
            # Headless settings
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Performance settings
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # Disable images
            
            # Anti-detection settings
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Suppress logging
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Initialize the Chrome WebDriver with service
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(10)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Browser initialized successfully in headless mode.")
        except WebDriverException as e:
            logger.error(f"WebDriverException during browser setup: {e}")
            self.driver = None # Set driver to None on error
            raise # Re-raise the exception
        except Exception as e:
            logger.error(f"Unexpected error during browser setup: {e}", exc_info=True)
            self.driver = None # Set driver to None on error
            raise # Re-raise the exception

    def _rotate_instance(self):
        """
        Rotate to next nitter instance.
        """
        self.current_instance = (self.current_instance + 1) % len(self.instances)
        logger.info(f"Switched to instance: {self.instances[self.current_instance]}")
    
    def _should_check_account(self, account: str) -> bool:
        """
        Determine if an account should be checked based on rate limiting rules.
        
        Args:
            account (str): Twitter account name
            
        Returns:
            bool: True if account should be checked, False otherwise
        """
        current_time = time.time()
        
        # Initialize tracking for new accounts
        if account not in self.last_check_times:
            self.last_check_times[account] = 0
            self.current_intervals[account] = self.rate_limit_config['min_interval']
            return True
            
        # Calculate time since last check
        time_since_last_check = current_time - self.last_check_times[account]
        
        # Check if enough time has passed
        if time_since_last_check >= self.current_intervals[account]:
            return True
            
        return False
        
    def _update_check_interval(self, account: str, activity_level: int):
        """
        Update the check interval for an account based on activity level.
        
        Args:
            account (str): Twitter account name
            activity_level (int): Number of new tweets found
        """
        current_interval = self.current_intervals[account]
        
        if activity_level >= self.rate_limit_config['activity_threshold']:
            # High activity - decrease interval (check more frequently)
            new_interval = max(
                self.rate_limit_config['min_interval'],
                current_interval * self.rate_limit_config['recovery_factor']
            )
            logger.info(f"High activity for {account} ({activity_level} tweets). Decreasing interval from {current_interval}s to {new_interval}s")
        elif activity_level == 0:
            # No activity - increase interval (check less frequently)
            new_interval = min(
                self.rate_limit_config['max_interval'],
                current_interval * self.rate_limit_config['backoff_factor']
            )
            logger.info(f"No activity for {account}. Increasing interval from {current_interval}s to {new_interval}s")
        else:
            # Moderate activity - keep current interval
            new_interval = current_interval
            logger.info(f"Moderate activity for {account} ({activity_level} tweets). Keeping interval at {current_interval}s")
            
        self.current_intervals[account] = new_interval
        self.last_check_times[account] = time.time()

    def check_account(self, account: str) -> List[Dict[str, Any]]:
        """
        Check for new tweets from a Twitter account using Selenium.
        
        Args:
            account (str): Twitter account name
            
        Returns:
            list: List of new tweets
        """
        instance = self.instances[self.current_instance]
        url = f"{instance}/{account}"
        new_tweets = []
        
        try:
            self.last_check_time = datetime.now()
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for tweets to load
            wait = WebDriverWait(self.driver, 10)
            tweets = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "timeline-item")))
            
            if not tweets:
                logger.info(f"No tweets found for {account}")
                return []

            # Process tweets
            processed_count_for_debug = 0 # Counter for debug processing
            max_tweets_to_debug = 3     # Process first 3 even if seen

            for tweet in tweets:
                try:
                    # Check if tweet is pinned
                    pinned = tweet.find_elements(By.CLASS_NAME, "pinned")
                    if pinned:
                        continue
                    
                    # Get tweet ID from permalink
                    permalink = tweet.find_element(By.CLASS_NAME, "tweet-link")
                    tweet_url = permalink.get_attribute("href")
                    # Extract ID robustly, handling potential query params
                    tweet_id_match = re.search(r'/status/(\d+)', tweet_url)
                    if not tweet_id_match:
                        logger.warning(f"Could not extract tweet ID from URL: {tweet_url}")
                        continue
                    tweet_id = tweet_id_match.group(1)

                    # --- TEMPORARY DEBUG LOGIC --- 
                    is_new_tweet = True
                    if account in self.last_tweet_ids and tweet_id == self.last_tweet_ids[account]:
                        is_new_tweet = False
                        # Original logic was to break here. We won't break for the first few.
                        
                    # Skip if we've seen this tweet AND we are past the debug count
                    if not is_new_tweet and processed_count_for_debug >= max_tweets_to_debug:
                         logger.debug(f"[Debug Skip] Breaking loop for {account} at tweet {tweet_id} (already seen and past debug count).")
                         break # Stop processing older tweets for this account in this run
                    # --- END TEMPORARY DEBUG LOGIC ---

                    # Get tweet content
                    content_elem = tweet.find_element(By.CLASS_NAME, "tweet-content")
                    tweet_text = content_elem.text
                    
                    # Get tweet timestamp
                    timestamp_elem = tweet.find_element(By.CLASS_NAME, "tweet-date")
                    # timestamp_url = timestamp_elem.get_attribute("href") # URL not needed directly
                    timestamp_text = timestamp_elem.text # Keep original text representation

                    # --- Scrape Engagement Data --- 
                    replies = 0
                    retweets = 0 # If needed later
                    likes = 0
                    try:
                        stats_container = tweet.find_element(By.CLASS_NAME, "tweet-stats")
                        
                        # Replies (comment icon)
                        reply_elem = stats_container.find_element(By.CSS_SELECTOR, ".icon-comment")
                        reply_span = reply_elem.find_element(By.XPATH, "./following-sibling::span")
                        replies_text = reply_span.text
                        replies = int(replies_text.replace(',', '')) if replies_text else 0
                        logger.debug(f"[Scrape Debug] Tweet {tweet_id}: Found replies text: '{replies_text}', Parsed replies: {replies}") # DEBUG LOG
                        
                        # Retweets (retweet icon)
                        # retweet_elem = stats_container.find_element(By.CSS_SELECTOR, ".icon-retweet") 
                        # retweet_span = retweet_elem.find_element(By.XPATH, "./following-sibling::span")
                        # retweets = int(retweet_span.text.replace(',', '')) if retweet_span.text else 0
                        
                        # Likes (heart icon)
                        like_elem = stats_container.find_element(By.CSS_SELECTOR, ".icon-heart")
                        like_span = like_elem.find_element(By.XPATH, "./following-sibling::span")
                        likes_text = like_span.text
                        likes = int(likes_text.replace(',', '')) if likes_text else 0
                        logger.debug(f"[Scrape Debug] Tweet {tweet_id}: Found likes text: '{likes_text}', Parsed likes: {likes}") # DEBUG LOG
                        
                    except Exception as scrape_err:
                        # Log the error specifically for scraping engagement
                        logger.warning(f"[Scrape Debug] Could not scrape engagement stats for tweet {tweet_id}: {scrape_err}")
                    # --- End Scrape Engagement Data --- 

                    # --- Increment Debug Counter ---
                    processed_count_for_debug += 1 
                    # --- End Increment Debug Counter ---

                    # Create tweet object
                    tweet_obj = {
                        'id': f"tweet_{tweet_id}", # Standardized ID prefix
                        'source': 'twitter',
                        'author': account,
                        'content': tweet_text,
                        'url': tweet_url,
                        'replies': replies, # Added
                        'likes': likes,     # Added
                        # 'retweets': retweets, # Add if scraped
                        'created_utc': int(datetime.now().timestamp()),  # Approximate, Nitter timestamp parsing is complex
                        'metadata': {
                            'tweet_id': tweet_id,
                            'timestamp_text': timestamp_text,
                            'platform': 'twitter',
                            'scraped_at': datetime.now().isoformat()
                        }
                    }
                    
                    # Add to new tweets
                    new_tweets.append(tweet_obj)
                    
                    # If this is the first tweet processed in this batch for the account, 
                    # update last_tweet_ids to prevent processing it again next time.
                    if account not in self.last_tweet_ids or len(new_tweets) == 1: 
                        self.last_tweet_ids[account] = tweet_id
                
                except Exception as e:
                    # Log error processing a specific tweet but continue with others
                    logger.error(f"Error processing a tweet from {account} (URL: {tweet_url if 'tweet_url' in locals() else 'unknown'}): {e}", exc_info=True)
            
            # Reverse the list so oldest tweets come first
            new_tweets.reverse()
            
            return new_tweets
        
        except TimeoutException:
            logger.error(f"Timeout accessing {url}")
            self._rotate_instance()
            return []
        except WebDriverException as e:
            logger.error(f"Browser error: {e}")
            # Try to recover the browser session
            try:
                self.driver.quit()
            except:
                pass
            self.setup_browser()
            self._rotate_instance()
            return []
        except Exception as e:
            logger.error(f"Error checking tweets: {e}")
            self._rotate_instance()
            return []
    
    def update_accounts(self, accounts: List[str]):
        """Dynamically update the list of Twitter accounts to track."""
        self.twitter_accounts = [a.strip() for a in accounts if a.strip()]
        logger.info(f"Updated Twitter accounts to track: {self.twitter_accounts}")
    
    def update_keywords(self, keywords: List[str]):
        """Dynamically update the list of keywords to track."""
        self.keywords = [k.strip() for k in keywords if k.strip()]
        logger.info(f"Updated Twitter keywords to track: {self.keywords}")
    
    def process_tweet(self, tweet: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a tweet to detect patterns.
        
        Args:
            tweet (dict): Tweet data
            
        Returns:
            list: List of detected items
        """
        detected_items = []
        tweet_text = tweet.get('content', '')
        
        # Check for contract addresses
        contract_matches = re.findall(self.contract_regex, tweet_text)
        for contract in contract_matches:
            logger.info(f"Found contract {contract} in tweet {tweet.get('id')}")
            
            # Create contract object
            contract_obj = {
                'address': contract,
                'source': 'twitter',
                'source_id': tweet.get('id'),
                'metadata': {
                    'tweet_text': tweet_text,
                    'tweet_url': tweet.get('url'),
                    'author': tweet.get('author')
                }
            }
            
            detected_items.append({
                'type': 'contract',
                'data': contract_obj
            })
        
        # Check for keywords
        for keyword in self.keywords:
            if keyword.lower() in tweet_text.lower():
                logger.info(f"Found keyword '{keyword}' in tweet {tweet.get('id')}")
                
                detected_items.append({
                    'type': 'keyword',
                    'data': {
                        'keyword': keyword,
                        'tweet_id': tweet.get('id')
                    }
                })
        
        return detected_items
    
    async def scan(self) -> None:
        """
        Scan Twitter accounts for new tweets and store them as memory nodes.
        Designed to be run periodically.
        """
        logger.info("Starting Twitter scan cycle...")
        
        if not self.driver:
             logger.error("Browser not initialized. Cannot scan Twitter.")
             return
             
        # Ensure DB connection handling is robust
        conn = None 
        try:
             conn = get_db_connection()
             if not conn:
                 logger.error("Failed to get DB connection for Twitter scan cycle.")
                 return
        except Exception as db_err:
             logger.error(f"Error getting DB connection: {db_err}")
             return # Cannot proceed without DB
        
        all_processed_items = [] # To collect items from process_tweet
        
        try:
            for account in self.twitter_accounts:
                account_lower = account.lower() # Use lowercase for consistency internally
                logger.info(f"Checking account: {account} ({account_lower})")
                
                # Apply rate limiting
                if not self._should_check_account(account_lower):
                    logger.info(f"Skipping {account_lower} due to rate limiting")
                    continue
                
                try:
                    # Fetch raw tweet data from BrowserManager
                    # Returns list of dicts: {'id', 'content', 'timestamp_iso', 'stats': {'replies', 'likes', ...}, 'url'}
                    new_tweets_raw = await self.check_account(account_lower)
                    logger.info(f"Found {len(new_tweets_raw)} raw tweets for {account}. Processing...")

                    if not new_tweets_raw:
                        logger.info(f"No raw tweets returned from BrowserManager for {account}.")
                        self._update_check_interval(account_lower, 0) # Update interval even if no tweets
                        continue

                    # --- TEMPORARY DEBUG: Process first few regardless of DB status --- 
                    processed_for_debug_count = 0
                    max_to_process_for_debug = 3 
                    # --- END TEMP DEBUG --- 

                    # Get existing IDs from DB *once* for efficiency
                    tweet_ids_to_check = [t.get('id') for t in new_tweets_raw if t.get('id')]
                    # Helper function assumed to exist or needs to be created:
                    # def get_existing_tweet_node_ids(conn, tweet_ids): 
                    #    placeholders = ','join('?' * len(tweet_ids))
                    #    node_ids = [f'tweet_{tid}' for tid in tweet_ids]
                    #    cursor = conn.execute(f"SELECT id FROM memory_nodes WHERE id IN ({placeholders})", node_ids)
                    #    return {row['id'] for row in cursor.fetchall()} 
                    # For now, we will check individually, which is less efficient
                    # existing_tweet_node_ids = set(get_existing_tweet_node_ids(conn, tweet_ids_to_check))
                    # logger.debug(f"Checked {len(tweet_ids_to_check)} tweet IDs against DB for {account}.")
                    
                    stored_count = 0
                    skipped_count = 0
                    error_count = 0
                    
                    for tweet_data_raw in new_tweets_raw:
                        tweet_id_numeric = tweet_data_raw.get('id')
                        if not tweet_id_numeric:
                            logger.warning("Skipping tweet due to missing ID from BrowserManager.")
                            error_count += 1
                            continue
                            
                        tweet_node_id = f"tweet_{tweet_id_numeric}"
                        
                        # --- Check if node exists (less efficient than bulk check) ---
                        existing_node = get_memory_node(tweet_node_id) # Assumes get_memory_node handles its own connection/cursor
                        node_exists_in_db = existing_node is not None
                        # --- End Check ---
                        
                        # --- TEMPORARY DEBUG: Check if processing is forced --- 
                        force_process_for_debug = processed_for_debug_count < max_to_process_for_debug
                        # --- END TEMP DEBUG --- 
                        
                        # Original check: Skip if tweet already exists AND we are not forcing debug processing
                        if node_exists_in_db and not force_process_for_debug:
                            skipped_count += 1
                            continue # Skip this tweet if already in DB and not forced

                        # --- If we reach here, we process the tweet (either new or forced for debug) ---
                        processed_for_debug_count += 1 # Increment debug counter if processed

                        # 1. Prepare data for memory node (map from BrowserManager format)
                        tweet_stats = tweet_data_raw.get('stats', {})
                        timestamp_iso = tweet_data_raw.get('timestamp_iso')
                        created_at_timestamp = int(time.time()) # Default to current time as int
                        if timestamp_iso:
                            try:
                                dt_obj = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
                                created_at_timestamp = int(dt_obj.timestamp())
                            except (ValueError, TypeError) as ts_err:
                                logger.warning(f"Could not parse ISO timestamp '{timestamp_iso}': {ts_err}. Using current time.")

                        # Define node_data dictionary correctly
                        node_data = {
                            'id': tweet_node_id,
                            'type': 'tweet',
                            'content': tweet_data_raw.get('content', ''),
                            'tags': ['tweet', account],
                            'created_at': created_at_timestamp,
                            'source_id': tweet_id_numeric,
                            'source_type': 'twitter_tweet',
                            'metadata': {
                                'tweet_id': tweet_id_numeric,
                                'timestamp_iso': timestamp_iso,
                                'url': tweet_data_raw.get('url'),
                                'platform': 'twitter',
                                'author': account,
                                'scraped_at': datetime.now().isoformat(),
                                'replies': tweet_stats.get('replies', 0),
                                'likes': tweet_stats.get('likes', 0),
                                'retweets': tweet_stats.get('retweets', 0),
                                'quotes': tweet_stats.get('quotes', 0)
                            }
                        }

                        # Log before storing (only if it wasn't skipped)
                        logger.info(f"Processing tweet {tweet_node_id} (Exists: {node_exists_in_db}, Forced: {force_process_for_debug})")
                        
                        # 2. Store/Update the original tweet as a memory node
                        # Using create_memory_node which handles its own connection implicitly
                        # We might need UPDATE logic if we want to update existing nodes when force_process_for_debug is True
                        created_node_id = None
                        if not node_exists_in_db:
                             created_node_id = create_memory_node(node_data) 
                        
                        # Proceed if node was newly created OR if it existed but we forced processing
                        if created_node_id or (node_exists_in_db and force_process_for_debug):
                            if created_node_id:
                                stored_count += 1
                                logger.info(f"Stored NEW tweet {tweet_node_id} as memory node {created_node_id}")
                            else:
                                # If forced and already exists, log differently or update node if needed
                                logger.info(f"Re-processing EXISTING tweet {tweet_node_id} for reply check.")
                                # Optional: Update existing node metadata if desired
                                # from ai_studio_package.infra.db_enhanced import update_memory_node 
                                # update_memory_node({'id': tweet_node_id, 'metadata': node_data['metadata']}) # Example update
                                pass

                            # 3. Process tweet for keywords/contracts (existing logic)
                            processed_items = self.process_tweet(node_data)
                            all_processed_items.extend(processed_items)
                            
                            # 4. Check for high traction and fetch replies if needed
                            replies = tweet_stats.get('replies', 0)
                            likes = tweet_stats.get('likes', 0)
                            
                            # --- Log Engagement Data Before Check --- 
                            logger.debug(f"[Threshold Check] Tweet {tweet_node_id}: Checking traction with Replies={replies}, Likes={likes}")
                            # --- End Log --- 
                            
                            if (replies >= self.min_replies_for_comment_fetch or 
                                likes >= self.min_likes_for_comment_fetch):
                                logger.info(f"High traction detected for tweet {tweet_node_id} (Replies: {replies}, Likes: {likes}). Fetching replies...")
                                # Pass the necessary data (URL, Node ID) from node_data
                                fetch_data = {
                                    'url': node_data['metadata']['url'],
                                    'id': node_data['id'] # Pass the node ID (e.g., tweet_123)
                                }
                            await self._fetch_and_process_replies(fetch_data) 
                            
                        elif not created_node_id and not node_exists_in_db:
                             # This case means create_memory_node failed for a non-existing node
                            logger.error(f"Failed to store NEW tweet {tweet_node_id} as memory node.")
                            error_count += 1
                            
                    logger.info(f"Finished processing for {account}. Inserted: {stored_count}, Skipped (Already Existed): {skipped_count}, Errors: {error_count}")
                    
                    # Update overall check interval for the account based on *raw* tweets found
                    self._update_check_interval(account_lower, len(new_tweets_raw))
                    
                    # Add delay between accounts
                    await asyncio.sleep(random.uniform(3, 7)) # Use async sleep

                except Exception as e:
                    logger.error(f"Error processing account {account}: {e}", exc_info=True)
                    # Continue to the next account even if one fails

            # --- Optional: Process all detected items after scanning all accounts ---
            # logger.info(f"Processing {len(all_processed_items)} detected items (keywords/contracts)...")
            # for item in all_processed_items:
            #     # Handle contracts, keywords etc.
            #     pass
            
        except Exception as e:
            logger.error(f"Unexpected error during Twitter scan cycle: {e}", exc_info=True)
        finally:
            if conn: 
                conn.close()
                logger.info("Closed main DB connection for Twitter scan cycle.")
                
        logger.info("Twitter scan cycle finished.")
    
    def cleanup(self):
        """
        Clean up resources (Selenium browser).
        """
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None  # Ensure driver is marked as closed
            except Exception as e:
                logger.error(f"Error quitting Selenium driver: {e}")
            logger.info("Browser closed")

    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for Twitter users using Nitter.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of user objects with id, handle, and name
        """
        instance = self.instances[self.current_instance]
        url = f"{instance}/search?f=users&q={query}"
        users = []
        
        try:
            # Navigate to search page
            self.driver.get(url)
            
            # Wait for results to load
            wait = WebDriverWait(self.driver, 10)
            user_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "profile-card")))
            
            # Process user elements
            for user_elem in user_elements[:limit]:
                try:
                    # Get user handle
                    handle_elem = user_elem.find_element(By.CLASS_NAME, "profile-card-username")
                    handle = handle_elem.text.strip("@")
                    
                    # Get user name
                    name_elem = user_elem.find_element(By.CLASS_NAME, "profile-card-fullname")
                    name = name_elem.text.strip()
                    
                    # Get profile URL
                    profile_link = user_elem.find_element(By.CLASS_NAME, "profile-card-link")
                    profile_url = profile_link.get_attribute("href")
                    
                    # Create user object
                    user_obj = {
                        'id': f"twitter_user_{handle}",
                        'handle': handle,
                        'name': name,
                        'url': profile_url,
                        'metadata': {
                            'platform': 'twitter',
                            'source': 'nitter_search'
                        }
                    }
                    
                    users.append(user_obj)
                
                except Exception as e:
                    logger.error(f"Error processing user element: {e}")
                    continue
            
            return users
        
        except TimeoutException:
            logger.error(f"Timeout accessing search URL: {url}")
            self._rotate_instance()
            return []
        except WebDriverException as e:
            logger.error(f"Browser error during user search: {e}")
            try:
                self.driver.quit()
                self.setup_browser()
            except Exception as setup_error:
                logger.error(f"Error recovering browser: {setup_error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during user search: {e}")
            return []

    async def _fetch_and_process_replies(self, original_tweet_data: Dict[str, Any]):
        """
        Fetches replies for a high-traction tweet using Selenium/Nitter 
        and processes them.
        
        Args:
            original_tweet_data: Dictionary containing data of the original tweet,
                                 including its 'url' and 'id'.
        """
        tweet_url = original_tweet_data.get('url')
        original_tweet_node_id = original_tweet_data.get('id') # e.g., tweet_12345
        
        if not tweet_url or not original_tweet_node_id:
            logger.error("Missing URL or ID in original tweet data for fetching replies.")
            return

        logger.info(f"Attempting to fetch replies for tweet: {tweet_url}")

        try:
            # Navigate to the individual tweet page
            self.driver.get(tweet_url)
            
            # Wait for the main tweet and potentially replies to load
            # We might need more specific waits depending on Nitter's structure
            wait = WebDriverWait(self.driver, 15)
            # Wait for the original tweet content to ensure the page is loaded
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-tweet")))
            # Try to find reply elements (adjust selector as needed)
            reply_elements = self.driver.find_elements(By.CSS_SELECTOR, ".reply .timeline-item") # Example selector
            
            logger.info(f"Found {len(reply_elements)} potential reply elements for {original_tweet_node_id}")
            
            processed_count = 0
            for reply_element in reply_elements:
                try:
                    reply_data = self._extract_reply_data(reply_element, original_tweet_node_id)
                    if reply_data:
                        self._process_reply(reply_data, original_tweet_node_id)
                        processed_count += 1
                except Exception as e:
                    logger.warning(f"Error processing a single reply element for {original_tweet_node_id}: {e}")
            
            logger.info(f"Processed {processed_count} replies for tweet {original_tweet_node_id}.")

        except TimeoutException:
            logger.error(f"Timeout loading replies page: {tweet_url}")
            # Consider rotating instance or just logging
        except WebDriverException as e:
            logger.error(f"Browser error fetching replies for {tweet_url}: {e}")
            # Consider trying to recover the browser
        except Exception as e:
            logger.error(f"Unexpected error fetching replies for {tweet_url}: {e}", exc_info=True)
            
    def _extract_reply_data(self, reply_element, original_tweet_id: str) -> Optional[Dict[str, Any]]:
        """Extracts data from a single reply HTML element."""
        try:
            # Extract reply ID (often part of the permalink)
            permalink_elem = reply_element.find_element(By.CLASS_NAME, "tweet-link")
            reply_url = permalink_elem.get_attribute("href")
            reply_id_match = re.search(r'/status/(\d+)', reply_url)
            reply_id = reply_id_match.group(1) if reply_id_match else f"unknown_{int(time.time()*1000)}"
            
            # Extract author handle
            author_elem = reply_element.find_element(By.CLASS_NAME, "username")
            author = author_elem.text
            
            # Extract content
            content_elem = reply_element.find_element(By.CLASS_NAME, "tweet-content")
            content = content_elem.text
            
            # Extract timestamp (optional, might be complex)
            timestamp_text = "unknown"
            try:
                timestamp_elem = reply_element.find_element(By.CLASS_NAME, "tweet-date")
                timestamp_text = timestamp_elem.text
            except Exception:
                pass # Ignore if timestamp isn't found
                
            return {
                'id': reply_id,
                'author': author,
                'text': content,
                'url': reply_url,
                'timestamp_text': timestamp_text
            }
            
        except Exception as e:
            logger.warning(f"Could not extract data from a reply element for {original_tweet_id}: {e}")
            return None
            
    def _process_reply(self, reply_data: Dict[str, Any], original_tweet_node_id: str):
        """
        Processes extracted reply data, creates memory node and edge.
        """
        reply_id = reply_data['id']
        original_tweet_id_numeric = original_tweet_node_id.replace('tweet_', '') # Get original ID number

        # Create Memory Node for the reply
        node_id = f"twitter_reply_{reply_id}"
        node_data = {
            'id': node_id,
            'type': 'tweet_reply',
            'content': reply_data['text'],
            'tags': ['reply', 'twitter', reply_data.get('author', 'unknown')],
            'created_at': int(datetime.now().timestamp()), # Use scrape time
            'source_id': reply_id,
            'source_type': 'tweet_reply',
            'metadata': {
                'original_tweet_id': original_tweet_id_numeric,
                'original_tweet_node_id': original_tweet_node_id,
                'author': reply_data.get('author', 'unknown'),
                'reply_url': reply_data.get('url'),
                'timestamp_text': reply_data.get('timestamp_text'),
                'scraped_at': datetime.now().isoformat(),
                # Placeholder for future AI analysis
                'sentiment': None,
                'keywords': []
            }
        }

        created_node_id = create_memory_node(node_data)

        if created_node_id:
            logger.info(f"Stored reply node: {created_node_id} (reply to {original_tweet_node_id})")

            # Create Memory Edge linking reply to original tweet
            edge_id = f"edge_reply_{reply_id}_to_{original_tweet_id_numeric}"
            edge_data = {
                'id': edge_id,
                'source_node_id': created_node_id,  # The reply node
                'target_node_id': original_tweet_node_id, # The original tweet node
                'label': 'reply_to',
                'weight': 1.0,
                'created_at': int(datetime.now().timestamp()),
                'metadata': {
                    'type': 'structural_link'
                }
            }
            
            edge_created = create_memory_edge(edge_data)
            
            if edge_created:
                logger.info(f"Created edge: {edge_id} linking reply to original tweet.")
            else:
                logger.error(f"Failed to create edge {edge_id} linking reply to original tweet.")
        else:
            logger.error(f"Failed to store reply node for reply ID {reply_id} (reply to {original_tweet_node_id})")

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Twitter tracker
    tracker = TwitterTracker()
    
    try:
        # Scan Twitter accounts
        asyncio.run(tracker.scan())
    finally:
        # Clean up
        tracker.cleanup()
