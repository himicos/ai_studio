"""
Database Module

This module handles the storage of Reddit data in an SQL database.
It provides functionality to create the database schema and store posts and comments.
"""

import sqlite3
import logging
import os
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("database.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditDatabase:
    """
    A class to handle database operations for Reddit data.
    """
    
    def __init__(self, db_path="reddit_data.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Connect to the database
        self._connect()
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _connect(self):
        """
        Connect to the SQLite database.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _create_tables(self):
        """
        Create the necessary tables if they don't exist.
        """
        try:
            # Create subreddits table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subreddits (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    subscribers INTEGER,
                    created_utc REAL,
                    description TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create posts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT,
                    created_utc REAL,
                    score INTEGER,
                    upvote_ratio REAL,
                    num_comments INTEGER,
                    permalink TEXT,
                    url TEXT,
                    is_self INTEGER,
                    is_video INTEGER,
                    is_original_content INTEGER,
                    over_18 INTEGER,
                    spoiler INTEGER,
                    stickied INTEGER,
                    subreddit TEXT,
                    subreddit_id TEXT,
                    domain TEXT,
                    selftext TEXT,
                    selftext_html TEXT,
                    link_flair_text TEXT,
                    gilded INTEGER,
                    total_awards_received INTEGER,
                    scraped_at TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subreddit_id) REFERENCES subreddits(id)
                )
            ''')
            
            # Create comments table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    post_id TEXT,
                    author TEXT,
                    created_utc REAL,
                    score INTEGER,
                    body TEXT,
                    body_html TEXT,
                    permalink TEXT,
                    is_submitter INTEGER,
                    stickied INTEGER,
                    parent_id TEXT,
                    gilded INTEGER,
                    total_awards_received INTEGER,
                    scraped_at TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id)
                )
            ''')
            
            # Create search_queries table to track searches
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    subreddit TEXT,
                    sort_by TEXT,
                    time_filter TEXT,
                    num_results INTEGER,
                    search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create post_history table to track changes in post scores over time
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    score INTEGER,
                    upvote_ratio REAL,
                    num_comments INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id)
                )
            ''')
            
            # Create comment_history table to track changes in comment scores over time
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS comment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comment_id TEXT,
                    score INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (comment_id) REFERENCES comments(id)
                )
            ''')
            
            # Create indices for faster queries
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_history_post_id ON post_history(post_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_comment_history_comment_id ON comment_history(comment_id)')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def store_subreddit(self, subreddit_data):
        """
        Store subreddit data in the database.
        
        Args:
            subreddit_data (dict): Dictionary containing subreddit data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO subreddits (
                    id, name, display_name, subscribers, created_utc, description, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                subreddit_data.get('id'),
                subreddit_data.get('name'),
                subreddit_data.get('display_name'),
                subreddit_data.get('subscribers'),
                subreddit_data.get('created_utc'),
                subreddit_data.get('description')
            ))
            
            self.conn.commit()
            logger.info(f"Stored subreddit data for {subreddit_data.get('display_name')}")
            return True
        except Exception as e:
            logger.error(f"Failed to store subreddit data: {e}")
            self.conn.rollback()
            return False
    
    def store_post(self, post_data):
        """
        Store post data in the database.
        
        Args:
            post_data (dict): Dictionary containing post data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if post already exists
            self.cursor.execute('SELECT id, score, upvote_ratio, num_comments FROM posts WHERE id = ?', (post_data.get('id'),))
            existing_post = self.cursor.fetchone()
            
            if existing_post:
                # Update existing post
                self.cursor.execute('''
                    UPDATE posts SET
                        title = ?,
                        author = ?,
                        score = ?,
                        upvote_ratio = ?,
                        num_comments = ?,
                        permalink = ?,
                        url = ?,
                        is_self = ?,
                        is_video = ?,
                        is_original_content = ?,
                        over_18 = ?,
                        spoiler = ?,
                        stickied = ?,
                        subreddit = ?,
                        subreddit_id = ?,
                        domain = ?,
                        selftext = ?,
                        selftext_html = ?,
                        link_flair_text = ?,
                        gilded = ?,
                        total_awards_received = ?,
                        scraped_at = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    post_data.get('title'),
                    post_data.get('author'),
                    post_data.get('score'),
                    post_data.get('upvote_ratio'),
                    post_data.get('num_comments'),
                    post_data.get('permalink'),
                    post_data.get('url'),
                    1 if post_data.get('is_self') else 0,
                    1 if post_data.get('is_video') else 0,
                    1 if post_data.get('is_original_content') else 0,
                    1 if post_data.get('over_18') else 0,
                    1 if post_data.get('spoiler') else 0,
                    1 if post_data.get('stickied') else 0,
                    post_data.get('subreddit'),
                    post_data.get('subreddit_id'),
                    post_data.get('domain'),
                    post_data.get('selftext'),
                    post_data.get('selftext_html'),
                    post_data.get('link_flair_text'),
                    post_data.get('gilded', 0),
                    post_data.get('total_awards_received', 0),
                    post_data.get('scraped_at'),
                    post_data.get('id')
                ))
                
                # Store history if score or comments changed
                if (existing_post['score'] != post_data.get('score') or 
                    existing_post['upvote_ratio'] != post_data.get('upvote_ratio') or 
                    existing_post['num_comments'] != post_data.get('num_comments')):
                    
                    self.cursor.execute('''
                        INSERT INTO post_history (post_id, score, upvote_ratio, num_comments)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        post_data.get('id'),
                        post_data.get('score'),
                        post_data.get('upvote_ratio'),
                        post_data.get('num_comments')
                    ))
                
                logger.info(f"Updated post data for {post_data.get('id')}")
            else:
                # Insert new post
                self.cursor.execute('''
                    INSERT INTO posts (
                        id, title, author, created_utc, score, upvote_ratio, num_comments,
                        permalink, url, is_self, is_video, is_original_content, over_18,
                        spoiler, stickied, subreddit, subreddit_id, domain, selftext,
                        selftext_html, link_flair_text, gilded, total_awards_received, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post_data.get('id'),
                    post_data.get('title'),
                    post_data.get('author'),
                    post_data.get('created_utc'),
                    post_data.get('score'),
                    post_data.get('upvote_ratio'),
                    post_data.get('num_comments'),
                    post_data.get('permalink'),
                    post_data.get('url'),
                    1 if post_data.get('is_self') else 0,
                    1 if post_data.get('is_video') else 0,
                    1 if post_data.get('is_original_content') else 0,
                    1 if post_data.get('over_18') else 0,
                    1 if post_data.get('spoiler') else 0,
                    1 if post_data.get('stickied') else 0,
                    post_data.get('subreddit'),
                    post_data.get('subreddit_id'),
                    post_data.get('domain'),
                    post_data.get('selftext'),
                    post_data.get('selftext_html'),
                    post_data.get('link_flair_text'),
                    post_data.get('gilded', 0),
                    post_data.get('total_awards_received', 0),
                    post_data.get('scraped_at')
                ))
                
                # Store initial history
                self.cursor.execute('''
                    INSERT INTO post_history (post_id, score, upvote_ratio, num_comments)
                    VALUES (?, ?, ?, ?)
                ''', (
                    post_data.get('id'),
                    post_data.get('score'),
                    post_data.get('upvote_ratio'),
                    post_data.get('num_comments')
                ))
                
                logger.info(f"Inserted new post data for {post_data.get('id')}")
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store post data: {e}")
            self.conn.rollback()
            return False
    
    def store_comment(self, comment_data):
        """
        Store comment data in the database.
        
        Args:
            comment_data (dict): Dictionary containing comment data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if comment already exists
            self.cursor.execute('SELECT id, score FROM comments WHERE id = ?', (comment_data.get('id'),))
            existing_comment = self.cursor.fetchone()
            
            if existing_comment:
                # Update existing comment
                self.cursor.execute('''
                    UPDATE comments SET
                        post_id = ?,
                        author = ?,
                        score = ?,
                        body = ?,
                        body_html = ?,
                        permalink = ?,
                        is_submitter = ?,
                        stickied = ?,
                        parent_id = ?,
                        gilded = ?,
                        total_awards_received = ?,
                        scraped_at = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    comment_data.get('post_id'),
                    comment_data.get('author'),
                    comment_data.get('score'),
                    comment_data.get('body'),
                    comment_data.get('body_html'),
                    comment_data.get('permalink'),
                    1 if comment_data.get('is_submitter') else 0,
                    1 if comment_data.get('stickied') else 0,
                    comment_data.get('parent_id'),
                    comment_data.get('gilded', 0),
                    comment_data.get('total_awards_received', 0),
                    comment_data.get('scraped_at'),
                    comment_data.get('id')
                ))
                
                # Store history if score changed
                if existing_comment['score'] != comment_data.get('score'):
                    self.cursor.execute('''
                        INSERT INTO comment_history (comment_id, score)
                        VALUES (?, ?)
                    ''', (
                        comment_data.get('id'),
                        comment_data.get('score')
                    ))
                
                logger.info(f"Updated comment data for {comment_data.get('id')}")
            else:
                # Insert new comment
                self.cursor.execute('''
                    INSERT INTO comments (
                        id, post_id, author, created_utc, score, body, body_html,
                        permalink, is_submitter, stickied, parent_id, gilded,
                        total_awards_received, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comment_data.get('id'),
                    comment_data.get('post_id'),
                    comment_data.get('author'),
                    comment_data.get('created_utc'),
                    comment_data.get('score'),
                    comment_data.get('body'),
                    comment_data.get('body_html'),
                    comment_data.get('permalink'),
                    1 if comment_data.get('is_submitter') else 0,
                    1 if comment_data.get('stickied') else 0,
                    comment_data.get('parent_id'),
                    comment_data.get('gilded', 0),
                    comment_data.get('total_awards_received', 0),
                    comment_data.get('scraped_at')
                ))
                
                # Store initial history
                self.cursor.execute('''
                    INSERT INTO comment_history (comment_id, score)
                    VALUES (?, ?)
                ''', (
                    comment_data.get('id'),
                    comment_data.get('score')
                ))
                
                logger.info(f"Inserted new comment data for {comment_data.get('id')}")
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store comment data: {e}")
            self.conn.rollback()
            return False
    
    def store_search_query(self, query, subreddit, sort_by, time_filter, num_results):
        """
        Store search query information.
        
        Args:
            query (str): Search query
            subreddit (str): Subreddit name
            sort_by (str): Sort method
            time_filter (str): Time filter
            num_results (int): Number of results found
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
                INSERT INTO search_queries (query, subreddit, sort_by, time_filter, num_results)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                query,
                subreddit,
                sort_by,
                time_filter,
                num_results
            ))
            
            self.conn.commit()
            logger.info(f"Stored search query: '{query}' in r/{subreddit}")
            return True
        except Exception as e:
            logger.error(f"Failed to store search query: {e}")
            self.conn.rollback()
            return False
    
    def store_posts_batch(self, posts_data):
        """
        Store multiple posts in a batch.
        
        Args:
            posts_data (list): List of dictionaries containing post data
            
        Returns:
            int: Number of successfully stored posts
        """
        success_count = 0
        for post_data in posts_data:
            if self.store_post(post_data):
                success_count += 1
        
        logger.info(f"Stored {success_count}/{len(posts_data)} posts in batch")
        return success_count
    
    def store_comments_batch(self, comments_data):
        """
        Store multiple comments in a batch.
        
        Args:
            comments_data (list): List of dictionaries containing comment data
            
        Returns:
            int: Number of successfully stored comments
        """
        success_count = 0
        for comment_data in comments_data:
            if self.store_comment(comment_data):
                success_count += 1
        
        logger.info(f"Stored {success_count}/{len(comments_data)} comments in batch")
        return success_count
    
    def get_post(self, post_id):
        """
        Get a post by ID.
        
        Args:
            post_id (str): Post ID
            
        Returns:
            dict: Post data or None if not found
        """
        try:
            self.cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
            post = self.cursor.fetchone()
            
            if post:
                return dict(post)
            else:
                logger.warning(f"Post {post_id} not found")
                return None
        except Exception as e:
            logger.error(f"Failed to get post {post_id}: {e}")
            return None
    
    def get_post_comments(self, post_id):
        """
        Get all comments for a post.
        
        Args:
            post_id (str): Post ID
            
        Returns:
            list: List of comment dictionaries
        """
        try:
            self.cursor.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY created_utc ASC', (post_id,))
            comments = self.cursor.fetchall()
            
            return [dict(comment) for comment in comments]
        except Exception as e:
            logger.error(f"Failed to get comments for post {post_id}: {e}")
            return []
    
    def get_post_history(self, post_id):
        """
        Get score history for a post.
        
        Args:
            post_id (str): Post ID
            
        Returns:
            list: List of history dictionaries
        """
        try:
            self.cursor.execute('''
                SELECT post_id, score, upvote_ratio, num_comments, recorded_at
                FROM post_history
                WHERE post_id = ?
                ORDER BY recorded_at ASC
            ''', (post_id,))
            history = self.cursor.fetchall()
            
            return [dict(record) for record in history]
        except Exception as e:
            logger.error(f"Failed to get history for post {post_id}: {e}")
            return []
    
    def get_subreddit_posts(self, subreddit, limit=100, offset=0):
        """
        Get posts from a subreddit.
        
        Args:
            subreddit (str): Subreddit name
            limit (int): Maximum number of posts to return
            offset (int): Offset for pagination
            
        Returns:
            list: List of post dictionaries
        """
        try:
            self.cursor.execute('''
                SELECT * FROM posts
                WHERE subreddit = ?
                ORDER BY created_utc DESC
                LIMIT ? OFFSET ?
            ''', (subreddit, limit, offset))
            posts = self.cursor.fetchall()
            
            return [dict(post) for post in posts]
        except Exception as e:
            logger.error(f"Failed to get posts from subreddit {subreddit}: {e}")
            return []
    
    def search_posts(self, query, subreddit=None, limit=100, offset=0):
        """
        Search for posts containing a query.
        
        Args:
            query (str): Search query
            subreddit (str, optional): Limit search to a specific subreddit
            limit (int): Maximum number of posts to return
            offset (int): Offset for pagination
            
        Returns:
            list: List of post dictionaries
        """
        try:
            if subreddit:
                self.cursor.execute('''
                    SELECT * FROM posts
                    WHERE (title LIKE ? OR selftext LIKE ?) AND subreddit = ?
                    ORDER BY created_utc DESC
                    LIMIT ? OFFSET ?
                ''', (f'%{query}%', f'%{query}%', subreddit, limit, offset))
            else:
                self.cursor.execute('''
                    SELECT * FROM posts
                    WHERE title LIKE ? OR selftext LIKE ?
                    ORDER BY created_utc DESC
                    LIMIT ? OFFSET ?
                ''', (f'%{query}%', f'%{query}%', limit, offset))
            
            posts = self.cursor.fetchall()
            
            # Store the search query
            self.store_search_query(query, subreddit, 'database', 'all', len(posts))
            
            return [dict(post) for post in posts]
        except Exception as e:
            logger.error(f"Failed to search for posts with query '{query}': {e}")
            return []
    
    def import_from_json(self, json_file, data_type):
        """
        Import data from a JSON file.
        
        Args:
            json_file (str): Path to the JSON file
            data_type (str): Type of data ('posts' or 'comments')
            
        Returns:
            int: Number of successfully imported items
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data_type == 'posts':
                return self.store_posts_batch(data)
            elif data_type == 'comments':
                return self.store_comments_batch(data)
            else:
                logger.error(f"Invalid data type: {data_type}")
                return 0
        except Exception as e:
            logger.error(f"Failed to import data from {json_file}: {e}")
            return 0
    
    def export_to_json(self, output_file, data_type, query=None, subreddit=None, limit=1000):
        """
        Export data to a JSON file.
        
        Args:
            output_file (str): Path to the output file
            data_type (str): Type of data ('posts', 'comments', or 'search')
            query (str, optional): Search query for 'search' data type
            subreddit (str, optional): Subreddit name for filtering
            limit (int): Maximum number of items to export
            
        Returns:
            int: Number of exported items
        """
        try:
            if data_type == 'posts':
                if subreddit:
                    data = self.get_subreddit_posts(subreddit, limit=limit)
                else:
                    self.cursor.execute('SELECT * FROM posts ORDER BY created_utc DESC LIMIT ?', (limit,))
                    data = [dict(post) for post in self.cursor.fetchall()]
            
            elif data_type == 'comments':
                if subreddit:
                    self.cursor.execute('''
                        SELECT c.* FROM comments c
                        JOIN posts p ON c.post_id = p.id
                        WHERE p.subreddit = ?
                        ORDER BY c.created_utc DESC
                        LIMIT ?
                    ''', (subreddit, limit))
                else:
                    self.cursor.execute('SELECT * FROM comments ORDER BY created_utc DESC LIMIT ?', (limit,))
                
                data = [dict(comment) for comment in self.cursor.fetchall()]
            
            elif data_type == 'search':
                if not query:
                    logger.error("Query is required for search export")
                    return 0
                
                data = self.search_posts(query, subreddit, limit=limit)
            
            else:
                logger.error(f"Invalid data type: {data_type}")
                return 0
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Exported {len(data)} items to {output_file}")
            return len(data)
        
        except Exception as e:
            logger.error(f"Failed to export data to {output_file}: {e}")
            return 0

# Example usage
if __name__ == "__main__":
    # Initialize the database
    db = RedditDatabase()
    
    # Create a sample post
    sample_post = {
        "id": "sample1",
        "title": "Sample Post",
        "author": "user123",
        "created_utc": 1617235200.0,
        "score": 42,
        "upvote_ratio": 0.95,
        "num_comments": 10,
        "permalink": "/r/test/comments/sample1/sample_post/",
        "url": "https://www.reddit.com/r/test/comments/sample1/sample_post/",
        "is_self": True,
        "is_video": False,
        "is_original_content": False,
        "over_18": False,
        "spoiler": False,
        "stickied": False,
        "subreddit": "test",
        "subreddit_id": "t5_2qh23",
        "domain": "self.test",
        "selftext": "This is a sample post for testing.",
        "selftext_html": "<div>This is a sample post for testing.</div>",
        "link_flair_text": "Test",
        "gilded": 0,
        "total_awards_received": 0,
        "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Store the sample post
    db.store_post(sample_post)
    
    # Create a sample comment
    sample_comment = {
        "id": "comment1",
        "post_id": "sample1",
        "author": "commenter456",
        "created_utc": 1617235300.0,
        "score": 15,
        "body": "This is a sample comment.",
        "body_html": "<div>This is a sample comment.</div>",
        "permalink": "/r/test/comments/sample1/sample_post/comment1/",
        "is_submitter": False,
        "stickied": False,
        "parent_id": "t3_sample1",
        "gilded": 0,
        "total_awards_received": 0,
        "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Store the sample comment
    db.store_comment(sample_comment)
    
    # Close the database connection
    db.close()
