"""
Reddit Tracker Module for AI Studio

This module handles Reddit monitoring for AI Studio, including:
- Monitoring subreddits for posts and comments
- Detecting patterns using regex
- Tracking upvotes and score changes over time
- Using proxy rotation to avoid rate limiting
"""

import os
import re
import time
import asyncio
import logging
import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
from dotenv import load_dotenv

# Import our modules
from infra.db import store_post, store_contract, log_action, get_post
from tools.burner_manager import BurnerManager

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class RedditTracker:
    """
    Reddit Tracker for AI Studio.
    
    This class monitors subreddits for posts and comments, detects patterns,
    and tracks upvotes and score changes over time.
    """
    
    def __init__(self):
        """
        Initialize the Reddit tracker.
        """
        # Load configuration from environment variables
        self.subreddits = os.getenv('SUBREDDITS', '').split(',')
        self.subreddits = [s.strip() for s in self.subreddits if s.strip()]
        
        self.keywords = os.getenv('KEYWORDS', '').split(',')
        self.keywords = [k.strip() for k in self.keywords if k.strip()]
        
        # Regex patterns
        self.contract_regex = r"0x[a-fA-F0-9]{40}"
        
        # State tracking
        self.last_post_ids = {}  # subreddit -> post_id
        self.last_check_time = None
        
        # Initialize burner manager
        self.burner_manager = BurnerManager()
        
        logger.info(f"Reddit tracker initialized with {len(self.subreddits)} subreddits and {len(self.keywords)} keywords")
    
    async def get_subreddit_posts(self, subreddit: str, limit: int = 25, sort: str = "new") -> List[Dict[str, Any]]:
        """
        Get posts from a subreddit using the JSON API.
        
        Args:
            subreddit (str): Subreddit name
            limit (int): Maximum number of posts to fetch
            sort (str): Sorting method ('new', 'hot', 'top', 'rising')
            
        Returns:
            list: List of posts
        """
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
        
        try:
            # Make request using burner manager
            response, data = await self.burner_manager.make_async_request(url)
            
            if not response or response.status != 200:
                logger.error(f"Failed to fetch posts from r/{subreddit}: Status {response.status if response else 'None'}")
                return []
            
            # Parse JSON response
            json_data = json.loads(data)
            
            # Extract posts
            posts = []
            for child in json_data.get('data', {}).get('children', []):
                if child.get('kind') == 't3':  # t3 is a post
                    post_data = child.get('data', {})
                    
                    # Create post object
                    post = {
                        'id': f"reddit_{post_data.get('id')}",
                        'source': 'reddit',
                        'title': post_data.get('title', ''),
                        'content': post_data.get('selftext', ''),
                        'author': post_data.get('author', ''),
                        'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                        'score': post_data.get('score', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'created_utc': post_data.get('created_utc', int(datetime.now().timestamp())),
                        'metadata': {
                            'subreddit': post_data.get('subreddit', ''),
                            'post_id': post_data.get('id', ''),
                            'upvote_ratio': post_data.get('upvote_ratio', 0),
                            'is_self': post_data.get('is_self', False),
                            'domain': post_data.get('domain', ''),
                            'link_flair_text': post_data.get('link_flair_text', ''),
                            'platform': 'reddit'
                        }
                    }
                    
                    posts.append(post)
            
            return posts
        
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
            return []
    
    async def get_post_comments(self, post_id: str, subreddit: str) -> List[Dict[str, Any]]:
        """
        Get comments for a post using the JSON API.
        
        Args:
            post_id (str): Post ID
            subreddit (str): Subreddit name
            
        Returns:
            list: List of comments
        """
        # Strip 'reddit_' prefix if present
        if post_id.startswith('reddit_'):
            post_id = post_id[7:]
        
        url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
        
        try:
            # Make request using burner manager
            response, data = await self.burner_manager.make_async_request(url)
            
            if not response or response.status != 200:
                logger.error(f"Failed to fetch comments for post {post_id}: Status {response.status if response else 'None'}")
                return []
            
            # Parse JSON response
            json_data = json.loads(data)
            
            if len(json_data) < 2:
                logger.warning(f"Unexpected response format for post {post_id}")
                return []
            
            # Extract comments
            comments = []
            self._extract_comments(json_data[1].get('data', {}).get('children', []), comments)
            
            return comments
        
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return []
    
    def _extract_comments(self, children: List[Dict[str, Any]], comments: List[Dict[str, Any]], depth: int = 0):
        """
        Recursively extract comments from the JSON response.
        
        Args:
            children (list): List of comment objects
            comments (list): List to store extracted comments
            depth (int): Current depth in the comment tree
        """
        for child in children:
            if child.get('kind') == 't1':  # t1 is a comment
                comment_data = child.get('data', {})
                
                # Create comment object
                comment = {
                    'id': f"reddit_comment_{comment_data.get('id')}",
                    'post_id': f"reddit_{comment_data.get('link_id', '').split('_')[1] if '_' in comment_data.get('link_id', '') else ''}",
                    'parent_id': f"reddit_comment_{comment_data.get('parent_id', '').split('_')[1] if '_' in comment_data.get('parent_id', '') else ''}",
                    'author': comment_data.get('author', ''),
                    'content': comment_data.get('body', ''),
                    'score': comment_data.get('score', 0),
                    'created_utc': comment_data.get('created_utc', int(datetime.now().timestamp())),
                    'depth': depth,
                    'metadata': {
                        'subreddit': comment_data.get('subreddit', ''),
                        'comment_id': comment_data.get('id', ''),
                        'is_submitter': comment_data.get('is_submitter', False),
                        'platform': 'reddit'
                    }
                }
                
                comments.append(comment)
                
                # Process replies
                replies = comment_data.get('replies', {})
                if isinstance(replies, dict) and 'data' in replies:
                    self._extract_comments(replies.get('data', {}).get('children', []), comments, depth + 1)
    
    def process_post(self, post: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a post to detect patterns.
        
        Args:
            post (dict): Post data
            
        Returns:
            list: List of detected items
        """
        detected_items = []
        
        # Combine title and content for pattern matching
        text = f"{post['title']} {post['content']}"
        
        # Check for contract addresses
        contract_matches = re.findall(self.contract_regex, text)
        for contract in contract_matches:
            logger.info(f"Found contract in post: {contract}")
            
            # Create contract object
            contract_obj = {
                'id': f"contract_{contract}_{int(datetime.now().timestamp())}",
                'address': contract,
                'source': 'reddit',
                'source_id': post['id'],
                'detected_at': int(datetime.now().timestamp()),
                'status': 'detected',
                'metadata': {
                    'post_title': post['title'],
                    'post_url': post['url'],
                    'author': post['author'],
                    'subreddit': post['metadata']['subreddit']
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
            if keyword.lower() in text.lower():
                logger.info(f"Found keyword '{keyword}' in post")
                
                # Add to detected items
                detected_items.append({
                    'type': 'keyword',
                    'data': {
                        'keyword': keyword,
                        'post': post
                    }
                })
        
        return detected_items
    
    async def track_post_upvotes(self, post_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Track upvotes for specific posts.
        
        Args:
            post_ids (list): List of post IDs to track
            
        Returns:
            list: List of updated posts
        """
        updated_posts = []
        
        for post_id in post_ids:
            # Strip 'reddit_' prefix if present
            reddit_post_id = post_id
            if post_id.startswith('reddit_'):
                reddit_post_id = post_id[7:]
            
            # Get post from database
            post = get_post(post_id)
            if not post:
                logger.warning(f"Post {post_id} not found in database")
                continue
            
            subreddit = post['metadata'].get('subreddit', '')
            if not subreddit:
                logger.warning(f"Subreddit not found for post {post_id}")
                continue
            
            try:
                # Fetch current post data
                url = f"https://www.reddit.com/r/{subreddit}/comments/{reddit_post_id}.json"
                response, data = await self.burner_manager.make_async_request(url)
                
                if not response or response.status != 200:
                    logger.error(f"Failed to fetch post {post_id}: Status {response.status if response else 'None'}")
                    continue
                
                # Parse JSON response
                json_data = json.loads(data)
                
                if not json_data or len(json_data) < 1:
                    logger.warning(f"Unexpected response format for post {post_id}")
                    continue
                
                # Extract post data
                post_data = json_data[0].get('data', {}).get('children', [])[0].get('data', {})
                
                # Update post
                updated_post = {
                    'id': post_id,
                    'source': 'reddit',
                    'title': post_data.get('title', post['title']),
                    'content': post_data.get('selftext', post['content']),
                    'author': post_data.get('author', post['author']),
                    'url': post['url'],
                    'score': post_data.get('score', post['score']),
                    'num_comments': post_data.get('num_comments', post['num_comments']),
                    'created_utc': post['created_utc'],
                    'metadata': {
                        'subreddit': post_data.get('subreddit', post['metadata'].get('subreddit', '')),
                        'post_id': post_data.get('id', post['metadata'].get('post_id', '')),
                        'upvote_ratio': post_data.get('upvote_ratio', post['metadata'].get('upvote_ratio', 0)),
                        'is_self': post_data.get('is_self', post['metadata'].get('is_self', False)),
                        'domain': post_data.get('domain', post['metadata'].get('domain', '')),
                        'link_flair_text': post_data.get('link_flair_text', post['metadata'].get('link_flair_text', '')),
                        'platform': 'reddit'
                    }
                }
                
                # Store updated post
                store_post(updated_post)
                
                # Add to updated posts
                updated_posts.append(updated_post)
                
                # Log action
                log_action('reddit_tracker', 'track_post_upvotes', f"Updated post {post_id}, score: {updated_post['score']}, comments: {updated_post['num_comments']}")
                
                # Add a delay between posts to avoid rate limiting
                await asyncio.sleep(random.uniform(1, 3))
            
            except Exception as e:
                logger.error(f"Error tracking post {post_id}: {e}")
                log_action('reddit_tracker', 'track_post_upvotes', f"Error tracking post {post_id}: {e}", status='error')
        
        return updated_posts
    
    async def scan(self) -> List[Dict[str, Any]]:
        """
        Scan subreddits for new posts.
        
        Returns:
            list: List of detected items
        """
        all_detected_items = []
        
        for subreddit in self.subreddits:
            logger.info(f"Checking subreddit: r/{subreddit}")
            
            try:
                # Get posts from subreddit
                posts = await self.get_subreddit_posts(subreddit)
                
                # Filter out posts we've already seen
                new_posts = []
                for post in posts:
                    post_id = post['metadata']['post_id']
                    if subreddit not in self.last_post_ids or post_id != self.last_post_ids[subreddit]:
                        new_posts.append(post)
                    else:
                        break
                
                # Update last post ID
                if posts and subreddit not in self.last_post_ids:
                    self.last_post_ids[subreddit] = posts[0]['metadata']['post_id']
                
                # Process new posts
                for post in new_posts:
                    # Store post in database
                    store_post(post)
                    
                    # Process post for patterns
                    detected_items = self.process_post(post)
                    all_detected_items.extend(detected_items)
                
                # Log action
                log_action('reddit_tracker', 'scan_subreddit', f"Checked subreddit r/{subreddit}, found {len(new_posts)} new posts")
                
                # Add a delay between subreddits to avoid rate limiting
                await asyncio.sleep(random.uniform(3, 5))
            
            except Exception as e:
                logger.error(f"Error scanning subreddit r/{subreddit}: {e}")
                log_action('reddit_tracker', 'scan_subreddit', f"Error scanning subreddit r/{subreddit}: {e}", status='error')
        
        return all_detected_items

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Reddit tracker
    tracker = RedditTracker()
    
    # Scan subreddits
    asyncio.run(tracker.scan())
