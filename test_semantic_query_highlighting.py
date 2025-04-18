#!/usr/bin/env python3
"""
Test script for Live Semantic Query Highlighting feature

This script tests the Live Semantic Query Highlighting feature by:
1. Testing the semantic search API to verify backend functionality
2. Analyzing the MemoryPanel.tsx and api.ts files to verify frontend implementation
3. Running a series of test queries to verify the feature's behavior
"""

import os
import sys
import json
import logging
import requests
import subprocess
from pathlib import Path
import webbrowser
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173/knowledge"
API_TS_PATH = "spyderweb/spyderweb/src/lib/api.ts"
MEMORY_PANEL_PATH = "spyderweb/spyderweb/src/components/panels/MemoryPanel.tsx"

def check_backend_running():
    """Check if the backend server is running"""
    logger.info("Checking if backend server is running...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend server is running")
            return True
        else:
            logger.error(f"❌ Backend server returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Backend server is not running: {e}")
        return False

def check_frontend_running():
    """Check if the frontend server is running"""
    logger.info("Checking if frontend server is running...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Frontend server is running")
            return True
        else:
            logger.error(f"❌ Frontend server returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Frontend server is not running: {e}")
        return False

def test_semantic_search_api(query_text: str, min_similarity: float = 0.15, limit: int = 50):
    """Test the semantic search API endpoint"""
    logger.info(f"Testing semantic search API with query: '{query_text}', min_similarity: {min_similarity}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/search/semantic",
            json={
                "query_text": query_text,
                "min_similarity": min_similarity,
                "limit": limit
            },
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"❌ Semantic search API returned status code {response.status_code}")
            return False, []
        
        results = response.json()
        
        # Check if results is a list (direct array) or has a 'results' property
        if isinstance(results, list):
            search_results = results
        elif isinstance(results, dict) and 'results' in results:
            search_results = results['results']
        else:
            logger.error(f"❌ Unexpected response format: {type(results)}")
            return False, []
        
        logger.info(f"✅ Semantic search API returned {len(search_results)} results")
        
        # Check if all results have similarity scores
        has_similarity = all('similarity' in result for result in search_results)
        if has_similarity:
            logger.info("✅ All results have similarity scores")
        else:
            logger.warning("⚠️ Some results are missing similarity scores")
        
        # Log a few results for inspection
        for i, result in enumerate(search_results[:3]):
            similarity = result.get('similarity', 'N/A')
            node_id = result.get('id', 'Unknown')
            node_type = result.get('type', 'Unknown')
            logger.info(f"  Result {i+1}: ID={node_id}, Type={node_type}, Similarity={similarity}")
        
        return True, search_results
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Semantic search API request failed: {e}")
        return False, []

def analyze_frontend_code():
    """Analyze the frontend code to verify implementation of the highlighting feature"""
    logger.info("Analyzing frontend code for Live Semantic Query Highlighting implementation...")
    
    # Check if the frontend files exist
    api_ts_exists = os.path.exists(API_TS_PATH)
    memory_panel_exists = os.path.exists(MEMORY_PANEL_PATH)
    
    if not (api_ts_exists and memory_panel_exists):
        logger.error("❌ Frontend files not found")
        return False
    
    # Read the API.ts file
    with open(API_TS_PATH, 'r', encoding='utf-8') as f:
        api_ts_content = f.read()
    
    # Read the MemoryPanel.tsx file
    with open(MEMORY_PANEL_PATH, 'r', encoding='utf-8') as f:
        memory_panel_content = f.read()
    
    # Check for searchMemoryNodes implementation
    if 'searchMemoryNodes' in api_ts_content and 'similarity' in api_ts_content:
        logger.info("✅ Found searchMemoryNodes function in api.ts")
        # Look for logging of similarity scores
        if 'similarity' in api_ts_content and 'similarityPercent' in api_ts_content:
            logger.info("✅ api.ts has code for handling similarity scores")
    else:
        logger.warning("⚠️ searchMemoryNodes implementation in api.ts is incomplete or missing")
    
    # Check for handleGraphSearch implementation
    if 'handleGraphSearch' in memory_panel_content and 'similarity' in memory_panel_content:
        logger.info("✅ Found handleGraphSearch function in MemoryPanel.tsx")
        # Look for node coloring based on similarity
        if 'color' in memory_panel_content and 'similarity' in memory_panel_content:
            logger.info("✅ MemoryPanel.tsx has code for coloring nodes based on similarity")
    else:
        logger.warning("⚠️ handleGraphSearch implementation in MemoryPanel.tsx is incomplete or missing")
    
    # Check for updateNodeVisualization function
    if 'updateNodeVisualization' in memory_panel_content:
        logger.info("✅ Found updateNodeVisualization function in MemoryPanel.tsx")
    else:
        logger.warning("⚠️ updateNodeVisualization function in MemoryPanel.tsx is missing")
    
    # Check for nodeSimilarities state
    if 'nodeSimilarities' in memory_panel_content and 'useState' in memory_panel_content:
        logger.info("✅ Found nodeSimilarities state in MemoryPanel.tsx")
    else:
        logger.warning("⚠️ nodeSimilarities state in MemoryPanel.tsx is missing")
    
    return True

