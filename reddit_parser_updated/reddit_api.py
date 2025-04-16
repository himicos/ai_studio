"""
Reddit API Integration Module

This module handles the integration with Reddit's API using PRAW (Python Reddit API Wrapper).
It provides functionality to connect to Reddit and fetch posts and comments from specified subreddits.
"""

import praw
import time
import random
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reddit_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditAPI:
    """
    A class to handle Reddit API interactions using PRAW.
    """
    
    def __init__(self, client_id, client_secret, user_agent):
        """
        Initialize the Reddit API connection.
        
        Args:
            client_id (str): Reddit API client ID
            client_secret (str): Reddit API client secret
            user_agent (str): User agent string for Reddit API
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        
        # Initialize the Reddit instance
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Successfully connected to Reddit API")
        except Exception as e:
            logger.error(f"Failed to connect to Reddit API: {e}")
            raise
    
    def get_subreddit(self, subreddit_name):
        """
        Get a subreddit instance.
        
        Args:
            subreddit_name (str): Name of the subreddit
            
        Returns:
            praw.models.Subreddit: Subreddit instance
        """
        try:
            return self.reddit.subreddit(subreddit_name)
        except Exception as e:
            logger.error(f"Failed to get subreddit {subreddit_name}: {e}")
            raise
    
    def get_posts(self, subreddit_name, limit=10, sort_by="new", time_filter="all"):
        """
        Get posts from a subreddit.
        
        Args:
            subreddit_name (str): Name of the subreddit
            limit (int): Maximum number of posts to fetch
            sort_by (str): Sorting method ('new', 'hot', 'top', 'rising')
            time_filter (str): Time filter for 'top' sorting ('all', 'day', 'week', 'month', 'year')
            
        Returns:
            list: List of submission objects
        """
        subreddit = self.get_subreddit(subreddit_name)
        
        try:
            if sort_by == "new":
                posts = subreddit.new(limit=limit)
            elif sort_by == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort_by == "top":
                posts = subreddit.top(limit=limit, time_filter=time_filter)
            elif sort_by == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                logger.warning(f"Invalid sort_by value: {sort_by}. Using 'new' instead.")
                posts = subreddit.new(limit=limit)
            
            # Convert generator to list to avoid issues with iteration
            posts_list = list(posts)
            logger.info(f"Successfully fetched {len(posts_list)} posts from r/{subreddit_name}")
            return posts_list
        
        except Exception as e:
            logger.error(f"Failed to fetch posts from r/{subreddit_name}: {e}")
            raise
    
    def get_comments(self, submission, limit=None):
        """
        Get comments from a submission.
        
        Args:
            submission (praw.models.Submission): Reddit submission object
            limit (int, optional): Maximum number of MoreComments objects to replace
            
        Returns:
            list: List of comment objects
        """
        try:
            # Replace MoreComments objects with actual Comment objects
            submission.comments.replace_more(limit=limit)
            comments = submission.comments.list()
            logger.info(f"Successfully fetched {len(comments)} comments from submission {submission.id}")
            return comments
        
        except Exception as e:
            logger.error(f"Failed to fetch comments from submission {submission.id}: {e}")
            raise
    
    def search_subreddit(self, subreddit_name, query, limit=10, sort_by="relevance", time_filter="all"):
        """
        Search for posts in a subreddit based on a query.
        
        Args:
            subreddit_name (str): Name of the subreddit
            query (str): Search query
            limit (int): Maximum number of posts to fetch
            sort_by (str): Sorting method ('relevance', 'hot', 'top', 'new', 'comments')
            time_filter (str): Time filter for results ('all', 'day', 'week', 'month', 'year')
            
        Returns:
            list: List of submission objects matching the query
        """
        subreddit = self.get_subreddit(subreddit_name)
        
        try:
            search_results = subreddit.search(query, sort=sort_by, time_filter=time_filter, limit=limit)
            results_list = list(search_results)
            logger.info(f"Successfully searched for '{query}' in r/{subreddit_name}, found {len(results_list)} results")
            return results_list
        
        except Exception as e:
            logger.error(f"Failed to search for '{query}' in r/{subreddit_name}: {e}")
            raise

# Example usage
if __name__ == "__main__":
    # These values should be replaced with actual credentials
    CLIENT_ID = "YOUR_CLIENT_ID"
    CLIENT_SECRET = "YOUR_CLIENT_SECRET"
    USER_AGENT = "python:reddit-topic-parser:v1.0 (by /u/YOUR_USERNAME)"
    
    # Initialize the Reddit API
    reddit_api = RedditAPI(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Get posts from a subreddit
    posts = reddit_api.get_posts("python", limit=5)
    
    # Print post details
    for post in posts:
        print(f"Title: {post.title}")
        print(f"Score: {post.score}")
        print(f"ID: {post.id}")
        print(f"URL: {post.url}")
        print("-" * 50)
        
        # Get comments for the post
        comments = reddit_api.get_comments(post, limit=0)
        
        # Print first 3 comments
        for i, comment in enumerate(comments[:3]):
            print(f"Comment {i+1}: {comment.body[:100]}...")
            print(f"Score: {comment.score}")
            print()
        
        print("=" * 50)
