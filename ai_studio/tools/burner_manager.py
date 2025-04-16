"""
Burner Manager Module for AI Studio

This module handles proxy rotation and user-agent switching for AI Studio, including:
- Loading proxies and user-agents from configuration
- Rotating between proxies to avoid rate limiting
- Managing HTTP sessions with different identities
- Providing fallback mechanisms when proxies fail
"""

import os
import random
import logging
import time
import json
import asyncio
import aiohttp
import requests
from typing import Dict, List, Optional, Tuple, Union, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class BurnerManager:
    """
    Manages proxy rotation and user-agent switching for API requests.
    
    This class provides functionality to rotate between proxies and user-agents
    to avoid rate limiting and IP bans when making requests to external APIs.
    """
    
    def __init__(self):
        """
        Initialize the burner manager.
        """
        # Load configuration from environment variables
        self.proxies = os.getenv('PROXIES', '').split(',')
        self.proxies = [p.strip() for p in self.proxies if p.strip()]
        
        self.user_agents = os.getenv('USER_AGENTS', '').split(',')
        self.user_agents = [ua.strip() for ua in self.user_agents if ua.strip()]
        
        # Default user agent if none provided
        if not self.user_agents:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        
        self.burner_mode = os.getenv('BURNER_MODE', 'true').lower() == 'true'
        
        # Track working and failed proxies
        self.working_proxies = []
        self.failed_proxies = []
        
        # Current proxy and user agent
        self.current_proxy = None
        self.current_user_agent = None
        
        logger.info(f"Burner manager initialized with {len(self.proxies)} proxies and {len(self.user_agents)} user agents")
        logger.info(f"Burner mode: {self.burner_mode}")
    
    def get_identity(self) -> Tuple[Optional[Dict[str, str]], str]:
        """
        Get a random proxy and user agent.
        
        Returns:
            tuple: (proxy_dict, user_agent)
        """
        # Select a random user agent
        user_agent = random.choice(self.user_agents)
        
        # If burner mode is disabled or no proxies available, return None for proxy
        if not self.burner_mode or not self.proxies:
            return None, user_agent
        
        # Prioritize working proxies if available
        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
        else:
            # Filter out failed proxies
            available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
            if not available_proxies:
                # Reset failed proxies if all have failed
                self.failed_proxies = []
                available_proxies = self.proxies
            
            proxy = random.choice(available_proxies) if available_proxies else None
        
        # Update current proxy and user agent
        self.current_proxy = proxy
        self.current_user_agent = user_agent
        
        # Convert proxy to dictionary format for requests
        proxy_dict = None
        if proxy:
            proxy_dict = {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}"
            }
        
        return proxy_dict, user_agent
    
    def mark_proxy_success(self):
        """
        Mark the current proxy as working.
        """
        if self.current_proxy and self.current_proxy not in self.working_proxies:
            self.working_proxies.append(self.current_proxy)
            if self.current_proxy in self.failed_proxies:
                self.failed_proxies.remove(self.current_proxy)
    
    def mark_proxy_failure(self):
        """
        Mark the current proxy as failed.
        """
        if self.current_proxy:
            if self.current_proxy in self.working_proxies:
                self.working_proxies.remove(self.current_proxy)
            if self.current_proxy not in self.failed_proxies:
                self.failed_proxies.append(self.current_proxy)
    
    def make_request(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, 
                    data: Optional[Any] = None, json_data: Optional[Dict[str, Any]] = None, 
                    max_retries: int = 3) -> Optional[requests.Response]:
        """
        Make a request using a proxy with automatic rotation on failure.
        
        Args:
            url (str): URL to request
            method (str): HTTP method (GET, POST, etc.)
            headers (dict, optional): HTTP headers
            data (any, optional): Form data for POST requests
            json_data (dict, optional): JSON data for POST requests
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            requests.Response: Response object or None if all retries failed
        """
        retries = 0
        
        while retries < max_retries:
            # Get a proxy and user agent
            proxy, user_agent = self.get_identity()
            
            # Prepare headers
            if headers is None:
                headers = {}
            headers['User-Agent'] = user_agent
            
            try:
                logger.debug(f"Making {method} request to {url} using proxy {self.current_proxy}")
                
                response = requests.request(
                    method=method,
                    url=url,
                    proxies=proxy,
                    headers=headers,
                    data=data,
                    json=json_data,
                    timeout=30
                )
                
                # Check if we hit a rate limit
                if response.status_code == 429:
                    logger.warning(f"Rate limited. Rotating proxy and retrying. Status code: {response.status_code}")
                    self.mark_proxy_failure()
                    retries += 1
                    time.sleep(random.uniform(5, 15))  # Random delay before retry
                    continue
                
                # Mark proxy as working
                self.mark_proxy_success()
                
                return response
            
            except Exception as e:
                logger.error(f"Request failed: {e}")
                self.mark_proxy_failure()
                retries += 1
                time.sleep(random.uniform(5, 15))  # Random delay before retry
        
        logger.error(f"All {max_retries} retry attempts failed.")
        return None
    
    async def get_aiohttp_session(self) -> Tuple[aiohttp.ClientSession, bool]:
        """
        Get an aiohttp session with a random proxy and user agent.
        
        Returns:
            tuple: (session, is_proxy_used)
        """
        # Get a proxy and user agent
        proxy, user_agent = self.get_identity()
        
        # Prepare headers
        headers = {
            'User-Agent': user_agent
        }
        
        # Create session
        if proxy:
            session = aiohttp.ClientSession(
                headers=headers,
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=30)
            )
            return session, True
        else:
            session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            return session, False
    
    async def make_async_request(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, 
                               data: Optional[Any] = None, json_data: Optional[Dict[str, Any]] = None, 
                               max_retries: int = 3) -> Optional[aiohttp.ClientResponse]:
        """
        Make an asynchronous request using a proxy with automatic rotation on failure.
        
        Args:
            url (str): URL to request
            method (str): HTTP method (GET, POST, etc.)
            headers (dict, optional): HTTP headers
            data (any, optional): Form data for POST requests
            json_data (dict, optional): JSON data for POST requests
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            aiohttp.ClientResponse: Response object or None if all retries failed
        """
        retries = 0
        
        while retries < max_retries:
            # Get a session with proxy and user agent
            session, is_proxy_used = await self.get_aiohttp_session()
            
            # Prepare headers
            if headers is None:
                headers = {}
            headers['User-Agent'] = self.current_user_agent
            
            try:
                logger.debug(f"Making async {method} request to {url} using proxy {self.current_proxy}")
                
                if method.upper() == "GET":
                    response = await session.get(url, headers=headers)
                elif method.upper() == "POST":
                    if json_data:
                        response = await session.post(url, headers=headers, json=json_data)
                    else:
                        response = await session.post(url, headers=headers, data=data)
                else:
                    response = await session.request(method, url, headers=headers, data=data)
                
                # Check if we hit a rate limit
                if response.status == 429:
                    logger.warning(f"Rate limited. Rotating proxy and retrying. Status code: {response.status}")
                    self.mark_proxy_failure()
                    await session.close()
                    retries += 1
                    await asyncio.sleep(random.uniform(5, 15))  # Random delay before retry
                    continue
                
                # Mark proxy as working
                self.mark_proxy_success()
                
                # Get response data
                response_data = await response.text()
                
                # Close session
                await session.close()
                
                return response, response_data
            
            except Exception as e:
                logger.error(f"Async request failed: {e}")
                if is_proxy_used:
                    self.mark_proxy_failure()
                await session.close()
                retries += 1
                await asyncio.sleep(random.uniform(5, 15))  # Random delay before retry
        
        logger.error(f"All {max_retries} async retry attempts failed.")
        return None, None

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create burner manager
    burner = BurnerManager()
    
    # Example: Make a request
    response = burner.make_request("https://httpbin.org/ip")
    if response:
        print(f"Response: {response.text}")
    
    # Example: Make an async request
    async def test_async():
        response, data = await burner.make_async_request("https://httpbin.org/ip")
        if response:
            print(f"Async response: {data}")
    
    asyncio.run(test_async())
