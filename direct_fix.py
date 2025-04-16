#!/usr/bin/env python
"""
Direct fix script that checks FAISS store and rebuilds it with direct access.
This bypasses potential permission issues or path problems.
"""
import os
import time
import json
import uuid
import faiss
import numpy as np
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("direct_fix")

# Define paths
FAISS_PATH = "data/vector_store.faiss"
METADATA_PATH = "data/vector_store_metadata.json"
DB_PATH = "data/memory.sqlite"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding_dim = 384  # Dimension of all-MiniLM-L6-v2 embeddings

def check_faiss_index():
    """Check if FAISS index exists and has vectors."""
    if os.path.exists(FAISS_PATH):
        try:
            index = faiss.read_index(FAISS_PATH)
            logger.info(f"FAISS index contains {index.ntotal} vectors")
            return index.ntotal > 0
        except Exception as e:
            logger.error(f"Error reading FAISS index: {e}")
            return False
    else:
        logger.warning(f"FAISS index not found at {FAISS_PATH}")
        return False

def create_test_content():
    """Create test content directly with FAISS."""
    # Create a new empty FAISS index
    index = faiss.IndexFlatL2(embedding_dim)
    index = faiss.IndexIDMap(index)  # Add ID mapping
    
    # Test content
    test_content = [
        {
            "id": str(uuid.uuid4()),
            "title": "Introduction to Artificial Intelligence",
            "content": "Artificial Intelligence (AI) is transforming industries by enabling machines to learn from data and make decisions. Machine learning, deep learning, and neural networks are key components of modern AI systems.",
            "type": "test_document",
            "tags": ["AI", "machine learning", "technology"],
            "created_at": int(time.time())
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Natural Language Processing",
            "content": "NLP is a branch of AI focused on enabling computers to understand, interpret, and generate human language. Applications include chatbots, translation, and sentiment analysis.",
            "type": "test_document",
            "tags": ["NLP", "language", "AI"],
            "created_at": int(time.time())
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Computer Vision",
            "content": "Computer vision systems use AI to process and analyze visual data from the world. Object detection, facial recognition, and image classification are common computer vision tasks.",
            "type": "test_document",
            "tags": ["computer vision", "AI", "image processing"],
            "created_at": int(time.time())
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Machine Learning Fundamentals",
            "content": "Machine learning is the core of modern AI. It involves algorithms that allow computers to learn patterns from data without explicit programming. Supervised, unsupervised, and reinforcement learning are key paradigms.",
            "type": "test_document",
            "tags": ["machine learning", "algorithms", "AI"],
            "created_at": int(time.time())
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Ethics in AI",
            "content": "As AI becomes more prevalent, ethical considerations become increasingly important. Issues include bias in algorithms, privacy concerns, and the impact of automation on jobs.",
            "type": "test_document",
            "tags": ["ethics", "AI", "society"],
            "created_at": int(time.time())
        }
    ]
    
    # Generate embeddings for all test content
    logger.info("Generating embeddings for test content...")
    metadata = {}
    all_embeddings = []
    ids = []
    
    for i, item in enumerate(test_content):
        # Generate embedding
        embedding = model.encode(item["content"], normalize_embeddings=True)
        all_embeddings.append(embedding)
        ids.append(i)  # Use integer ID for FAISS
        
        # Store metadata
        metadata[str(i)] = {
            "id": item["id"],
            "title": item["title"],
            "type": item["type"],
            "tags": item["tags"],
            "created_at": item["created_at"]
        }
    
    # Convert to numpy array and add to FAISS index
    embeddings_array = np.array(all_embeddings).astype('float32')
    ids_array = np.array(ids).astype('int64')
    index.add_with_ids(embeddings_array, ids_array)
    
    # Save the FAISS index
    logger.info(f"Saving FAISS index with {index.ntotal} vectors to {FAISS_PATH}")
    faiss.write_index(index, FAISS_PATH)
    
    # Save the metadata
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved metadata for {len(metadata)} items to {METADATA_PATH}")
    
    return len(test_content)

def test_search():
    """Test if search works with the new index."""
    try:
        # Load the FAISS index
        index = faiss.read_index(FAISS_PATH)
        
        # Load metadata
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
        
        # Test queries, both regular and with ellipses
        test_queries = [
            "artificial intelligence",
            "machine learning",
            "natural language processing",
            "ethics in AI",
            "computer vision"
        ]
        
        test_queries_with_ellipses = [q + "..." for q in test_queries]
        all_queries = test_queries + test_queries_with_ellipses
        
        passed = True
        for query in all_queries:
            # Generate embedding for query
            query_embedding = model.encode([query], normalize_embeddings=True)
            
            # Search in FAISS
            k = 3  # Number of results to return
            distances, indices = index.search(query_embedding.astype('float32'), k)
            
            logger.info(f"Query: '{query}'")
            found_results = False
            
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx >= 0 and str(idx) in metadata:  # Check if idx is valid
                    item = metadata[str(idx)]
                    # Different similarity calculation based on index type
                    similarity = 1 - distance/2  # Convert L2 distance to similarity score
                    logger.info(f"  Result {i+1}: '{item['title']}' (Similarity: {similarity:.4f})")
                    found_results = True
                else:
                    if idx >= 0:
                        logger.warning(f"  Invalid index: {idx} (not in metadata)")
                    else:
                        logger.warning(f"  No match found for position {i+1}")
            
            if not found_results:
                logger.error(f"No results found for query: '{query}'")
                passed = False
        
        return passed
    except Exception as e:
        logger.error(f"Error testing search: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting direct FAISS fix")
    
    # Force rebuild by deleting existing files
    if os.path.exists(FAISS_PATH):
        os.remove(FAISS_PATH)
        logger.info(f"Removed existing FAISS index at {FAISS_PATH}")
    
    if os.path.exists(METADATA_PATH):
        os.remove(METADATA_PATH)
        logger.info(f"Removed existing metadata at {METADATA_PATH}")
    
    # Check if FAISS index exists and has vectors
    if check_faiss_index():
        logger.info("FAISS index already contains vectors")
    else:
        logger.warning("FAISS index is empty or corrupted, creating new test content")
        num_items = create_test_content()
        logger.info(f"Created {num_items} test items with embeddings")
    
    # Test search functionality
    logger.info("Testing search functionality...")
    success = test_search()
    
    if success:
        logger.info("Search test successful!")
        logger.info("RESTART THE BACKEND SERVER with 'python main.py' to apply changes")
    else:
        logger.error("Search test failed. Check logs for details.") 