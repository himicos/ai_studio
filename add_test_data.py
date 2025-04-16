import sqlite3
import os
import uuid
import json
import datetime
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss

# Path to the SQLite database
DB_PATH = "data/memory.sqlite"

def get_db_connection():
    """Get SQLite database connection"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def add_sample_data():
    """Add sample Twitter and Reddit data to the database"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate sample Twitter data
        twitter_id = str(uuid.uuid4())
        twitter_data = {
            "id": twitter_id,
            "title": "AI Advancements",
            "content": "Artificial intelligence is revolutionizing how we interact with technology. The future of AI looks promising with advancements in machine learning and neural networks.",
            "type": "twitter",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "has_embedding": False,
            "tags": json.dumps(["AI", "MachineLearning", "Technology"]),
            "metadata": json.dumps({
                "user": "tech_enthusiast",
                "likes": 245,
                "retweets": 56,
                "url": "https://twitter.com/tech_enthusiast/status/123456789",
                "timestamp": datetime.datetime.now().isoformat()
            })
        }
        
        # Insert Twitter data
        cursor.execute('''
            INSERT INTO memory_nodes (id, title, content, type, created_at, updated_at, has_embedding, tags, metadata)
            VALUES (:id, :title, :content, :type, :created_at, :updated_at, :has_embedding, :tags, :metadata)
        ''', twitter_data)
        print(f"Added Twitter node with ID: {twitter_id}")
        
        # Generate sample Reddit data
        reddit_id = str(uuid.uuid4())
        reddit_data = {
            "id": reddit_id,
            "title": "Deep Learning Discussion",
            "content": "Neural networks are becoming increasingly complex. Deep learning models can now solve problems that were considered impossible just a decade ago. What do you think will be the next breakthrough in this field?",
            "type": "reddit",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "has_embedding": False,
            "tags": json.dumps(["DeepLearning", "NeuralNetworks", "AI"]),
            "metadata": json.dumps({
                "author": "data_scientist",
                "upvotes": 128,
                "subreddit": "MachineLearning",
                "url": "https://reddit.com/r/MachineLearning/comments/abcdef",
                "timestamp": datetime.datetime.now().isoformat()
            })
        }
        
        # Insert Reddit data
        cursor.execute('''
            INSERT INTO memory_nodes (id, title, content, type, created_at, updated_at, has_embedding, tags, metadata)
            VALUES (:id, :title, :content, :type, :created_at, :updated_at, :has_embedding, :tags, :metadata)
        ''', reddit_data)
        print(f"Added Reddit node with ID: {reddit_id}")
        
        # Commit transaction
        conn.commit()
        
        # Generate embeddings for the new nodes
        print("Generating embeddings...")
        twitter_embedding_success = generate_embedding_for_node_faiss(twitter_id)
        reddit_embedding_success = generate_embedding_for_node_faiss(reddit_id)
        
        print(f"Twitter embedding generated: {twitter_embedding_success}")
        print(f"Reddit embedding generated: {reddit_embedding_success}")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_sample_data() 