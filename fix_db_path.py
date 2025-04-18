#!/usr/bin/env python
"""
Fix the database path across all files to ensure consistency
"""

import os
import shutil
import re
import sqlite3
from pathlib import Path

def ensure_dir(path):
    """Ensure directory exists"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def check_db_contents(path):
    """Check basic database contents and return table info"""
    if not os.path.exists(path):
        return {"exists": False, "tables": [], "counts": {}}
    
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get counts for key tables
        counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = -1
        
        conn.close()
        return {
            "exists": True,
            "tables": tables,
            "counts": counts
        }
    except Exception as e:
        print(f"Error checking {path}: {e}")
        return {"exists": False, "tables": [], "counts": {}, "error": str(e)}

def copy_db(src, dest, overwrite=False):
    """Copy database file with backup"""
    if not os.path.exists(src):
        print(f"Source database {src} doesn't exist")
        return False
    
    if os.path.exists(dest) and not overwrite:
        print(f"Destination {dest} already exists and overwrite=False")
        return False
    
    # Create backup if destination exists
    if os.path.exists(dest):
        backup = dest + ".bak"
        print(f"Creating backup of {dest} to {backup}")
        shutil.copy2(dest, backup)
    
    # Ensure directory exists
    ensure_dir(dest)
    
    # Copy the file
    print(f"Copying {src} to {dest}")
    shutil.copy2(src, dest)
    return True

def fix_db_paths():
    """Fix database paths across the codebase"""
    # Define paths
    memory_db = "memory/memory.sqlite"
    data_db = "data/memory.sqlite"
    target_db = "data/memory.sqlite"  # <-- Our desired final location
    
    # 1. Check database contents
    memory_info = check_db_contents(memory_db)
    data_info = check_db_contents(data_db)
    
    print(f"\nChecking database: {memory_db}")
    print(f"  Exists: {memory_info['exists']}")
    if memory_info['exists']:
        print(f"  Tables: {', '.join(memory_info['tables'])}")
        for table, count in memory_info['counts'].items():
            print(f"    {table}: {count} rows")
    
    print(f"\nChecking database: {data_db}")
    print(f"  Exists: {data_info['exists']}")
    if data_info['exists']:
        print(f"  Tables: {', '.join(data_info['tables'])}")
        for table, count in data_info['counts'].items():
            print(f"    {table}: {count} rows")
    
    # 2. Determine which DB to use as source
    source_db = None
    if memory_info['exists'] and memory_info['counts'].get('reddit_posts', 0) > 0:
        source_db = memory_db
        print(f"\nUsing {memory_db} as source (has {memory_info['counts'].get('reddit_posts', 0)} reddit posts)")
    elif data_info['exists'] and data_info['counts'].get('reddit_posts', 0) > 0:
        source_db = data_db
        print(f"\nUsing {data_db} as source (has {data_info['counts'].get('reddit_posts', 0)} reddit posts)")
    else:
        print("\nNeither database has reddit_posts data!")
        if memory_info['exists']:
            source_db = memory_db
            print(f"Falling back to {memory_db} as source")
        elif data_info['exists']:
            source_db = data_db
            print(f"Falling back to {data_db} as source")
        else:
            print("No valid database found!")
            return False
    
    # 3. Copy source DB to target if needed
    if source_db != target_db:
        if not copy_db(source_db, target_db, overwrite=False):
            if input(f"Overwrite {target_db} with {source_db}? (y/n): ").lower() == 'y':
                copy_db(source_db, target_db, overwrite=True)
            else:
                print("Aborting without copying.")
                return False
    
    # 4. Update db.py to use target_db path
    db_path = "ai_studio_package/infra/db.py"
    if os.path.exists(db_path):
        print(f"\nUpdating database path in {db_path}")
        with open(db_path, 'r') as f:
            content = f.read()
        
        # Check current path
        db_path_match = re.search(r'DB_PATH\s*=\s*["\']([^"\']+)["\']', content)
        if db_path_match:
            current_path = db_path_match.group(1)
            print(f"  Current DB_PATH: {current_path}")
            
            # Replace with target path
            new_content = re.sub(
                r'(DB_PATH\s*=\s*)["\']([^"\']+)["\']', 
                f'\\1"data/memory.sqlite"  # Updated for unified approach', 
                content
            )
            
            # Write back to file
            with open(db_path, 'w') as f:
                f.write(new_content)
            print(f"  Updated DB_PATH to: data/memory.sqlite")
    
    # 5. Verify final DB
    target_info = check_db_contents(target_db)
    print(f"\nVerifying target database: {target_db}")
    print(f"  Tables: {', '.join(target_info['tables'])}")
    for table, count in target_info['counts'].items():
        print(f"    {table}: {count} rows")
    
    # 6. Update or create init_script to call init_db()
    main_py = "ai_studio_package/main.py"
    if os.path.exists(main_py):
        print(f"\nChecking main.py for init_db() call")
        with open(main_py, 'r') as f:
            content = f.read()
        
        if "init_db()" not in content and "from ai_studio_package.infra.db import init_db" not in content:
            # Add init_db call to startup code
            with open(main_py, 'r') as f:
                lines = f.readlines()
            
            # Find a good place to add the import and function call
            app_setup_index = -1
            for i, line in enumerate(lines):
                if "app = FastAPI" in line:
                    app_setup_index = i
                    break
            
            if app_setup_index >= 0:
                # Add before app initialization
                lines.insert(app_setup_index, "\n# Initialize database\nfrom ai_studio_package.infra.db import init_db\ninit_db()\n\n")
                
                with open(main_py, 'w') as f:
                    f.writelines(lines)
                print("  Added init_db() call to main.py")
            else:
                print("  Couldn't find a good place to add init_db() in main.py")
    
    print("\nDone! Database paths have been unified to use data/memory.sqlite.")
    return True

if __name__ == "__main__":
    fix_db_paths() 