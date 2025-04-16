"""
Basic database operations and connections.

This module provides the essential database operations and connections,
separate from the enhanced database functionality in db_enhanced.py.
"""

import os
import sqlite3
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Database paths
DB_PATH = "data/memory.sqlite"

def get_db_connection():
    """
    Get a connection to the SQLite database.
    Sets up the connection with row factory and WAL mode for better concurrency.
    
    Returns:
        sqlite3.Connection: Connection to the database
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Enable Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    return conn

def init_db():
    """
    Initialize the database with the required tables.
    This is a simplified version that only creates the memory_nodes table.
    The full version is in db_enhanced.py.
    """
    try:
        conn = get_db_connection()
        
        # Create memory nodes table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS memory_nodes (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            type TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            has_embedding INTEGER DEFAULT 0,
            tags TEXT,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close() 