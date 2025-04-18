#!/usr/bin/env python3
"""
Comprehensive test script for AI Studio functionality

This script tests and diagnoses the following functionality:
1. Self-Improvement Loop (SIL)
2. Live Semantic Query Highlighting
3. Vector Store & Embedding functionality
4. Knowledge Graph implementation
"""

import os
import sys
import json
import sqlite3
import argparse
import logging
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import traceback

# Set up logging with color support
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'SUCCESS': '\033[92m\033[1m',  # Bold Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[91m\033[1m',  # Bold Red
        'RESET': '\033[0m'     # Reset
    }

    def format(self, record):
        # Add SUCCESS level
        if not hasattr(logging, 'SUCCESS'):
            logging.SUCCESS = 25  # Between INFO and WARNING
            logging.addLevelName(logging.SUCCESS, 'SUCCESS')
            
        # Add success method to logger
        if not hasattr(logging.Logger, 'success'):
            def success(self, message, *args, **kwargs):
                self.log(logging.SUCCESS, message, *args, **kwargs)
            logging.Logger.success = success
            
        # Get the original format
        log_fmt = super().format(record)
        # Apply color based on level
        levelname = record.levelname
        if levelname in self.COLORS:
            return f"{self.COLORS[levelname]}{log_fmt}{self.COLORS['RESET']}"
        return log_fmt

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler with color formatter
console_handler = logging.StreamHandler()
console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Add file handler for persistent logs
file_handler = logging.FileHandler('ai_studio_test.log')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Constants
MEMORY_DB_PATH = "memory/memory.sqlite"
VECTOR_STORE_PATH = "data/vector_store.faiss"
VECTOR_METADATA_PATH = "data/vector_store_metadata.json"
API_BASE_URL = "http://localhost:8000"

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists and report the size"""
    path = Path(file_path)
    exists = path.exists()
    
    if exists:
        size = path.stat().st_size
        logger.info(f"[OK] File exists: {file_path} (Size: {size/1024:.2f} KB)")
        return True
    else:
        logger.error(f"[X] File missing: {file_path}")
        return False

def run_command(command: str, timeout: int = 60) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr"""
    logger.info(f"Running command: {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
        
        if exit_code == 0:
            logger.info(f"[SUCCESS] Command executed successfully (exit code: {exit_code})")
        else:
            logger.error(f"[ERROR] Command failed with exit code: {exit_code}")
            logger.error(f"Error output: {stderr}")
            
        return exit_code, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        logger.error(f"[ERROR] Command timed out after {timeout} seconds")
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"[ERROR] Error executing command: {e}")
        return -1, "", str(e)

