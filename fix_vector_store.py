#!/usr/bin/env python
"""
Script to diagnose and fix the VectorStoreManager model attribute error
"""
import os
import sys
import json
import logging
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vector_store_fix")

# Constants
DEFAULT_VECTOR_STORE_PATH = "data/vector_store.faiss"
DEFAULT_METADATA_PATH = "data/vector_store_metadata.json"
DB_PATH = "data/memory.sqlite"

def check_database():
    """Check the SQLite database status"""
    try:
        if not os.path.exists(DB_PATH):
            logger.error(f"Database file not found at {DB_PATH}")
            return False
            
        # Connect to SQLite DB
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total count of memory nodes
        cursor.execute("SELECT COUNT(*) FROM memory_nodes")
        total_nodes = cursor.fetchone()[0]
        
        # Get count of memory nodes with embeddings
        cursor.execute("SELECT COUNT(*) FROM memory_nodes WHERE has_embedding = 1")
        nodes_with_embeddings = cursor.fetchone()[0]
        
        # Get count by type
        cursor.execute("SELECT type, COUNT(*) FROM memory_nodes GROUP BY type")
        type_counts = cursor.fetchall()
        
        logger.info(f"Database contains {total_nodes} total memory nodes")
        logger.info(f"Database has {nodes_with_embeddings} nodes with embeddings")
        
        logger.info("Node counts by type:")
        for row in type_counts:
            logger.info(f"  {row['type']}: {row['count']}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

def check_faiss_index():
    """Check FAISS index status"""
    try:
        # Check if FAISS index file exists
        if not os.path.exists(DEFAULT_VECTOR_STORE_PATH):
            logger.error(f"FAISS index file not found at {DEFAULT_VECTOR_STORE_PATH}")
            return False
            
        # Check if metadata file exists
        if not os.path.exists(DEFAULT_METADATA_PATH):
            logger.error(f"FAISS metadata file not found at {DEFAULT_METADATA_PATH}")
            return False
            
        # Load metadata
        with open(DEFAULT_METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            
        logger.info(f"FAISS metadata contains {len(metadata)} entries")
        
        # Count by type in metadata
        type_counts = {}
        for idx, entry in metadata.items():
            node_type = entry.get('type')
            if node_type:
                type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        logger.info("FAISS node counts by type:")
        for node_type, count in type_counts.items():
            logger.info(f"  {node_type}: {count}")
            
        return True
    except Exception as e:
        logger.error(f"Error checking FAISS index: {e}")
        return False

def fix_vector_store():
    """
    Fix the VectorStoreManager model attribute error
    
    The error occurs because the model attribute is missing in VectorStoreManager.
    This function adds the model attribute when loading the vector store.
    """
    try:
        from ai_studio_package.infra.vector_adapter import get_vector_store
        from ai_studio_package.infra.vector_store import VectorStoreManager
        
        # Check if VectorStoreManager has the model attribute
        logger.info("Checking VectorStoreManager class...")
        model_exists = hasattr(VectorStoreManager, 'model')
        logger.info(f"VectorStoreManager has model attribute: {model_exists}")
        
        if not model_exists:
            logger.info("Patching VectorStoreManager to include the model attribute...")
            
            # Create original method reference
            original_init = VectorStoreManager.__init__
            
            # Define patched init method
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                # Add the model attribute
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Added model attribute to VectorStoreManager instance")
                
            # Replace the init method
            VectorStoreManager.__init__ = patched_init
            
            logger.info("VectorStoreManager patched successfully")
            
            # Test the patch
            vector_store = get_vector_store()
            logger.info(f"Vector store loaded successfully: {vector_store is not None}")
            logger.info(f"Vector store now has model attribute: {hasattr(vector_store, 'model')}")
            
            # Test a search 
            test_query = "artificial intelligence"
            logger.info(f"Testing search with query: '{test_query}'")
            
            # Generate embedding for test query
            embedding = vector_store.model.encode([test_query])[0]
            
            # Log success
            logger.info("Test search embedding generated successfully")
            logger.info("Patch applied successfully")
            
            return True
        else:
            logger.info("VectorStoreManager already has model attribute, no fix needed")
            return True
    except Exception as e:
        logger.error(f"Error fixing vector store: {e}")
        return False

def fix_search_similar_nodes_faiss():
    """
    Fix the search_similar_nodes_faiss function to handle the model attribute error
    """
    try:
        import importlib.util
        
        # Path to the vector_adapter.py file
        vector_adapter_path = "ai_studio_package/infra/vector_adapter.py"
        
        if not os.path.exists(vector_adapter_path):
            logger.error(f"Vector adapter file not found at {vector_adapter_path}")
            return False
            
        # Read the file content
        with open(vector_adapter_path, 'r') as f:
            content = f.read()
            
        # Check if the function uses vector_store.model
        if "model = vector_store.model" in content:
            logger.info("Found the error: vector_adapter.py uses vector_store.model")
            
            # Create a fixed version of the file
            fixed_content = content.replace(
                "model = vector_store.model", 
                "# Initialize model directly if not available in vector_store\n    model = getattr(vector_store, 'model', SentenceTransformer('all-MiniLM-L6-v2'))"
            )
            
            # Write the fixed content back
            with open(vector_adapter_path, 'w') as f:
                f.write(fixed_content)
                
            logger.info("Fixed vector_adapter.py to handle missing model attribute")
            return True
        else:
            logger.info("Could not find the exact error pattern in vector_adapter.py")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing search_similar_nodes_faiss function: {e}")
        return False

def main():
    """Main entry point"""
    logger.info("Starting diagnosis and fix for VectorStoreManager model attribute error")
    
    # Check database status
    logger.info("Checking database status...")
    db_status = check_database()
    
    # Check FAISS index status
    logger.info("\nChecking FAISS index status...")
    faiss_status = check_faiss_index()
    
    # Apply fixes
    logger.info("\nApplying fixes...")
    
    # Fix search_similar_nodes_faiss function
    fix_success_1 = fix_search_similar_nodes_faiss()
    
    # Fix VectorStoreManager
    fix_success_2 = fix_vector_store()
    
    # Summary
    logger.info("\nSummary:")
    logger.info(f"Database check: {'OK' if db_status else 'FAILED'}")
    logger.info(f"FAISS index check: {'OK' if faiss_status else 'FAILED'}")
    logger.info(f"Vector adapter fix: {'APPLIED' if fix_success_1 else 'FAILED'}")
    logger.info(f"VectorStoreManager fix: {'APPLIED' if fix_success_2 else 'FAILED'}")
    
    if fix_success_1 or fix_success_2:
        logger.info("\nFix applied successfully. Please restart your application.")
    else:
        logger.info("\nNo fixes were applied. Please check the logs for details.")

if __name__ == "__main__":
    main() 