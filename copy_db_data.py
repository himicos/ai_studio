#!/usr/bin/env python
"""
Copy data between databases
"""

import os
import sqlite3
import shutil
import sys

def copy_table_data(src_path, dest_path, table_name):
    """Copy table data from source to destination"""
    if not os.path.exists(src_path) or not os.path.exists(dest_path):
        print(f"Source or destination database doesn't exist")
        return False
    
    try:
        # Connect to both databases
        src_conn = sqlite3.connect(src_path)
        src_conn.row_factory = sqlite3.Row
        src_cursor = src_conn.cursor()
        
        dest_conn = sqlite3.connect(dest_path)
        dest_cursor = dest_conn.cursor()
        
        # Check if table exists in both databases
        src_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not src_cursor.fetchone():
            print(f"Table {table_name} doesn't exist in source database")
            return False
            
        dest_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not dest_cursor.fetchone():
            print(f"Table {table_name} doesn't exist in destination database")
            return False
        
        # Get column names from source table
        src_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in src_cursor.fetchall()]
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(["?" for _ in columns])
        
        # Get data from source
        src_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
        rows = src_cursor.fetchall()
        print(f"Found {len(rows)} rows in source {table_name} table")
        
        # Begin transaction in destination
        dest_conn.execute("BEGIN TRANSACTION")
        
        # Get current row count in destination
        dest_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        dest_count_before = dest_cursor.fetchone()[0]
        
        # Insert into destination
        inserted = 0
        errors = 0
        for row in rows:
            try:
                values = tuple(row[col] for col in columns)
                dest_cursor.execute(f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders_str})", values)
                inserted += 1
            except Exception as e:
                print(f"Error inserting row: {e}")
                errors += 1
        
        # Commit transaction
        dest_conn.commit()
        
        # Get new row count
        dest_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        dest_count_after = dest_cursor.fetchone()[0]
        
        print(f"Inserted/updated {inserted} rows, errors: {errors}")
        print(f"Destination {table_name} rows: {dest_count_before} -> {dest_count_after}")
        
        # Close connections
        src_conn.close()
        dest_conn.close()
        
        return True
    except Exception as e:
        print(f"Error copying data: {e}")
        return False

def copy_all_data():
    """Copy all necessary data between databases"""
    memory_db = "memory/memory.sqlite"
    data_db = "data/memory.sqlite"
    
    # Ensure both databases exist
    if not os.path.exists(memory_db):
        print(f"Source database {memory_db} doesn't exist")
        return False
        
    if not os.path.exists(data_db):
        print(f"Destination database {data_db} doesn't exist")
        return False
    
    # Make a backup of the destination database
    backup_path = data_db + ".bak"
    print(f"Creating backup of {data_db} to {backup_path}")
    shutil.copy2(data_db, backup_path)
    
    # Tables to copy
    tables = ["reddit_posts", "memory_nodes"]
    
    success = True
    for table in tables:
        print(f"\nCopying {table} from {memory_db} to {data_db}...")
        if not copy_table_data(memory_db, data_db, table):
            success = False
    
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reverse":
        print("Copying from data/memory.sqlite to memory/memory.sqlite...")
        copy_table_data("data/memory.sqlite", "memory/memory.sqlite", "reddit_posts")
        copy_table_data("data/memory.sqlite", "memory/memory.sqlite", "memory_nodes")
    else:
        print("Copying from memory/memory.sqlite to data/memory.sqlite...")
        copy_all_data() 