def run_test_queries():
    """Run a series of test queries to verify the feature's behavior"""
    logger.info("Running test queries...")
    
    # Define test queries with varying complexity
    test_queries = [
        "knowledge graph",
        "self improvement",
        "data visualization",
        "embeddings",
        "reddit posts"
    ]
    
    # Test each query with different similarity thresholds
    thresholds = [0.5, 0.3, 0.15, 0.01]
    
    results = {}
    
    for query in test_queries:
        query_results = {}
        for threshold in thresholds:
            success, search_results = test_semantic_search_api(query, threshold)
            query_results[threshold] = len(search_results)
        results[query] = query_results
    
    # Log summary
    logger.info("Test query results summary:")
    for query, thresholds_dict in results.items():
        result_str = ", ".join([f"{threshold}: {count} results" for threshold, count in thresholds_dict.items()])
        logger.info(f"  Query '{query}': {result_str}")
    
    return results

def test_frontend_interaction():
    """Test frontend interaction by opening the browser to the knowledge graph page"""
    logger.info("Testing frontend interaction...")
    
    # Check if frontend is running
    if not check_frontend_running():
        logger.error("❌ Cannot test frontend interaction: Frontend server is not running")
        return False
    
    # Open the browser to the knowledge graph page
    logger.info(f"Opening browser to {FRONTEND_URL}")
    
    try:
        webbrowser.open(FRONTEND_URL)
        logger.info("✅ Browser opened successfully")
        logger.info("Please perform the following manual tests:")
        logger.info("1. Enter each test query in the search box")
        logger.info("2. Verify that nodes are highlighted with different colors based on similarity")
        logger.info("3. Verify that the view zooms to focus on highlighted nodes")
        logger.info("4. Try different queries to test the feature's behavior")
        return True
    except Exception as e:
        logger.error(f"❌ Error opening browser: {e}")
        return False

def launch_servers():
    """Launch the backend and frontend servers if needed"""
    logger.info("Checking if servers need to be launched...")
    
    # Check if servers are already running
    backend_running = check_backend_running()
    frontend_running = check_frontend_running()
    
    if backend_running and frontend_running:
        logger.info("✅ Both servers are already running")
        return True
    
    # Launch servers if needed
    if not backend_running:
        logger.info("Launching backend server...")
        subprocess.Popen(
            "start cmd /k python main.py",
            shell=True
        )
        logger.info("Waiting for backend server to start...")
        time.sleep(5)
    
    if not frontend_running:
        logger.info("Launching frontend server...")
        subprocess.Popen(
            "start cmd /k cd spyderweb/spyderweb && npm run dev",
            shell=True
        )
        logger.info("Waiting for frontend server to start...")
        time.sleep(10)
    
    # Check again if servers are running
    backend_running = check_backend_running()
    frontend_running = check_frontend_running()
    
    return backend_running and frontend_running

def main():
    """Main function to test the Live Semantic Query Highlighting feature"""
    logger.info("=== Live Semantic Query Highlighting Test ===")
    
    # Launch servers if needed
    servers_running = launch_servers()
    if not servers_running:
        logger.error("❌ Failed to launch servers. Please start them manually.")
        logger.error("   Backend: python main.py")
        logger.error("   Frontend: cd spyderweb/spyderweb && npm run dev")
        return 1
    
    # Test backend API
    test_semantic_search_api("test query", 0.01)
    
    # Analyze frontend code
    analyze_frontend_code()
    
    # Run test queries
    run_test_queries()
    
    # Test frontend interaction
    test_frontend_interaction()
    
    logger.info("=== Live Semantic Query Highlighting Test Complete ===")
    logger.info("""
Test Summary:
1. Backend API: Tested the semantic search API with various queries and thresholds
2. Frontend Code: Analyzed the implementation in api.ts and MemoryPanel.tsx
3. Test Queries: Ran a series of test queries with different similarity thresholds
4. Frontend Interaction: Opened the browser for manual testing

Next Steps:
1. Complete any manual tests in the browser
2. Verify that nodes are highlighted with different colors based on similarity
3. Verify that the view zooms to focus on highlighted nodes
4. Address any warnings or errors found during testing
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 