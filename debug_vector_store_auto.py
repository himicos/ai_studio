#!/usr/bin/env python3
"""
Debug script for FAISS vector store and semantic search (automated version)
"""

import os
import json
import numpy as np
import uuid
import sys
import logging
from pprint import pprint
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Try to import directly from the package
try:
    from ai_studio_package.infra.vector_store import VectorStoreManager
    from ai_studio_package.infra.vector_adapter import get_vector_store, search_similar_nodes_faiss
    from sentence_transformers import SentenceTransformer
    DIRECT_IMPORT = True
except ImportError:
    logger.warning("Could not import directly from ai_studio_package. Will use alternate methods.")
    DIRECT_IMPORT = False

# Constants
VECTOR_STORE_PATH = "data/vector_store.faiss"
METADATA_PATH = "data/vector_store_metadata.json"
MODEL_NAME = "all-MiniLM-L6-v2"
DIMENSIONS = 384

def load_vector_store():
    """Load the existing vector store"""
    logger.info(f"Loading vector store from {VECTOR_STORE_PATH}")
    
    if DIRECT_IMPORT:
        # Use the package's function
        return get_vector_store()
    else:
        # Create a new instance manually
        os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
        vector_store = VectorStoreManager(
            index_path=VECTOR_STORE_PATH,
            metadata_path=METADATA_PATH,
            embedding_model_name=MODEL_NAME,
            dimensions=DIMENSIONS,
            create_if_missing=True
        )
        vector_store.load()
        return vector_store

def add_test_vectors(vector_store):
    """Add test vectors to the vector store"""
    logger.info("Adding test vectors to vector store")
    
    # Load the model to generate embeddings
    model = SentenceTransformer(MODEL_NAME)
    
    # Test data
    test_data = [
        {"title": "Artificial Intelligence Basics", "content": "AI is the simulation of human intelligence in machines."},
        {"title": "Machine Learning Applications", "content": "Machine learning powers recommendation systems, fraud detection, and autonomous vehicles."},
        {"title": "Natural Language Processing", "content": "NLP enables computers to understand, interpret, and generate human language."},
        {"title": "Computer Vision Systems", "content": "Computer vision allows machines to identify objects and people in images and videos."},
        {"title": "Reinforcement Learning", "content": "Reinforcement learning is training algorithms using rewards and punishments."}
    ]
    
    added_count = 0
    for item in test_data:
        # Generate embedding
        embedding = model.encode(item["content"], convert_to_numpy=True)
        
        # Create metadata
        node_id = str(uuid.uuid4())
        metadata = {
            "id": node_id,
            "title": item["title"],
            "content": item["content"],
            "type": "test_document",
            "tags": ["AI", "test", "debug"],
            "created_at": int(datetime.now().timestamp())
        }
        
        # Add to vector store
        success = vector_store.add_embedding(embedding, metadata)
        
        if success:
            logger.info(f"Added test vector: {item['title']}")
            added_count += 1
        else:
            logger.error(f"Failed to add test vector: {item['title']}")
    
    if added_count > 0:
        # Save the vector store
        vector_store.save()
        logger.info(f"Added {added_count} test vectors to vector store")
    
    return added_count

def test_search(vector_store):
    """Test searching the vector store"""
    logger.info("Testing search functionality")
    
    # Load the model to generate query embedding
    model = SentenceTransformer(MODEL_NAME)
    
    # Test queries
    test_queries = [
        "artificial intelligence",
        "machine learning",
        "natural language",
        "computer vision",
        "AI applications"
    ]
    
    search_success = False
    for query in test_queries:
        logger.info(f"Searching for: '{query}'")
        
        # Generate query embedding
        query_embedding = model.encode(query, convert_to_numpy=True)
        
        # Search directly with the vector store
        results = vector_store.search(query_embedding, limit=5, score_threshold=0.01)
        
        if results:
            logger.info(f"Found {len(results)} results for query '{query}'")
            for i, result in enumerate(results[:3]):
                similarity = result.get("score", 0) * 100
                node_id = result.get("id", "unknown")
                logger.info(f"  Result {i+1}: Node {node_id} - Similarity: {similarity:.1f}%")
            search_success = True
        else:
            logger.warning(f"No results found for query '{query}'")
        
        # If the FAISS adapter function is available, test it too
        if DIRECT_IMPORT:
            try:
                logger.info(f"Testing search_similar_nodes_faiss with '{query}'")
                faiss_results = search_similar_nodes_faiss(
                    query_text=query,
                    limit=5,
                    min_similarity=0.01
                )
                
                if faiss_results:
                    logger.info(f"Found {len(faiss_results)} results via search_similar_nodes_faiss")
                    for i, result in enumerate(faiss_results[:3]):
                        similarity = result.get("similarity", 0) * 100
                        node_id = result.get("id", "unknown")
                        node_type = result.get("type", "unknown")
                        logger.info(f"  Result {i+1}: Node {node_id} (Type: {node_type}) - Similarity: {similarity:.1f}%")
                    search_success = True
                else:
                    logger.warning(f"No results found via search_similar_nodes_faiss")
            except Exception as e:
                logger.error(f"Error with search_similar_nodes_faiss: {e}")
    
    return search_success

def main():
    """Main function"""
    # Parse command line arguments
    add_vectors = "--add-vectors" in sys.argv
    only_add = "--only-add" in sys.argv
    only_search = "--only-search" in sys.argv
    view_metadata = "--view-metadata" in sys.argv
    
    # Print a banner
    print("\n========== FAISS VECTOR STORE DEBUG ==========\n")
    
    # Get the vector store
    vector_store = load_vector_store()
    
    # Check existing store if viewing metadata or not only adding vectors
    if not only_add or view_metadata:
        if hasattr(vector_store, "metadata") and vector_store.metadata:
            logger.info(f"Vector store already has {len(vector_store.metadata)} vectors")
            
            # Display some metadata
            if hasattr(vector_store, "id_to_node_id") and vector_store.id_to_node_id:
                id_to_node_count = len(vector_store.id_to_node_id)
                logger.info(f"id_to_node_id has {id_to_node_count} entries")
                
                if id_to_node_count > 0:
                    sample_entries = list(vector_store.id_to_node_id.items())[:3]
                    logger.info(f"Sample id_to_node_id entries: {sample_entries}")
            else:
                logger.warning("id_to_node_id attribute is missing or empty")
                
            # Display additional metadata if requested
            if view_metadata and hasattr(vector_store, "metadata"):
                logger.info("Vector store metadata sample (first 3 entries):")
                for idx, meta in list(vector_store.metadata.items())[:3]:
                    logger.info(f"  Index {idx}: {meta}")
        else:
            logger.warning("Vector store is empty or metadata is not loaded properly")
    
    # Add test vectors if requested or if the store is empty and we're not only searching
    should_add_vectors = add_vectors or (
        (not hasattr(vector_store, "metadata") or not vector_store.metadata) and 
        not only_search
    )
    
    if should_add_vectors:
        added_count = add_test_vectors(vector_store)
        if added_count == 0:
            logger.error("Failed to add any test vectors")
            return 1
    
    # Test search if not only adding vectors
    if not only_add:
        search_success = test_search(vector_store)
        if not search_success:
            logger.error("No successful searches were performed")
            return 1
    
    logger.info("Debug complete")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 