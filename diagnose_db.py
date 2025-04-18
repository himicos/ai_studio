#!/usr/bin/env python
"""
Diagnose the database state and connection issues
"""

import os
import sqlite3
import sys

def diagnose_db():
    print("=== DATABASE PATH DIAGNOSIS ===")
    memory_path = "memory/memory.sqlite"
    data_path = "data/memory.sqlite"
    
    print(f"memory/memory.sqlite exists: {os.path.exists(memory_path)}")
    print(f"data/memory.sqlite exists: {os.path.exists(data_path)}")
    
    # Check both databases
    for path in [memory_path, data_path]:
        if os.path.exists(path):
            print(f"\n=== Examining {path} ===")
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Tables: {', '.join(tables)}")
            
            # Check rows in key tables
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table}: {count} rows")
                    
                    # Sample data from important tables
                    if table in ['reddit_posts', 'memory_nodes'] and count > 0:
                        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                        row = dict(cursor.fetchone())
                        print(f"  Sample {table} entry ID: {row.get('id')}")
                        print(f"  Sample {table} columns: {list(row.keys())}")
                except Exception as e:
                    print(f"  Error reading {table}: {e}")
            
            # Check for WAL mode
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            print(f"Journal mode: {journal_mode}")
            
            conn.close()
    
    print("\n=== CHECKING DB MODULE PATH ===")
    
    try:
        # Try to import directly from the project
        sys.path.append(os.path.abspath("."))
        from ai_studio_package.infra.db import DB_PATH, get_db_connection
        
        print(f"DB_PATH from module: {DB_PATH}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables via module connection: {', '.join(tables)}")
        
        # Check rows in reddit_posts
        if 'reddit_posts' in tables:
            cursor.execute("SELECT COUNT(*) FROM reddit_posts")
            count = cursor.fetchone()[0]
            print(f"reddit_posts via module: {count} rows")
        
        conn.close()
    except Exception as e:
        print(f"Error checking module: {e}")
    
    print("\n=== RECOMMENDATIONS ===")
    print("Based on the diagnosis:")
    if os.path.exists(memory_path) and os.path.exists(data_path):
        print("1. Both databases exist. You should consolidate to one.")
        print("2. Update db.py to use the database with the most data.")
        print("3. Consider backing up both before proceeding.")

if __name__ == "__main__":
    diagnose_db() 