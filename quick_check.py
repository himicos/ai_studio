# quick_check.py
import sqlite3
import os
import time # Import time

# Add a delay to allow WAL checkpointing/filesystem sync
print("Waiting 5 seconds before checking database...")
time.sleep(5) # Add 5-second delay

# Define the path to the CORRECT existing database
DB_PATH = os.path.join("memory", "memory.sqlite")  # <-- Changed from "data" to "memory"

print(f"Attempting to connect to DB at: {os.path.abspath(DB_PATH)}")

if not os.path.exists(DB_PATH):
    print(f"ERROR: Database file not found at {DB_PATH}")
    exit()

conn = None
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check total posts
    cursor.execute("SELECT COUNT(*) FROM reddit_posts;")
    post_count = cursor.fetchone()[0]
    print(f"Total rows in reddit_posts: {post_count}")

    # Check existing summaries
    cursor.execute("SELECT COUNT(*) FROM memory_nodes WHERE type = 'reddit_summary';")
    summary_count = cursor.fetchone()[0]
    print(f"Total rows in memory_nodes with type='reddit_summary': {summary_count}")

    # Run the exact query from run_embeddings.py
    print("\nChecking for posts needing summary (LIMIT 10):")
    query = """
        SELECT rp.id
        FROM reddit_posts rp
        LEFT JOIN memory_nodes mn ON mn.id = 'reddit_summary_' || rp.id
        WHERE mn.id IS NULL
        ORDER BY rp.created_utc DESC
        LIMIT 10;
    """
    print(f"Executing query:\n{query}")
    cursor.execute(query)
    results = cursor.fetchall()
    if results:
        print("Found posts needing summary:")
        for row in results:
            print(f"- {row[0]}")
    else:
        print("No posts found needing summary according to the query.")

except sqlite3.Error as e:
    print(f"SQLite error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    if conn:
        conn.close()
        print("Database connection closed.")