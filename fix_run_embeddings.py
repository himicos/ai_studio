#!/usr/bin/env python
"""
Fix the run_embeddings.py script to properly handle database paths
"""

import os
import sys
import re

def fix_run_embeddings():
    script_path = os.path.join("ai_studio_package", "scripts", "run_embeddings.py")
    
    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return False
    
    print(f"Reading {script_path}...")
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Make a backup
    backup_path = script_path + ".bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Backup created at {backup_path}")
    
    # Fix 1: Add datetime import
    if "from datetime import datetime as dt" not in content:
        print("Adding missing datetime import...")
        content = re.sub(
            r"from typing import List, Dict, Any, Optional",
            r"from typing import List, Dict, Any, Optional\nfrom datetime import datetime as dt  # Added for dt.fromisoformat",
            content
        )
    
    # Fix 2: Fix DB_PATH handling
    print("Updating database path handling...")
    # Replace the DB_PATH override block with more robust path checking
    db_override_pattern = r"# IMPORTANT: Override the database path.*?# Now import and use database functions as normal"
    db_override_replacement = """# Import DB functionality
from ai_studio_package.infra import db
# Store original path for debugging
ORIGINAL_DB_PATH = db.DB_PATH
# Check if memory directory exists
memory_path = os.path.join("memory", "memory.sqlite")
data_path = os.path.join("data", "memory.sqlite")

if os.path.exists(memory_path):
    # Override to the correct path if memory/memory.sqlite exists
    db.DB_PATH = memory_path
    print(f"[run_embeddings.py] Using memory/memory.sqlite for DB_PATH")
elif os.path.exists(data_path):
    # Use data/memory.sqlite if it exists
    db.DB_PATH = data_path
    print(f"[run_embeddings.py] Using data/memory.sqlite for DB_PATH")
else:
    print(f"[run_embeddings.py] Using default DB_PATH: {db.DB_PATH}")

# Now import and use database functions as normal"""
    
    content = re.sub(db_override_pattern, db_override_replacement, content, flags=re.DOTALL)
    
    # Fix 3: Update logging to show the DB path
    content = re.sub(
        r'logger.info\("Initializing database schema if necessary..."\)',
        r'logger.info(f"Initializing database schema if necessary at {db.DB_PATH}...")',
        content
    )
    
    # Write changes back to file
    print(f"Writing changes to {script_path}...")
    with open(script_path, 'w') as f:
        f.write(content)
    
    print("Done! Run the script now with:")
    print("cd ai_studio_package/scripts && python run_embeddings.py --process-reddit")
    return True

if __name__ == "__main__":
    success = fix_run_embeddings()
    sys.exit(0 if success else 1) 