"""
Vector Store Manager for FAISS-based vector storage.

This module provides a class for managing FAISS vector indices, including
search, add, and delete operations as well as persistence functionality.
"""

import os
import json
import faiss
import numpy as np
import torch
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Configure logging
logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Manager for FAISS vector storage operations, including search, add and delete.
    Handles persistence of both the index and metadata.
    """
    
    def __init__(
        self, 
        index_path: str,
        metadata_path: str,
        embedding_model_name: str = 'all-MiniLM-L6-v2',
        dimensions: int = 384,
        create_if_missing: bool = True
    ):
        """
        Initialize the vector store manager.
        
        Args:
            index_path (str): Path to the FAISS index file.
            metadata_path (str): Path to the metadata JSON file.
            embedding_model_name (str): Name of the embedding model to use.
            dimensions (int): Dimensions of the embeddings.
            create_if_missing (bool): Create index and metadata if missing.
        """
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedding_model_name = embedding_model_name
        self.dimensions = dimensions
        
        # Initialize the index and metadata dict
        self.index = None
        self.metadata = {}
        self.next_id = 0
        
        # Load the embedding model
        self._embedding_model = None
        
        # Initialize or load existing index
        if create_if_missing:
            self._initialize_or_load()
    
    def _initialize_or_load(self) -> None:
        """Initialize a new index or load an existing one."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.load()
                logger.info(f"Loaded existing vector store from {self.index_path}")
                return
            except Exception as e:
                logger.error(f"Error loading vector store: {e}. Creating a new one.")
        
        # Create a new index
        self._create_new_index()
        self.metadata = {}
        self.next_id = 0
        
        # Save the empty index
        self.save()
        logger.info(f"Created new vector store at {self.index_path}")
    
    def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        # Create a new L2 index
        self.index = faiss.IndexFlatL2(self.dimensions)
        
        # Convert to IndexIDMap to support vector removal by ID
        self.index = faiss.IndexIDMap(self.index)
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """
        Get or initialize the embedding model.
        
        Returns:
            SentenceTransformer: The embedding model.
        """
        if self._embedding_model is None:
            try:
                # Try to initialize with GPU support
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._embedding_model = SentenceTransformer(self.embedding_model_name, device=device)
                logger.info(f"Initialized embedding model {self.embedding_model_name} on {device}")
            except Exception as e:
                # Fall back to CPU
                logger.warning(f"Error initializing model with GPU, falling back to CPU: {e}")
                self._embedding_model = SentenceTransformer(self.embedding_model_name, device="cpu")
        
        return self._embedding_model
    
    def load(self) -> bool:
        """
        Load the index and metadata from disk.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Load the index
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.debug(f"Loaded FAISS index from {self.index_path}")
            else:
                self._create_new_index()
                logger.debug(f"FAISS index not found, created new one")
            
            # Load the metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = data.get('metadata', {})
                    self.next_id = data.get('next_id', 0)
                    
                    # If the metadata doesn't have 'metadata' key, assume the whole file is metadata
                    if 'metadata' not in data and data:
                        self.metadata = data
                        
                logger.debug(f"Loaded metadata from {self.metadata_path}: {len(self.metadata)} entries")
            else:
                self.metadata = {}
                self.next_id = 0
                logger.debug(f"Metadata file not found, initialized empty metadata")
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            # Initialize empty index and metadata
            self._create_new_index()
            self.metadata = {}
            self.next_id = 0
            return False
    
    def save(self) -> bool:
        """
        Save the index and metadata to disk.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save the index
            faiss.write_index(self.index, self.index_path)
            
            # Save the metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': self.metadata,
                    'next_id': self.next_id,
                    'dimensions': self.dimensions,
                    'model': self.embedding_model_name,
                    'updated_at': int(datetime.now().timestamp())
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved vector store with {self.index.ntotal} vectors and {len(self.metadata)} metadata entries")
            return True
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            return False
    
    def add_text(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a text entry to the vector store.
        
        Args:
            text (str): The text to add.
            metadata (Dict[str, Any], optional): Additional metadata.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            
            # Add to index
            return self.add_embedding(embedding, metadata)
            
        except Exception as e:
            logger.error(f"Error adding text to vector store: {e}")
            return False
    
    def add_embedding(self, embedding: np.ndarray, metadata: Dict[str, Any] = None) -> bool:
        """
        Add an embedding to the vector store.
        
        Args:
            embedding (np.ndarray): The embedding to add.
            metadata (Dict[str, Any], optional): Additional metadata.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure embedding is of the right shape and type
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)
            
            if embedding.shape[1] != self.dimensions:
                raise ValueError(f"Embedding dimension mismatch: expected {self.dimensions}, got {embedding.shape[1]}")
            
            embedding = embedding.astype(np.float32)
            
            # Get or use provided ID
            node_id = metadata.get('id') if metadata and 'id' in metadata else f"auto_{self.next_id}"
            vector_id = self.next_id
            self.next_id += 1
            
            # Add to index
            self.index.add_with_ids(embedding, np.array([vector_id], dtype=np.int64))
            
            # Add metadata
            self.metadata[str(vector_id)] = {
                'id': node_id,
                'metadata': metadata or {},
                'added_at': int(datetime.now().timestamp())
            }
            
            logger.debug(f"Added embedding with vector_id={vector_id}, node_id={node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding embedding to vector store: {e}")
            return False
    
    def search(
        self, 
        query: Union[str, np.ndarray], 
        limit: int = 10, 
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query (Union[str, np.ndarray]): Query text or embedding.
            limit (int): Maximum number of results.
            score_threshold (float): Minimum score (0 to 1) for results.
            
        Returns:
            List[Dict[str, Any]]: List of results with metadata and scores.
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("Vector store is empty, returning empty results")
                return []
            
            # Generate embedding if query is a string
            if isinstance(query, str):
                query_vector = self.embedding_model.encode(query, convert_to_numpy=True)
            else:
                query_vector = query
            
            # Ensure vector is the right shape
            if len(query_vector.shape) == 1:
                query_vector = query_vector.reshape(1, -1)
            
            # Search the index
            distances, indices = self.index.search(query_vector.astype(np.float32), k=limit)
            
            # Process results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                # Skip invalid indices (-1 means no match)
                if idx == -1:
                    continue
                
                # Convert L2 distance to similarity score (0 to 1)
                # The L2 distance is unbounded, so we use a heuristic transformation
                # Lower distance = higher similarity
                similarity = 1.0 / (1.0 + distance)
                
                # Apply score threshold
                if similarity < score_threshold:
                    continue
                
                # Get metadata
                metadata = self.metadata.get(str(idx), {})
                node_id = metadata.get('id')
                metadata_content = metadata.get('metadata', {})
                
                # Add to results
                results.append({
                    'id': node_id,
                    'score': similarity,
                    'metadata': metadata_content,
                    'vector_id': int(idx)
                })
            
            logger.debug(f"Search found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def delete(self, node_id: str) -> bool:
        """
        Delete a vector by node ID.
        
        Args:
            node_id (str): Node ID to delete.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Find all vector IDs with this node ID
            vector_ids_to_remove = []
            for vector_id, metadata in self.metadata.items():
                if metadata.get('id') == node_id:
                    vector_ids_to_remove.append(int(vector_id))
            
            if not vector_ids_to_remove:
                logger.warning(f"No vectors found for node {node_id}")
                return False
            
            # Remove from the index
            self.index.remove_ids(np.array(vector_ids_to_remove, dtype=np.int64))
            
            # Remove from metadata
            for vector_id in vector_ids_to_remove:
                if str(vector_id) in self.metadata:
                    del self.metadata[str(vector_id)]
            
            logger.info(f"Deleted {len(vector_ids_to_remove)} vectors for node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector(s) for node {node_id}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear the entire vector store.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create a new empty index
            self._create_new_index()
            
            # Clear metadata
            self.metadata = {}
            self.next_id = 0
            
            logger.info("Vector store cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dict[str, Any]: Statistics about the vector store.
        """
        return {
            'vector_count': self.index.ntotal if self.index else 0,
            'metadata_count': len(self.metadata),
            'dimensions': self.dimensions,
            'model': self.embedding_model_name,
            'index_file': self.index_path,
            'metadata_file': self.metadata_path
        } 