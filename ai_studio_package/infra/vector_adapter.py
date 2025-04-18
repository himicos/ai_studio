"""
Vector Adapter Module

This module provides an adapter layer between the existing SQLite-based vector storage
and the new FAISS-based vector store. It enables a gradual migration path while 
maintaining backward compatibility.
"""

import os
import json
import logging
import numpy as np
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import time
import traceback

# Import embedding model
from sentence_transformers import SentenceTransformer

# Import the vector store manager
from ai_studio_package.infra.vector_store import VectorStoreManager

# Import model configuration
from ai_studio_package.infra.models import embedding_model_name, embedding_dimensions

# Import db functions without creating circular imports
from ai_studio_package.infra.db import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)

# Singleton instance of VectorStoreManager
_vector_store_instance = None

# Default paths
DEFAULT_VECTOR_STORE_PATH = "data/vector_store.faiss"
DEFAULT_METADATA_PATH = "data/vector_store_metadata.json"

# Flag to control which vector store to use
USE_FAISS_VECTOR_STORE = os.environ.get("USE_FAISS_VECTOR_STORE", "true").lower() == "true"

# Flag to enable writing to both SQLite and FAISS during migration
_DUAL_WRITE_MODE = os.environ.get("VECTOR_DUAL_WRITE", "false").lower() == "true"

def dual_write_enabled() -> bool:
    """Check if dual write mode is enabled."""
    return _DUAL_WRITE_MODE

def set_dual_write_mode(enabled: bool = True) -> None:
    """
    Set dual write mode programmatically.
    
    Args:
        enabled (bool): Whether to enable dual write mode.
    """
    global _DUAL_WRITE_MODE
    _DUAL_WRITE_MODE = enabled
    logger.info(f"Dual write mode {'enabled' if enabled else 'disabled'}")

def get_vector_store(force_init: bool = False) -> VectorStoreManager:
    """
    Get the singleton instance of VectorStoreManager.
    
    Args:
        force_init (bool): Force reinitialization of the vector store.
        
    Returns:
        VectorStoreManager: The vector store manager instance.
    """
    global _vector_store_instance
    
    if _vector_store_instance is None or force_init:
        # Use the imported model configuration
        # No need to define them here anymore
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(DEFAULT_VECTOR_STORE_PATH), exist_ok=True)
        
        # Create the vector store
        _vector_store_instance = VectorStoreManager(
            index_path=DEFAULT_VECTOR_STORE_PATH,
            metadata_path=DEFAULT_METADATA_PATH,
            embedding_model_name=embedding_model_name,
            dimensions=embedding_dimensions,
            create_if_missing=True
        )
        
        # Ensure the model attribute is set
        if not hasattr(_vector_store_instance, 'model'):
            # Initialize model directly
            _vector_store_instance.model = SentenceTransformer(embedding_model_name)
            logger.info(f"Added missing model attribute to vector store using {embedding_model_name}")
        
        # Load the vector store
        _vector_store_instance.load()
        
    return _vector_store_instance

