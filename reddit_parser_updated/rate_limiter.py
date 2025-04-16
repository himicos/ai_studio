"""
Rate Limiter Module

This module handles rate limiting and error handling for Reddit API requests.
It provides functionality to manage request rates and handle errors gracefully.
"""

import time
import random
import logging
import requests
from functools import wraps
import backoff
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rate_limiter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A class to handle rate limiting for API requests.
    """
    
    def __init__(self, requests_per_minute=30, burst_limit=60):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute (int): Maximum number of requests per minute
            burst_limit (int): Maximum number of requests in a burst
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_timestamps = []
        self.last_request_time = None
        self.min_interval = 60.0 / requests_per_minute  # Minimum time between requests in seconds
    
    def wait_if_needed(self):
        """
        Wait if necessary to comply with rate limits.
        
        Returns:
            float: Time waited in seconds
        """
        now = time.time()
        
        # Clean up old timestamps (older than 1 minute)
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
        
        # Check if we've hit the burst limit
        if len(self.request_timestamps) >= self.burst_limit:
            wait_time = 60 - (now - self.request_timestamps[0])
            if wait_time > 0:
                logger.warning(f"Burst limit reached. Waiting {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                now = time.time()  # Update current time after waiting
        
        # Check if we need to wait based on the minimum interval
        if self.last_request_time is not None:
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                
                # Add some jitter to avoid synchronized requests
                jitter = random.uniform(0, 1)
                wait_time += jitter
                
                logger.info(f"Rate limiting. Waiting {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                now = time.time()  # Update current time after waiting
                return wait_time + jitter
        
        # Record this request
        self.request_timestamps.append(now)
        self.last_request_time = now
        return 0.0
    
    def __call__(self, func):
        """
        Decorator to apply rate limiting to a function.
        
        Args:
            func: Function to decorate
            
        Returns:
            function: Decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper


# Define custom exceptions
class RedditAPIError(Exception):
    """Base exception for Reddit API errors."""
    pass

class RateLimitError(RedditAPIError):
    """Exception raised when rate limited by Reddit."""
    pass

class AuthenticationError(RedditAPIError):
    """Exception raised when authentication fails."""
    pass

class NetworkError(RedditAPIError):
    """Exception raised when network issues occur."""
    pass

class NotFoundError(RedditAPIError):
    """Exception raised when a resource is not found."""
    pass

class ServerError(RedditAPIError):
    """Exception raised when Reddit servers have an error."""
    pass


# Define backoff strategies
def backoff_hdlr(details):
    """Handler for backoff events."""
    logger.warning(
        f"Backing off {details['wait']:.2f} seconds after {details['tries']} tries "
        f"calling function {details['target'].__name__} with args {details['args']} and kwargs "
        f"{details['kwargs']}"
    )

def rate_limit_giveup(e):
    """Determine when to give up on rate limit errors."""
    # Don't give up on rate limit errors, keep retrying
    return False

def network_giveup(e):
    """Determine when to give up on network errors."""
    # Give up after 5 minutes of continuous network errors
    if not hasattr(network_giveup, 'first_error_time'):
        network_giveup.first_error_time = datetime.now()
    
    # If it's been more than 5 minutes since the first error, give up
    if datetime.now() - network_giveup.first_error_time > timedelta(minutes=5):
        logger.error("Giving up after 5 minutes of continuous network errors.")
        return True
    
    return False

def server_giveup(e):
    """Determine when to give up on server errors."""
    # Give up on 500 errors after 10 retries
    if hasattr(server_giveup, 'retries'):
        server_giveup.retries += 1
    else:
        server_giveup.retries = 1
    
    if server_giveup.retries > 10:
        logger.error("Giving up after 10 retries on server errors.")
        return True
    
    return False


# Define decorators for error handling with backoff
def handle_rate_limit_errors(func):
    """
    Decorator to handle rate limit errors with exponential backoff.
    
    Args:
        func: Function to decorate
        
    Returns:
        function: Decorated function
    """
    @backoff.on_exception(
        backoff.expo,
        RateLimitError,
        max_time=300,  # 5 minutes max
        on_backoff=backoff_hdlr,
        giveup=rate_limit_giveup
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Get the 'Retry-After' header if available
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    try:
                        # Convert to float and add some buffer
                        retry_after = float(retry_after) + 5
                        logger.warning(f"Rate limited. Retry after {retry_after} seconds.")
                        time.sleep(retry_after)
                    except (ValueError, TypeError):
                        pass
                
                raise RateLimitError(f"Rate limited by Reddit: {e}")
            raise
    return wrapper

def handle_network_errors(func):
    """
    Decorator to handle network errors with exponential backoff.
    
    Args:
        func: Function to decorate
        
    Returns:
        function: Decorated function
    """
    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_time=300,  # 5 minutes max
        on_backoff=backoff_hdlr,
        giveup=network_giveup
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise NetworkError(f"Network error: {e}")
    return wrapper

def handle_server_errors(func):
    """
    Decorator to handle server errors with exponential backoff.
    
    Args:
        func: Function to decorate
        
    Returns:
        function: Decorated function
    """
    @backoff.on_exception(
        backoff.expo,
        ServerError,
        max_time=300,  # 5 minutes max
        on_backoff=backoff_hdlr,
        giveup=server_giveup
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if 500 <= e.response.status_code < 600:
                raise ServerError(f"Reddit server error: {e}")
            raise
    return wrapper

def handle_all_errors(func):
    """
    Decorator to handle all types of errors with appropriate strategies.
    
    Args:
        func: Function to decorate
        
    Returns:
        function: Decorated function
    """
    @handle_rate_limit_errors
    @handle_network_errors
    @handle_server_errors
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 or e.response.status_code == 403:
                raise AuthenticationError(f"Authentication error: {e}")
            elif e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {e}")
            else:
                raise RedditAPIError(f"Reddit API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    return wrapper


# Example usage
if __name__ == "__main__":
    # Create a rate limiter
    limiter = RateLimiter(requests_per_minute=30)
    
    # Example function with rate limiting and error handling
    @limiter
    @handle_all_errors
    def make_reddit_request(url):
        """
        Make a request to Reddit API with rate limiting and error handling.
        
        Args:
            url (str): URL to request
            
        Returns:
            requests.Response: Response object
        """
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        return response
    
    # Test the function
    try:
        # This would normally hit rate limits without our limiter
        for i in range(5):
            logger.info(f"Making request {i+1}")
            response = make_reddit_request("https://www.reddit.com/r/python/about.json")
            logger.info(f"Response status: {response.status_code}")
            
            # Process the response
            data = response.json()
            logger.info(f"Subreddit subscribers: {data['data']['subscribers']}")
    except Exception as e:
        logger.error(f"Error: {e}")
