"""
Model Loading Utilities for AI Studio

This module provides functions for loading, initializing, and using various ML models,
particularly for embedding generation and vector operations.
"""

import logging
import os
import torch
from typing import Optional, Dict, Any, Union
from sentence_transformers import SentenceTransformer

# Configure logging
logger = logging.getLogger(__name__)

# Global model cache to avoid reloading models
_model_cache = {}

# Define embedding model configuration directly
# This avoids circular imports with db_enhanced
embedding_model_name = 'all-MiniLM-L6-v2'
embedding_dimensions = 384  # Dimensions for MiniLM-L6-v2

def load_embedding_model(model_name: Optional[str] = None) -> SentenceTransformer:
    """
    Load a sentence transformer embedding model.
    
    Args:
        model_name: Name of the model to load. If None, will use the default model.
        
    Returns:
        SentenceTransformer: The loaded model
    """
    # Use the default model if none specified
    if model_name is None:
        model_name = embedding_model_name
    
    # Check if model is already loaded
    if model_name in _model_cache:
        return _model_cache[model_name]
    
    try:
        # Try to load model with GPU support if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(model_name, device=device)
        logger.info(f"Loaded embedding model {model_name} on {device}")
        
        # Store in cache
        _model_cache[model_name] = model
        return model
        
    except Exception as e:
        logger.error(f"Error loading embedding model {model_name}: {e}")
        
        # Fall back to CPU if GPU failed
        if "cuda" in str(e).lower() and torch.cuda.is_available():
            logger.warning(f"GPU error, falling back to CPU for model {model_name}")
            try:
                model = SentenceTransformer(model_name, device="cpu")
                _model_cache[model_name] = model
                return model
            except Exception as fallback_error:
                logger.error(f"Error loading fallback CPU model: {fallback_error}")
                
        # Return None or raise error depending on your error handling preference
        raise ValueError(f"Failed to load embedding model {model_name}")

def get_model(model_type: str, model_name: Optional[str] = None) -> Any:
    """
    Get a model by type.
    
    Args:
        model_type: Type of model to load ('embedding', 'summarization', etc.)
        model_name: Specific model name (optional)
        
    Returns:
        The loaded model
    """
    if model_type == 'embedding':
        return load_embedding_model(model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def get_embedding_dimensions(model_name: Optional[str] = None) -> int:
    """
    Get the embedding dimensions for a model.
    
    Args:
        model_name: Name of the model. If None, will use the default model.
        
    Returns:
        int: Dimensions of the model's embeddings
    """
    if model_name is None:
        return embedding_dimensions
    
    # Load the model if needed
    model = load_embedding_model(model_name)
    return model.get_sentence_embedding_dimension() 