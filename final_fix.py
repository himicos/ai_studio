#!/usr/bin/env python
"""
Final script to fix the run_embeddings.py issue
"""

import os
import sys
import sqlite3
import shutil
import re

def check_db(path):
    """Check if database has data"""
    if not os.path.exists(path):
        return False, {}
    
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check key tables
        tables = ["reddit_posts", "memory_nodes"]
        counts = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0
        
        conn.close()
        return True, counts
    except:
        return False, {}

def fix_run_embeddings():
    """Fix issues in run_embeddings.py"""
    script_path = "ai_studio_package/scripts/run_embeddings.py"
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        return False
    
    # Create backup
    backup_path = script_path + ".final.bak"
    if not os.path.exists(backup_path):
        print(f"Creating backup at {backup_path}")
        shutil.copy2(script_path, backup_path)
    
    # Read file
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Add diagnostic print to show actual data
    if "print(f\"Using {db.DB_PATH} with" not in content:
        # Add after the DB_PATH override
        content = re.sub(
            r'print\(f"\[run_embeddings\.py\] Using (.*) for DB_PATH"\)',
            r'print(f"[run_embeddings.py] Using \\1 for DB_PATH")\n'
            r'    # Add diagnostic info\n'
            r'    try:\n'
            r'        diag_conn = get_db_connection()\n'
            r'        diag_cursor = diag_conn.cursor()\n'
            r'        diag_cursor.execute("SELECT COUNT(*) FROM reddit_posts")\n'
            r'        reddit_count = diag_cursor.fetchone()[0]\n'
            r'        diag_cursor.execute("SELECT COUNT(*) FROM memory_nodes")\n'
            r'        memory_count = diag_cursor.fetchone()[0]\n'
            r'        print(f"Using {db.DB_PATH} with {reddit_count} reddit_posts and {memory_count} memory_nodes")\n'
            r'        diag_conn.close()\n'
            r'    except Exception as e:\n'
            r'        print(f"Diagnostic error: {e}")',
            content
        )
    
    # Fix 2: Comment out init_db() call
    content = re.sub(
        r'(logger\.info\(f"Initializing database schema if necessary at \{db\.DB_PATH\}\.\.\."\)\s+)(init_db\(\))',
        r'\1# \2  # Commented out to prevent DB reset',
        content
    )
    
    # Fix 3: Fix row fetching issue
    content = re.sub(
        r'cursor\.execute\("SELECT rp\.id FROM reddit_posts rp LIMIT 5"\)',
        r'cursor.execute("SELECT id FROM reddit_posts LIMIT 5")',
        content
    )
    
    # Write changes back
    with open(script_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {script_path} with fixes")
    print("Now try running:")
    print("cd ai_studio_package/scripts && python run_embeddings.py --process-reddit")
    
    return True

if __name__ == "__main__":
    # First ensure memory/memory.sqlite is being used
    db_path = "ai_studio_package/infra/db.py"
    if os.path.exists(db_path):
        with open(db_path, 'r') as f:
            content = f.read()
        
        # Check DB_PATH
        db_path_match = re.search(r'DB_PATH\s*=\s*["\']([^"\']+)["\']', content)
        if db_path_match:
            current_path = db_path_match.group(1)
            if current_path != "memory/memory.sqlite":
                print("Warning: DB_PATH is not set to memory/memory.sqlite")
                print("Run python update_db_path.py first")
                sys.exit(1)
    
    # Fix run_embeddings.py
    fix_run_embeddings() 