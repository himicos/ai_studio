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

# Import our modules
from ai_studio_package.infra.db_enhanced import create_memory_node, get_db_connection
from tools.burner_manager import BurnerManager

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

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
            for tweet in tweets:
                try:
                    # Check if tweet is pinned
                    pinned = tweet.find_elements(By.CLASS_NAME, "pinned")
                    if pinned:
                        continue
                    
                    # Get tweet ID from permalink
                    permalink = tweet.find_element(By.CLASS_NAME, "tweet-link")
                    tweet_url = permalink.get_attribute("href")
                    tweet_id = tweet_url.split("/")[-1]
                    
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
                    
                    # Create tweet object
                    tweet_obj = {
                        'id': f"twitter_{tweet_id}",
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
                    
                    # If this is the first tweet, update last_tweet_ids
                    if len(new_tweets) == 1:
                        self.last_tweet_ids[account] = tweet_id
                
                except Exception as e:
                    logger.error(f"Error processing tweet: {e}")
            
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
        
        # This connection should be managed carefully if scan runs continuously
        # For simplicity, get a connection per scan cycle. Consider pooling for performance.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get DB connection for Twitter scan.")
            return
        
        try:
            for account in self.twitter_accounts:
                logger.info(f"Checking account: {account}")
                
                # Apply rate limiting
                if not self._should_check_account(account):
                    logger.info(f"Skipping {account} due to rate limiting")
                    continue
                
                try:
                    # Check for new tweets using Selenium/Nitter
                    new_tweets = self.check_account(account)  # This is synchronous
                    
                    # Update rate limiting based on activity
                    self._update_check_interval(account, len(new_tweets))
                    
                    # Process and store new tweets
                    stored_count = 0
                    for tweet_data in new_tweets:
                        # Structure data for memory node
                        node_content = tweet_data.get('content', '')
                        node_source_id = tweet_data.get('id')  # Nitter's internal ID? or actual tweet ID? Check check_account
                        node_metadata = {
                            'platform': 'twitter',
                            'url': tweet_data.get('url'),
                            'author': tweet_data.get('author'),
                            'account': account,  # The account being scanned
                            'likes': tweet_data.get('likes'),
                            'retweets': tweet_data.get('retweets'),
                            'comments': tweet_data.get('comments'),
                            'timestamp_utc': tweet_data.get('timestamp'),  # Assuming check_account provides UTC timestamp
                            # Add other relevant fields from tweet_data if needed
                        }
                        
                        # Process for keywords/contracts - maybe add tags?
                        # detected = self.process_tweet(tweet_data)
                        # node_tags = [item['data']['keyword'] for item in detected if item['type'] == 'keyword']
                        # For now, keep tags simple or omit
                        node_tags = ['twitter', account]
                        
                        # Store tweet as memory node
                        node_id = create_memory_node(
                            conn=conn,
                            node_type='tweet',
                            content=node_content,
                            source_id=node_source_id,
                            source_type='twitter',
                            metadata=node_metadata,
                            tags=node_tags
                            # embedding=None # Embedding generation happens elsewhere
                        )
                        if node_id:
                            logger.info(f"Stored tweet node: {node_id} from account {account}")
                            stored_count += 1
                        else:
                            logger.error(f"Failed to store tweet node for tweet {node_source_id} from account {account}")
                    
                    # Log action (replace old log_action if necessary)
                    logger.info(f"Checked account {account}, found {len(new_tweets)} new tweets, stored {stored_count} nodes.")
                    
                    # Add a delay between accounts to avoid rate limiting/overloading nitter
                    await asyncio.sleep(5)  # Keep the async sleep
                
                except Exception as e:
                    logger.error(f"Error scanning account {account}: {e}")
        
        finally:
            if conn:
                conn.close()
        logger.info("Finished Twitter scan cycle.")
    
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
