#!/usr/bin/env python
"""
Script to fix search functionality by rebuilding the FAISS index and adding test content.
"""
import os
import time
import uuid
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("search_fix")

# Import necessary modules
from ai_studio_package.infra.db import get_db_connection, init_db
from ai_studio_package.infra.vector_store import VectorStoreManager
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Initialize database if needed
init_db()

def add_test_content():
    """Add sample AI-related content to the database for testing search."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we already have enough test content
    cursor.execute("SELECT COUNT(*) FROM memory_nodes")
    count = cursor.fetchone()[0]
    logger.info(f"Found {count} existing memory nodes")
    
    if count < 5:
        logger.info("Adding sample test content...")
        
        # Add 5 test documents with AI-related content
        test_contents = [
            {
                "title": "Introduction to Artificial Intelligence",
                "content": "Artificial Intelligence (AI) is transforming industries by enabling machines to learn from data and make decisions. Machine learning, deep learning, and neural networks are key components of modern AI systems.",
                "type": "test_document",
                "tags": '["AI", "machine learning", "technology"]'
            },
            {
                "title": "Natural Language Processing",
                "content": "NLP is a branch of AI focused on enabling computers to understand, interpret, and generate human language. Applications include chatbots, translation, and sentiment analysis.",
                "type": "test_document",
                "tags": '["NLP", "language", "AI"]'
            },
            {
                "title": "Computer Vision",
                "content": "Computer vision systems use AI to process and analyze visual data from the world. Object detection, facial recognition, and image classification are common computer vision tasks.",
                "type": "test_document",
                "tags": '["computer vision", "AI", "image processing"]'
            },
            {
                "title": "Reinforcement Learning",
                "content": "Reinforcement learning is an AI technique where agents learn to make decisions by receiving rewards or penalties. It's used in robotics, game playing, and autonomous systems.",
                "type": "test_document",
                "tags": '["reinforcement learning", "AI", "decision making"]'
            },
            {
                "title": "Ethics in AI",
                "content": "As AI becomes more prevalent, ethical considerations become increasingly important. Issues include bias in algorithms, privacy concerns, and the impact of automation on jobs.",
                "type": "test_document",
                "tags": '["ethics", "AI", "society"]'
            }
        ]
        
        for content in test_contents:
            node_id = str(uuid.uuid4())
            current_time = int(time.time())
            
            cursor.execute(
                'INSERT INTO memory_nodes (id, title, content, type, created_at, updated_at, has_embedding, tags, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (node_id, content["title"], content["content"], content["type"], current_time, current_time, 0, content["tags"], '{}')
            )
            conn.commit()
            
            # Generate embedding for the node
            generate_embedding_for_node_faiss(node_id)
            logger.info(f"Created test node: {content['title']} with ID: {node_id}")
    else:
        logger.info("Sufficient content already exists in the database")

def rebuild_faiss_index():
    """Rebuild the FAISS index from scratch using all nodes in the database."""
    logger.info("Rebuilding FAISS index from scratch...")
    
    # Remove existing FAISS index if it exists
    faiss_path = os.path.join("data", "vector_store.faiss")
    metadata_path = os.path.join("data", "vector_store_metadata.json")
    
    if os.path.exists(faiss_path):
        os.rename(faiss_path, f"{faiss_path}.bak")
    
    if os.path.exists(metadata_path):
        os.rename(metadata_path, f"{metadata_path}.bak")
    
    # Create a new empty vector store
    vector_store = VectorStoreManager(faiss_path, metadata_path)
    
    # Get all nodes from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM memory_nodes")
    node_ids = [row[0] for row in cursor.fetchall()]
    
    logger.info(f"Rebuilding embeddings for {len(node_ids)} nodes...")
    
    # Process each node
    success_count = 0
    for node_id in node_ids:
        try:
            generate_embedding_for_node_faiss(node_id)
            success_count += 1
            if success_count % 10 == 0:
                logger.info(f"Processed {success_count}/{len(node_ids)} nodes")
        except Exception as e:
            logger.error(f"Error processing node {node_id}: {e}")
    
    logger.info(f"Successfully rebuilt embeddings for {success_count}/{len(node_ids)} nodes")

if __name__ == "__main__":
    logger.info("Starting search fix process")
    
    # Add test content if needed
    add_test_content()
    
    # Rebuild FAISS index
    rebuild_faiss_index()
    
    logger.info("Search fix complete. You can now restart the backend server with 'python main.py'") 