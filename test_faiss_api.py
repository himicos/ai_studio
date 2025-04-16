#!/usr/bin/env python
"""
Test script to directly test FAISS API functions
"""
import logging
import json
from ai_studio_package.infra.vector_adapter import search_similar_nodes_faiss, get_vector_store
from ai_studio_package.infra.db_enhanced import search_similar_nodes
from ai_studio_package.infra.models import embedding_model_name
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_faiss_api")

def test_faiss_direct():
    """Test FAISS search directly."""
    queries = [
        "artificial intelligence",
        "machine learning",
        "computer vision",
        "natural language processing",
        "ethics in AI"
    ]
    
    logger.info("Testing FAISS search directly...")
    
    for query in queries:
        min_similarity = 0.15  # Set to a very low value to get any results
        
        logger.info(f"\nTesting query: '{query}' with min_similarity={min_similarity}")
        results = search_similar_nodes_faiss(
            query_text=query,
            limit=5,
            node_type=None,
            min_similarity=min_similarity
        )
        
        if results:
            logger.info(f"Found {len(results)} results:")
            for i, result in enumerate(results):
                logger.info(f"  Result {i+1}: ID={result.get('id')}, "
                           f"Type={result.get('type')}, "
                           f"Similarity={result.get('similarity', 0):.4f}")
        else:
            logger.warning(f"No results found for '{query}'")
    
    return True

def test_vector_store_contents():
    """Test contents of vector store."""
    logger.info("\nChecking vector store contents")
    
    try:
        vector_store = get_vector_store()
        
        logger.info(f"Vector store has {vector_store.index.ntotal} vectors")
        logger.info(f"Vector store has {len(vector_store.metadata)} metadata entries")
        
        # Print first 5 metadata entries
        for i, (idx, metadata) in enumerate(list(vector_store.metadata.items())[:5]):
            logger.info(f"  Entry {i+1}: Index={idx}, ID={metadata.get('id')}, Type={metadata.get('type')}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking vector store: {e}")
        return False

def test_models_direct():
    """Test embedding model directly."""
    logger.info("\nTesting embedding model directly")
    
    try:
        model = SentenceTransformer(embedding_model_name)
        
        query = "artificial intelligence"
        logger.info(f"Embedding query: '{query}'")
        
        embedding = model.encode(query)
        logger.info(f"Generated embedding with shape: {embedding.shape}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing embedding model: {e}")
        return False

def test_fallback_search():
    """Test original search_similar_nodes from db_enhanced."""
    queries = [
        "artificial intelligence",
        "machine learning",
        "computer vision"
    ]
    
    logger.info("\nTesting fallback search_similar_nodes...")
    
    for query in queries:
        min_similarity = 0.15  # Set to a very low value to get any results
        
        logger.info(f"\nTesting query: '{query}' with min_similarity={min_similarity}")
        
        try:
            results = search_similar_nodes(
                query_text=query,
                limit=5,
                node_type=None,
                min_similarity=min_similarity
            )
            
            if results:
                logger.info(f"Found {len(results)} results:")
                for i, result in enumerate(results):
                    logger.info(f"  Result {i+1}: ID={result.get('id')}, "
                               f"Type={result.get('type')}, "
                               f"Similarity={result.get('similarity', 0):.4f}")
            else:
                logger.warning(f"No results found for '{query}'")
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
    
    return True

def test_memory_node_fetching():
    """Test that get_memory_node can find nodes."""
    logger.info("\nTesting memory node fetching from database...")
    
    from ai_studio_package.infra.vector_adapter import get_memory_node
    
    # Get metadata of existing vectors
    vector_store = get_vector_store()
    
    if not vector_store.metadata:
        logger.warning("No metadata found in vector store")
        return False
    
    # Try to fetch a few nodes from the metadata
    fetched = 0
    for idx, metadata in list(vector_store.metadata.items())[:3]:
        node_id = metadata.get('id')
        if not node_id:
            continue
        
        logger.info(f"Attempting to fetch node with ID: {node_id}")
        node = get_memory_node(node_id)
        
        if node:
            logger.info(f"Successfully fetched node: {json.dumps(node, default=str)[:200]}...")
            fetched += 1
        else:
            logger.warning(f"Failed to fetch node with ID: {node_id}")
    
    logger.info(f"Fetched {fetched} nodes from database")
    return fetched > 0

if __name__ == "__main__":
    logger.info("Starting FAISS API test")
    
    # Test vector store contents
    test_vector_store_contents()
    
    # Test embedding model
    test_models_direct()
    
    # Test FAISS search
    test_faiss_direct()
    
    # Test fallback search
    test_fallback_search()
    
    # Test node fetching
    test_memory_node_fetching() 