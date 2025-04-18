#!/usr/bin/env python3
"""
Fix Vector Store script for AI Studio

This script diagnoses and fixes issues with the FAISS vector store:
1. Checks if the vector store exists and has data
2. Validates the metadata file
3. Re-indexes memory nodes that should have embeddings
4. Tests the semantic search functionality
"""

import os
import sys
import json
import sqlite3
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_DB_PATH = "memory/memory.sqlite"
VECTOR_STORE_PATH = "data/vector_store.faiss"
VECTOR_METADATA_PATH = "data/vector_store_metadata.json"

def check_files():
    """Check if vector store files exist and report their status"""
    logger.info("=== Checking Vector Store Files ===")
    
    # Check if main database exists
    db_path = Path(MEMORY_DB_PATH)
    if not db_path.exists():
        logger.error(f"❌ Main database missing: {MEMORY_DB_PATH}")
        return False
    logger.info(f"✅ Main database exists: {MEMORY_DB_PATH} (Size: {db_path.stat().st_size/1024:.2f} KB)")
    
    # Check if FAISS index exists
    faiss_path = Path(VECTOR_STORE_PATH)
    if not faiss_path.exists():
        logger.error(f"❌ FAISS index missing: {VECTOR_STORE_PATH}")
        return False
    
    faiss_size = faiss_path.stat().st_size
    logger.info(f"✅ FAISS index exists: {VECTOR_STORE_PATH} (Size: {faiss_size/1024:.2f} KB)")
    
    if faiss_size < 1000:
        logger.warning(f"⚠️ FAISS index is very small ({faiss_size} bytes). It might be empty or corrupted.")
    
    # Check if metadata file exists
    metadata_path = Path(VECTOR_METADATA_PATH)
    if not metadata_path.exists():
        logger.error(f"❌ Vector metadata missing: {VECTOR_METADATA_PATH}")
        return False
    
    metadata_size = metadata_path.stat().st_size
    logger.info(f"✅ Vector metadata exists: {VECTOR_METADATA_PATH} (Size: {metadata_size/1024:.2f} KB)")
    
    if metadata_size < 100:
        logger.warning(f"⚠️ Vector metadata is very small ({metadata_size} bytes). It might be empty or corrupted.")
    
    return True

