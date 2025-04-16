import sqlite3
import os

db_path = "data/memory.sqlite"

if not os.path.exists(db_path):
    print(f"Database file not found at: {db_path}")
    exit(1)

# Connect to the database
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get node types and counts
    c.execute('SELECT type, COUNT(*) as count FROM memory_nodes GROUP BY type')
    print('Types of nodes:')
    for row in c.fetchall():
        print(f"  {row['type']}: {row['count']}")
    
    # Get count of nodes with embeddings
    c.execute('SELECT COUNT(*) as count FROM memory_nodes WHERE has_embedding=1')
    with_embedding = c.fetchone()['count']
    print(f'Nodes with embeddings: {with_embedding}')
    
    # Get count of total nodes
    c.execute('SELECT COUNT(*) as count FROM memory_nodes')
    total_nodes = c.fetchone()['count']
    print(f'Total nodes: {total_nodes}')
    
    # Get some sample node IDs and their types
    c.execute('SELECT id, type, has_embedding FROM memory_nodes LIMIT 5')
    print('\nSample nodes:')
    for row in c.fetchall():
        print(f"  ID: {row['id']}, Type: {row['type']}, Has Embedding: {row['has_embedding']}")
    
    conn.close()
except Exception as e:
    print(f"Error querying database: {e}") 