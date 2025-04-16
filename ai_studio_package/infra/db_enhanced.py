"""
Enhanced Database Module for AI Studio with Vector Memory Support

This module extends the database operations for AI Studio to include:
- Vector storage for memory nodes
- Embedding generation and retrieval
- Graph relationships between memory nodes
- Advanced querying capabilities
"""

import os
import sqlite3
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio # Make sure asyncio is imported

# Set up logging
logger = logging.getLogger(__name__)

# Database paths
DB_PATH = os.path.join("memory", "memory.sqlite")
VECTOR_DB_PATH = os.path.join("memory", "vectors.sqlite")

# It's better to load the model once. We can make this more robust later.
# This line should ideally be outside the function, maybe near the top after imports.
# We'll place it here for now for simplicity in the edit.
embedding_model_name = 'all-MiniLM-L6-v2' 
embedding_model = SentenceTransformer(embedding_model_name)
embedding_dimensions = 384 # Specify dimensions for MiniLM-L6-v2

def get_db_connection():
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    # Increase timeout (e.g., to 10 seconds) to wait longer for locks
    conn = sqlite3.connect(DB_PATH, timeout=10.0) 
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    # Enable Write-Ahead Logging for potentially better concurrency
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        logger.info("SQLite journal_mode set to WAL.")
    except Exception as e:
        logger.warning(f"Could not set journal_mode to WAL: {e}")
    return conn

def get_vector_db_connection():
    """
    Get a connection to the vector SQLite database.
    
    Returns:
        sqlite3.Connection: Vector database connection object
    """
    conn = sqlite3.connect(VECTOR_DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """
    Initialize the database with the required tables.
    """
    logger.info("Starting database initialization")
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    logger.info(f"Database directory created/verified at {os.path.dirname(DB_PATH)}")
    
    # Connect to the database
    conn = get_db_connection()
    logger.info("Database connection established")
    cursor = conn.cursor()
    
    # Create tables
    logger.info("Creating tables...")
    
    # Create posts table
    logger.info("Creating posts table")
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
    logger.info("Creating post_history table")
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
    logger.info("Creating logs table")
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
    logger.info("Creating prompts table")
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
    logger.info("Creating contracts table")
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
    
    # Create memory_nodes table
    logger.info("Creating memory_nodes table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_nodes (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT,          -- Store as JSON string
        created_at INTEGER NOT NULL,
        source_id TEXT,
        source_type TEXT,
        metadata TEXT,      -- Store as JSON string
        has_embedding INTEGER DEFAULT 0,
        updated_at INTEGER
    )
    ''')
    
    # Create memory_edges table
    logger.info("Creating memory_edges table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_edges (
        id TEXT PRIMARY KEY,
        source_node_id TEXT NOT NULL,
        target_node_id TEXT NOT NULL,
        label TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        created_at INTEGER NOT NULL,
        metadata TEXT,      -- Store as JSON string
        FOREIGN KEY (source_node_id) REFERENCES memory_nodes (id),
        FOREIGN KEY (target_node_id) REFERENCES memory_nodes (id)
    )
    ''')
    
    # Create tracked_users table
    logger.info("Creating tracked_users table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tracked_users (
      id TEXT PRIMARY KEY, -- Usually user_id from Twitter API
      handle TEXT NOT NULL UNIQUE,
      tags TEXT, -- Store as JSON string
      added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # Create tracked_tweets table
    logger.info("Creating tracked_tweets table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tracked_tweets (
      tweet_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      content TEXT,
      date_posted TIMESTAMP,
      engagement_likes INTEGER DEFAULT 0,
      engagement_retweets INTEGER DEFAULT 0,
      engagement_replies INTEGER DEFAULT 0,
      url TEXT,
      score REAL,
      sentiment TEXT,
      keywords TEXT, -- Store as JSON string
      added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES tracked_users (id) ON DELETE CASCADE
    );
    ''')

    # Create tracked_subreddits table
    logger.info("Creating tracked_subreddits table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tracked_subreddits (
      name TEXT PRIMARY KEY, -- Store lowercased subreddit name
      added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      is_active BOOLEAN DEFAULT 1,
      last_scanned_post_id TEXT,
      last_scanned_timestamp TIMESTAMP
    );
    ''')

    # Create reddit_posts table
    logger.info("Creating reddit_posts table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id TEXT PRIMARY KEY, -- Reddit post ID (e.g., abcdef)
        subreddit TEXT NOT NULL,
        title TEXT,
        author TEXT,
        created_utc TEXT NOT NULL, -- ISO 8601 format string
        score INTEGER,
        upvote_ratio REAL,
        num_comments INTEGER,
        permalink TEXT UNIQUE,
        url TEXT,
        selftext TEXT,
        is_self BOOLEAN,
        is_video BOOLEAN,
        over_18 BOOLEAN,
        spoiler BOOLEAN,
        stickied BOOLEAN,
        scraped_at TEXT NOT NULL, -- ISO 8601 format string
        -- Added AI Columns
        sentiment TEXT,
        sentiment_score REAL,
        keywords TEXT -- Store as JSON string
    );
    ''')

    # Add indexes for reddit_posts table
    logger.info("Creating indexes for reddit_posts table")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit ON reddit_posts (subreddit);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_posts_created_utc ON reddit_posts (created_utc DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_posts_score ON reddit_posts (score DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_posts_author ON reddit_posts (author);")

    # Create embeddings table
    logger.info("Creating embeddings table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        node_id TEXT PRIMARY KEY, -- Corresponds to memory_nodes.id
        vector BLOB NOT NULL,     -- Store the embedding as a binary large object
        model_name TEXT NOT NULL, -- Track which embedding model was used
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (node_id) REFERENCES memory_nodes (id) -- Logical link, not enforced across DBs
    );
    ''')

    # Create embedding_models table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embedding_models (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        version TEXT,
        is_default BOOLEAN DEFAULT 0
    )
    ''')
    
    # Insert default embedding model
    cursor.execute('''
    INSERT OR IGNORE INTO embedding_models (id, name, provider, dimensions, version, is_default)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ('openai-text-embedding-3-small', 'text-embedding-3-small', 'OpenAI', 1536, '1.0', 1))

    # Commit changes and close connection
    conn.commit()
    logger.info("Database changes committed")
    conn.close()
    logger.info("Database connection closed")
    
    logger.info(f"Database initialized at {DB_PATH}")