def check_metadata():
    """Check vector store metadata for consistency"""
    logger.info("=== Checking Vector Store Metadata ===")
    
    try:
        with open(VECTOR_METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            
        # Check if the metadata has the expected structure
        if not isinstance(metadata, dict):
            logger.error(f"❌ Vector metadata is not a dictionary: {type(metadata)}")
            return False
            
        required_keys = ['id_to_node_id', 'embedding_model']
        missing_keys = [key for key in required_keys if key not in metadata]
        
        if missing_keys:
            logger.error(f"❌ Vector metadata is missing required keys: {missing_keys}")
            return False
            
        # Check if there are any vectors
        vector_count = len(metadata.get('id_to_node_id', {}))
        logger.info(f"Vector metadata contains {vector_count} vector mappings")
        
        if vector_count == 0:
            logger.warning("⚠️ Vector metadata contains no vector mappings")
            
        # Check embedding model
        embedding_model = metadata.get('embedding_model', 'Unknown')
        logger.info(f"Embedding model: {embedding_model}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error reading vector metadata: {e}")
        return False

def query_database(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a query against the database and return results as dictionaries"""
    try:
        conn = sqlite3.connect(MEMORY_DB_PATH)
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

def check_database_nodes():
    """Check nodes in the database that should have embeddings"""
    logger.info("=== Checking Database Nodes ===")
    
    # Check total nodes
    total_nodes = query_database("SELECT COUNT(*) as count FROM memory_nodes")
    total_count = total_nodes[0]['count'] if total_nodes else 0
    logger.info(f"Database contains {total_count} memory nodes in total")
    
    # Check nodes with embeddings
    embedded_nodes = query_database("SELECT COUNT(*) as count FROM memory_nodes WHERE has_embedding = 1")
    embedded_count = embedded_nodes[0]['count'] if embedded_nodes else 0
    logger.info(f"Database has {embedded_count} nodes marked as having embeddings")
    
    # Check nodes missing embeddings
    unembedded_nodes = query_database("SELECT COUNT(*) as count FROM memory_nodes WHERE has_embedding = 0")
    unembedded_count = unembedded_nodes[0]['count'] if unembedded_nodes else 0
    logger.info(f"Database has {unembedded_count} nodes marked as missing embeddings")
    
    # Get sample node types to understand what kinds of nodes should have embeddings
    node_types = query_database("SELECT type, COUNT(*) as count FROM memory_nodes GROUP BY type")
    logger.info("Node types in the database:")
    for node_type in node_types:
        logger.info(f"  - {node_type['type']}: {node_type['count']} nodes")
    
    return total_count, embedded_count, unembedded_count

def backup_vector_files():
    """Create backups of the vector store files"""
    logger.info("=== Creating Backups ===")
    
    timestamp = int(time.time())
    
    # Backup FAISS index if it exists
    faiss_path = Path(VECTOR_STORE_PATH)
    if faiss_path.exists():
        backup_path = f"{VECTOR_STORE_PATH}.backup.{timestamp}"
        try:
            import shutil
            shutil.copy2(VECTOR_STORE_PATH, backup_path)
            logger.info(f"✅ Created backup of FAISS index: {backup_path}")
        except Exception as e:
            logger.error(f"❌ Failed to backup FAISS index: {e}")
    
    # Backup metadata if it exists
    metadata_path = Path(VECTOR_METADATA_PATH)
    if metadata_path.exists():
        backup_path = f"{VECTOR_METADATA_PATH}.backup.{timestamp}"
        try:
            import shutil
            shutil.copy2(VECTOR_METADATA_PATH, backup_path)
            logger.info(f"✅ Created backup of vector metadata: {backup_path}")
        except Exception as e:
            logger.error(f"❌ Failed to backup vector metadata: {e}")
    
    return timestamp

def find_migration_script():
    """Find any FAISS migration scripts in the project"""
    logger.info("=== Looking for Migration Scripts ===")
    
    # Common paths to check
    paths_to_check = [
        "migrate_to_faiss.py",
        "scripts/migrate_to_faiss.py",
        "ai_studio_package/scripts/migrate_to_faiss.py",
        "tools/migrate_to_faiss.py"
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            logger.info(f"✅ Found migration script: {path}")
            return path
    
    logger.warning("⚠️ No migration script found")
    return None

def reset_embedding_flags():
    """Reset embedding flags in the database"""
    logger.info("=== Resetting Embedding Flags ===")
    
    try:
        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()
        
        # Reset has_embedding to 0 for all nodes
        cursor.execute("UPDATE memory_nodes SET has_embedding = 0")
        affected_rows = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Reset embedding flags for {affected_rows} nodes")
        return affected_rows
    except Exception as e:
        logger.error(f"❌ Error resetting embedding flags: {e}")
        return 0

def run_migration_script(script_path):
    """Run the migration script to rebuild the vector store"""
    logger.info(f"=== Running Migration Script: {script_path} ===")
    
    try:
        import subprocess
        
        # Run the script as a subprocess
        process = subprocess.Popen(
            f"python {script_path}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        
        if exit_code == 0:
            logger.info(f"✅ Migration script executed successfully")
            # Log some output
            for line in stdout.split('\n')[:20]:  # Show first 20 lines
                if line.strip():
                    logger.info(f"  {line.strip()}")
            return True
        else:
            logger.error(f"❌ Migration script failed with exit code: {exit_code}")
            logger.error(f"Error output: {stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Error running migration script: {e}")
        return False

def rebuild_vector_store():
    """Attempt to rebuild the vector store"""
    logger.info("=== Rebuilding Vector Store ===")
    
    # Find a migration script
    migration_script = find_migration_script()
    
    if not migration_script:
        logger.error("❌ Cannot rebuild vector store: No migration script found")
        return False
    
    # Create backups
    backup_timestamp = backup_vector_files()
    
    # Reset embedding flags
    reset_embedding_flags()
    
    # Run the migration script
    success = run_migration_script(migration_script)
    
    if success:
        logger.info("✅ Vector store rebuild completed successfully")
        
        # Verify the results
        check_files()
        check_metadata()
        check_database_nodes()
        
        return True
    else:
        logger.error("❌ Vector store rebuild failed")
        return False

def sample_nodes_without_embeddings(limit=5):
    """Get a sample of nodes without embeddings"""
    logger.info(f"=== Sampling {limit} Nodes Without Embeddings ===")
    
    nodes = query_database(
        f"SELECT id, type, content FROM memory_nodes WHERE has_embedding = 0 LIMIT {limit}"
    )
    
    if not nodes:
        logger.info("No nodes found without embeddings")
        return []
    
    logger.info(f"Found {len(nodes)} nodes without embeddings:")
    for node in nodes:
        # Truncate content for display
        content = node['content']
        if len(content) > 50:
            content = content[:50] + "..."
        logger.info(f"  - Node {node['id']} (Type: {node['type']}): {content}")
    
    return nodes

def main():
    """Main function to diagnose and fix vector store issues"""
    logger.info("=== Vector Store Diagnosis and Fix ===")
    
    # Check if files exist
    if not check_files():
        logger.error("❌ Essential files are missing. Cannot proceed with diagnosis.")
        return 1
    
    # Check metadata
    metadata_ok = check_metadata()
    
    # Check database nodes
    total_count, embedded_count, unembedded_count = check_database_nodes()
    
    # Sample nodes without embeddings
    sample_nodes_without_embeddings()
    
    # Determine if we need to rebuild
    needs_rebuild = False
    
    if not metadata_ok:
        logger.warning("⚠️ Vector store metadata has issues")
        needs_rebuild = True
    
    if embedded_count == 0:
        logger.warning("⚠️ No nodes have embeddings")
        needs_rebuild = True
    
    if Path(VECTOR_STORE_PATH).stat().st_size < 1000:
        logger.warning("⚠️ FAISS index is very small")
        needs_rebuild = True
    
    # Ask for confirmation
    if needs_rebuild:
        logger.warning("⚠️ Vector store needs to be rebuilt")
        response = input("Would you like to rebuild the vector store? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            logger.info("Proceeding with vector store rebuild")
            success = rebuild_vector_store()
            
            if success:
                logger.info("✅ Vector store has been successfully rebuilt")
            else:
                logger.error("❌ Vector store rebuild failed")
                return 1
        else:
            logger.info("Vector store rebuild skipped by user")
    else:
        logger.info("✓ Vector store appears to be in good condition")
    
    logger.info("=== Vector Store Fix Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 