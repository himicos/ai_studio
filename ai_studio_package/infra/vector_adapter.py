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
            dimensions=embedding_dimensions
        )
        
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

def search_similar_nodes_faiss(query_text, limit=10, node_type=None, min_similarity=0.7, vector_store=None):
    """
    Search for semantically similar nodes using FAISS.
    
    Args:
        query_text (str): The text query to search for
        limit (int): Maximum number of results to return
        node_type (str, optional): Filter by node type
        min_similarity (float): Minimum similarity score (0.0 to 1.0)
        vector_store (VectorStoreManager, optional): Optional vector store instance
    
    Returns:
        list: List of memory nodes with similarity scores
    """
    try:
        # Always use a very low internal threshold to get results then filter
        internal_min_similarity = 0.01
        
        logger.info(f"FAISS Search: query='{query_text}', limit={limit}, node_type={node_type}, "
                   f"requested_min_similarity={min_similarity}, internal_min_similarity={internal_min_similarity}")
        
        # Get the vector store if not provided
        try:
            vector_store = vector_store or get_vector_store()
            
            # Check if the FAISS index exists and has vectors
            if not hasattr(vector_store, 'index') or vector_store.index is None:
                logger.error("No valid FAISS index found in vector store")
                return []
                
            # Check if there's metadata
            if not hasattr(vector_store, 'metadata') or not vector_store.metadata:
                logger.error("No metadata found in vector store")
                return []
                
            # Check vector count
            vector_count = vector_store.index.ntotal if hasattr(vector_store.index, 'ntotal') else 0
            if vector_count == 0:
                logger.warning("FAISS index contains no vectors")
                return []
                
            logger.info(f"FAISS index contains {vector_count} vectors with {len(vector_store.metadata)} metadata entries")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            return []
        
        # Initialize the embedding model directly or from vector_store if available
        try:
            # Get model from vector_store.embedding_model if available, otherwise create directly
            if hasattr(vector_store, 'embedding_model'):
                model = vector_store.embedding_model
                logger.debug("Using embedding model from vector_store.embedding_model")
            else:
                # Initialize model directly
                model = SentenceTransformer(embedding_model_name)
                logger.debug(f"Initialized embedding model directly: {embedding_model_name}")
            
            # Generate embedding for query text
            query_embedding = model.encode(query_text)
        except Exception as e:
            logger.error(f"Error generating embedding for query: {e}")
            return []
        
        # Search for similar vectors
        # Get more results than we need so we can filter by node_type if needed
        search_limit = limit * 5 if node_type else limit
        max_index_size = len(vector_store.metadata)
        
        try:
            # Note: this search against FAISS will always return results if index has vectors,
            # we'll filter by similarity threshold later
            distances, indices = vector_store.index.search(
                np.array([query_embedding]).astype(np.float32),
                k=min(search_limit, max_index_size)
            )
            
            # Log the raw indices and distances
            logger.info(f"FAISS raw results: found {indices.shape[1]} initial matches")
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []
        
        results = []
        
        # Get memory nodes for results
        for i in range(indices.shape[1]):
            try:
                # Get the index
                idx = int(indices[0][i])
                
                # Skip if index is invalid
                if idx < 0:
                    continue
                    
                # Convert to string index for metadata lookup
                str_idx = str(idx)
                
                if str_idx not in vector_store.metadata:
                    continue
                    
                # Get metadata for this index
                metadata = vector_store.metadata[str_idx]
                
                # Get ID from metadata
                node_id = metadata.get('id')
                if not node_id:
                    continue
                    
                # Calculate similarity from distance (L2 distance to cosine similarity)
                # This formula converts L2 distance to cosine similarity
                distance = float(distances[0][i])
                similarity = 1 - (distance / 2.0)
                
                # Skip if similarity is below threshold
                if similarity < min_similarity:
                    continue
                    
                # Get memory node from database
                memory_node = get_memory_node(node_id)
                
                # If node not found in DB and metadata, create a synthetic node
                if not memory_node:
                    # Create a synthetic node for testing directly from metadata
                    # This is useful for test data created by direct_fix.py
                    title = metadata.get('title', f"Node {node_id[:8]}")
                    content = metadata.get('content', title)
                    if not content and 'title' in metadata:
                        # Use title as content if no content available
                        content = metadata['title']
                        
                    memory_node = {
                        'id': node_id,
                        'type': metadata.get('type', 'test_document'),
                        'title': title,
                        'content': content,
                        'tags': metadata.get('tags', []),
                        'created_at': metadata.get('created_at', int(time.time())),
                        'has_embedding': 1,
                        'metadata': metadata
                    }
                    
                    logger.info(f"Created synthetic node {node_id} from FAISS metadata")
                    
                # Add similarity score to node
                memory_node['similarity'] = float(similarity)
                
                # Add to results
                results.append(memory_node)
                
                # Debug log
                logger.debug(f"Added result: id={node_id}, type={memory_node['type']}, similarity={memory_node['similarity']:.4f}")
            except Exception as e:
                logger.warning(f"Error processing result {i}: {e}")
                continue
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        # Apply user's original requested similarity filter
        filtered_results = [node for node in results if node.get("similarity", 0) >= min_similarity]
        
        # Limit results
        final_results = filtered_results[:limit]
        
        # Log the filtering process
        logger.info(f"FAISS search filtering: raw={indices.shape[1]} → valid with metadata={len(results)} → "
                   f"above min_similarity={len(filtered_results)} → final limited results={len(final_results)}")
        
        # Log all results for debugging
        for i, node in enumerate(final_results):
            logger.info(f"FAISS result {i+1}: ID={node.get('id')}, Type={node.get('type')}, "
                       f"Similarity={node.get('similarity', 0):.4f}")
        
        if not final_results:
            logger.warning(f"No results found with min_similarity={min_similarity}. "
                          f"Try lowering the threshold or checking if FAISS index contains data.")
        
        return final_results
        
    except Exception as e:
        logger.error(f"Error in search_similar_nodes_faiss: {e}", exc_info=True)
        # Return empty list on error
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