def get_memory_node(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Get memory node by ID.
    
    Args:
        node_id (str): The ID of the node to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: The memory node data or None if not found
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM memory_nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        
        if row:
            # SQLite row to dict
            node_data = dict(row)
            
            # Parse JSON fields
            for field in ["metadata", "tags"]:
                if field in node_data and node_data[field]:
                    try:
                        node_data[field] = json.loads(node_data[field])
                    except Exception as e:
                        logger.warning(f"Error parsing {field} JSON for node {node_id}: {e}")
                        # Keep as string if JSON parsing fails
            
            return node_data
        else:
            # Node not found in database, try to get from FAISS metadata
            logger.warning(f"Node {node_id} not found in database, trying FAISS metadata")
            
            # Get vector store
            vector_store = get_vector_store()
            
            # Check if vector store has metadata
            if not hasattr(vector_store, 'metadata'):
                return None
                
            # Search for node in metadata
            for idx, metadata in vector_store.metadata.items():
                if metadata.get('id') == node_id:
                    # Found the node in FAISS metadata, create a memory node from it
                    logger.info(f"Found node {node_id} in FAISS metadata, creating synthetic memory node")
                    
                    # Get title from metadata
                    title = metadata.get('title', f"Node {node_id[:8]}")
                    
                    # Create synthetic node with required fields
                    return {
                        'id': node_id,
                        'type': metadata.get('type', 'unknown'),
                        'title': title,
                        'content': metadata.get('content', title),
                        'tags': metadata.get('tags', []),
                        'created_at': metadata.get('created_at', int(time.time())),
                        'updated_at': metadata.get('updated_at', int(time.time())),
                        'has_embedding': 1,
                        'metadata': metadata
                    }
            
            logger.warning(f"Node {node_id} not found in FAISS metadata")
            return None
    except Exception as e:
        logger.error(f"Error getting memory node {node_id}: {e}")
        return None

def generate_embedding_for_node_faiss(node_id: str, text: str = None, embedding: np.ndarray = None) -> bool:
    """
    Generate and store embedding for a memory node using FAISS.
    
    Args:
        node_id (str): Node ID from memory_nodes table.
        text (str, optional): Text content to embed. If None, will fetch from database.
        embedding (np.ndarray, optional): Pre-computed embedding. If None, will generate from text.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # 1. Get the vector store
        vector_store = get_vector_store()
        
        if embedding is not None:
            # Use provided embedding
            node_content = text
            logger.debug(f"Using provided embedding for node {node_id}")
        else:
            # Get node content and generate embedding
            node = None
            if text is not None:
                node_content = text
            else:
                # Get node content from main DB
                node = get_memory_node(node_id)
                if not node or not node.get('content'):
                    logger.error(f"Node {node_id} not found or has no content for embedding.")
                    return False
                node_content = node['content']
            
            logger.debug(f"Generating FAISS embedding for node {node_id}...")
        
        # 2. Prepare metadata
        if node is None and text is not None:
            # If we're using provided text but don't have the node details,
            # try to fetch them for metadata
            node = get_memory_node(node_id)
            
        # 3. Create metadata
        metadata = {
            "id": node_id,
            "type": node.get('type') if node else None,
            "created_at": node.get('created_at', int(datetime.now().timestamp())) if node else int(datetime.now().timestamp()),
            "tags": node.get('tags', []) if node else []
        }
        
        # 4. Add to the vector store
        success = False
        if embedding is not None:
            # Use provided embedding
            success = vector_store.add_embedding(embedding, metadata)
        else:
            # Generate embedding from text
            success = vector_store.add_text(node_content, metadata)
        
        if success:
            # 5. Update flag in main DB
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE memory_nodes SET has_embedding = 1, updated_at = ? WHERE id = ?
            ''', (int(datetime.now().timestamp()), node_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully stored FAISS embedding for node {node_id}.")
            return True
        else:
            logger.error(f"Failed to add node {node_id} to FAISS vector store.")
            return False
            
    except Exception as e:
        logger.error(f"Error generating FAISS embedding for node {node_id}: {e}")
        return False

def search_similar_nodes_faiss(
    query_text: str,
    limit: int = 10,
    min_similarity: float = 0.7,
    node_type: Optional[str] = None,
    **kwargs  # Add **kwargs to handle any additional parameters
) -> List[Dict[str, Any]]:
    """
    Search for similar nodes using FAISS.
    
    Args:
        query_text: The text to search for.
        limit: Maximum number of results.
        min_similarity: Minimum similarity score (0-1) for results.
        node_type: Optional filter for specific node types.
        **kwargs: Additional parameters for backward compatibility.
        
    Returns:
        List of node dictionaries with similarity scores.
    """
    try:
        # Get the vector store
        vector_store = get_vector_store()
        
        if not vector_store:
            logger.error("Failed to get vector store for search")
            return []
        
        # Initialize model directly if not available in vector_store
        model = getattr(vector_store, 'model', None)
        if model is None:
            # Initialize model directly
            # Try to use CUDA if available
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                if device == "cuda":
                    logger.info(f"Using CUDA for embedding generation on model {embedding_model_name}")
                else:
                    logger.info(f"CUDA not available, using CPU for embedding generation")
                
                model = SentenceTransformer(embedding_model_name, device=device)
            except ImportError:
                logger.info(f"Torch not available, falling back to CPU")
                model = SentenceTransformer(embedding_model_name)
            
            logger.info(f"Created fallback model instance using {embedding_model_name}")
        
        # Generate embedding for query
        query_embedding = model.encode(query_text)
        
        # Search for similar vectors
        results = vector_store.search(
            query_embedding, 
            limit=limit, 
            score_threshold=min_similarity
        )
        
        if not results:
            logger.info(f"FAISS search returned no results for query '{query_text}' with min_similarity={min_similarity}")
            return []
        
        # Process results to node format
        nodes = []
        for result in results:
            node_id = result.get('id')
            similarity = result.get('score', 0.0)
            metadata = result.get('metadata', {})
            
            # Try to get essential node properties from metadata
            content = metadata.get('content', '')
            node_type_value = metadata.get('type', 'unknown')
            
            # Skip if node_type filter is specified and doesn't match
            if node_type and node_type_value != node_type:
                logger.debug(f"Filtering out node {node_id} with type {node_type_value} (requested: {node_type})")
                continue
                
            created_at = metadata.get('created_at', 0)
            tags = metadata.get('tags', [])
            
            # Add to results if passes all filters
            nodes.append({
                'id': node_id,
                'content': content or f"[No content available for node {node_id}]",
                'type': node_type_value,
                'created_at': created_at,
                'tags': tags or [],
                'similarity': similarity
            })
        
        logger.info(f"FAISS search found {len(nodes)} matching nodes for query '{query_text}' (after filtering)")
        return nodes
        
    except Exception as e:
        logger.error(f"Error searching FAISS: {e}")
        return []

def migrate_all_embeddings_to_faiss() -> Dict[str, Any]:
    """
    Migrate all embeddings from SQLite to FAISS.
    
    Returns:
        Dict[str, Any]: Status of the migration.
    """
    try:
        logger.info("Starting migration of embeddings from SQLite to FAISS...")
        
        # Check if a migration script exists
        migration_script_path = os.path.join(os.path.dirname(__file__), "migrate_vectors.py")
        if os.path.exists(migration_script_path):
            logger.info(f"Found migration script at {migration_script_path}. Running...")
            # Use exec to run the script in the current process
            with open(migration_script_path, 'r') as f:
                exec(f.read())
            logger.info("Migration script executed.")
            return {"status": "success", "message": "Migration script executed successfully."}
        
        # No migration script, so do it manually
        logger.info("No migration script found. Performing manual migration.")
        
        # Get vector DB connection
        conn_vector = sqlite3.connect("data/vectors.sqlite")
        conn_vector.row_factory = sqlite3.Row
        cursor_vector = conn_vector.cursor()
        
        # Check if the embeddings table exists
        cursor_vector.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
        if not cursor_vector.fetchone():
            logger.info("No embeddings table found in SQLite. Nothing to migrate.")
            conn_vector.close()
            return {"status": "success", "message": "No embeddings to migrate."}
        
        # Get all embeddings
        cursor_vector.execute("SELECT node_id, embedding, model, dimensions FROM embeddings")
        embeddings_data = cursor_vector.fetchall()
        conn_vector.close()
        
        if not embeddings_data:
            logger.info("No embeddings found in SQLite. Nothing to migrate.")
            return {"status": "success", "message": "No embeddings to migrate."}
        
        logger.info(f"Found {len(embeddings_data)} embeddings to migrate.")
        
        # Get the vector store
        vector_store = get_vector_store(force_init=True)
        
        # Process each embedding
        migrated_count = 0
        failed_count = 0
        
        for row in embeddings_data:
            try:
                node_id = row['node_id']
                embedding_blob = row['embedding']
                
                # Get the node data
                node = get_memory_node(node_id)
                if not node:
                    logger.warning(f"Node {node_id} not found. Skipping migration.")
                    failed_count += 1
                    continue
                
                # Convert BLOB to numpy array
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                
                # Add to FAISS with the embedding directly
                metadata = {
                    "id": node_id,
                    "type": node.get('type'),
                    "title": node.get('title', ''),
                    "created_at": node.get('created_at', int(datetime.now().timestamp())),
                    "tags": node.get('tags', [])
                }
                
                success = vector_store.add_embedding(embedding, metadata)
                
                if success:
                    migrated_count += 1
                    # Log progress periodically
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count}/{len(embeddings_data)} embeddings.")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to migrate embedding for node {node_id}.")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error migrating embedding for node {node_id}: {e}")
        
        # Save the vector store
        vector_store.save()
        
        logger.info(f"Migration complete. Migrated {migrated_count} embeddings. Failed: {failed_count}.")
        return {
            "status": "success",
            "message": f"Migration complete. Migrated {migrated_count} embeddings. Failed: {failed_count}.",
            "migrated_count": migrated_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return {
            "status": "error",
            "message": f"Migration failed: {str(e)}",
            "migrated_count": 0,
            "failed_count": 0
        } 