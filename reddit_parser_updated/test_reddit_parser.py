"""
Test script for the Reddit Topic Parser

This script tests the functionality of the Reddit Topic Parser components.
"""

import os
import sys
import logging
import unittest
import json
from unittest.mock import MagicMock, patch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from reddit_api import RedditAPI
from proxy_rotator import ProxyRotator
from data_scraper import RedditScraper
from database import RedditDatabase
from rate_limiter import RateLimiter
from reddit_parser import RedditTopicParser

class TestRedditParser(unittest.TestCase):
    """
    Test cases for the Reddit Topic Parser.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample proxies file
        with open("test_proxies.txt", "w") as f:
            f.write("# Test proxies\n")
            f.write("127.0.0.1:8080\n")
            f.write("127.0.0.1:8081\n")
        
        # Mock Reddit API credentials
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.user_agent = "test_user_agent"
        
        # Use an in-memory database for testing
        self.db_path = ":memory:"
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove test files
        if os.path.exists("test_proxies.txt"):
            os.remove("test_proxies.txt")
        
        # Remove any other test files
        for file in os.listdir("."):
            if file.startswith("test_") and file.endswith(".json"):
                os.remove(file)
    
    @patch('praw.Reddit')
    def test_reddit_api_initialization(self, mock_reddit):
        """Test Reddit API initialization."""
        # Set up the mock
        mock_reddit.return_value = MagicMock()
        
        # Initialize the Reddit API
        reddit_api = RedditAPI(self.client_id, self.client_secret, self.user_agent)
        
        # Check if Reddit was initialized with the correct parameters
        mock_reddit.assert_called_once_with(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
        
        # Check if the Reddit instance was stored
        self.assertIsNotNone(reddit_api.reddit)
    
    def test_proxy_rotator_initialization(self):
        """Test proxy rotator initialization."""
        # Initialize the proxy rotator
        rotator = ProxyRotator("test_proxies.txt")
        
        # Check if proxies were loaded
        self.assertEqual(len(rotator.proxies), 2)
        self.assertIn("127.0.0.1:8080", rotator.proxies)
        self.assertIn("127.0.0.1:8081", rotator.proxies)
    
    def test_proxy_rotator_get_proxy(self):
        """Test proxy rotator get_proxy method."""
        # Initialize the proxy rotator
        rotator = ProxyRotator("test_proxies.txt")
        
        # Get a proxy
        proxy = rotator.get_proxy()
        
        # Check if the proxy is in the correct format
        self.assertIsInstance(proxy, dict)
        self.assertIn("http", proxy)
        self.assertIn("https", proxy)
        
        # Check if the proxy is one of the loaded proxies
        http_proxy = proxy["http"].replace("http://", "")
        self.assertIn(http_proxy, rotator.proxies)
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Initialize the database
        db = RedditDatabase(self.db_path)
        
        # Check if the connection was established
        self.assertIsNotNone(db.conn)
        self.assertIsNotNone(db.cursor)
        
        # Close the database connection
        db.close()
    
    def test_database_store_post(self):
        """Test database store_post method."""
        # Initialize the database
        db = RedditDatabase(self.db_path)
        
        # Create a sample post
        post_data = {
            "id": "test_post_id",
            "title": "Test Post",
            "author": "test_author",
            "created_utc": 1617235200.0,
            "score": 42,
            "upvote_ratio": 0.95,
            "num_comments": 10,
            "permalink": "/r/test/comments/test_post_id/test_post/",
            "url": "https://www.reddit.com/r/test/comments/test_post_id/test_post/",
            "is_self": True,
            "is_video": False,
            "is_original_content": False,
            "over_18": False,
            "spoiler": False,
            "stickied": False,
            "subreddit": "test",
            "subreddit_id": "t5_2qh23",
            "domain": "self.test",
            "selftext": "This is a test post.",
            "selftext_html": "<div>This is a test post.</div>",
            "link_flair_text": "Test",
            "gilded": 0,
            "total_awards_received": 0,
            "scraped_at": "2025-04-06 00:00:00"
        }
        
        # Store the post
        result = db.store_post(post_data)
        
        # Check if the post was stored successfully
        self.assertTrue(result)
        
        # Retrieve the post
        db.cursor.execute("SELECT * FROM posts WHERE id = ?", ("test_post_id",))
        post = db.cursor.fetchone()
        
        # Check if the post was retrieved successfully
        self.assertIsNotNone(post)
        self.assertEqual(post["id"], "test_post_id")
        self.assertEqual(post["title"], "Test Post")
        self.assertEqual(post["score"], 42)
        
        # Close the database connection
        db.close()
    
    def test_database_store_comment(self):
        """Test database store_comment method."""
        # Initialize the database
        db = RedditDatabase(self.db_path)
        
        # Create a sample post first
        post_data = {
            "id": "test_post_id",
            "title": "Test Post",
            "author": "test_author",
            "created_utc": 1617235200.0,
            "score": 42,
            "upvote_ratio": 0.95,
            "num_comments": 10,
            "permalink": "/r/test/comments/test_post_id/test_post/",
            "url": "https://www.reddit.com/r/test/comments/test_post_id/test_post/",
            "is_self": True,
            "is_video": False,
            "is_original_content": False,
            "over_18": False,
            "spoiler": False,
            "stickied": False,
            "subreddit": "test",
            "subreddit_id": "t5_2qh23",
            "domain": "self.test",
            "selftext": "This is a test post.",
            "selftext_html": "<div>This is a test post.</div>",
            "link_flair_text": "Test",
            "gilded": 0,
            "total_awards_received": 0,
            "scraped_at": "2025-04-06 00:00:00"
        }
        db.store_post(post_data)
        
        # Create a sample comment
        comment_data = {
            "id": "test_comment_id",
            "post_id": "test_post_id",
            "author": "test_commenter",
            "created_utc": 1617235300.0,
            "score": 15,
            "body": "This is a test comment.",
            "body_html": "<div>This is a test comment.</div>",
            "permalink": "/r/test/comments/test_post_id/test_post/test_comment_id/",
            "is_submitter": False,
            "stickied": False,
            "parent_id": "t3_test_post_id",
            "gilded": 0,
            "total_awards_received": 0,
            "scraped_at": "2025-04-06 00:00:00"
        }
        
        # Store the comment
        result = db.store_comment(comment_data)
        
        # Check if the comment was stored successfully
        self.assertTrue(result)
        
        # Retrieve the comment
        db.cursor.execute("SELECT * FROM comments WHERE id = ?", ("test_comment_id",))
        comment = db.cursor.fetchone()
        
        # Check if the comment was retrieved successfully
        self.assertIsNotNone(comment)
        self.assertEqual(comment["id"], "test_comment_id")
        self.assertEqual(comment["post_id"], "test_post_id")
        self.assertEqual(comment["body"], "This is a test comment.")
        self.assertEqual(comment["score"], 15)
        
        # Close the database connection
        db.close()
    
    def test_rate_limiter(self):
        """Test rate limiter."""
        # Initialize the rate limiter
        limiter = RateLimiter(requests_per_minute=60)
        
        # Test the wait_if_needed method
        start_time = time.time()
        wait_time = limiter.wait_if_needed()
        elapsed_time = time.time() - start_time
        
        # The first call should not wait
        self.assertLessEqual(elapsed_time, 0.1)
        
        # Test the decorator
        @limiter
        def test_function():
            return "test"
        
        # Call the decorated function
        result = test_function()
        
        # Check if the function returned the correct result
        self.assertEqual(result, "test")
    
    @patch('praw.Reddit')
    @patch('proxy_rotator.ProxyRotator.get_proxy')
    @patch('database.RedditDatabase.store_post')
    @patch('database.RedditDatabase.store_comment')
    def test_reddit_topic_parser(self, mock_store_comment, mock_store_post, mock_get_proxy, mock_reddit):
        """Test the main RedditTopicParser class."""
        # Set up the mocks
        mock_reddit.return_value = MagicMock()
        mock_get_proxy.return_value = {"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}
        mock_store_post.return_value = True
        mock_store_comment.return_value = True
        
        # Initialize the Reddit Topic Parser
        parser = RedditTopicParser(
            self.client_id,
            self.client_secret,
            self.user_agent,
            "test_proxies.txt",
            self.db_path
        )
        
        # Check if all components were initialized
        self.assertIsNotNone(parser.reddit_api)
        self.assertIsNotNone(parser.proxy_rotator)
        self.assertIsNotNone(parser.rate_limiter)
        self.assertIsNotNone(parser.scraper)
        self.assertIsNotNone(parser.db)
        
        # Close the parser
        parser.close()

if __name__ == "__main__":
    unittest.main()
