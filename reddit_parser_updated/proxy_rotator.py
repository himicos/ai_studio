"""
Proxy Rotation Module

This module handles proxy rotation for Reddit API requests to avoid rate limiting.
It provides functionality to read proxies from a file and rotate between them.
"""

import random
import requests
import logging
import time
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("proxy_rotation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProxyRotator:
    """
    A class to handle proxy rotation for API requests.
    """
    
    def __init__(self, proxy_file_path="proxies.txt", test_url="https://www.reddit.com"):
        """
        Initialize the proxy rotator.
        
        Args:
            proxy_file_path (str): Path to the file containing proxy IPs
            test_url (str): URL to test proxies against
        """
        self.proxy_file_path = proxy_file_path
        self.test_url = test_url
        self.proxies = []
        self.current_proxy = None
        self.working_proxies = []
        self.failed_proxies = []
        
        # Create empty proxies file if it doesn't exist
        if not os.path.exists(proxy_file_path):
            logger.warning(f"Proxy file {proxy_file_path} not found. Creating empty file.")
            with open(proxy_file_path, 'w') as f:
                f.write("# Add your proxies here in the format: ip:port\n")
        
        # Load proxies from file
        self.load_proxies()
    
    def load_proxies(self):
        """
        Load proxies from the proxy file.
        
        Returns:
            bool: True if proxies were loaded successfully, False otherwise
        """
        try:
            with open(self.proxy_file_path, 'r') as file:
                lines = file.readlines()
                
            # Filter out comments and empty lines
            self.proxies = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
            
            if not self.proxies:
                logger.warning("No proxies found in the proxy file.")
                return False
            
            logger.info(f"Successfully loaded {len(self.proxies)} proxies from {self.proxy_file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
            return False
    
    def get_proxy(self):
        """
        Get a random proxy from the list.
        
        Returns:
            dict: Proxy configuration for requests
        """
        if not self.proxies:
            logger.warning("No proxies available. Returning None.")
            return None
        
        # Prioritize working proxies if available
        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
        else:
            proxy = random.choice(self.proxies)
        
        self.current_proxy = proxy
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}"
        }
        
        logger.info(f"Selected proxy: {proxy}")
        return proxy_dict
    
    def test_proxy(self, proxy):
        """
        Test if a proxy is working.
        
        Args:
            proxy (dict): Proxy configuration for requests
            
        Returns:
            bool: True if proxy is working, False otherwise
        """
        try:
            response = requests.get(
                self.test_url,
                proxies=proxy,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Proxy {self.current_proxy} is working.")
                
                # Add to working proxies if not already there
                if self.current_proxy not in self.working_proxies:
                    self.working_proxies.append(self.current_proxy)
                
                return True
            else:
                logger.warning(f"Proxy {self.current_proxy} returned status code {response.status_code}.")
                return False
        
        except Exception as e:
            logger.error(f"Proxy {self.current_proxy} test failed: {e}")
            
            # Add to failed proxies if not already there
            if self.current_proxy not in self.failed_proxies:
                self.failed_proxies.append(self.current_proxy)
            
            return False
    
    def rotate_proxy(self):
        """
        Rotate to a new proxy.
        
        Returns:
            dict: New proxy configuration for requests
        """
        # Remove current proxy from the list if it failed
        if self.current_proxy in self.failed_proxies and self.current_proxy in self.proxies:
            self.proxies.remove(self.current_proxy)
        
        # Get a new proxy
        new_proxy = self.get_proxy()
        
        # Test the new proxy
        if new_proxy:
            self.test_proxy(new_proxy)
        
        return new_proxy
    
    def make_request(self, url, method="GET", headers=None, data=None, json=None, max_retries=3):
        """
        Make a request using a proxy with automatic rotation on failure.
        
        Args:
            url (str): URL to request
            method (str): HTTP method (GET, POST, etc.)
            headers (dict): HTTP headers
            data (dict): Form data for POST requests
            json (dict): JSON data for POST requests
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            requests.Response: Response object or None if all retries failed
        """
        retries = 0
        
        while retries < max_retries:
            proxy = self.get_proxy()
            
            if not proxy:
                logger.error("No proxies available for request.")
                return None
            
            try:
                logger.info(f"Making {method} request to {url} using proxy {self.current_proxy}")
                
                response = requests.request(
                    method=method,
                    url=url,
                    proxies=proxy,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=30
                )
                
                # Check if we hit a rate limit
                if response.status_code == 429:
                    logger.warning(f"Rate limited. Rotating proxy and retrying. Status code: {response.status_code}")
                    self.rotate_proxy()
                    retries += 1
                    time.sleep(random.uniform(5, 15))  # Random delay before retry
                    continue
                
                # Add to working proxies if successful
                if self.current_proxy not in self.working_proxies:
                    self.working_proxies.append(self.current_proxy)
                
                return response
            
            except Exception as e:
                logger.error(f"Request failed: {e}")
                self.rotate_proxy()
                retries += 1
                time.sleep(random.uniform(5, 15))  # Random delay before retry
        
        logger.error(f"All {max_retries} retry attempts failed.")
        return None

# Example usage
if __name__ == "__main__":
    # Create a sample proxies.txt file with some example proxies
    with open("proxies.txt", "w") as f:
        f.write("# Example proxies - replace with real ones\n")
        f.write("123.123.123.123:8080\n")
        f.write("234.234.234.234:8080\n")
    
    # Initialize the proxy rotator
    rotator = ProxyRotator()
    
    # Get a proxy
    proxy = rotator.get_proxy()
    print(f"Selected proxy: {proxy}")
    
    # Test the proxy
    if proxy:
        is_working = rotator.test_proxy(proxy)
        print(f"Proxy working: {is_working}")
    
    # Make a request with automatic proxy rotation
    response = rotator.make_request("https://www.reddit.com/r/python.json")
    
    if response:
        print(f"Response status code: {response.status_code}")
        print(f"Response size: {len(response.text)} bytes")
    else:
        print("Request failed after all retries.")
