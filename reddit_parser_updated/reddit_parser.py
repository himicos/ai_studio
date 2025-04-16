"""
Reddit Topic Parser with Upvotes Tracking

This is the main module that integrates all components of the Reddit Topic Parser.
It provides a command-line interface to scrape Reddit data, track upvotes, and store data in a database.
"""

import os
import sys
import argparse
import logging
import time
import json
import random
from datetime import datetime

# Import our custom modules
from reddit_api import RedditAPI
from proxy_rotator import ProxyRotator
from data_scraper import RedditScraper
from database import RedditDatabase
from rate_limiter import RateLimiter, handle_all_errors

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reddit_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditTopicParser:
    """
    Main class that integrates all components of the Reddit Topic Parser.
    """
    
    def __init__(self, client_id, client_secret, user_agent, proxy_file=None, db_path="reddit_data.db"):
        """
        Initialize the Reddit Topic Parser.
        
        Args:
            client_id (str): Reddit API client ID
            client_secret (str): Reddit API client secret
            user_agent (str): User agent string for Reddit API
            proxy_file (str, optional): Path to the proxy file
            db_path (str): Path to the SQLite database file
        """
        logger.info("Initializing Reddit Topic Parser")
        
        # Initialize the Reddit API
        self.reddit_api = RedditAPI(client_id, client_secret, user_agent)
        logger.info("Reddit API initialized")
        
        # Initialize the proxy rotator if a proxy file is provided
        self.proxy_rotator = None
        if proxy_file:
            self.proxy_rotator = ProxyRotator(proxy_file)
            logger.info(f"Proxy rotator initialized with {proxy_file}")
        
        # Initialize the rate limiter
        self.rate_limiter = RateLimiter()
        logger.info("Rate limiter initialized")
        
        # Initialize the data scraper
        self.scraper = RedditScraper(self.reddit_api, self.proxy_rotator)
        logger.info("Data scraper initialized")
        
        # Initialize the database
        self.db = RedditDatabase(db_path)
        logger.info(f"Database initialized at {db_path}")
    
    def parse_subreddit(self, subreddit_name, limit=100, sort_by="new", time_filter="all", store_comments=True, comments_limit=None):
        """
        Parse posts from a subreddit and store them in the database.
        
        Args:
            subreddit_name (str): Name of the subreddit
            limit (int): Maximum number of posts to fetch
            sort_by (str): Sorting method ('new', 'hot', 'top', 'rising')
            time_filter (str): Time filter for 'top' sorting ('all', 'day', 'week', 'month', 'year')
            store_comments (bool): Whether to store comments for each post
            comments_limit (int, optional): Maximum number of MoreComments objects to replace
            
        Returns:
            dict: Summary of the parsing operation
        """
        logger.info(f"Parsing subreddit: r/{subreddit_name}")
        start_time = time.time()
        
        # Scrape posts from the subreddit
        posts = self.scraper.scrape_subreddit(subreddit_name, limit, sort_by, time_filter)
        
        # Store posts in the database
        posts_stored = self.db.store_posts_batch(posts)
        
        # Store comments if requested
        comments_stored = 0
        if store_comments and posts:
            for post in posts:
                # Add a random delay between post processing
                time.sleep(random.uniform(1, 3))
                
                # Scrape comments for the post
                comments = self.scraper.scrape_post_comments(post['id'], subreddit_name, comments_limit)
                
                # Store comments in the database
                comments_stored += self.db.store_comments_batch(comments)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Create summary
        summary = {
            "subreddit": subreddit_name,
            "posts_fetched": len(posts),
            "posts_stored": posts_stored,
            "comments_stored": comments_stored,
            "elapsed_time": f"{elapsed_time:.2f} seconds",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"Parsing summary: {summary}")
        return summary
    
    def parse_search_results(self, subreddit_name, query, limit=100, sort_by="relevance", time_filter="all", store_comments=True, comments_limit=None):
        """
        Parse search results from a subreddit and store them in the database.
        
        Args:
            subreddit_name (str): Name of the subreddit
            query (str): Search query
            limit (int): Maximum number of posts to fetch
            sort_by (str): Sorting method ('relevance', 'hot', 'top', 'new', 'comments')
            time_filter (str): Time filter for results ('all', 'day', 'week', 'month', 'year')
            store_comments (bool): Whether to store comments for each post
            comments_limit (int, optional): Maximum number of MoreComments objects to replace
            
        Returns:
            dict: Summary of the parsing operation
        """
        logger.info(f"Parsing search results for '{query}' in r/{subreddit_name}")
        start_time = time.time()
        
        # Search for posts and scrape the results
        posts = self.scraper.search_and_scrape(subreddit_name, query, limit, sort_by, time_filter)
        
        # Store posts in the database
        posts_stored = self.db.store_posts_batch(posts)
        
        # Store search query information
        self.db.store_search_query(query, subreddit_name, sort_by, time_filter, len(posts))
        
        # Store comments if requested
        comments_stored = 0
        if store_comments and posts:
            for post in posts:
                # Add a random delay between post processing
                time.sleep(random.uniform(1, 3))
                
                # Scrape comments for the post
                comments = self.scraper.scrape_post_comments(post['id'], subreddit_name, comments_limit)
                
                # Store comments in the database
                comments_stored += self.db.store_comments_batch(comments)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Create summary
        summary = {
            "subreddit": subreddit_name,
            "query": query,
            "posts_fetched": len(posts),
            "posts_stored": posts_stored,
            "comments_stored": comments_stored,
            "elapsed_time": f"{elapsed_time:.2f} seconds",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"Search parsing summary: {summary}")
        return summary
    
    def track_post_upvotes(self, post_ids, interval=3600, duration=86400):
        """
        Track upvotes for specific posts over time.
        
        Args:
            post_ids (list): List of post IDs to track
            interval (int): Time interval between checks in seconds (default: 1 hour)
            duration (int): Total duration to track in seconds (default: 24 hours)
            
        Returns:
            dict: Summary of the tracking operation
        """
        logger.info(f"Tracking upvotes for {len(post_ids)} posts")
        start_time = time.time()
        end_time = start_time + duration
        
        # Initialize tracking stats
        tracking_stats = {
            "posts_tracked": len(post_ids),
            "checks_performed": 0,
            "posts_updated": 0,
            "start_time": datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S'),
            "post_stats": {}
        }
        
        # Initialize post stats
        for post_id in post_ids:
            post = self.db.get_post(post_id)
            if post:
                tracking_stats["post_stats"][post_id] = {
                    "title": post["title"],
                    "initial_score": post["score"],
                    "initial_comments": post["num_comments"],
                    "final_score": post["score"],
                    "final_comments": post["num_comments"],
                    "score_change": 0,
                    "comments_change": 0
                }
        
        # Track posts until duration is reached
        while time.time() < end_time:
            tracking_stats["checks_performed"] += 1
            
            for post_id in post_ids:
                # Get the submission
                try:
                    submission = self.reddit_api.reddit.submission(id=post_id)
                    
                    # Extract post data
                    post_data = {
                        "id": post_id,
                        "title": submission.title,
                        "author": str(submission.author) if submission.author else "[deleted]",
                        "score": submission.score,
                        "upvote_ratio": submission.upvote_ratio,
                        "num_comments": submission.num_comments,
                        "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Store post data in the database
                    if self.db.store_post(post_data):
                        tracking_stats["posts_updated"] += 1
                    
                    # Update tracking stats
                    if post_id in tracking_stats["post_stats"]:
                        tracking_stats["post_stats"][post_id]["final_score"] = submission.score
                        tracking_stats["post_stats"][post_id]["final_comments"] = submission.num_comments
                        tracking_stats["post_stats"][post_id]["score_change"] = submission.score - tracking_stats["post_stats"][post_id]["initial_score"]
                        tracking_stats["post_stats"][post_id]["comments_change"] = submission.num_comments - tracking_stats["post_stats"][post_id]["initial_comments"]
                
                except Exception as e:
                    logger.error(f"Failed to track post {post_id}: {e}")
                
                # Add a random delay between post processing
                time.sleep(random.uniform(1, 3))
            
            # Wait for the next interval
            next_check = time.time() + interval
            sleep_time = next_check - time.time()
            if sleep_time > 0:
                logger.info(f"Waiting {sleep_time:.2f} seconds until next check")
                time.sleep(sleep_time)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        tracking_stats["actual_duration"] = f"{elapsed_time:.2f} seconds"
        
        logger.info(f"Tracking completed: {tracking_stats}")
        return tracking_stats
    
    def export_data(self, output_dir="exports", format="json"):
        """
        Export data from the database to files.
        
        Args:
            output_dir (str): Directory to save exported files
            format (str): Export format ('json' or 'csv')
            
        Returns:
            dict: Summary of the export operation
        """
        logger.info(f"Exporting data to {output_dir} in {format} format")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Initialize export stats
        export_stats = {
            "format": format,
            "output_dir": output_dir,
            "files_created": [],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Export posts
        posts_file = os.path.join(output_dir, f"posts.{format}")
        posts_count = self.db.export_to_json(posts_file, "posts")
        if posts_count > 0:
            export_stats["files_created"].append({
                "file": posts_file,
                "type": "posts",
                "count": posts_count
            })
        
        # Export comments
        comments_file = os.path.join(output_dir, f"comments.{format}")
        comments_count = self.db.export_to_json(comments_file, "comments")
        if comments_count > 0:
            export_stats["files_created"].append({
                "file": comments_file,
                "type": "comments",
                "count": comments_count
            })
        
        logger.info(f"Export completed: {export_stats}")
        return export_stats
    
    def close(self):
        """
        Close all connections and clean up resources.
        """
        logger.info("Closing Reddit Topic Parser")
        
        # Close the database connection
        if hasattr(self, 'db') and self.db:
            self.db.close()
            logger.info("Database connection closed")


def main():
    """
    Main function to run the Reddit Topic Parser from the command line.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Reddit Topic Parser with Upvotes Tracking")
    
    # API credentials
    parser.add_argument("--client-id", required=True, help="Reddit API client ID")
    parser.add_argument("--client-secret", required=True, help="Reddit API client secret")
    parser.add_argument("--user-agent", required=True, help="User agent string for Reddit API")
    
    # Mode selection
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    
    # Subreddit parsing mode
    subreddit_parser = subparsers.add_parser("subreddit", help="Parse posts from a subreddit")
    subreddit_parser.add_argument("subreddit", help="Name of the subreddit")
    subreddit_parser.add_argument("--limit", type=int, default=100, help="Maximum number of posts to fetch")
    subreddit_parser.add_argument("--sort-by", choices=["new", "hot", "top", "rising"], default="new", help="Sorting method")
    subreddit_parser.add_argument("--time-filter", choices=["all", "day", "week", "month", "year"], default="all", help="Time filter for 'top' sorting")
    subreddit_parser.add_argument("--no-comments", action="store_true", help="Don't store comments")
    subreddit_parser.add_argument("--comments-limit", type=int, help="Maximum number of MoreComments objects to replace")
    
    # Search mode
    search_parser = subparsers.add_parser("search", help="Search for posts in a subreddit")
    search_parser.add_argument("subreddit", help="Name of the subreddit")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=100, help="Maximum number of posts to fetch")
    search_parser.add_argument("--sort-by", choices=["relevance", "hot", "top", "new", "comments"], default="relevance", help="Sorting method")
    search_parser.add_argument("--time-filter", choices=["all", "day", "week", "month", "year"], default="all", help="Time filter for results")
    search_parser.add_argument("--no-comments", action="store_true", help="Don't store comments")
    search_parser.add_argument("--comments-limit", type=int, help="Maximum number of MoreComments objects to replace")
    
    # Tracking mode
    track_parser = subparsers.add_parser("track", help="Track upvotes for specific posts")
    track_parser.add_argument("post_ids", nargs="+", help="Post IDs to track")
    track_parser.add_argument("--interval", type=int, default=3600, help="Time interval between checks in seconds")
    track_parser.add_argument("--duration", type=int, default=86400, help="Total duration to track in seconds")
    
    # Export mode
    export_parser = subparsers.add_parser("export", help="Export data from the database")
    export_parser.add_argument("--output-dir", default="exports", help="Directory to save exported files")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    
    # Common options
    parser.add_argument("--proxy-file", help="Path to the proxy file")
    parser.add_argument("--db-path", default="reddit_data.db", help="Path to the SQLite database file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="Logging level")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check if mode is specified
    if not args.mode:
        parser.print_help()
        return
    
    # Initialize the Reddit Topic Parser
    parser = RedditTopicParser(
        args.client_id,
        args.client_secret,
        args.user_agent,
        args.proxy_file,
        args.db_path
    )
    
    try:
        # Run the appropriate mode
        if args.mode == "subreddit":
            summary = parser.parse_subreddit(
                args.subreddit,
                args.limit,
                args.sort_by,
                args.time_filter,
                not args.no_comments,
                args.comments_limit
            )
            print(json.dumps(summary, indent=4))
        
        elif args.mode == "search":
            summary = parser.parse_search_results(
                args.subreddit,
                args.query,
                args.limit,
                args.sort_by,
                args.time_filter,
                not args.no_comments,
                args.comments_limit
            )
            print(json.dumps(summary, indent=4))
        
        elif args.mode == "track":
            summary = parser.track_post_upvotes(
                args.post_ids,
                args.interval,
                args.duration
            )
            print(json.dumps(summary, indent=4))
        
        elif args.mode == "export":
            summary = parser.export_data(
                args.output_dir,
                args.format
            )
            print(json.dumps(summary, indent=4))
    
    finally:
        # Close the parser
        parser.close()


if __name__ == "__main__":
    main()
