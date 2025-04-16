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

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.headless = headless
        self.proxy = proxy
        self.driver: Optional[webdriver.Chrome] = None
        self.tabs: Dict[str, webdriver.Chrome] = {}
        # Use only nitter.net
        self.nitter_instance = "https://nitter.net"
        logger.info(f"Using Nitter instance: {self.nitter_instance}")
        
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
        if self.proxy:
            logger.info(f"Configuring proxy: {self.proxy}")
            chrome_options.add_argument(f'--proxy-server={self.proxy}')
        
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
        """Get tweets for a specific user using enhanced browser."""
        if not self.driver:
            try:
                self.driver = self.setup_driver()
            except Exception as setup_err:
                 logger.error(f"Failed to setup driver, cannot get tweets: {setup_err}")
                 return [] # Return empty on setup failure
            
        # Use the hardcoded instance
        url = f"{self.nitter_instance}/{username}"
        logger.info(f"Navigating to Nitter URL: {url}")
        
        try:
            self.driver.get(url)
            
            # Apply navigator.webdriver fix after page load
            logger.info("Applying navigator.webdriver fix...")
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            time.sleep(0.5) # Small delay after script execution

            # Wait for the first tweet item to load within the timeline
            tweet_item_selector = "div.timeline-item" 
            logger.info(f"Waiting for the first tweet item ({tweet_item_selector}) to be present...")
            try:
                WebDriverWait(self.driver, 10).until(  # Reduced from 30 to 10 seconds
                    EC.presence_of_element_located((By.CSS_SELECTOR, tweet_item_selector))
                )
                logger.info("First tweet item found. Finding all tweet bodies...")
            except TimeoutException:
                logger.error(f"Timeout waiting for tweets to load for user {username} on {self.nitter_instance}")
                return []  # Return empty list on timeout
            
            # Find tweet *bodies* now, as they contain content, date, stats
            tweets = []
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.tweet-body") # Find tweet bodies
            logger.info(f"Found {len(tweet_elements)} elements with class 'tweet-body'.")
            
            # Adjust parsing loop to work relative to tweet-body
            for body in tweet_elements[:max_tweets]:
                tweet_id = None 
                tweet_url = None
                timestamp_iso = None
                tweet_stats = {'replies': 0, 'retweets': 0, 'likes': 0, 'quotes': 0 }
                try:
                    # --- Parse ID & URL--- 
                    parent_item = body.find_element(By.XPATH, "..") 
                    link_element = parent_item.find_element(By.CSS_SELECTOR, "a.tweet-link")
                    href = link_element.get_attribute("href")
                    if href:
                        tweet_id = href.split("/")[-1].split("#")[0]
                        # Construct full Nitter URL from relative href
                        tweet_url = f"{self.nitter_instance}{href}" 

                    # --- Parse Content --- 
                    content_element = body.find_element(By.CSS_SELECTOR, "div.tweet-content")
                    # Use JavaScript to get textContent, which often handles complex nodes better
                    tweet_content = self.driver.execute_script("return arguments[0].textContent;", content_element)
                    if tweet_content: 
                        tweet_content = tweet_content.strip()
                    else:
                        tweet_content = "" # Ensure it's an empty string if null/undefined
                        
                    logger.debug(f"Parsed content for tweet {tweet_id}: '{tweet_content[:100]}...'" )

                    # --- Parse Date --- 
                    timestamp_iso = None # Initialize
                    try:
                        date_element = body.find_element(By.CSS_SELECTOR, "span.tweet-date a") 
                        date_title = date_element.get_attribute("title") # e.g., "Apr 14, 2025 · 9:47 PM UTC"
                        if date_title:
                            # Nitter format: Month Day, Year · Hour:Minute AM/PM UTC
                            # Python format code: %b %d, %Y · %I:%M %p UTC
                            date_str_cleaned = date_title.replace(" UTC", "") # Remove UTC suffix
                            # Use strptime with the specific format
                            dt_obj = dt.strptime(date_str_cleaned, "%b %d, %Y · %I:%M %p")
                            # Assume UTC and make timezone-aware
                            dt_obj_utc = pytz.utc.localize(dt_obj)
                            timestamp_iso = dt_obj_utc.isoformat() # Convert to ISO 8601 string
                    except ValueError as date_fmt_err:
                        logger.warning(f"Could not parse date for tweet {tweet_id} using specific format: {date_fmt_err}. Raw: '{date_title}'")
                        timestamp_iso = None # Default to None if parsing fails
                    except Exception as date_err:
                         logger.warning(f"General error parsing date for tweet {tweet_id}: {date_err}")
                         timestamp_iso = None # Default to None if parsing fails

                    # --- Parse Stats --- 
                    try:
                        stats_container = body.find_element(By.CSS_SELECTOR, "div.tweet-stats")
                        stat_spans = stats_container.find_elements(By.CSS_SELECTOR, "span.tweet-stat")
                        for span in stat_spans:
                            icon_div = span.find_element(By.CSS_SELECTOR, "div.icon-container span[class^='icon-']") # Find the icon span
                            icon_class = icon_div.get_attribute("class")
                            stat_text = span.text.strip() # Get the text next to the icon
                            count = 0
                            if stat_text: # Check if there is text (count)
                                try:
                                    count = int(stat_text.replace(",", "")) # Convert text count to int
                                except ValueError:
                                    count = 0 # Default to 0 if text isn't a number
                            
                            if "icon-comment" in icon_class:
                                tweet_stats['replies'] = count
                            elif "icon-retweet" in icon_class:
                                tweet_stats['retweets'] = count
                            elif "icon-heart" in icon_class:
                                tweet_stats['likes'] = count
                            elif "icon-quote" in icon_class:
                                tweet_stats['quotes'] = count
                                
                    except Exception as stats_err:
                        logger.warning(f"Could not parse stats for tweet {tweet_id}: {stats_err}")
                        # Keep default stats if parsing fails
                    
                    # --- Construct Data --- 
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
                         logger.warning("Skipping tweet due to missing ID.")
                         
                except Exception as e:
                    logger.error(f"Error parsing tweet body (ID={tweet_id}): {e}", exc_info=True)
                    continue
                    
            return tweets
            
        except TimeoutException:
            logger.error(f"Timeout waiting for tweets to load for user {username} on {self.nitter_instance}")
            return [] # Return empty list on timeout 
        except WebDriverException as e:
            logger.error(f"Browser error on {self.nitter_instance}: {e}")
            # Optionally try to restart the driver here?
            return []
        except Exception as e:
            logger.error(f"Unexpected error scraping {self.nitter_instance}: {e}", exc_info=True)
            return []
            
    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for users on Nitter and return basic profile info."""
        if not self.driver:
            self.driver = self.setup_driver()
            
        search_url = f"https://nitter.net/search?f=users&q={query}" # Use f=users for user search
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

        profile_url = f"{base_url}/{handle}"
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