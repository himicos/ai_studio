#!/usr/bin/env python3
"""
Test script for semantic search after fixing vector_adapter.py
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_semantic_search():
    """Test semantic search API endpoint"""
    url = "http://localhost:8000/api/search/semantic"
    
    test_queries = [
        "artificial intelligence",
        "machine learning",
        "knowledge graph"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        
        # Create payload
        payload = {
            "query_text": query,
            "limit": 5,
            "min_similarity": 0.1
        }
        
        try:
            # Send request
            response = requests.post(url, json=payload)
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                logger.info(f"✅ Success! Got {len(results)} results for query '{query}'")
                
                # Log some results
                for i, result in enumerate(results[:3]):
                    similarity = result.get("similarity", 0) * 100
                    node_id = result.get("id", "unknown")
                    node_type = result.get("type", "unknown")
                    logger.info(f"  Result {i+1}: Node {node_id} ({node_type}) - Similarity: {similarity:.1f}%")
            else:
                logger.error(f"❌ Error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"❌ Exception: {e}")

if __name__ == "__main__":
    logger.info("Semantic Search Test")
    test_semantic_search()
    logger.info("Test completed") 