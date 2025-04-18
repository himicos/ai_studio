import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
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
from urllib.parse import urljoin, quote_plus
import requests

from ai_studio_package.infra.db_enhanced import get_db_connection

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        """Initialize the browser manager."""
        self.driver = None
        self.nitter_instance = os.getenv('NITTER_BASE_URL', 'http://localhost:8080')
        
        # Configure connection pool with higher limits
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,  # Increased from default
            pool_maxsize=30,     # Increased from default
            max_retries=3,       # Add retries
            pool_block=False     # Don't block when pool is full
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        logger.info("Browser manager initialized with enhanced connection pool")
        
    def _init_driver(self):
        """Initialize the browser driver if not already initialized."""
        if not self.driver:
            try:
                options = webdriver.ChromeOptions()
                
                # Basic headless setup
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                # Additional stability options
                options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-logging')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-default-apps')
                options.add_argument('--disable-popup-blocking')
                options.add_argument('--ignore-certificate-errors')
                options.add_argument('--log-level=3')  # Only show fatal errors
                
                # Memory and performance options
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-features=TranslateUI')
                options.add_argument('--disable-web-security')
                options.add_argument('--disable-site-isolation-trials')
                options.add_argument('--memory-pressure-off')
                
                # Create service with specific args
                service = Service(
                    ChromeDriverManager().install(),
                    service_args=['--verbose', '--log-path=chromedriver.log']
                )
                
                # Initialize driver with options and service
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.set_page_load_timeout(30)  # Increased timeout
                
                # Apply CDP commands for enhanced browser control
                self.driver.execute_cdp_cmd('Network.enable', {})
                self.driver.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
                
                logger.info("Browser initialized successfully with enhanced options")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize browser: {e}", exc_info=True)
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                return False
        return True

    def _apply_cdp_commands(self):
        """Apply CDP commands to make the browser more stealthy."""
        try:
            # Set user agent
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Hide webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Additional stealth settings
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32'
                    });
                """
            })
            
            logger.info("CDP commands applied successfully")
        except Exception as e:
            logger.error(f"Error applying CDP commands: {e}")
            raise

    def _load_keywords(self) -> List[str]:
        # ... implementation ...
        return [] # Placeholder
        
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
    
    async def get_driver(self) -> webdriver.Chrome:
        async with self.lock:
            if not self.driver or not self._is_driver_alive():
                logger.info("Driver not initialized or not alive. Setting up new driver.")
                if self.driver: # Close dead driver if exists
                    try: 
                        self.driver.quit()
                    except: pass # Ignore errors quitting old driver
                self.driver = await asyncio.to_thread(self.setup_driver)
            return self.driver
            
    def _is_driver_alive(self) -> bool:
        if not self.driver:
            return False
        try:
            # Check a simple property
            _ = self.driver.title
            # Optionally ping window handles
            return len(self.driver.window_handles) > 0
        except WebDriverException as e:
            logger.warning(f"Driver seems dead: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking driver status: {e}")
            return False # Assume dead on unexpected errors

    async def get_user_tweets(self, username: str, max_tweets: int = 50) -> List[dict]:
        """Get tweets for a specific user using enhanced browser. Runs blocking Selenium calls in an executor."""
        self._init_driver()  # Ensure driver is initialized
        if not self.driver:
            logger.error("Failed to get WebDriver instance.")
            return []

        try:
            # Run the synchronous scraping logic in a separate thread
            loop = asyncio.get_running_loop()
            tweets = await loop.run_in_executor(
                None, # Use default executor
                self._sync_get_user_tweets, # The sync function to run
                username, 
                max_tweets
            )
            return tweets
        except Exception as e:
            logger.error(f"Error in executor running _sync_get_user_tweets for {username}: {e}", exc_info=True)
            return []
            
    def _convert_nitter_to_twitter_url(self, nitter_url: str) -> str:
        """Convert a Nitter URL to a Twitter/X.com URL."""
        try:
            # Extract username and tweet ID from Nitter URL
            # Example: http://localhost:8080/username/status/123456 -> https://x.com/username/status/123456
            parts = nitter_url.split('/')
            username_idx = parts.index(parts[-3])  # Get username part
            username = parts[username_idx]
            tweet_id = parts[-1].split('#')[0]  # Remove any anchor
            return f"https://x.com/{username}/status/{tweet_id}"
        except Exception as e:
            logger.error(f"Error converting Nitter URL {nitter_url}: {e}")
            return nitter_url

    def _sync_get_user_tweets(self, username: str, max_tweets: int = 50) -> List[dict]:
        """Synchronous helper to get tweets with improved error handling."""
        if not self._init_driver():
            logger.error("[Executor] Failed to initialize driver")
            return []
            
        tweets = []
        processed_tweet_ids = set()
        user_url = f"{self.nitter_instance}/{username}"
        logger.info(f"[Executor] Navigating to: {user_url}")

        try:
            self.driver.get(user_url)
            wait = WebDriverWait(self.driver, 30)  # Increased timeout
            
            # Wait for timeline container
            timeline = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".timeline")))
            logger.info(f"[Executor] Timeline container found for {username}")

            # Process tweets with better error handling
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
            for element in tweet_elements[:max_tweets]:
                try:
                    # Check for pinned tweet using JavaScript
                    is_pinned = self.driver.execute_script(
                        "return arguments[0].querySelector('.pinned') !== null",
                        element
                    )
                    if is_pinned:
                        continue
                        
                    # Get tweet link and ID
                    permalink = element.find_element(By.CSS_SELECTOR, ".tweet-link")
                    nitter_url = permalink.get_attribute("href")
                    if not nitter_url:
                        continue
                        
                    # Convert to absolute URL if relative
                    if not nitter_url.startswith('http'):
                        nitter_url = urljoin(self.nitter_instance, nitter_url)
                        
                    # Extract tweet ID and convert to x.com URL
                    tweet_id = nitter_url.split('/')[-1].split('#')[0]
                    if not tweet_id or tweet_id in processed_tweet_ids:
                        continue

                    # Get the actual author handle from the tweet
                    try:
                        author_element = element.find_element(By.CSS_SELECTOR, ".username")
                        author = author_element.text.strip().lstrip('@')
                    except NoSuchElementException:
                        author = username  # Fallback to the username we're scraping
                        
                    tweet_data = {
                        'id': tweet_id,
                        'url': self._convert_nitter_to_twitter_url(nitter_url),
                        'author': author,  # Use the actual author from the tweet
                        'username': username  # Keep original username for reference
                    }

                    # Get tweet content
                    try:
                        content_element = element.find_element(By.CSS_SELECTOR, ".tweet-content")
                        tweet_data['content'] = content_element.text.strip()
                    except NoSuchElementException:
                        continue  # Skip tweets without content

                    # Get timestamp
                    try:
                        ts_element = element.find_element(By.CSS_SELECTOR, ".tweet-date > a")
                        tweet_data['timestamp_str'] = ts_element.get_attribute('title')
                    except NoSuchElementException:
                        tweet_data['timestamp_str'] = None

                    # Get tweet stats
                    stats_map = {'comment': 0, 'retweet': 0, 'quote': 0, 'like': 0}
                    try:
                        stats_container = element.find_element(By.CSS_SELECTOR, ".tweet-stats")
                        stat_elements = stats_container.find_elements(By.CSS_SELECTOR, ".tweet-stat")
                        for stat_elem in stat_elements:
                            icon_element = stat_elem.find_element(By.CSS_SELECTOR, ".icon-container span[class*='icon-']")
                            icon_class = icon_element.get_attribute('class')
                            count_text = stat_elem.text.strip().replace(',', '')
                            count = int(count_text) if count_text.isdigit() else 0
                            
                            if 'icon-comment' in icon_class: stats_map['comment'] = count
                            elif 'icon-retweet' in icon_class: stats_map['retweet'] = count
                            elif 'icon-quote' in icon_class: stats_map['quote'] = count
                            elif any(x in icon_class for x in ['icon-like', 'icon-heart']): stats_map['like'] = count
                    except NoSuchElementException:
                        pass
                    tweet_data['stats'] = stats_map

                    tweets.append(tweet_data)
                    processed_tweet_ids.add(tweet_id)
                    
                except Exception as e:
                    logger.error(f"[Executor] Error processing tweet: {str(e)}")
                    continue
                    
            return tweets
            
        except TimeoutException as te:
            logger.error(f"[Executor] Timeout loading page for {username}: {te}")
            return []
        except Exception as e:
            logger.error(f"[Executor] Error scraping tweets for {username}: {e}", exc_info=True)
            return []
        finally:
            # Ensure we're not leaving any stale connections
            if hasattr(self, 'session'):
                self.session.close()

    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for users on Nitter and return basic profile info."""
        driver = await self.get_driver()
        if not driver:
            logger.error("Failed to get WebDriver instance for user search.")
            return []
            
        search_url = f"{self.nitter_instance}/search?f=users&q={quote_plus(query)}" 
        logger.info(f"Navigating to user search: {search_url}")
        users = []

        try:
            await asyncio.to_thread(driver.get, search_url)
            
            # Use asyncio.to_thread for WebDriver waits within async function
            wait = WebDriverWait(driver, 15)
            user_elements = await asyncio.to_thread(
                wait.until, 
                EC.presence_of_all_elements_located((By.CLASS_NAME, "profile-card"))
            )
            
            logger.info(f"Found {len(user_elements)} potential user elements for query '{query}'. Limiting to {limit}")

            # Process elements - keep this part synchronous as it reads properties
            for user_elem in user_elements[:limit]:
                try:
                    # These are synchronous Selenium calls, okay within this loop after async wait
                    handle_elem = user_elem.find_element(By.CLASS_NAME, "profile-card-username")
                    handle = handle_elem.text.strip("@")
                    
                    name_elem = user_elem.find_element(By.CLASS_NAME, "profile-card-fullname")
                    name = name_elem.text.strip()
                    
                    profile_link_elem = user_elem.find_element(By.CLASS_NAME, "profile-card-link")
                    profile_url_path = profile_link_elem.get_attribute("href")
                    # Ensure the profile URL is absolute
                    profile_url = urljoin(search_url, profile_url_path)
                    
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
                    logger.error(f"Error processing user element: {e}", exc_info=True)
                    continue # Skip this user if parsing fails
            
            logger.info(f"Successfully processed {len(users)} users for query '{query}'.")
            return users
        
        except TimeoutException:
            logger.error(f"Timeout accessing search URL: {search_url}")
            return []
        except WebDriverException as e:
            logger.error(f"Browser error during user search: {e}")
            # Consider attempting driver restart if appropriate
            return []
        except Exception as e:
             logger.error(f"Unexpected error during user search for '{query}': {e}", exc_info=True)
             return []

    async def close_driver(self):
        """Close the WebDriver instance if it exists."""
        async with self.lock:
            if self.driver:
                logger.info("Closing WebDriver instance.")
                try:
                    await asyncio.to_thread(self.driver.quit)
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {e}")
                finally:
                    self.driver = None

    def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as quit_error:
                    logger.error(f"Error during driver quit: {quit_error}")
                finally:
                    self.driver = None
                    
            if hasattr(self, 'session'):
                try:
                    self.session.close()
                except Exception as session_error:
                    logger.error(f"Error closing session: {session_error}")
                    
            logger.info("Browser resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}", exc_info=True)

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