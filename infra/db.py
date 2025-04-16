"""
Database Module for AI Studio

This module handles database operations for AI Studio, including:
- Creating and initializing the database
- Storing and retrieving data from Twitter and Reddit
- Logging system actions and prompt processing
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# Set up logging
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join("memory", "memory.sqlite")

def get_db_connection():
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """
    Initialize the database with the required tables.
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create posts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        title TEXT,
        content TEXT,
        author TEXT,
        url TEXT,
        score INTEGER,
        num_comments INTEGER,
        created_utc INTEGER,
        scraped_at INTEGER,
        metadata TEXT
    )
    ''')
    
    # Create post_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS post_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT NOT NULL,
        score INTEGER,
        num_comments INTEGER,
        recorded_at INTEGER,
        FOREIGN KEY (post_id) REFERENCES posts (id)
    )
    ''')
    
    # Create logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        agent TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        status TEXT
    )
    ''')
    
    # Create prompts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        prompt TEXT NOT NULL,
        route TEXT NOT NULL,
        output TEXT,
        status TEXT
    )
    ''')
    
    # Create contracts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contracts (
        id TEXT PRIMARY KEY,
        address TEXT NOT NULL,
        source TEXT NOT NULL,
        source_id TEXT,
        detected_at INTEGER NOT NULL,
        processed_at INTEGER,
        status TEXT,
        metadata TEXT
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    logger.info(f"Database initialized at {DB_PATH}")

