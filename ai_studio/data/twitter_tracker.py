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
from infra.db import store_post, store_contract, log_action
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
        
        # Initialize browser
        self.setup_browser()
        
        # Initialize burner manager
        self.burner_manager = BurnerManager()
        
        logger.info(f"Twitter tracker initialized with {len(self.twitter_accounts)} accounts and {len(self.keywords)} keywords")
    
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
            
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up browser: {e}")
            if self.driver:
                self.driver.quit()
            raise
    
    def _rotate_instance(self):
        """
        Rotate to next nitter instance.
        """
        self.current_instance = (self.current_instance + 1) % len(self.instances)
        logger.info(f"Switched to instance: {self.instances[self.current_instance]}")
    
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
    
    def process_tweet(self, tweet: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a tweet to detect patterns.
        
        Args:
            tweet (dict): Tweet data
            
        Returns:
            list: List of detected items
        """
        detected_items = []
        tweet_text = tweet['content']
        
        # Check for contract addresses
        contract_matches = re.findall(self.contract_regex, tweet_text)
        for contract in contract_matches:
            logger.info(f"Found contract in tweet: {contract}")
            
            # Create contract object
            contract_obj = {
                'id': f"contract_{contract}_{int(datetime.now().timestamp())}",
                'address': contract,
                'source': 'twitter',
                'source_id': tweet['id'],
                'detected_at': int(datetime.now().timestamp()),
                'status': 'detected',
                'metadata': {
                    'tweet_text': tweet_text,
                    'tweet_url': tweet['url'],
                    'author': tweet['author']
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
    
    async def scan(self) -> List[Dict[str, Any]]:
        """
        Scan Twitter accounts for new tweets.
        
        Returns:
            list: List of detected items
        """
        all_detected_items = []
        
        for account in self.twitter_accounts:
            logger.info(f"Checking account: {account}")
            
            try:
                # Check for new tweets
                new_tweets = self.check_account(account)
                
                # Process new tweets
                for tweet in new_tweets:
                    # Store tweet in database
                    store_post(tweet)
                    
                    # Process tweet for patterns
                    detected_items = self.process_tweet(tweet)
                    all_detected_items.extend(detected_items)
                
                # Log action
                log_action('twitter_tracker', 'scan_account', f"Checked account {account}, found {len(new_tweets)} new tweets")
                
                # Add a delay between accounts to avoid rate limiting
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Error scanning account {account}: {e}")
                log_action('twitter_tracker', 'scan_account', f"Error scanning account {account}: {e}", status='error')
        
        return all_detected_items
    
    def cleanup(self):
        """
        Clean up resources.
        """
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            logger.info("Browser closed")

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