def query_database(query: str, params: tuple = (), db_path: str = MEMORY_DB_PATH) -> List[Dict[str, Any]]:
    """Execute a query against the database and return results as dictionaries"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"❌ Database query error: {e}")
        return []

def call_api_endpoint(
    endpoint: str, 
    method: str = "GET", 
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 10
) -> Dict[str, Any]:
    """Call an API endpoint and return the JSON response"""
    # Ensure endpoint starts with a slash
    if not endpoint.startswith('/'):
        endpoint = f'/{endpoint}'
        
    url = f"{API_BASE_URL}{endpoint}"
    logger.info(f"Calling API: {method} {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=payload, timeout=timeout)
        else:
            logger.error(f"[ERROR] Unsupported HTTP method: {method}")
            return {"error": f"Unsupported HTTP method: {method}"}
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR] API call error: {e}")
        return {"error": str(e)}
        
def test_execution_logs():
    """Test the execution logs table and initialization"""
    logger.info("=== Testing Execution Logs ===")
    
    # 1. Check if execution_logs table exists
    tables = query_database("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
    if tables:
        logger.info("[PASS] execution_logs table exists in the database")
    else:
        logger.error("[FAIL] execution_logs table not found in the database")
        
        # Try to initialize the table
        logger.info("Initializing execution_logs table...")
        exit_code, stdout, stderr = run_command("python ai_studio_package/scripts/initialize_execution_logs.py")
        
        if exit_code == 0:
            logger.info("[PASS] Successfully initialized execution_logs table")
            
            # Check again if the table exists
            tables = query_database("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
            if tables:
                logger.info("[PASS] execution_logs table now exists in the database")
            else:
                logger.error("[FAIL] execution_logs table still not found after initialization")
                return False
        else:
            logger.error(f"[FAIL] Failed to initialize execution_logs table: {stderr}")
            return False
    
    # 2. Check if there are any logs in the table
    logs = query_database("SELECT COUNT(*) as count FROM execution_logs")
    log_count = logs[0]['count'] if logs else 0
    logger.info(f"Found {log_count} execution logs in the database")
    
    return True

def test_critic_agent():
    """Test the Critic Agent module"""
    logger.info("=== Testing Critic Agent ===")
    
    # Check if the Critic Agent script executed successfully
    exit_code, stdout, stderr = run_command("python -m ai_studio_package.agents.critic_agent")
    
    if exit_code != 0:
        logger.error(f"[FAIL] Critic Agent execution failed: {stderr}")
        return False
    
    # Check for critique nodes in memory
    critique_nodes = query_database(
        "SELECT * FROM memory_nodes WHERE type = 'critique' ORDER BY created_at DESC LIMIT 5"
    )
    
    logger.info(f"[PASS] Found {len(critique_nodes)} critique nodes")
    
    # Show the content of the critique nodes
    for node in critique_nodes:
        logger.info(f"  - Critique node ID: {node['id']}\n")
        content = node['content']
        content_preview = content[:100] + "..." if len(content) > 100 else content
        logger.info(f"    Content: {content_preview}")
    
    return True

def test_refactor_agent():
    """Test the Refactor Agent module"""
    logger.info("=== Testing Refactor Agent ===")
    
    # Check if the Refactor Agent module exists
    if not os.path.exists("ai_studio_package/agents/refactor_agent.py"):
        logger.error("[FAIL] Refactor Agent module not found")
        return False
    
    # Get a critique node ID to use for testing
    critique_nodes = query_database(
        "SELECT id FROM memory_nodes WHERE type = 'critique' ORDER BY created_at DESC LIMIT 1"
    )
    
    if not critique_nodes:
        logger.warning("No critique nodes found to test with. Run test_critic_agent first.")
        return False
    
    critique_id = critique_nodes[0]['id']
    logger.info(f"Using critique node: {critique_id}\n")
    
    # Run the Refactor Agent with the critique node ID
    exit_code, stdout, stderr = run_command(
        f"python -m ai_studio_package.agents.refactor_agent --critique-id {critique_id}"
    )
    
    if exit_code != 0:
        logger.error(f"[FAIL] Refactor Agent execution failed: {stderr}")
        return False
    
    # Check for code patch nodes in memory
    patch_nodes = query_database(
        "SELECT * FROM memory_nodes WHERE type = 'code_patch' ORDER BY created_at DESC LIMIT 5"
    )
    
    if not patch_nodes:
        logger.warning("[NOTE] No code patch nodes found. This is normal if the system hasn't needed to apply any refactors yet.")
        return True
    
    logger.info(f"[PASS] Found {len(patch_nodes)} code patch nodes")
    
    # Show the content of the patch nodes
    for node in patch_nodes:
        logger.info(f"  - Code patch node ID: {node['id']}\n")
        content = node['content']
        content_preview = content[:100] + "..." if len(content) > 100 else content
        logger.info(f"    Content: {content_preview}")
    
    return True

def test_vector_store():
    """Test the vector store (FAISS) functionality"""
    logger.info("=== Testing Vector Store ===")
    
    # 1. Check if vector store files exist
    faiss_exists = check_file_exists(VECTOR_STORE_PATH)
    metadata_exists = check_file_exists(VECTOR_METADATA_PATH)
    
    if not (faiss_exists and metadata_exists):
        logger.error("[X] Vector store files are missing")
        return False
        
    # 2. Check vector store metadata
    try:
        with open(VECTOR_METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            
        vector_count = len(metadata.get('id_to_node_id', {}))
        logger.info(f"[OK] Vector store metadata contains {vector_count} vectors")
        
        # Show a sample of the vectors if any exist
        if vector_count > 0:
            sample = list(metadata.get('id_to_node_id', {}).items())[:5]
            logger.info(f"Sample vectors: {sample}")
    except Exception as e:
        logger.error(f"[X] Error reading vector store metadata: {e}")
        return False
        
    # 3. Check nodes with embeddings in the database
    nodes_with_embeddings = query_database("SELECT COUNT(*) as count FROM memory_nodes WHERE has_embedding = 1")
    embedding_count = nodes_with_embeddings[0]['count'] if nodes_with_embeddings else 0
    logger.info(f"Database contains {embedding_count} nodes with embeddings")
    
    # 4. Test semantic search via API
    search_response = call_api_endpoint(
        "/api/search/semantic",
        method="POST",
        payload={
            "query_text": "test query",
            "limit": 10,
            "min_similarity": 0.1  # Lower threshold for testing
        }
    )
    
    if "error" in search_response:
        logger.error(f"[X] Semantic search API call failed: {search_response['error']}")
    else:
        results = search_response.get("results", [])
        logger.info(f"[OK] Semantic search returned {len(results)} results")
        
    return True

def test_knowledge_graph():
    """Test knowledge graph endpoints and visualization"""
    logger.info("=== Testing Knowledge Graph ===")
    
    # Test memory nodes API
    nodes_response = call_api_endpoint("/api/memory/nodes?limit=5")
    
    if "error" in nodes_response:
        logger.error(f"[FAIL] Failed to fetch memory nodes: {nodes_response['error']}")
        return False
    
    node_count = len(nodes_response)
    logger.info(f"[PASS] Memory nodes API returned {node_count} nodes")
    
    # Test memory edges API
    edges_response = call_api_endpoint("/api/memory/edges?limit=5")
    
    if "error" in edges_response:
        logger.error(f"[FAIL] Failed to fetch memory edges: {edges_response['error']}")
        return False
    
    edge_count = len(edges_response)
    logger.info(f"[PASS] Memory edges API returned {edge_count} edges")
    
    # Test node weights API (for visualization scaling)
    weights_response = call_api_endpoint("/api/memory/nodes/weights")
    
    if "error" in weights_response:
        # Try alternative endpoint
        weights_response = call_api_endpoint("/api/memory/weights")
        
        if "error" in weights_response:
            logger.error(f"[FAIL] Alternative node weights API also failed: {weights_response['error']}")
            return False
        
        logger.info(f"[PASS] Alternative node weights API returned weights for {len(weights_response)} nodes")
    else:
        logger.info(f"[PASS] Node weights API returned weights for {len(weights_response)} nodes")
    
    # Test graph generation API
    generate_response = call_api_endpoint(
        "/api/memory/generate-graph",
        method="POST",
        payload={"text": "This is a test of graph generation", "limit": 10, "generate_edges": True}
    )
    
    if "error" in generate_response:
        logger.error(f"[FAIL] Graph generation API call failed: {generate_response['error']}")
        return False
    
    nodes_created = generate_response.get("nodes_created", 0)
    edges_created = generate_response.get("edges_created", 0)
    logger.info(f"[PASS] Graph generation created {nodes_created} nodes and {edges_created} edges")
    
    return True

def test_live_semantic_highlighting():
    """Test the Live Semantic Query Highlighting feature"""
    logger.info("=== Testing Live Semantic Query Highlighting ===")
    
    # Note: A full test of this feature requires manual interaction with the frontend UI
    logger.info("[i] To fully test Live Semantic Query Highlighting, use the frontend UI")
    logger.info("[i] The feature should enhance searchMemoryNodes() in api.ts and handleGraphSearch() in MemoryPanel.tsx")
    
    # Check if the frontend is running
    frontend_running = check_service_running("http://localhost:5173", timeout=1)
    if not frontend_running:
        logger.warning("Frontend server not running. Please start with: cd spyderweb/spyderweb && npm run dev")
    
    # Test the semantic search API itself to verify backend functionality
    try:
        # First, set up test queries with expected minimum result counts
        test_queries = [
            {"query": "knowledge", "expected_min": 3},
            {"query": "agent", "expected_min": 1},
            {"query": "memory", "expected_min": 1},
        ]
        
        for test_case in test_queries:
            query = test_case["query"]
            expected_min = test_case["expected_min"]
            logger.info(f"Testing semantic search with query: '{query}'")
            
            # Call the API directly
            response = call_api_endpoint(
                "/api/search/semantic",
                method="POST",
                payload={"query_text": query, "limit": 10, "min_similarity": 0.1}
            )
            
            if "error" in response:
                logger.error(f"[FAIL] Failed to call semantic search API: {str(response.get('error'))}")
                continue
                
            # Check if the results meet expectations
            if "results" in response:
                nodes = response["results"]
                
                if len(nodes) >= expected_min:
                    logger.info(f"[PASS] Query '{query}' returned sufficient results ({len(nodes)} >= {expected_min})")
                else:
                    logger.warning(f"[WARN] Query '{query}' returned fewer results than expected ({len(nodes)} < {expected_min})")
                
                # Check that results include similarity scores
                if nodes and not all("similarity" in node for node in nodes):
                    logger.warning("[WARN] Nodes missing 'similarity' property in response")
            else:
                logger.warning(f"[WARN] Semantic search API response missing 'results' key for query '{query}'")
                
    except Exception as e:
        logger.error(f"[FAIL] Error testing Live Semantic Query Highlighting: {str(e)}")
        return False
        
    return True

def generate_test_data():
    """Generate test data for the memory graph if needed"""
    logger.info("=== Generating Test Data ===")
    
    # Check if there's already sufficient data
    nodes = query_database("SELECT COUNT(*) as count FROM memory_nodes")
    count = nodes[0]['count'] if nodes else 0
    
    if count > 10:
        logger.info(f"[INFO] Database already has {count} memory nodes, no need to generate test data")
        return True
    
    # Generate some test nodes and edges
    test_data = {
        "texts": [
            "Artificial intelligence is revolutionizing the tech industry.",
            "Knowledge graphs help organize information in a connected way.",
            "Machine learning models improve with more high-quality training data.",
            "Natural language processing enables computers to understand human language.",
            "The future of AI depends on solving complex ethical challenges."
        ]
    }
    
    response = call_api_endpoint(
        "/api/memory/generate-graph",
        method="POST",
        payload=test_data
    )
    
    if "error" in response:
        logger.error(f"[FAIL] Failed to generate test data: {response['error']}")
        return False
    
    logger.info(f"[PASS] Generated {response.get('nodes_created', 0)} nodes and {response.get('edges_created', 0)} edges")
    return True

def fix_common_issues():
    """Fix common issues with the AI Studio setup"""
    logger.info("=== Fixing Common Issues ===")
    
    # 1. Ensure execution logs table exists
    run_command("python ai_studio_package/scripts/initialize_execution_logs.py")
    
    # 2. Ensure FAISS vector store is initialized
    run_command("python ai_studio_package/scripts/initialize_vector_store.py")
    
    return True

def check_service_running(url: str, timeout: int = 3) -> bool:
    """Check if a service is running at the given URL"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 400  # Any 2xx or 3xx status code
    except requests.exceptions.RequestException:
        return False

