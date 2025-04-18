#!/usr/bin/env python
"""
Fix the database inconsistency between memory/memory.sqlite and data/memory.sqlite
"""

import os
import sqlite3
import shutil
import sys

def check_db(path):
    """Check tables and row counts in a database"""
    if not os.path.exists(path):
        print(f"Database {path} doesn't exist")
        return {}
    
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get row counts for each table
    table_counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
        except Exception as e:
            print(f"Error counting rows in {table}: {e}")
            table_counts[table] = -1
    
    conn.close()
    return table_counts

def fix_db_issue():
    memory_db = "memory/memory.sqlite"
    data_db = "data/memory.sqlite"
    
    # Check both databases
    print(f"Checking {memory_db}...")
    memory_counts = check_db(memory_db)
    for table, count in memory_counts.items():
        print(f"  {table}: {count} rows")
    
    print(f"\nChecking {data_db}...")
    data_counts = check_db(data_db)
    for table, count in data_counts.items():
        print(f"  {table}: {count} rows")
    
    # Suggest fixes
    print("\nSuggested fixes:")
    
    # 1. Make sure the script uses the correct DB
    script_path = os.path.join("ai_studio_package", "scripts", "run_embeddings.py")
    if os.path.exists(script_path):
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check if it's already using the right DB path
        if "memory/memory.sqlite" in content and "data/memory.sqlite" not in content:
            print("1. Update run_embeddings.py to check for both database paths")
            print("   (Already fixed by previous fix_run_embeddings.py script)")
    
    # 2. Check if DB paths match in infra/db.py
    db_path = os.path.join("ai_studio_package", "infra", "db.py")
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            content = f.read()
        
        # Extract DB_PATH value
        import re
        db_path_match = re.search(r'DB_PATH\s*=\s*["\']([^"\']+)["\']', content)
        if db_path_match:
            configured_path = db_path_match.group(1)
            print(f"2. The DB_PATH in db.py is set to: {configured_path}")
            
            if configured_path != "memory/memory.sqlite" and os.path.exists("memory/memory.sqlite"):
                if input("   Would you like to update it to 'memory/memory.sqlite'? (y/n): ").lower() == 'y':
                    new_content = re.sub(
                        r'(DB_PATH\s*=\s*)["\']([^"\']+)["\']', 
                        r'\1"memory/memory.sqlite"', 
                        content
                    )
                    with open(db_path, 'w') as f:
                        f.write(new_content)
                    print("   Updated db.py to use memory/memory.sqlite")
    
    # 3. Ask if user wants to copy data between DBs
    if 'reddit_posts' in memory_counts and memory_counts['reddit_posts'] > 0 and \
       'reddit_posts' in data_counts and data_counts['reddit_posts'] == 0:
        if input("\n3. Would you like to copy reddit_posts data from memory/memory.sqlite to data/memory.sqlite? (y/n): ").lower() == 'y':
            # Make backup first
            if os.path.exists(data_db):
                backup_path = data_db + ".bak"
                shutil.copy2(data_db, backup_path)
                print(f"   Created backup at {backup_path}")
            
            # Copy data
            src_conn = sqlite3.connect(memory_db)
            src_cursor = src_conn.cursor()
            
            dst_conn = sqlite3.connect(data_db)
            dst_cursor = dst_conn.cursor()
            
            # Get column names
            src_cursor.execute("PRAGMA table_info(reddit_posts)")
            columns = [row[1] for row in src_cursor.fetchall()]
            columns_str = ", ".join(columns)
            placeholder_str = ", ".join(["?" for _ in columns])
            
            # Get data from source
            src_cursor.execute(f"SELECT {columns_str} FROM reddit_posts")
            rows = src_cursor.fetchall()
            
            # Insert into destination
            for row in rows:
                try:
                    dst_cursor.execute(f"INSERT OR IGNORE INTO reddit_posts ({columns_str}) VALUES ({placeholder_str})", row)
                except Exception as e:
                    print(f"   Error inserting row: {e}")
            
            dst_conn.commit()
            src_conn.close()
            dst_conn.close()
            
            print(f"   Copied {len(rows)} rows from {memory_db} to {data_db}")
    
    print("\nDone! Run the script again to check results:")
    print("python fix_db_issue.py")

if __name__ == "__main__":
    fix_db_issue() 