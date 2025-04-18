import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
from typing import Optional, Dict, List, Any
import json
import time # Import time for potential delays
import os # Import os for platform-specific operations
import random
from datetime import datetime as dt # Import datetime directly
import pytz # Import pytz for timezone handling
from bs4 import BeautifulSoup
import re
import functools # Add functools import

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, proxy_manager=None, headless=True, use_nitter_instances=True):
        self.proxy_manager = proxy_manager
        self.headless = headless
        self.use_nitter_instances = use_nitter_instances
        self.lock = asyncio.Lock() # Ensure thread safety for browser operations

        # --- Nitter Configuration ---
        # Use environment variable for Nitter URL, fallback to localhost default
        self.nitter_instance = os.environ.get('NITTER_BASE_URL', 'http://localhost:8080').rstrip('/')
        logger.info(f"Using Nitter instance URL: {self.nitter_instance}")
        # ---------------------------

        # Load keywords from DB
        self.keywords = self._load_keywords()
        self.driver: Optional[webdriver.Chrome] = None
        self.tabs: Dict[str, webdriver.Chrome] = {}
        
    def setup_driver(self) -> webdriver.Chrome:
        """Initialize Chrome driver with enhanced anti-detection options."""
        logger.info("Setting up WebDriver with anti-detection...")
        chrome_options = Options()
        
        # Headless and basic stability
        if self.headless:
            # Use the 'new' headless mode which is generally better
            chrome_options.add_argument('--headless=new') 
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--window-size=1920,1080") # Define window size

        # Performance / Reduced Footprint
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging') # Different from excludeSwitches
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false') # Disable images

        # Anti-detection settings from MiraiSniper
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"]) # Combine excludes
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add proxy if configured (existing logic)
        if self.proxy_manager:
            logger.info(f"Configuring proxy: {self.proxy_manager}")
            chrome_options.add_argument(f'--proxy-server={self.proxy_manager}')
        
        try:
            # Initialize the Chrome WebDriver with service
            # Suppress console window using creationflags (Windows specific)
            service_args = []
            creation_flags = 0
            if os.name == 'nt': # Only use creation flags on Windows
                 creation_flags = 0x08000000 # CREATE_NO_WINDOW
                 
            service = Service(ChromeDriverManager().install(), service_args=service_args, creationflags=creation_flags)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout (from MiraiSniper)
            driver.set_page_load_timeout(20) # Using 20s instead of 10s initially
            
            # Apply CDP commands for stealth (from MiraiSniper)
            logger.info("Applying CDP commands for stealth...")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            # The navigator.webdriver fix might need to run on each page load via execute_script
            # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # We will add this execute_script call within get_user_tweets before waiting.
            
            logger.info("Browser initialized successfully with enhanced options.")
            return driver
        except Exception as e:
            logger.error(f"Error setting up browser: {e}", exc_info=True)
            raise
    
    async def get_user_tweets(self, username: str, max_tweets: int = 50) -> List[dict]:
        """Get tweets for a specific user using enhanced browser. Runs blocking Selenium calls in an executor."""
        
        # Run the core blocking logic in an executor
        loop = asyncio.get_running_loop()
        try:
            tweets = await loop.run_in_executor(
                None, # Use default ThreadPoolExecutor
                functools.partial(self._get_user_tweets_sync, username, max_tweets)
            )
            return tweets
        except Exception as e:
            logger.error(f"Error executing _get_user_tweets_sync in executor: {e}", exc_info=True)
            return [] # Return empty list on executor error

    # --- New Synchronous Helper Method --- 
    def _get_user_tweets_sync(self, username: str, max_tweets: int) -> List[dict]:
        """Synchronous helper method containing the blocking Selenium logic."""
        if not self.driver:
            try:
                # Note: setup_driver itself might block briefly, acceptable here as it runs in executor
                self.driver = self.setup_driver() 
            except Exception as setup_err:
                 logger.error(f"Failed to setup driver in executor, cannot get tweets: {setup_err}")
                 return [] 
            
        # Use the hardcoded instance
        url = f"{self.nitter_instance}/{username}"
        logger.info(f"[Executor] Navigating to Nitter URL: {url}")
        
        try:
            self.driver.get(url)
            
            # --- Temporarily comment out the webdriver fix ---
            # logger.info("[Executor] Applying navigator.webdriver fix...")
            # self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # time.sleep(0.5) 
            # --- End temporary comment out ---

            tweet_item_selector = "div.timeline-item" 
            logger.info(f"[Executor] Waiting for the first tweet item ({tweet_item_selector}) ...")
            try:
                # --- Increase Timeout --- 
                WebDriverWait(self.driver, 20).until( # Increased timeout to 20 seconds
                    EC.presence_of_element_located((By.CSS_SELECTOR, tweet_item_selector))
                )
                # --- End Increase Timeout ---
                logger.info("[Executor] First tweet item found. Finding all tweet bodies...")
            except TimeoutException:
                logger.error(f"[Executor] Timeout waiting for tweets for user {username} on {self.nitter_instance}")
                # Optional: Log page source on timeout for debugging selectors
                # try:
                #    logger.debug(f"[Timeout Debug] Page source for {username}:\n{self.driver.page_source[:2000]}")
                # except:
                #    pass 
                return []  
            
            tweets = []
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.tweet-body") 
            logger.info(f"[Executor] Found {len(tweet_elements)} elements with class 'tweet-body'.")
            
            for body in tweet_elements[:max_tweets]:
                tweet_id = None 
                tweet_url = None
                timestamp_iso = None
                tweet_stats = {'replies': 0, 'retweets': 0, 'likes': 0, 'quotes': 0 }
                logger.debug(f"[Executor Scrape Debug] Processing tweet body...") 
                try:
                    parent_item = body.find_element(By.XPATH, "..") 
                    link_element = parent_item.find_element(By.CSS_SELECTOR, "a.tweet-link")
                    href = link_element.get_attribute("href")
                    if href:
                        tweet_id = href.split("/")[-1].split("#")[0]
                        tweet_url = f"{self.nitter_instance}{href}" 

                    content_element = body.find_element(By.CSS_SELECTOR, "div.tweet-content")
                    tweet_content = self.driver.execute_script("return arguments[0].textContent;", content_element)
                    tweet_content = tweet_content.strip() if tweet_content else ""
                    logger.debug(f"[Executor] Parsed content for tweet {tweet_id}: '{tweet_content[:100]}...'" )

                    timestamp_iso = None
                    try:
                        date_element = body.find_element(By.CSS_SELECTOR, "span.tweet-date a") 
                        date_title = date_element.get_attribute("title")
                        if date_title:
                            date_str_cleaned = date_title.replace(" UTC", "")
                            dt_obj = dt.strptime(date_str_cleaned, "%b %d, %Y · %I:%M %p")
                            dt_obj_utc = pytz.utc.localize(dt_obj)
                            timestamp_iso = dt_obj_utc.isoformat()
                    except ValueError as date_fmt_err:
                        logger.warning(f"[Executor] Could not parse date fmt for tweet {tweet_id}: {date_fmt_err}. Raw: '{date_title}'")
                    except Exception as date_err:
                         logger.warning(f"[Executor] General error parsing date for tweet {tweet_id}: {date_err}")
                         timestamp_iso = None

                    try:
                        stats_container = body.find_element(By.CSS_SELECTOR, "div.tweet-stats")
                        stat_spans = stats_container.find_elements(By.CSS_SELECTOR, "span.tweet-stat")
                        for span in stat_spans:
                            icon_div = span.find_element(By.CSS_SELECTOR, "div.icon-container span[class^='icon-']")
                            icon_class = icon_div.get_attribute("class")
                            stat_text = span.text.strip()
                            count = 0
                            if stat_text:
                                try:
                                    count = int(stat_text.replace(",", ""))
                                except ValueError:
                                    count = 0
                            if "icon-comment" in icon_class: tweet_stats['replies'] = count
                            elif "icon-retweet" in icon_class: tweet_stats['retweets'] = count
                            elif "icon-heart" in icon_class: tweet_stats['likes'] = count
                            elif "icon-quote" in icon_class: tweet_stats['quotes'] = count
                        logger.debug(f"[Executor Scrape Debug] Tweet {tweet_id}: Parsed Stats: {tweet_stats}")
                    except Exception as stats_err:
                        logger.warning(f"[Executor] Could not parse stats for tweet {tweet_id}: {stats_err}")
                    
                    tweet_data = {
                        'id': tweet_id,
                        'content': tweet_content,
                        'timestamp_iso': timestamp_iso,
                        'stats': tweet_stats,
                        'url': tweet_url
                    }
                    if tweet_id: 
                         tweets.append(tweet_data)
                    else:
                         logger.warning("[Executor] Skipping tweet due to missing ID.")
                         
                except Exception as e:
                    logger.error(f"[Executor] Error parsing tweet body (ID={tweet_id}): {e}", exc_info=True)
                    continue
                    
            return tweets
            
        except TimeoutException:
            logger.error(f"[Executor] Timeout waiting for tweets for user {username} on {self.nitter_instance}")
            return [] 
        except WebDriverException as e:
            logger.error(f"[Executor] Browser error on {self.nitter_instance}: {e}")
            return []
        except Exception as e:
            logger.error(f"[Executor] Unexpected error scraping {self.nitter_instance}: {e}", exc_info=True)
            return []
    # --- End Synchronous Helper Method --- 
            
    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for users on Nitter and return basic profile info."""
        if not self.driver:
            self.driver = self.setup_driver()
            
        search_url = f"{self.nitter_instance}/search?f=users&q={query}" # Use f=users for user search
        logger.info(f"Navigating to user search: {search_url}")
        
        try:
            self.driver.get(search_url)
            
            # Wait for search results (user profile cards) to load
            # Adjust selector based on Nitter's current structure for user search results
            profile_card_selector = ".timeline-item .profile-card"
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, profile_card_selector))
            )
            
            logger.info(f"User search results loaded for query: {query}")
            
            # Extract user information
            users_found = []
            profile_cards = self.driver.find_elements(By.CSS_SELECTOR, profile_card_selector)
            
            logger.info(f"Found {len(profile_cards)} profile cards.")

            for card in profile_cards[:limit]:
                try:
                    # Extract details - Adjust selectors as needed for Nitter's HTML
                    name_element = card.find_element(By.CSS_SELECTOR, ".fullname")
                    handle_element = card.find_element(By.CSS_SELECTOR, ".username")
                    # Nitter might not expose a stable user ID easily in search results
                    # We might need to derive it or use the handle as a proxy ID initially
                    user_handle = handle_element.text.lstrip('@') # Remove leading @
                    user_name = name_element.text
                    user_id = f"handle_{user_handle}" # Create a temporary ID based on handle
                    
                    user_data = {
                        'id': user_id, 
                        'handle': user_handle,
                        'name': user_name
                    }
                    users_found.append(user_data)
                    # logger.debug(f"Parsed user: {user_data}")
                    
                except Exception as parse_err:
                    logger.error(f"Error parsing profile card for query '{query}': {parse_err}", exc_info=True)
                    continue # Skip this card if parsing fails
                    
            logger.info(f"Successfully parsed {len(users_found)} users for query: {query}")
            return users_found
            
        except TimeoutException:
            logger.warning(f"Timeout waiting for user search results for query '{query}'. No users found or page didn't load.")
            return [] # Return empty list if no results found or timeout
        except WebDriverException as e:
            logger.error(f"Browser error during user search for query '{query}': {e}", exc_info=True)
            return [] # Return empty list on browser errors
        except Exception as e:
            logger.error(f"Unexpected error during user search for query '{query}': {e}", exc_info=True)
            return []

    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.tabs.clear() 

    async def scrape_profile(self, handle: str, base_url: str = "https://nitter.net") -> List[Dict[str, Any]]:
        """Scrapes tweets from a user's profile page on Nitter."""
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot scrape profile.")
            return []

        profile_url = f"{self.nitter_instance}/{handle}"
        logger.info(f"[Scrape Profile] Attempting to scrape profile: {profile_url}")
        
        try:
            self.driver.get(profile_url)
            # Wait for potential redirects and initial page load
            time.sleep(random.uniform(3, 5)) 
            
            page_title = self.driver.title
            logger.info(f"[Scrape Profile] Landed on page with title: '{page_title}' for handle '{handle}'")

            # Scroll down to load more tweets (adjust scrolls and delay as needed)
            for _ in range(2): # Scroll down twice
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4)) # Wait for content to load

            # Wait specifically for tweet elements to appear
            tweet_selector = "div.timeline-item" # Selector might need updating
            logger.debug(f"[Scrape Profile] Waiting for tweet elements using selector: '{tweet_selector}'")
            try:
                 WebDriverWait(self.driver, 15).until(
                     EC.presence_of_element_located((By.CSS_SELECTOR, tweet_selector))
                 )
                 logger.debug(f"[Scrape Profile] Tweet elements ('{tweet_selector}') found for handle '{handle}'.")
            except TimeoutException:
                 logger.error(f"[Scrape Profile] Timeout waiting for tweets ('{tweet_selector}') to load for user {handle} on {profile_url}")
                 # Optionally take a screenshot on timeout
                 # self.save_screenshot(f"timeout_{handle}.png")
                 return [] # Return empty list if tweets don't load

            # Get page source after loading
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find tweet containers
            tweet_elements = soup.select(tweet_selector)
            logger.info(f"[Scrape Profile] Found {len(tweet_elements)} potential tweet elements for {handle}.")

            if not tweet_elements:
                logger.warning(f"[Scrape Profile] No tweet elements found using selector '{tweet_selector}' for {handle} after waiting.")
                # Optionally take a screenshot if no elements found
                # self.save_screenshot(f"no_elements_{handle}.png")
                return []
            
            # Ensure list is not empty before accessing index 0
            if tweet_elements:
                 try:
                     first_tweet_html = tweet_elements[0].prettify()
                     logger.debug(f"[Scrape Profile] Raw HTML of first tweet element found for '{handle}':\n{first_tweet_html}")
                 except IndexError:
                     logger.debug("[Scrape Profile] tweet_elements list was unexpectedly empty after check.")
                 except Exception as log_err:
                     logger.error(f"[Scrape Profile] Error logging first tweet HTML: {log_err}")

            tweets_data = []
            for tweet_element in tweet_elements:
                try:
                    # --- PARSING LOGIC --- 
                    # ... (existing parsing for content, date, stats, url etc.) ...
                    
                    # Ensure data extraction is robust
                    content_element = tweet_element.select_one('.tweet-content')
                    content = content_element.text.strip() if content_element else None
                    
                    # ... (other fields) ...
                    
                    if content: # Basic validation - skip if no content found
                       tweets_data.append({
                           # ... (append extracted data) ...
                       })
                       
                except Exception as parse_err:
                    logger.error(f"Error parsing individual tweet element for {handle}: {parse_err}", exc_info=False) # Less verbose logging for individual errors
                    # Log the problematic element HTML for debugging
                    logger.debug(f"Problematic tweet element HTML:\n{tweet_element.prettify()}")
                    continue # Skip this tweet on error
                    
            logger.info(f"[Scrape Profile] Successfully parsed {len(tweets_data)} tweets for {handle}.")
            return tweets_data

        except TimeoutException:
            logger.error(f"[Scrape Profile] Page load timeout for {profile_url}")
            # self.save_screenshot(f"timeout_page_load_{handle}.png")
            return []
        except Exception as e:
            logger.error(f"[Scrape Profile] Error scraping profile for {handle}: {e}", exc_info=True)
            # Optionally save screenshot on general error
            # self.save_screenshot(f"error_{handle}.png")
            return [] 