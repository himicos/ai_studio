#!/usr/bin/env python
"""
Simple script to check database tables
"""

import os
import sqlite3
import sys

def check_db(path):
    print(f"Checking database at {path}")
    print(f"File exists: {os.path.exists(path)}")
    
    if not os.path.exists(path):
        print(f"Error: Database file {path} does not exist")
        return
    
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"Tables in database: {', '.join(tables)}")
        
        # Check for specific tables
        print(f"'reddit_posts' exists: {'reddit_posts' in tables}")
        print(f"'memory_nodes' exists: {'memory_nodes' in tables}")
        
        # If reddit_posts exists, check its schema
        if 'reddit_posts' in tables:
            cursor.execute("PRAGMA table_info(reddit_posts)")
            columns = [row['name'] for row in cursor.fetchall()]
            print(f"Columns in reddit_posts: {', '.join(columns)}")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM reddit_posts")
            count = cursor.fetchone()[0]
            print(f"Number of rows in reddit_posts: {count}")
            
            # Sample first row if available
            if count > 0:
                cursor.execute("SELECT * FROM reddit_posts LIMIT 1")
                row = cursor.fetchone()
                print("Sample row keys:", list(dict(row).keys()))
        
    except Exception as e:
        print(f"Error accessing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Check memory/memory.sqlite
    check_db("memory/memory.sqlite")
    
    # Also check data/memory.sqlite if it exists
    if os.path.exists("data/memory.sqlite"):
        print("\n")
        check_db("data/memory.sqlite") 