def store_post(post: Dict[str, Any]) -> bool:
    """
    Store a post in the database.
    
    Args:
        post (dict): Post data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if post already exists
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post['id'],))
        existing_post = cursor.fetchone()
        
        if existing_post:
            # Update existing post
            cursor.execute('''
            UPDATE posts SET
                title = ?,
                content = ?,
                author = ?,
                url = ?,
                score = ?,
                num_comments = ?,
                scraped_at = ?,
                metadata = ?
            WHERE id = ?
            ''', (
                post.get('title', ''),
                post.get('content', ''),
                post.get('author', ''),
                post.get('url', ''),
                post.get('score', 0),
                post.get('num_comments', 0),
                int(datetime.now().timestamp()),
                json.dumps(post.get('metadata', {})),
                post['id']
            ))
            
            # Store post history
            cursor.execute('''
            INSERT INTO post_history (post_id, score, num_comments, recorded_at)
            VALUES (?, ?, ?, ?)
            ''', (
                post['id'],
                post.get('score', 0),
                post.get('num_comments', 0),
                int(datetime.now().timestamp())
            ))
            
            conn.commit()
            conn.close()
            return True
        else:
            # Insert new post
            cursor.execute('''
            INSERT INTO posts (
                id, source, title, content, author, url, score, num_comments, 
                created_utc, scraped_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['id'],
                post['source'],
                post.get('title', ''),
                post.get('content', ''),
                post.get('author', ''),
                post.get('url', ''),
                post.get('score', 0),
                post.get('num_comments', 0),
                post.get('created_utc', int(datetime.now().timestamp())),
                int(datetime.now().timestamp()),
                json.dumps(post.get('metadata', {}))
            ))
            
            # Store initial post history
            cursor.execute('''
            INSERT INTO post_history (post_id, score, num_comments, recorded_at)
            VALUES (?, ?, ?, ?)
            ''', (
                post['id'],
                post.get('score', 0),
                post.get('num_comments', 0),
                int(datetime.now().timestamp())
            ))
            
            conn.commit()
            conn.close()
            return True
    
    except Exception as e:
        logger.error(f"Error storing post: {e}")
        return False

def get_post(post_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a post from the database.
    
    Args:
        post_id (str): Post ID
        
    Returns:
        dict: Post data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        
        conn.close()
        
        if post:
            post_dict = dict(post)
            # Parse metadata JSON
            if post_dict.get('metadata'):
                post_dict['metadata'] = json.loads(post_dict['metadata'])
            return post_dict
        else:
            return None
    
    except Exception as e:
        logger.error(f"Error getting post: {e}")
        return None

def get_posts(source: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get posts from the database.
    
    Args:
        source (str, optional): Filter by source (e.g., 'twitter', 'reddit')
        limit (int): Maximum number of posts to return
        
    Returns:
        list: List of post dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if source:
            cursor.execute(
                "SELECT * FROM posts WHERE source = ? ORDER BY created_utc DESC LIMIT ?", 
                (source, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM posts ORDER BY created_utc DESC LIMIT ?", 
                (limit,)
            )
        
        posts = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries and parse metadata JSON
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            if post_dict.get('metadata'):
                post_dict['metadata'] = json.loads(post_dict['metadata'])
            posts_list.append(post_dict)
        
        return posts_list
    
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return []

def store_contract(contract: Dict[str, Any]) -> bool:
    """
    Store a contract in the database.
    
    Args:
        contract (dict): Contract data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate ID if not provided
        if 'id' not in contract:
            contract['id'] = f"{contract['source']}_{contract['address']}_{int(datetime.now().timestamp())}"
        
        # Check if contract already exists
        cursor.execute("SELECT id FROM contracts WHERE address = ? AND source = ?", 
                      (contract['address'], contract['source']))
        existing_contract = cursor.fetchone()
        
        if existing_contract:
            # Update existing contract
            cursor.execute('''
            UPDATE contracts SET
                source_id = ?,
                processed_at = ?,
                status = ?,
                metadata = ?
            WHERE id = ?
            ''', (
                contract.get('source_id', ''),
                contract.get('processed_at', None),
                contract.get('status', 'detected'),
                json.dumps(contract.get('metadata', {})),
                existing_contract['id']
            ))
        else:
            # Insert new contract
            cursor.execute('''
            INSERT INTO contracts (
                id, address, source, source_id, detected_at, processed_at, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contract['id'],
                contract['address'],
                contract['source'],
                contract.get('source_id', ''),
                contract.get('detected_at', int(datetime.now().timestamp())),
                contract.get('processed_at', None),
                contract.get('status', 'detected'),
                json.dumps(contract.get('metadata', {}))
            ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error storing contract: {e}")
        return False

def log_action(agent: str, action: str, details: Optional[str] = None, status: str = "success") -> bool:
    """
    Log an action in the database.
    
    Args:
        agent (str): Agent name
        action (str): Action description
        details (str, optional): Additional details
        status (str): Status of the action
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO logs (timestamp, agent, action, details, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            int(datetime.now().timestamp()),
            agent,
            action,
            details,
            status
        ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error logging action: {e}")
        return False

def store_prompt(prompt: str, route: str, output: Optional[str] = None, status: str = "pending") -> int:
    """
    Store a prompt in the database.
    
    Args:
        prompt (str): The schizoprompt
        route (str): The route (e.g., 'grok', 'claude', 'gpt4o', 'manus')
        output (str, optional): The output of the prompt
        status (str): Status of the prompt processing
        
    Returns:
        int: Prompt ID or -1 if failed
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO prompts (timestamp, prompt, route, output, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            int(datetime.now().timestamp()),
            prompt,
            route,
            output,
            status
        ))
        
        prompt_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return prompt_id
    
    except Exception as e:
        logger.error(f"Error storing prompt: {e}")
        return -1

def update_prompt(prompt_id: int, output: str, status: str = "completed") -> bool:
    """
    Update a prompt in the database.
    
    Args:
        prompt_id (int): Prompt ID
        output (str): The output of the prompt
        status (str): Status of the prompt processing
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE prompts SET
            output = ?,
            status = ?
        WHERE id = ?
        ''', (
            output,
            status,
            prompt_id
        ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error updating prompt: {e}")
        return False

def get_prompt_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get prompt history from the database.
    
    Args:
        limit (int): Maximum number of prompts to return
        
    Returns:
        list: List of prompt dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM prompts ORDER BY timestamp DESC LIMIT ?", 
            (limit,)
        )
        
        prompts = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        return [dict(prompt) for prompt in prompts]
    
    except Exception as e:
        logger.error(f"Error getting prompt history: {e}")
        return []

def export_data(table: str, output_file: str) -> int:
    """
    Export data from a table to a JSON file.
    
    Args:
        table (str): Table name
        output_file (str): Output file path
        
    Returns:
        int: Number of rows exported
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        data = [dict(row) for row in rows]
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        return len(data)
    
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return 0

# Example usage
if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Example: Store a post
    post = {
        'id': 'test_post_1',
        'source': 'twitter',
        'title': 'Test Post',
        'content': 'This is a test post',
        'author': 'test_user',
        'url': 'https://twitter.com/test_user/status/123456789',
        'score': 10,
        'num_comments': 5,
        'created_utc': int(datetime.now().timestamp()),
        'metadata': {
            'hashtags': ['test', 'example']
        }
    }
    
    success = store_post(post)
    print(f"Post stored: {success}")
    
    # Example: Get a post
    retrieved_post = get_post('test_post_1')
    print(f"Retrieved post: {retrieved_post}")
    
    # Example: Log an action
    log_success = log_action('test_agent', 'test_action', 'This is a test action')
    print(f"Action logged: {log_success}")
    
    # Example: Store a prompt
    prompt_id = store_prompt('Test prompt', 'gpt4o')
    print(f"Prompt stored with ID: {prompt_id}")
    
    # Example: Update a prompt
    update_success = update_prompt(prompt_id, 'Test output')
    print(f"Prompt updated: {update_success}")