def init_vector_db():
    """
    Initialize the vector database with the required tables.
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
    
    # Connect to the vector database
    conn = get_vector_db_connection()
    cursor = conn.cursor()
    
    # Create embeddings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        node_id TEXT PRIMARY KEY,
        embedding BLOB NOT NULL,
        model TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        FOREIGN KEY (node_id) REFERENCES memory_nodes (id)
    )
    ''')
    
    # Create embedding_models table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embedding_models (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        version TEXT,
        is_default BOOLEAN DEFAULT 0
    )
    ''')
    
    # Insert default embedding model
    cursor.execute('''
    INSERT OR IGNORE INTO embedding_models (id, name, provider, dimensions, version, is_default)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', ('openai-text-embedding-3-small', 'text-embedding-3-small', 'OpenAI', 1536, '1.0', 1))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    logger.info(f"Vector database initialized at {VECTOR_DB_PATH}")

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
            
            # Also update memory node if it exists
            update_memory_from_post(post)
            
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
            
            # Also create memory node
            create_memory_from_post(post)
            
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
        
        # Create memory node for the prompt
        if prompt_id > 0:
            create_memory_node({
                'id': f"prompt_{prompt_id}",
                'type': 'prompt',
                'content': prompt,
                'tags': ['prompt', route],
                'source_id': str(prompt_id),
                'source_type': 'prompt',
                'metadata': {
                    'route': route,
                    'status': status
                }
            })
            
            # If output is provided, create a node for it too
            if output:
                create_memory_node({
                    'id': f"prompt_output_{prompt_id}",
                    'type': 'prompt_output',
                    'content': output,
                    'tags': ['output', route],
                    'source_id': str(prompt_id),
                    'source_type': 'prompt',
                    'metadata': {
                        'route': route,
                        'status': status
                    }
                })
                
                # Create edge between prompt and output
                create_memory_edge({
                    'id': f"prompt_to_output_{prompt_id}",
                    'from_node_id': f"prompt_{prompt_id}",
                    'to_node_id': f"prompt_output_{prompt_id}",
                    'relation_type': 'generates'
                })
        
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
        
        # Update or create memory nodes
        output_node_id = f"prompt_output_{prompt_id}"
        
        # Check if output node exists
        if get_memory_node(output_node_id):
            # Update existing node
            update_memory_node({
                'id': output_node_id,
                'content': output,
                'metadata': {
                    'status': status
                }
            })
        else:
            # Create new output node
            create_memory_node({
                'id': output_node_id,
                'type': 'prompt_output',
                'content': output,
                'tags': ['output'],
                'source_id': str(prompt_id),
                'source_type': 'prompt',
                'metadata': {
                    'status': status
                }
            })
            
            # Create edge between prompt and output
            create_memory_edge({
                'id': f"prompt_to_output_{prompt_id}",
                'from_node_id': f"prompt_{prompt_id}",
                'to_node_id': output_node_id,
                'relation_type': 'generates'
            })
        
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

# Memory Node Functions

def create_memory_node(node: Dict[str, Any]) -> Optional[str]:
    """
    Create a new memory node.
    
    Args:
        node (dict): Node data
        
    Returns:
        Optional[str]: The ID of the created node, or None if failed.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate ID if not provided
        if 'id' not in node:
            node['id'] = f"node_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"
        
        # Convert tags to JSON string if provided as list
        tags = node.get('tags', [])
        if isinstance(tags, list):
            tags = json.dumps(tags)
        
        # Convert metadata to JSON string if provided as dict
        metadata = node.get('metadata', {})
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        
        # Insert node - use INSERT OR IGNORE to handle duplicate IDs gracefully
        cursor.execute('''
        INSERT OR IGNORE INTO memory_nodes (
            id, type, content, tags, created_at, source_id, source_type, metadata, has_embedding, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node['id'],
            node['type'],
            node['content'],
            tags,
            node.get('created_at', int(datetime.now().timestamp())),
            node.get('source_id'),
            node.get('source_type'),
            metadata,
            0,  # No embedding yet
            int(datetime.now().timestamp())
        ))
        
        # Check if the row was actually inserted (or ignored)
        row_inserted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        # Generate embedding only if the row was newly inserted
        if row_inserted:
             logger.debug(f"New memory node {node['id']}. Generating embedding.")
             generate_embedding_for_node(node['id']) 
        else:
             logger.debug(f"Memory node {node['id']} already existed. Insertion ignored.")
            
        return node['id'] # Return ID even if ignored, as the node exists
    
    except Exception as e:
        logger.error(f"Error creating memory node: {e}")
        return None

def update_memory_node(node: Dict[str, Any]) -> bool:
    """
    Update an existing memory node.
    
    Args:
        node (dict): Node data with id
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if 'type' in node:
            update_fields.append("type = ?")
            params.append(node['type'])
        
        if 'content' in node:
            update_fields.append("content = ?")
            params.append(node['content'])
            # Content changed, need new embedding
            update_fields.append("has_embedding = ?")
            params.append(0)
        
        if 'tags' in node:
            tags = node['tags']
            if isinstance(tags, list):
                tags = json.dumps(tags)
            update_fields.append("tags = ?")
            params.append(tags)
        
        if 'source_id' in node:
            update_fields.append("source_id = ?")
            params.append(node['source_id'])
        
        if 'source_type' in node:
            update_fields.append("source_type = ?")
            params.append(node['source_type'])
        
        if 'metadata' in node:
            metadata = node['metadata']
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
            update_fields.append("metadata = ?")
            params.append(metadata)
        
        # Add node ID to params
        params.append(node['id'])
        
        # Execute update if there are fields to update
        if update_fields:
            query = f"UPDATE memory_nodes SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            # If content was updated, regenerate embedding
            if 'content' in node:
                generate_embedding_for_node(node['id'])
            
            return True
        else:
            conn.close()
            return False
    
    except Exception as e:
        logger.error(f"Error updating memory node: {e}")
        return False

def update_memory_node_metadata(node_id: str, metadata_updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update the metadata for a specific memory node and touches the updated_at timestamp.
    
    Args:
        node_id (str): Node ID
        metadata_updates (dict): Metadata updates
        
    Returns:
        dict: Updated node data or None if failed
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch existing metadata
        cursor.execute("SELECT metadata FROM memory_nodes WHERE id = ?", (node_id,))
        result = cursor.fetchone()
        if not result:
            logger.error(f"Node with ID {node_id} not found for metadata update.")
            return None

        existing_metadata_json = result[0]
        existing_metadata = json.loads(existing_metadata_json) if existing_metadata_json else {}

        # 2. Merge new metadata updates
        updated_metadata = {**existing_metadata, **metadata_updates}
        updated_metadata_json = json.dumps(updated_metadata)
        updated_at = datetime.now().timestamp()

        # 3. Execute UPDATE statement
        cursor.execute("""
            UPDATE memory_nodes 
            SET metadata = ?, updated_at = ?
            WHERE id = ?
        """, (updated_metadata_json, updated_at, node_id))
        
        conn.commit()
        logger.info(f"Successfully updated metadata for node {node_id}")

        # 4. Fetch and return the updated node
        return get_memory_node(node_id) # Reuse existing function to get the full updated node

    except sqlite3.Error as e:
        logger.error(f"Database error updating metadata for node {node_id}: {e}")
        if conn:
            conn.rollback()
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding existing metadata JSON for node {node_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_memory_node(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a memory node by ID.
    
    Args:
        node_id (str): Node ID
        
    Returns:
        dict: Node data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memory_nodes WHERE id = ?", (node_id,))
        node = cursor.fetchone()
        
        conn.close()
        
        if node:
            node_dict = dict(node)
            
            # Parse tags JSON
            if node_dict.get('tags'):
                try:
                    node_dict['tags'] = json.loads(node_dict['tags'])
                except:
                    node_dict['tags'] = []
            else:
                node_dict['tags'] = []
            
            # Parse metadata JSON
            if node_dict.get('metadata'):
                try:
                    node_dict['metadata'] = json.loads(node_dict['metadata'])
                except:
                    node_dict['metadata'] = {}
            else:
                node_dict['metadata'] = {}
            
            return node_dict
        else:
            return None
    
    except Exception as e:
        logger.error(f"Error getting memory node: {e}")
        return None

def get_memory_nodes(
    node_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    search_query: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get memory nodes with filtering.
    
    Args:
        node_type (str, optional): Filter by node type
        tags (list, optional): Filter by tags
        start_date (int, optional): Filter by start date (timestamp)
        end_date (int, optional): Filter by end date (timestamp)
        search_query (str, optional): Filter by content search
        limit (int): Maximum number of nodes to return
        offset (int): Number of nodes to skip
        
    Returns:
        list: List of node dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM memory_nodes WHERE 1=1"
        params = []
        
        if node_type:
            query += " AND type = ?"
            params.append(node_type)
        
        if tags:
            # For each tag, check if it's in the JSON array
            for tag in tags:
                query += f" AND tags LIKE ?"
                params.append(f"%{tag}%")
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        
        if search_query:
            query += " AND content LIKE ?"
            params.append(f"%{search_query}%")
        
        # Add order and limit
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        cursor.execute(query, params)
        nodes = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries and parse JSON
        nodes_list = []
        for node in nodes:
            node_dict = dict(node)
            
            # Parse tags JSON
            if node_dict.get('tags'):
                try:
                    node_dict['tags'] = json.loads(node_dict['tags'])
                except:
                    node_dict['tags'] = []
            else:
                node_dict['tags'] = []
            
            # Parse metadata JSON
            if node_dict.get('metadata'):
                try:
                    node_dict['metadata'] = json.loads(node_dict['metadata'])
                except:
                    node_dict['metadata'] = {}
            else:
                node_dict['metadata'] = {}
            
            nodes_list.append(node_dict)
        
        return nodes_list
    
    except Exception as e:
        logger.error(f"Error getting memory nodes: {e}")
        return []

def get_prompt_nodes_history(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieves a list of memory nodes with type 'prompt', ordered by creation date descending."""
    conn = None
    nodes = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Select nodes where type is 'prompt', order by creation time descending, apply limit/offset
        cursor.execute("""
            SELECT node_id, node_type, content, tags, metadata, created_at, updated_at
            FROM memory_nodes 
            WHERE node_type = 'prompt'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        for row in rows:
            node = dict(zip(columns, row))
            # Deserialize JSON fields
            node['tags'] = json.loads(node['tags']) if node['tags'] else []
            node['metadata'] = json.loads(node['metadata']) if node['metadata'] else {}
            nodes.append(node)
            
        logger.info(f"Retrieved {len(nodes)} prompt nodes for history (limit={limit}, offset={offset})")
        return nodes
        
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving prompt history: {e}")
        return [] # Return empty list on error
    except json.JSONDecodeError as e:
         logger.error(f"Error decoding JSON for prompt history node: {e}")
         # Decide how to handle - skip node or return partial? Returning partial for now.
         # Consider adding node_id to log message if possible.
         return nodes # Return nodes successfully decoded so far
    finally:
        if conn:
            conn.close()

# Memory Edge Functions

def create_memory_edge(edge: Dict[str, Any]) -> bool:
    """
    Create a new memory edge.
    
    Args:
        edge (dict): Edge data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate ID if not provided
        if 'id' not in edge:
            edge['id'] = f"edge_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"
        
        # Convert metadata to JSON string if provided as dict
        metadata = edge.get('metadata', {})
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        
        # Insert edge
        cursor.execute('''
        INSERT INTO memory_edges (
            id, source_node_id, target_node_id, label, weight, created_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            edge['id'],
            edge['source_node_id'],
            edge['target_node_id'],
            edge['label'],
            edge.get('weight', 1.0),
            edge.get('created_at', int(datetime.now().timestamp())),
            metadata
        ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error creating memory edge: {e}")
        return False

def get_memory_edge(edge_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a memory edge by ID.
    
    Args:
        edge_id (str): Edge ID
        
    Returns:
        dict: Edge data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memory_edges WHERE id = ?", (edge_id,))
        edge = cursor.fetchone()
        
        conn.close()
        
        if edge:
            edge_dict = dict(edge)
            
            # Parse metadata JSON
            if edge_dict.get('metadata'):
                try:
                    edge_dict['metadata'] = json.loads(edge_dict['metadata'])
                except:
                    edge_dict['metadata'] = {}
            else:
                edge_dict['metadata'] = {}
            
            return edge_dict
        else:
            return None
    
    except Exception as e:
        logger.error(f"Error getting memory edge: {e}")
        return None

def get_memory_edges(
    source_node_id: Optional[str] = None,
    target_node_id: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get memory edges with filtering.
    
    Args:
        source_node_id (str, optional): Filter by source node ID
        target_node_id (str, optional): Filter by target node ID
        label (str, optional): Filter by label
        limit (int): Maximum number of edges to return
        offset (int): Number of edges to skip
        
    Returns:
        list: List of edge dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM memory_edges WHERE 1=1"
        params = []
        
        if source_node_id:
            query += " AND source_node_id = ?"
            params.append(source_node_id)
        
        if target_node_id:
            query += " AND target_node_id = ?"
            params.append(target_node_id)
        
        if label:
            query += " AND label = ?"
            params.append(label)
        
        # Add order and limit
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        cursor.execute(query, params)
        edges = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries and parse JSON
        edges_list = []
        for edge in edges:
            edge_dict = dict(edge)
            
            # Parse metadata JSON
            if edge_dict.get('metadata'):
                try:
                    edge_dict['metadata'] = json.loads(edge_dict['metadata'])
                except:
                    edge_dict['metadata'] = {}
            else:
                edge_dict['metadata'] = {}
            
            edges_list.append(edge_dict)
        
        return edges_list
    
    except Exception as e:
        logger.error(f"Error getting memory edges: {e}")
        return []

# Vector Embedding Functions

def generate_embedding_for_node(node_id: str) -> bool:
    """
    Generate and store embedding for a memory node using a sentence transformer.
    
    Args:
        node_id (str): Node ID from memory_nodes table.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    conn_main = None
    try:
        # 1. Get node content from main DB
        node = get_memory_node(node_id)
        if not node or not node.get('content'):
            logger.error(f"Node {node_id} not found or has no content for embedding.")
            return False
        
        node_content = node['content']
        logger.debug(f"Generating embedding for node {node_id}...")

        # 2. Generate embedding (using the globally loaded model)
        embedding = embedding_model.encode(node_content, convert_to_numpy=True)
        
        # Ensure it's float32 for consistent storage
        if embedding.dtype != np.float32:
            embedding = embedding.astype(np.float32)
            
        embedding_bytes = embedding.tobytes()
        
        # 3. Store embedding in vector DB
        conn_vec = get_vector_db_connection()
        cursor_vec = conn_vec.cursor()
        
        cursor_vec.execute('''
        INSERT OR REPLACE INTO embeddings (
            node_id, embedding, model, dimensions, created_at
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            node_id,
            embedding_bytes,
            embedding_model_name, 
            embedding_dimensions,
            int(datetime.now().timestamp())
        ))
        conn_vec.commit()
        logger.debug(f"Stored embedding for node {node_id} in vector DB.")

        # 4. Update flag in main DB
        conn_main = get_db_connection()
        cursor_main = conn_main.cursor()
        
        cursor_main.execute('''
        UPDATE memory_nodes SET has_embedding = 1, updated_at = ? WHERE id = ?
        ''', (int(datetime.now().timestamp()), node_id))
        
        conn_main.commit()
        logger.info(f"Successfully generated and stored embedding for node {node_id}.")
        return True
    
    except Exception as e:
        logger.error(f"Error generating embedding for node {node_id}: {e}", exc_info=True)
        # Rollback transactions if they were started
        if conn_main and conn_main.in_transaction: conn_main.rollback()
        return False
    finally:
        # Ensure connections opened in this function are closed
        if conn_main:
            try: conn_main.close() 
            except: pass
        if conn_vec:
            try: conn_vec.close()
            except: pass

def get_embedding(node_id: str) -> Optional[np.ndarray]:
    """
    Get embedding for a memory node.
    
    Args:
        node_id (str): Node ID
        
    Returns:
        numpy.ndarray: Embedding vector or None if not found
    """
    try:
        conn = get_vector_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT embedding, dimensions FROM embeddings WHERE node_id = ?", (node_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            embedding_bytes = result['embedding']
            dimensions = result['dimensions']
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # Ensure correct shape
            if embedding.shape[0] != dimensions:
                embedding = embedding.reshape(dimensions)
            
            return embedding
        else:
            return None
    
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return None

def search_similar_nodes(
    query_text: str,
    limit: int = 10,
    node_type: Optional[str] = None,
    min_similarity: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Search for memory nodes semantically similar to the query text using vector embeddings.
    
    Args:
        query_text (str): Query text.
        limit (int): Maximum number of results.
        node_type (str, optional): Filter results by node type AFTER similarity search.
        min_similarity (float): Minimum cosine similarity score (0 to 1).
        
    Returns:
        list: List of node dictionaries with 'similarity' score included, sorted by similarity.
    """
    conn_vec = None
    conn_main = None
    try:
        # 1. Generate query embedding
        if not query_text:
            return []
            
        query_embedding = embedding_model.encode([query_text], convert_to_numpy=True)
        
        # Ensure correct shape (1, dimensions) for cosine_similarity
        if query_embedding.ndim == 1:
             query_embedding = query_embedding.reshape(1, -1)
             
        if query_embedding.dtype != np.float32:
             query_embedding = query_embedding.astype(np.float32)

        # 2. Fetch all embeddings from vector DB
        conn_vec = get_vector_db_connection()
        cursor_vec = conn_vec.cursor()
        
        # Fetch node_id, embedding BLOB, and dimensions
        cursor_vec.execute("SELECT node_id, embedding, dimensions FROM embeddings")
        all_embeddings_data = cursor_vec.fetchall()
        conn_vec.close() # Close connection after fetching

        if not all_embeddings_data:
            logger.info("No embeddings found in the vector database.")
            return []

        # 3. Decode embeddings and calculate similarity
        node_ids = []
        stored_embeddings_list = []
        
        for row in all_embeddings_data:
            node_id = row['node_id']
            embedding_bytes = row['embedding']
            dimensions = row['dimensions'] # Use stored dimension
            
            # Decode BLOB to numpy array
            try:
                 stored_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                 # Basic sanity check for dimensions
                 if stored_embedding.size == dimensions:
                      stored_embeddings_list.append(stored_embedding.reshape(1, -1)) # Reshape for cosine_similarity
                      node_ids.append(node_id)
                 else:
                      logger.warning(f"Dimension mismatch for node {node_id}. Expected {dimensions}, got {stored_embedding.size}. Skipping.")
            except Exception as decode_err:
                 logger.error(f"Error decoding embedding for node {node_id}: {decode_err}")


        if not stored_embeddings_list:
             logger.warning("No valid embeddings decoded.")
             return []

        # Stack embeddings into a single numpy array for efficient calculation
        stored_embeddings_matrix = np.vstack(stored_embeddings_list)

        # Calculate cosine similarities
        similarities = cosine_similarity(query_embedding, stored_embeddings_matrix)[0] # Get the 1D array of scores

        # >>> ADD LOGGING <<<
        logger.debug(f"Semantic search received min_similarity threshold: {min_similarity}")
        logger.debug(f"Calculated scores (Top 5): {sorted(similarities, reverse=True)[:5]}") 

        # 4. Combine node IDs with scores, filter, and sort
        results = []
        for node_id, score in zip(node_ids, similarities):
            # >>> ADD LOGGING <<<
            logger.debug(f"Checking node {node_id}: score={score:.4f} >= threshold={min_similarity}? {score >= min_similarity}")
            if score >= min_similarity:
                results.append({'node_id': node_id, 'similarity': float(score)}) # Store as float

        # Sort by similarity descending
        results.sort(key=lambda x: x['similarity'], reverse=True)

        # Apply limit
        top_results = results[:limit]

        if not top_results:
            logger.info(f"No nodes found with similarity >= {min_similarity} for query.")
            return []
            
        top_node_ids = [res['node_id'] for res in top_results]
        similarity_map = {res['node_id']: res['similarity'] for res in top_results}

        # 5. Fetch node details from main DB for the top node IDs
        conn_main = get_db_connection()
        cursor_main = conn_main.cursor()
        
        # Prepare placeholder string for IN clause
        placeholders = ','.join('?' * len(top_node_ids))
        query = f"SELECT * FROM memory_nodes WHERE id IN ({placeholders})"
        
        # Optionally add node_type filter to the main query
        params = top_node_ids
        if node_type:
            query += " AND type = ?"
            params.append(node_type)
            
        cursor_main.execute(query, params)
        nodes_data = cursor_main.fetchall()
        conn_main.close() # Close main connection

        # 6. Combine node data with similarity scores and parse JSON fields
        final_results = []
        for node_row in nodes_data:
            node_dict = dict(node_row)
            node_id = node_dict['id']
            
            # Parse tags JSON
            if node_dict.get('tags'):
                try:
                    node_dict['tags'] = json.loads(node_dict['tags'])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode tags JSON for node {node_id}")
                    node_dict['tags'] = []
            else:
                node_dict['tags'] = []
            
            # Parse metadata JSON
            if node_dict.get('metadata'):
                try:
                    node_dict['metadata'] = json.loads(node_dict['metadata'])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode metadata JSON for node {node_id}")
                    node_dict['metadata'] = {}
            else:
                node_dict['metadata'] = {}
            
            # Add similarity score
            node_dict['similarity'] = similarity_map.get(node_id, 0.0) # Use .get just in case
            
            final_results.append(node_dict)

        # Sort the final list by similarity again, as the DB fetch order isn't guaranteed
        final_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        logger.info(f"Semantic search found {len(final_results)} similar nodes for query.")
        return final_results
    
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        # Ensure connections are closed on error
        if conn_vec:
            try: conn_vec.close() 
            except: pass
        if conn_main:
            try: conn_main.close()
            except: pass
        return []

# Integration Functions

def create_memory_from_post(post: Dict[str, Any]) -> bool:
    """
    Create memory node from a post.
    
    Args:
        post (dict): Post data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create node
        node_id = f"post_{post['source']}_{post['id']}"
        
        # Prepare content
        content = post.get('content', '')
        if post.get('title'):
            content = f"{post['title']}\n\n{content}"
        
        # Prepare tags
        tags = ['post', post['source']]
        if post.get('metadata') and post['metadata'].get('hashtags'):
            tags.extend(post['metadata']['hashtags'])
        
        # Create node
        success = create_memory_node({
            'id': node_id,
            'type': post['source'],
            'content': content,
            'tags': tags,
            'created_at': post.get('created_utc', int(datetime.now().timestamp())),
            'source_id': post['id'],
            'source_type': post['source'],
            'metadata': post.get('metadata', {})
        })
        
        return success
    
    except Exception as e:
        logger.error(f"Error creating memory from post: {e}")
        return False

def update_memory_from_post(post: Dict[str, Any]) -> bool:
    """
    Update memory node from a post.
    
    Args:
        post (dict): Post data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get node ID
        node_id = f"post_{post['source']}_{post['id']}"
        
        # Check if node exists
        node = get_memory_node(node_id)
        if not node:
            # Create new node if it doesn't exist
            return create_memory_from_post(post)
        
        # Prepare content
        content = post.get('content', '')
        if post.get('title'):
            content = f"{post['title']}\n\n{content}"
        
        # Prepare tags
        tags = ['post', post['source']]
        if post.get('metadata') and post['metadata'].get('hashtags'):
            tags.extend(post['metadata']['hashtags'])
        
        # Update node
        success = update_memory_node({
            'id': node_id,
            'content': content,
            'tags': tags,
            'metadata': post.get('metadata', {})
        })
        
        return success
    
    except Exception as e:
        logger.error(f"Error updating memory from post: {e}")
        return False

def get_memory_graph(
    node_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    search_query: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get a subgraph of the memory graph.
    
    Args:
        node_types (list, optional): Filter by node types
        tags (list, optional): Filter by tags
        start_date (int, optional): Filter by start date (timestamp)
        end_date (int, optional): Filter by end date (timestamp)
        search_query (str, optional): Filter by content search
        limit (int): Maximum number of nodes to return
        
    Returns:
        dict: Graph with nodes and edges
    """
    try:
        # Get nodes
        nodes = get_memory_nodes(
            node_type=node_types[0] if node_types and len(node_types) > 0 else None,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            limit=limit
        )
        
        # Get node IDs
        node_ids = [node['id'] for node in nodes]
        
        # Get edges between these nodes
        edges = []
        for node_id in node_ids:
            # Get outgoing edges
            outgoing_edges = get_memory_edges(source_node_id=node_id)
            for edge in outgoing_edges:
                if edge['target_node_id'] in node_ids:
                    edges.append(edge)
            
            # Get incoming edges
            incoming_edges = get_memory_edges(target_node_id=node_id)
            for edge in incoming_edges:
                if edge['source_node_id'] in node_ids and edge['id'] not in [e['id'] for e in edges]:
                    edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    except Exception as e:
        logger.error(f"Error getting memory graph: {e}")
        return {'nodes': [], 'edges': []}

def get_memory_stats() -> Dict[str, Any]:
    """
    Get memory statistics.
    
    Returns:
        dict: Memory statistics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total nodes
        cursor.execute("SELECT COUNT(*) as count FROM memory_nodes")
        total_nodes = cursor.fetchone()['count']
        
        # Get total edges
        cursor.execute("SELECT COUNT(*) as count FROM memory_edges")
        total_edges = cursor.fetchone()['count']
        
        # Get node types
        cursor.execute("SELECT type, COUNT(*) as count FROM memory_nodes GROUP BY type")
        node_types = {row['type']: row['count'] for row in cursor.fetchall()}
        
        # Get relation types
        cursor.execute("SELECT label, COUNT(*) as count FROM memory_edges GROUP BY label")
        relation_types = {row['label']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'node_types': node_types,
            'relation_types': relation_types
        }
    
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return {
            'total_nodes': 0,
            'total_edges': 0,
            'node_types': {},
            'relation_types': {}
        }

# === Reddit Tracking Functions ===

def add_tracked_subreddit(conn: sqlite3.Connection, subreddit_name: str):
    """
    Adds a subreddit to the tracking list. Stores name in lowercase.
    Uses INSERT OR IGNORE to avoid errors if the subreddit already exists.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO tracked_subreddits (name) VALUES (?)
        """, (subreddit_name.lower(),))
        logger.info(f"Attempted to add/ignore tracked subreddit: {subreddit_name.lower()}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error adding tracked subreddit {subreddit_name.lower()}: {e}")
        raise # Re-raise the exception after logging

def remove_tracked_subreddit(conn: sqlite3.Connection, subreddit_name: str):
    """
    Removes a subreddit from the tracking list. Uses lowercase name.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tracked_subreddits WHERE name = ?", (subreddit_name.lower(),))
        if cursor.rowcount > 0:
             logger.info(f"Removed tracked subreddit: {subreddit_name.lower()}")
        else:
             logger.warning(f"Attempted to remove non-existent tracked subreddit: {subreddit_name.lower()}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error removing tracked subreddit {subreddit_name.lower()}: {e}")
        raise

def get_tracked_subreddits_with_state(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Retrieves all tracked subreddits along with their last scanned post ID and active status.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT name, last_scanned_post_id, is_active
            FROM tracked_subreddits
            ORDER BY name ASC
        """)
        rows = cursor.fetchall()
        # Convert Row objects to dictionaries
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"SQLite error getting tracked subreddits: {e}")
        raise

def update_subreddit_scan_state(conn: sqlite3.Connection, subreddit_name: str, last_scanned_post_id: str):
    """
    Updates the last scanned post ID and timestamp for a specific subreddit.
    """
    cursor = conn.cursor()
    now_iso = datetime.utcnow().isoformat() + "Z"
    try:
        cursor.execute("""
            UPDATE tracked_subreddits
            SET last_scanned_post_id = ?, last_scanned_timestamp = ?
            WHERE name = ?
        """, (last_scanned_post_id, now_iso, subreddit_name.lower()))
        logger.debug(f"Updated scan state for r/{subreddit_name.lower()} to ID {last_scanned_post_id}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error updating scan state for {subreddit_name.lower()}: {e}")
        raise

def insert_reddit_posts(conn: sqlite3.Connection, posts_data: List[Dict[str, Any]]):
    """
    Inserts or replaces multiple Reddit posts into the reddit_posts table.
    Assumes posts_data is a list of dictionaries matching the table schema.
    Uses INSERT OR REPLACE to handle potential duplicates based on post ID.
    """
    if not posts_data:
        return

    cursor = conn.cursor()
    # Ensure keys match the table columns exactly
    columns = [
        "id", "subreddit", "title", "author", "created_utc", "score",
        "upvote_ratio", "num_comments", "permalink", "url", "selftext",
        "is_self", "is_video", "over_18", "spoiler", "stickied", "scraped_at",
        "sentiment", "sentiment_score", "keywords"
    ]
    placeholders = ", ".join("?" * len(columns))
    sql = f"INSERT OR REPLACE INTO reddit_posts ({', '.join(columns)}) VALUES ({placeholders})"

    # Convert list of dicts to list of tuples in the correct column order
    data_tuples = []
    for post in posts_data:
        try:
            # Ensure boolean values are stored as integers (0 or 1)
            post["is_self"] = 1 if post.get("is_self") else 0
            post["is_video"] = 1 if post.get("is_video") else 0
            post["over_18"] = 1 if post.get("over_18") else 0
            post["spoiler"] = 1 if post.get("spoiler") else 0
            post["stickied"] = 1 if post.get("stickied") else 0

            # Ensure all columns exist in the dict, providing None if missing (should not happen if _process_posts is correct)
            tuple_data = tuple(post.get(col) for col in columns)
            data_tuples.append(tuple_data)
        except KeyError as e:
             logger.error(f"Missing key {e} in post data: {post.get('id')}")
             continue # Skip this post

    if not data_tuples:
         logger.warning("No valid post data tuples generated for insertion.")
         return

    try:
        cursor.executemany(sql, data_tuples)
        logger.info(f"Inserted/Replaced {len(data_tuples)} posts into reddit_posts.")
    except sqlite3.Error as e:
        logger.error(f"SQLite error inserting reddit posts: {e}")
        # Log the first problematic tuple if possible (be careful with large data)
        if data_tuples:
             logger.error(f"First data tuple causing error (potentially): {data_tuples[0]}")
        raise

def get_reddit_feed(
    conn: sqlite3.Connection,
    subreddit: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = 'created_utc',
    sort_order: str = 'desc',
    search_term: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves a feed of Reddit posts from the database, with filtering and sorting.
    """
    cursor = conn.cursor()
    valid_sort_columns = ['created_utc', 'score', 'num_comments', 'author', 'subreddit']
    sort_by_column = sort_by if sort_by in valid_sort_columns else 'created_utc'
    sort_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'

    query = f"SELECT * FROM reddit_posts"
    params: List[Union[str, int]] = []

    conditions = []
    if subreddit:
        conditions.append("subreddit = ?")
        params.append(subreddit.lower())
    if search_term:
        # Basic search across title and selftext
        conditions.append("(title LIKE ? OR selftext LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY {sort_by_column} {sort_direction}"
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # Convert Row objects to dictionaries
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"SQLite error fetching reddit feed: {e}")
        raise

def get_tweet_by_id(conn: sqlite3.Connection, tweet_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific tweet by its ID, joining with user handle."""
    cursor = conn.cursor()
    query = f"""
        SELECT t.*, u.user_handle 
        FROM tracked_tweets t
        LEFT JOIN tracked_users u ON t.user_id = u.id 
        WHERE t.tweet_id = ?
    """
    try:
        cursor.execute(query, (tweet_id,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            tweet_dict = dict(zip(columns, row))
            return tweet_dict
        else:
            return None
    except sqlite3.Error as e:
        logger.error(f"SQLite error fetching tweet by ID {tweet_id}: {e}")
        raise # Re-raise to be handled by the API route

# === Twitter Tracking Functions ===

def get_twitter_feed(
    conn: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
    keyword: Optional[str] = None,
    sort_by: str = 'created_at', # Changed default to created_at
    sort_order: str = 'desc'
) -> List[Dict[str, Any]]:
    """Retrieves a feed of Twitter posts from the database, with filtering and sorting."""
    cursor = conn.cursor()
    # Updated valid sort columns for tracked_tweets table
    valid_sort_columns = [
        'created_at', 'content', 'retweet_count', 
        'like_count', 'reply_count', 'score' 
    ]
    sort_by_column = sort_by if sort_by in valid_sort_columns else 'created_at'
    sort_direction = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
    
    # Include user_handle from tracked_users table via JOIN
    query = f"""
        SELECT t.*, u.user_handle 
        FROM tracked_tweets t
        JOIN tracked_users u ON t.user_id = u.id 
    """
    params: List[Union[str, int]] = [] # Need to import Union from typing

    conditions = []
    if keyword:
        conditions.append("t.content LIKE ?")
        params.append(f"%{keyword}%")
    
    # Add more conditions if needed (e.g., filter by user_id)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Ensure ORDER BY references the table alias 't' if column names are ambiguous
    query += f" ORDER BY t.{sort_by_column} {sort_direction}"
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # Convert Row objects to dictionaries
        columns = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            tweet_dict = dict(zip(columns, row)) 
            results.append(tweet_dict)
        return results
    except sqlite3.Error as e:
        logger.error(f"SQLite error fetching twitter feed: {e}")
        raise # Re-raise to be handled by the API route

# === End Reddit Tracking Functions ===

async def regenerate_all_embeddings(force_model_name: str = embedding_model_name):
    """
    Clears existing embeddings and regenerates them for all memory nodes.
    Uses the globally defined embedding_model.

    Args:
        force_model_name: The model name to ensure is used for regeneration.
                         Defaults to the globally defined embedding_model_name.
    """
    logger.info("Starting regeneration of all embeddings...")
    conn_vec = None
    conn_main = None
    nodes_to_process = []
    processed_count = 0
    failed_count = 0

    # Basic check to ensure the intended model is loaded
    if embedding_model_name != force_model_name:
         logger.warning(f"Current global model '{embedding_model_name}' differs from requested '{force_model_name}'. Ensure the correct model is loaded globally.")
         # Depending on strictness, we could raise an error or just proceed with the global one.
         # Let's proceed but log the warning prominently.

    try:
        # 1. Clear old embeddings from vector DB
        conn_vec = get_vector_db_connection()
        cursor_vec = conn_vec.cursor()
        logger.info("Clearing existing embeddings from vectors.sqlite...")
        cursor_vec.execute("DELETE FROM embeddings")
        conn_vec.commit()
        logger.info("Existing embeddings cleared.")
        conn_vec.close() # Close vector connection for now

        # 2. Mark all nodes for re-embedding in main DB and get IDs
        conn_main = get_db_connection()
        cursor_main = conn_main.cursor()
        logger.info("Marking all memory nodes for re-embedding (has_embedding=0)...")
        cursor_main.execute("UPDATE memory_nodes SET has_embedding = 0")
        conn_main.commit()
        logger.info("Memory nodes marked.")

        logger.info("Fetching all node IDs to process...")
        cursor_main.execute("SELECT id FROM memory_nodes")
        nodes_to_process = [row['id'] for row in cursor_main.fetchall()]
        logger.info(f"Found {len(nodes_to_process)} nodes to regenerate embeddings for.")
        conn_main.close() # Close main connection for now

        # 3. Iterate and regenerate
        # Note: generate_embedding_for_node handles its own DB connections
        logger.info("Beginning embedding generation loop...")
        for i, node_id in enumerate(nodes_to_process):
            logger.debug(f"Processing node {i+1}/{len(nodes_to_process)}: {node_id}")
            # Assuming generate_embedding_for_node is synchronous as currently written
            # If it were async, you would need: await generate_embedding_for_node(node_id)
            success = generate_embedding_for_node(node_id)
            if success:
                processed_count += 1
            else:
                failed_count += 1
            # Optional: add a small delay to avoid overwhelming resources if needed
            # await asyncio.sleep(0.05) # Requires the function to be async

        logger.info(f"Embedding regeneration complete. Success: {processed_count}, Failed: {failed_count}")

    except Exception as e:
        logger.error(f"Error during embedding regeneration: {e}", exc_info=True)
        # Rollback potentially open transactions if error happened mid-operation
        if conn_main and conn_main.in_transaction: conn_main.rollback()
        if conn_vec and conn_vec.in_transaction: conn_vec.rollback()
    finally:
        # Ensure connections opened in this function are closed
        if conn_main:
            try: conn_main.close() 
            except: pass
        if conn_vec:
            try: conn_vec.close()
            except: pass

def get_top_reddit_posts(conn, limit: int = 10, metric: str = 'score') -> List[Dict[str, Any]]:
    """Retrieve the top N Reddit posts based on a specified metric."""
    cursor = conn.cursor()
    # Validate metric column
    valid_metrics = ['score', 'num_comments', 'created_utc']
    if metric not in valid_metrics:
        metric = 'score' # Default to score

    # Construct the query
    query = f"""
        SELECT 
            id, subreddit, title, author, created_utc, score, upvote_ratio,
            num_comments, permalink, url, selftext, is_self, is_video, 
            over_18, spoiler, stickied, scraped_at, sentiment, sentiment_score, keywords
        FROM reddit_posts
        ORDER BY {metric} DESC
        LIMIT ?
    """

    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    # Convert rows to list of dictionaries
    results = [dict(row) for row in rows]
    # Deserialize JSON fields if needed (keywords?)
    for result in results:
        if result.get('keywords'):
            try:
                result['keywords'] = json.loads(result['keywords']) if isinstance(result['keywords'], str) else result['keywords']
            except json.JSONDecodeError:
                 logger.warning(f"Failed to decode keywords JSON for Reddit post {result.get('id')}")
                 result['keywords'] = []
        else:
            result['keywords'] = []
    return results

def get_top_twitter_posts(conn, limit: int = 10, metric: str = 'retweet_count') -> List[Dict[str, Any]]:
    """Retrieve the top N tweets based on a specified metric."""
    cursor = conn.cursor()
    # Validate metric column to prevent SQL injection
    valid_metrics = ['engagement_retweets', 'engagement_likes', 'engagement_replies', 'score', 'date_posted']
    if metric not in valid_metrics:
        # Ensure default matches a valid DB column
        metric = 'engagement_retweets' 

    # Construct the query safely with JOIN
    query = f"""
        SELECT 
            t.tweet_id, t.user_id, u.handle, t.content, t.date_posted, 
            t.url, t.engagement_likes, t.engagement_retweets, t.engagement_replies,
            t.sentiment, t.keywords, t.score
        FROM tracked_tweets t
        JOIN tracked_users u ON t.user_id = u.id
        ORDER BY t.{metric} DESC 
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    conn.row_factory = sqlite3.Row # Use row factory for dict access

    # Convert rows to list of dictionaries using correct indices/names
    results = []
    for row in rows:
        try:
            engagement_dict = {
                "likes": row['engagement_likes'] or 0,
                "retweets": row['engagement_retweets'] or 0,
                "replies": row['engagement_replies'] or 0
            }
            keywords_list = json.loads(row['keywords']) if row['keywords'] else []
            # Construct full URL (assuming URL column stores path)
            base_nitter_url = "https://nitter.net" 
            partial_url = row['url'] 
            full_url = f"{base_nitter_url}{partial_url}" if partial_url and partial_url.startswith('/') else partial_url

            results.append({
                "id": row['tweet_id'],
                "user_id": row['user_id'],
                "handle": row['handle'], # Get handle from JOIN
                "content": row['content'],
                "date_posted": str(row['date_posted']) if row['date_posted'] else None,
                "url": full_url,
                "sentiment": row['sentiment'],
                "engagement": engagement_dict,
                "keywords": keywords_list,
                "score": row['score'] 
            })
        except Exception as parse_err:
            logger.error(f"Error parsing tweet row for top posts (ID: {row.get('tweet_id', 'unknown')}): {parse_err}", exc_info=True)
            continue # Skip faulty row

    return results

# Example usage
if __name__ == "__main__":
    import asyncio # Make sure asyncio is imported

    # Optional: Setup logging specifically for script execution if needed
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Initialize the databases (important if they don't exist)
    init_db()
    init_vector_db()
    logger.info("Databases initialized for script execution.")

    # --- RUN REGENERATION ---
    logger.info("Running embedding regeneration function...")
    # Since regenerate_all_embeddings is async, we need asyncio.run
    # If generate_embedding_for_node remains sync, regenerate_all_embeddings can be sync too
    # Let's assume it stays async for now due to potential future async ops
    asyncio.run(regenerate_all_embeddings())
    logger.info("Embedding regeneration function finished.")

    # --- Optional: Add other testing code after regeneration if needed ---
    # print("Running other tests...")
    # post = { 
    #     'id': 'test_post_1',
    #     'source': 'script',
    #     'title': 'Regen Test Post',
    #     'content': 'This post was added after regeneration.',
    #     'author': 'script_user',
    #     'created_utc': int(datetime.now().timestamp()),
    # } 
    # success = store_post(post)
    # print(f"Test post stored: {success}")
    
    # print("Script finished.")
