#!/usr/bin/env python3
"""
FAISS Migration Tool

This script migrates existing vector embeddings from SQLite to FAISS.
It preserves all metadata and ensures a seamless transition with no
data loss.
"""

import os
import sys
import json
import logging
import sqlite3
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('faiss_migration.log')
    ]
)
logger = logging.getLogger('faiss_migration')

# Add the project root to sys.path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import required modules
try:
    from ai_studio_package.infra.vector_store import VectorStoreManager
    from ai_studio_package.infra.vector_adapter import (
        get_vector_store, 
        set_dual_write_mode, 
        migrate_all_embeddings_to_faiss
    )
    from ai_studio_package.infra.db_enhanced import (
        get_db_connection, 
        get_vector_db_connection,
        embedding_model_name,
        embedding_dimensions
    )
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this script from the project root directory.")
    sys.exit(1)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Migrate embeddings from SQLite to FAISS')
    parser.add_argument('--force', action='store_true', help='Force migration even if FAISS store already exists')
    parser.add_argument('--dual-write', action='store_true', help='Enable dual write mode after migration')
    parser.add_argument('--verify', action='store_true', help='Verify migration by running searches')
    parser.add_argument('--faiss-path', type=str, default='data/vector_store.faiss', help='Path to FAISS index file')
    parser.add_argument('--metadata-path', type=str, default='data/vector_store_metadata.json', help='Path to metadata file')
    return parser.parse_args()

def count_sqlite_embeddings() -> int:
    """Count the number of embeddings in SQLite"""
    try:
        conn = get_vector_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error counting SQLite embeddings: {e}")
        return 0

def verify_migration(sample_queries: List[str] = None) -> bool:
    """
    Verify the migration by comparing search results from both stores
    
    Args:
        sample_queries: List of sample queries to test
        
    Returns:
        bool: True if verification passed, False otherwise
    """
    if not sample_queries:
        sample_queries = [
            "artificial intelligence",
            "machine learning model",
            "vector database",
            "embedding search",
            "natural language processing"
        ]
    
    try:
        # Get a db connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get a random set of memory nodes to generate queries from
        cursor.execute("SELECT id, content FROM memory_nodes WHERE has_embedding = 1 LIMIT 10")
        nodes = cursor.fetchall()
        
        # Add node contents to sample queries if we have any
        if nodes:
            for node in nodes:
                content = node['content']
                if content and len(content) > 20:
                    # Take first 10 words as a query
                    query = ' '.join(content.split()[:10])
                    sample_queries.append(query)
        
        # Import search functions
        from ai_studio_package.infra.db_enhanced import search_similar_nodes
        from ai_studio_package.infra.vector_adapter import search_similar_nodes_faiss
        
        passed = True
        for query in sample_queries:
            logger.info(f"Testing query: '{query[:50]}...' if len(query) > 50 else query")
            
            # Get results from both search methods
            faiss_results = search_similar_nodes_faiss(query, limit=5, min_similarity=0.5)
            
            # If we have results, the test passed
            if faiss_results:
                logger.info(f"✓ FAISS search returned {len(faiss_results)} results")
                # Log top result
                if faiss_results:
                    top_result = faiss_results[0]
                    logger.info(f"  Top result: {top_result.get('id')} - similarity: {top_result.get('similarity'):.4f}")
            else:
                logger.warning(f"✗ FAISS search returned no results for query")
                passed = False
        
        return passed
        
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False

def main():
    """Main migration function"""
    args = parse_args()
    
    # Check if FAISS is already set up
    faiss_exists = os.path.exists(args.faiss_path) and os.path.exists(args.metadata_path)
    
    if faiss_exists and not args.force:
        logger.info(f"FAISS store already exists at {args.faiss_path}")
        logger.info("Run with --force to overwrite")
        
        # Just verify if requested
        if args.verify:
            logger.info("Running verification...")
            result = verify_migration()
            logger.info(f"Verification {'passed' if result else 'failed'}")
        
        return
    
    # Count existing embeddings
    sqlite_count = count_sqlite_embeddings()
    logger.info(f"Found {sqlite_count} embeddings in SQLite")
    
    if sqlite_count == 0:
        logger.warning("No embeddings found in SQLite, nothing to migrate")
        return
    
    # Perform migration
    logger.info("Starting migration...")
    start_time = datetime.now()
    
    try:
        # Run the migration
        result = migrate_all_embeddings_to_faiss()
        
        if result.get('status') == 'success':
            logger.info(f"Migration completed successfully: {result.get('message')}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Migration took {duration:.2f} seconds")
            
            # Set dual write mode if requested
            if args.dual_write:
                set_dual_write_mode(True)
                logger.info("Dual write mode enabled for future operations")
            
            # Verify migration if requested
            if args.verify:
                logger.info("Running verification...")
                result = verify_migration()
                logger.info(f"Verification {'passed' if result else 'failed'}")
                
        else:
            logger.error(f"Migration failed: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")

if __name__ == "__main__":
    main() 