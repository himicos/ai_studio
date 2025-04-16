#!/usr/bin/env python3
"""
AI Studio Setup Script

This script sets up the AI Studio environment by:
1. Installing the correct version of dependencies
2. Setting up required directories
3. Creating missing module files
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Basic environment setup - run first
def setup_basic_env():
    """Create basic environment components"""
    print("Setting up basic environment...")
    
    # Create required directories
    dirs = ["memory", "data", "memory/logs"]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    # Create empty __init__.py files in key directories if missing
    init_dirs = [
        "ai_studio_package",
        "ai_studio_package/infra",
        "ai_studio_package/web",
        "ai_studio_package/web/routes"
    ]
    
    for dir_path in init_dirs:
        os.makedirs(dir_path, exist_ok=True)
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                pass  # Create empty file
            print(f"✓ Created __init__.py in {dir_path}")

# Install dependencies with specific versions to avoid conflicts
def install_dependencies():
    """Install correct versions of dependencies"""
    print("\nInstalling dependencies...")
    
    try:
        # First, uninstall problematic packages
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "numpy", "faiss-cpu", "torch", "torchvision"],
            check=False, capture_output=True
        )
        
        # Install compatible NumPy
        print("Installing NumPy 1.24.3...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "numpy==1.24.3"],
            check=True, capture_output=True
        )
        
        # Install PyTorch with compatible dependencies
        print("Installing PyTorch with CUDA support...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "torch==2.0.1", "torchvision==0.15.2", "--index-url", "https://download.pytorch.org/whl/cu118"],
            check=True, capture_output=True
        )
        
        # Install FAISS CPU with specific version
        print("Installing FAISS CPU...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "faiss-cpu==1.7.4"],
            check=True, capture_output=True
        )
        
        # Install other dependencies
        print("Installing other dependencies...")
        dependencies = [
            "fastapi", "uvicorn", "sentence-transformers==2.2.2", 
            "transformers==4.30.2", "scikit-learn", "tqdm"
        ]
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + dependencies,
            check=True, capture_output=True
        )
        
        print("✓ Dependencies installed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print(f"Output: {e.output.decode()}")
        print(f"Error: {e.stderr.decode()}")
        return False
    
    return True

# Create missing module files
def create_missing_modules():
    """Create any missing Python modules required for operation"""
    print("\nChecking for missing modules...")
    
    # Create ai_studio_package/infra/db.py if missing
    db_path = "ai_studio_package/infra/db.py"
    if not os.path.exists(db_path):
        print(f"Creating {db_path}...")
        with open(db_path, "w") as f:
            f.write("""\"\"\"
Basic Database Module for AI Studio

This module provides essential database operations and connections.
It contains simplified versions of functions from db_enhanced.py to avoid circular imports.
\"\"\"

import os
import sqlite3
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Database paths
DB_PATH = os.path.join("memory", "memory.sqlite")

def get_db_connection():
    \"\"\"
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    \"\"\"
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Increase timeout to wait longer for locks
    conn = sqlite3.connect(DB_PATH, timeout=10.0) 
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    
    # Enable Write-Ahead Logging for better concurrency
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        logger.debug("SQLite journal_mode set to WAL.")
    except Exception as e:
        logger.warning(f"Could not set journal_mode to WAL: {e}")
    
    return conn

def init_db():
    \"\"\"
    Initialize the database with the basic required tables.
    This is a simplified version - full initialization is in db_enhanced.py
    \"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create memory_nodes table (minimal version, full version in db_enhanced)
    cursor.execute(\'\'\'
    CREATE TABLE IF NOT EXISTS memory_nodes (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT,
        created_at INTEGER NOT NULL,
        metadata TEXT,
        has_embedding INTEGER DEFAULT 0,
        updated_at INTEGER
    )
    \'\'\')
    
    # Commit and close
    conn.commit()
    conn.close()
    
    logger.info(f"Basic database initialized at {DB_PATH}")
""")
        print(f"✓ Created {db_path}")
    
    # Create ai_studio_package/infra/models.py if missing
    models_path = "ai_studio_package/infra/models.py"
    if not os.path.exists(models_path):
        print(f"Creating {models_path}...")
        with open(models_path, "w") as f:
            f.write("""\"\"\"
Model Loading Utilities for AI Studio

This module provides functions for loading, initializing, and using various ML models,
particularly for embedding generation and vector operations.
\"\"\"

import logging
import os
import torch
from typing import Optional, Dict, Any, Union
from sentence_transformers import SentenceTransformer

# Configure logging
logger = logging.getLogger(__name__)

# Global model cache to avoid reloading models
_model_cache = {}

def load_embedding_model(model_name: Optional[str] = None) -> SentenceTransformer:
    \"\"\"
    Load a sentence transformer embedding model.
    
    Args:
        model_name: Name of the model to load. If None, will use the default model.
        
    Returns:
        SentenceTransformer: The loaded model
    \"\"\"
    # Use the default model if none specified
    if model_name is None:
        from ai_studio_package.infra.db_enhanced import embedding_model_name
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
    \"\"\"
    Get a model by type.
    
    Args:
        model_type: Type of model to load ('embedding', 'summarization', etc.)
        model_name: Specific model name (optional)
        
    Returns:
        The loaded model
    \"\"\"
    if model_type == 'embedding':
        return load_embedding_model(model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def get_embedding_dimensions(model_name: Optional[str] = None) -> int:
    \"\"\"
    Get the embedding dimensions for a model.
    
    Args:
        model_name: Name of the model. If None, will use the default model.
        
    Returns:
        int: Dimensions of the model's embeddings
    \"\"\"
    if model_name is None:
        from ai_studio_package.infra.db_enhanced import embedding_dimensions
        return embedding_dimensions
    
    # Load the model if needed
    model = load_embedding_model(model_name)
    return model.get_sentence_embedding_dimension()
""")
        print(f"✓ Created {models_path}")
    
    print("Module creation complete")

def main():
    print("="*60)
    print("AI Studio Setup")
    print("="*60)
    
    # Set up basic environment
    setup_basic_env()
    
    # Create missing module files
    create_missing_modules()
    
    # Install dependencies
    if install_dependencies():
        print("\nSetup completed successfully.")
        print("You can now run 'python main.py' to start the application.")
    else:
        print("\nSetup encountered some issues with dependency installation.")
        print("Please review the errors above and try again.")
    
    print("="*60)

if __name__ == "__main__":
    main() 