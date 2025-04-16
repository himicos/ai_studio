#!/usr/bin/env python
"""
Script to check FAISS index contents and test direct searches.
"""
import os
import json
import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_faiss")

# Define paths
FAISS_PATH = "data/vector_store.faiss"
METADATA_PATH = "data/vector_store_metadata.json"

def check_index_status():
    """Check if the FAISS index exists and has data."""
    try:
        if not os.path.exists(FAISS_PATH):
            logger.error(f"FAISS index not found at {FAISS_PATH}")
            return False
            
        index = faiss.read_index(FAISS_PATH)
        logger.info(f"FAISS index contains {index.ntotal} vectors")
        
        if not os.path.exists(METADATA_PATH):
            logger.error(f"Metadata file not found at {METADATA_PATH}")
            return False
            
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            
        logger.info(f"Metadata file contains {len(metadata)} entries")
        
        # Check if counts match
        if index.ntotal != len(metadata):
            logger.warning(f"Vector count ({index.ntotal}) does not match metadata count ({len(metadata)})")
        
        # Show sample metadata entries
        for idx, (key, data) in enumerate(metadata.items()):
            if idx < 5:  # Show first 5 entries
                logger.info(f"Metadata entry {idx}: ID={data.get('id')}, Type={data.get('type')}, Tags={data.get('tags')}")
            else:
                break
                
        return index.ntotal > 0
        
    except Exception as e:
        logger.error(f"Error checking index: {e}")
        return False

def test_direct_search():
    """Test direct search against the FAISS index."""
    try:
        # Load the index
        index = faiss.read_index(FAISS_PATH)
        
        # Load metadata
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            
        # Initialize the model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test queries
        test_queries = [
            "artificial intelligence",
            "machine learning",
            "ethics in AI",
            "computer vision"
        ]
        
        # Also test queries with ellipses to see if they match
        test_queries_with_ellipses = [q + "..." for q in test_queries]
        
        logger.info(f"Testing {len(test_queries)} queries directly against FAISS")
        
        def search_query(query, k=3):
            # Generate embedding
            query_embedding = model.encode([query], normalize_embeddings=True)
            
            # Search
            distances, indices = index.search(query_embedding.astype('float32'), k)
            
            logger.info(f"\nQuery: '{query}'")
            results = []
            
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx >= 0 and str(idx) in metadata:
                    item = metadata[str(idx)]
                    similarity = 1 - distance/2  # Convert L2 distance to similarity score
                    logger.info(f"  Result {i+1}: ID={item.get('id')}, Type={item.get('type')}, Similarity={similarity:.4f}")
                    results.append({
                        'id': item.get('id'),
                        'type': item.get('type'),
                        'similarity': similarity
                    })
                else:
                    logger.warning(f"  Invalid index: {idx}")
            
            return len(results) > 0
            
        # Test normal queries
        for query in test_queries:
            success = search_query(query)
            if not success:
                logger.error(f"No results found for query: '{query}'")
                
        # Test queries with ellipses
        for query in test_queries_with_ellipses:
            success = search_query(query)
            if not success:
                logger.error(f"No results found for query with ellipses: '{query}'")
        
    except Exception as e:
        logger.error(f"Error during direct search test: {e}")

def test_api_search():
    """Test search through the API."""
    try:
        logger.info("Testing search API with various thresholds...")
        api_url = "http://localhost:8000/api/search/semantic"
        
        # Test queries with different thresholds
        test_cases = [
            {"query": "computer vision", "threshold": 0.7},
            {"query": "computer vision", "threshold": 0.5},
            {"query": "computer vision", "threshold": 0.3},
            {"query": "computer vision", "threshold": 0.2},
            {"query": "computer vision", "threshold": 0.1},
            {"query": "artificial intelligence", "threshold": 0.1},
            {"query": "machine learning", "threshold": 0.1},
        ]
        
        for test_case in test_cases:
            query = test_case["query"]
            threshold = test_case["threshold"]
            
            payload = {
                "query_text": query,
                "min_similarity": threshold,
                "limit": 10
            }
            
            try:
                response = requests.post(api_url, json=payload)
                response.raise_for_status()  # Raise exception for non-200 status codes
                results = response.json()
                
                logger.info(f"API query: '{query}', threshold: {threshold}")
                if "results" in results and results["results"]:
                    logger.info(f"  Found {len(results['results'])} results")
                    for i, result in enumerate(results["results"][:3]):  # Show first 3 results
                        logger.info(f"  Result {i+1}: ID={result.get('id')}, Type={result.get('type')}, Similarity={result.get('similarity', 0):.4f}")
                else:
                    logger.warning(f"  No results found for query: '{query}', threshold: {threshold}")
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                
    except Exception as e:
        logger.error(f"Error testing API search: {e}")

def compare_direct_vs_api():
    """Compare direct FAISS search vs API search for the same query."""
    try:
        # Load the index
        index = faiss.read_index(FAISS_PATH)
        
        # Load metadata
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            
        # Initialize the model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test query
        query = "computer vision"
        
        # 1. Direct FAISS search
        logger.info(f"\nDirect FAISS search for query: '{query}'")
        query_embedding = model.encode([query], normalize_embeddings=True)
        distances, indices = index.search(query_embedding.astype('float32'), 3)
        
        direct_results = []
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx >= 0 and str(idx) in metadata:
                item = metadata[str(idx)]
                similarity = 1 - distance/2  # Convert L2 distance to similarity score
                logger.info(f"  Direct Result {i+1}: ID={item.get('id')}, Type={item.get('type')}, Similarity={similarity:.4f}")
                direct_results.append({
                    'id': item.get('id'),
                    'type': item.get('type'),
                    'similarity': similarity
                })
        
        # 2. API search
        logger.info(f"\nAPI search for query: '{query}'")
        api_url = "http://localhost:8000/api/search/semantic"
        payload = {
            "query_text": query,
            "min_similarity": 0.01,  # Very low threshold to get any results
            "limit": 3
        }
        
        try:
            response = requests.post(api_url, json=payload)
            response.raise_for_status()
            results = response.json()
            
            if "results" in results and results["results"]:
                logger.info(f"  Found {len(results['results'])} API results")
                for i, result in enumerate(results["results"]):
                    logger.info(f"  API Result {i+1}: ID={result.get('id')}, Type={result.get('type')}, Similarity={result.get('similarity', 0):.4f}")
            else:
                logger.warning(f"  No API results found for query: '{query}'")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            
    except Exception as e:
        logger.error(f"Error comparing direct vs API search: {e}")

if __name__ == "__main__":
    logger.info("Starting FAISS index check")
    
    # Check index status
    if check_index_status():
        logger.info("FAISS index is valid and contains data")
        
        # Test direct search
        test_direct_search()
        
        # Test API search
        test_api_search()
        
        # Compare direct vs API search
        compare_direct_vs_api()
    else:
        logger.error("FAISS index is empty or invalid") 