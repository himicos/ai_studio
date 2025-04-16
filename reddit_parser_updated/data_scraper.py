"""
Reddit Data Scraper Module

This module handles the scraping of Reddit data, including posts and comments.
It uses the RedditAPI and ProxyRotator modules to fetch data while avoiding rate limits.
"""

import logging
import time
import random
import json
import os
from datetime import datetime

# Import our custom modules
from reddit_api import RedditAPI
from proxy_rotator import ProxyRotator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditScraper:
    """
    A class to handle scraping of Reddit data.
    """
    
    def __init__(self, reddit_api, proxy_rotator=None):
        """
        Initialize the Reddit scraper.
        
        Args:
            reddit_api (RedditAPI): Instance of the RedditAPI class
            proxy_rotator (ProxyRotator, optional): Instance of the ProxyRotator class
        """
        self.reddit_api = reddit_api
        self.proxy_rotator = proxy_rotator
        self.data_dir = os.path.join(os.getcwd(), "data")
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created data directory: {self.data_dir}")
    
    def scrape_subreddit(self, subreddit_name, limit=100, sort_by="new", time_filter="all", save_to_file=True):
        """
        Scrape posts from a subreddit.
        
        Args:
            subreddit_name (str): Name of the subreddit
            limit (int): Maximum number of posts to fetch
            sort_by (str): Sorting method ('new', 'hot', 'top', 'rising')
            time_filter (str): Time filter for 'top' sorting ('all', 'day', 'week', 'month', 'year')
            save_to_file (bool): Whether to save the scraped data to a file
            
        Returns:
            list: List of dictionaries containing post data
        """
        logger.info(f"Scraping subreddit: r/{subreddit_name}")
        
        # Fetch posts from the subreddit
        try:
            posts = self.reddit_api.get_posts(subreddit_name, limit=limit, sort_by=sort_by, time_filter=time_filter)
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
        except Exception as e:
            logger.error(f"Failed to fetch posts from r/{subreddit_name}: {e}")
            return []
        
        # Process each post
        processed_posts = []
        for i, post in enumerate(posts):
            logger.info(f"Processing post {i+1}/{len(posts)}: {post.id}")
            
            # Extract post data
            post_data = self._extract_post_data(post)
            
            # Add to processed posts
            processed_posts.append(post_data)
            
            # Introduce random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
        
        # Save to file if requested
        if save_to_file:
            self._save_to_file(processed_posts, f"{subreddit_name}_posts.json")
        
        return processed_posts
    
    def scrape_post_comments(self, post_id, subreddit_name=None, limit=None, save_to_file=True):
        """
        Scrape comments from a post.
        
        Args:
            post_id (str): ID of the post
            subreddit_name (str, optional): Name of the subreddit (for file naming)
            limit (int, optional): Maximum number of MoreComments objects to replace
            save_to_file (bool): Whether to save the scraped data to a file
            
        Returns:
            list: List of dictionaries containing comment data
        """
        logger.info(f"Scraping comments for post: {post_id}")
        
        # Get the submission
        try:
            submission = self.reddit_api.reddit.submission(id=post_id)
            logger.info(f"Fetched submission: {submission.title}")
        except Exception as e:
            logger.error(f"Failed to fetch submission {post_id}: {e}")
            return []
        
        # Fetch comments
        try:
            comments = self.reddit_api.get_comments(submission, limit=limit)
            logger.info(f"Fetched {len(comments)} comments from post {post_id}")
        except Exception as e:
            logger.error(f"Failed to fetch comments from post {post_id}: {e}")
            return []
        
        # Process each comment
        processed_comments = []
        for i, comment in enumerate(comments):
            logger.info(f"Processing comment {i+1}/{len(comments)}: {comment.id}")
            
            # Extract comment data
            comment_data = self._extract_comment_data(comment, post_id)
            
            # Add to processed comments
            processed_comments.append(comment_data)
            
            # Introduce random delay to avoid rate limiting
            if i % 10 == 0 and i > 0:  # Every 10 comments
                time.sleep(random.uniform(1, 2))
        
        # Save to file if requested
        if save_to_file:
            filename = f"{post_id}_comments.json"
            if subreddit_name:
                filename = f"{subreddit_name}_{post_id}_comments.json"
            self._save_to_file(processed_comments, filename)
        
        return processed_comments
    
    def search_and_scrape(self, subreddit_name, query, limit=100, sort_by="relevance", time_filter="all", save_to_file=True):
        """
        Search for posts in a subreddit and scrape the results.
        
        Args:
            subreddit_name (str): Name of the subreddit
            query (str): Search query
            limit (int): Maximum number of posts to fetch
            sort_by (str): Sorting method ('relevance', 'hot', 'top', 'new', 'comments')
            time_filter (str): Time filter for results ('all', 'day', 'week', 'month', 'year')
            save_to_file (bool): Whether to save the scraped data to a file
            
        Returns:
            list: List of dictionaries containing post data
        """
        logger.info(f"Searching for '{query}' in r/{subreddit_name}")
        
        # Search for posts
        try:
            posts = self.reddit_api.search_subreddit(subreddit_name, query, limit=limit, sort_by=sort_by, time_filter=time_filter)
            logger.info(f"Found {len(posts)} posts matching '{query}' in r/{subreddit_name}")
        except Exception as e:
            logger.error(f"Failed to search for '{query}' in r/{subreddit_name}: {e}")
            return []
        
        # Process each post
        processed_posts = []
        for i, post in enumerate(posts):
            logger.info(f"Processing search result {i+1}/{len(posts)}: {post.id}")
            
            # Extract post data
            post_data = self._extract_post_data(post)
            
            # Add to processed posts
            processed_posts.append(post_data)
            
            # Introduce random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
        
        # Save to file if requested
        if save_to_file:
            query_filename = query.replace(" ", "_").lower()
            self._save_to_file(processed_posts, f"{subreddit_name}_{query_filename}_search.json")
        
        return processed_posts
    
    def _extract_post_data(self, post):
        """
        Extract relevant data from a post.
        
        Args:
            post (praw.models.Submission): Reddit submission object
            
        Returns:
            dict: Dictionary containing post data
        """
        # Basic post data
        post_data = {
            "id": post.id,
            "title": post.title,
            "author": str(post.author) if post.author else "[deleted]",
            "created_utc": post.created_utc,
            "created_date": datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "permalink": post.permalink,
            "url": post.url,
            "is_self": post.is_self,
            "is_video": post.is_video,
            "is_original_content": post.is_original_content,
            "over_18": post.over_18,
            "spoiler": post.spoiler,
            "stickied": post.stickied,
            "subreddit": post.subreddit.display_name,
            "subreddit_id": post.subreddit_id,
            "subreddit_subscribers": post.subreddit.subscribers,
            "domain": post.domain,
            "selftext": post.selftext if post.is_self else "",
            "selftext_html": post.selftext_html if post.is_self else None,
            "link_flair_text": post.link_flair_text,
            "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Try to get additional attributes that might not be available for all posts
        try:
            post_data["gilded"] = post.gilded
        except:
            post_data["gilded"] = 0
        
        try:
            post_data["total_awards_received"] = post.total_awards_received
        except:
            post_data["total_awards_received"] = 0
        
        return post_data
    
    def _extract_comment_data(self, comment, post_id):
        """
        Extract relevant data from a comment.
        
        Args:
            comment (praw.models.Comment): Reddit comment object
            post_id (str): ID of the parent post
            
        Returns:
            dict: Dictionary containing comment data
        """
        # Basic comment data
        comment_data = {
            "id": comment.id,
            "post_id": post_id,
            "author": str(comment.author) if comment.author else "[deleted]",
            "created_utc": comment.created_utc,
            "created_date": datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "score": comment.score,
            "body": comment.body,
            "body_html": comment.body_html,
            "permalink": comment.permalink,
            "is_submitter": comment.is_submitter,
            "stickied": comment.stickied,
            "parent_id": comment.parent_id,
            "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Try to get additional attributes that might not be available for all comments
        try:
            comment_data["gilded"] = comment.gilded
        except:
            comment_data["gilded"] = 0
        
        try:
            comment_data["total_awards_received"] = comment.total_awards_received
        except:
            comment_data["total_awards_received"] = 0
        
        return comment_data
    
    def _save_to_file(self, data, filename):
        """
        Save data to a JSON file.
        
        Args:
            data (list): Data to save
            filename (str): Name of the file
        """
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Saved data to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save data to {filepath}: {e}")

# Example usage
if __name__ == "__main__":
    # These values should be replaced with actual credentials
    CLIENT_ID = "YOUR_CLIENT_ID"
    CLIENT_SECRET = "YOUR_CLIENT_SECRET"
    USER_AGENT = "python:reddit-topic-parser:v1.0 (by /u/YOUR_USERNAME)"
    
    # Initialize the Reddit API
    reddit_api = RedditAPI(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Initialize the proxy rotator (optional)
    proxy_rotator = ProxyRotator()
    
    # Initialize the Reddit scraper
    scraper = RedditScraper(reddit_api, proxy_rotator)
    
    # Scrape a subreddit
    posts = scraper.scrape_subreddit("python", limit=5)
    
    # Scrape comments from the first post
    if posts:
        comments = scraper.scrape_post_comments(posts[0]["id"], "python")
        
    # Search for posts and scrape the results
    search_results = scraper.search_and_scrape("python", "web scraping", limit=5)
