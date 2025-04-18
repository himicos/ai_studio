#!/usr/bin/env python
"""
Simple script to update DB_PATH in db.py
"""

import os
import re

def update_db_path():
    db_path = "ai_studio_package/infra/db.py"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return False
    
    print(f"Reading {db_path}...")
    with open(db_path, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_path = db_path + ".bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Backup created at {backup_path}")
    
    # Find current DB_PATH
    db_path_match = re.search(r'DB_PATH\s*=\s*["\']([^"\']+)["\']', content)
    if not db_path_match:
        print("Could not find DB_PATH in file")
        return False
    
    current_path = db_path_match.group(1)
    print(f"Current DB_PATH: {current_path}")
    
    # Always use memory/memory.sqlite
    new_path = "memory/memory.sqlite"
    print(f"Setting new DB_PATH: {new_path}")
    
    # Update the file
    new_content = re.sub(
        r'(DB_PATH\s*=\s*)["\']([^"\']+)["\']',
        f'\\1"{new_path}"  # Unified database path',
        content
    )
    
    with open(db_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated {db_path} to use {new_path}")
    print("\nNow make sure not to call init_db() in run_embeddings.py as it may reset the database")
    print("You can check that tables are properly initialized using:")
    print("  python diagnose_db.py")
    return True

if __name__ == "__main__":
    update_db_path() 