def test_semantic_search_api():
    """Test the semantic search API endpoint."""
    logger.info("Testing semantic search API endpoint...")
    
    # Define API endpoint (ensure proper URL formatting)
    host = "http://localhost:8000"
    endpoint = "/api/search/semantic"
    url = f"{host.rstrip('/')}/{endpoint.lstrip('/')}"
    
    # List of test queries with different parameters
    test_queries = [
        {"query": "knowledge graph", "limit": 5, "min_similarity": 0.15, "node_type": None},
        {"query": "agent", "limit": 10, "min_similarity": 0.1, "node_type": "memory"},
        {"query": "python", "limit": 5, "min_similarity": 0.1, "node_type": "code"}
    ]
    
    success = False
    
    for test_case in test_queries:
        query = test_case["query"]
        limit = test_case["limit"]
        min_similarity = test_case["min_similarity"]
        node_type = test_case["node_type"]
        
        # Build payload, only include node_type if not None
        payload = {
            "query_text": query,
            "limit": limit,
            "min_similarity": min_similarity
        }
        
        if node_type is not None:
            payload["node_type"] = node_type
        
        try:
            logger.info(f"Testing semantic search with query: '{query}', limit: {limit}, min_similarity: {min_similarity}, node_type: {node_type}")
            
            # Make the API call
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                num_results = len(results)
                
                logger.info(f"Semantic search API returned {num_results} results for '{query}'")
                
                if num_results > 0:
                    top_result = results[0]
                    logger.info(f"Top result: ID: {top_result.get('id')}, Similarity: {top_result.get('similarity', 0.0):.2f}")
                    logger.info(f"Top result type: {top_result.get('type', 'unknown')}")
                    
                    # Only show a preview of content
                    content = top_result.get('content', '')
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    logger.info(f"Content preview: {content_preview}")
                    
                    success = True
                else:
                    logger.warning(f"No results found for query '{query}'")
            else:
                logger.error(f"API request failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"Error testing semantic search API: {e}")
    
    if success:
        logger.info("[PASS] Semantic search API test completed successfully")
    else:
        logger.error("[FAIL] Semantic search API test failed")
    
    return success

def main():
    """Main function to run all tests"""
    parser = argparse.ArgumentParser(description="Test AI Studio functionality")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues")
    parser.add_argument("--generate-data", action="store_true", help="Generate test data if needed")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--test", choices=["all", "sil", "vector", "graph", "semantic"], default="all", 
                        help="Specify which test to run")
    
    args = parser.parse_args()
    
    global API_BASE_URL
    API_BASE_URL = args.api_url
    
    logger.info("=== AI Studio Functionality Test ===")
    logger.info(f"Testing against API: {API_BASE_URL}")
    
    # Check basic prerequisites
    if not check_file_exists(MEMORY_DB_PATH):
        logger.error("[X] Cannot proceed: Main database file is missing")
        return 1
    
    # Fix common issues if requested
    if args.fix:
        fix_common_issues()
    
    # Generate test data if requested
    if args.generate_data:
        generate_test_data()
    
    # Run the specified tests
    if args.test in ["all", "sil"]:
        test_execution_logs()
        test_critic_agent()
        test_refactor_agent()
        
    if args.test in ["all", "vector", "semantic"]:
        test_vector_store()
        test_live_semantic_highlighting()
        test_semantic_search_api()
        
    if args.test in ["all", "graph"]:
        test_knowledge_graph()
    
    logger.info("=== Test Completed ===")
    logger.info("""
Test Summary:
1. Review the log output for any errors marked with [X]
2. To test Live Semantic Query Highlighting:
   a. Start the backend: python main.py
   b. Start the frontend: cd spyderweb/spyderweb && npm run dev
   c. Open the Knowledge Graph view in your browser
   d. Enter search terms in the graph search field
   e. Observe how nodes are highlighted and the view zooms
3. To test Self-Improvement Loop functionality:
   a. Generate API activity by using the system
   b. Run: python ai_studio_package/scripts/schedule_critic.py --run-now
   c. Check for new critique nodes in the database
4. To test Semantic Search API directly:
   a. Start the backend: python main.py
   b. Run: python test_all_functionality.py --test semantic
   c. Check the logs for successful API responses and result details
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 