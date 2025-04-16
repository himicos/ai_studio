#!/usr/bin/env python3
"""
Fix Environment Script

This script fixes common environment issues, such as:
1. Downgrading NumPy to <2.0 to resolve compatibility with PyTorch
2. Checking for missing dependencies and modules
3. Initializing required directories
"""

import os
import sys
import subprocess
import logging
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_environment")

def check_module_exists(module_name):
    """Check if a Python module exists"""
    return importlib.util.find_spec(module_name) is not None

def run_command(cmd, cwd=None):
    """Run a shell command and log its output"""
    logger.info(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            text=True, 
            capture_output=True,
            cwd=cwd
        )
        logger.info(f"Command output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def fix_numpy_version():
    """Fix NumPy version to be compatible with PyTorch"""
    logger.info("Checking NumPy version...")
    
    try:
        import numpy as np
        numpy_version = np.__version__
        logger.info(f"Current NumPy version: {numpy_version}")
        
        if numpy_version.startswith("2."):
            logger.warning("NumPy 2.x detected, which may cause issues with PyTorch")
            logger.info("Downgrading NumPy to version 1.24.3...")
            
            run_command("pip install numpy==1.24.3 --force-reinstall")
            logger.info("NumPy downgraded successfully. Please restart your application.")
            return True
    except ImportError:
        logger.error("NumPy not installed")
        run_command("pip install numpy==1.24.3")
        return True
    
    return False

def ensure_directories():
    """Ensure all required directories exist"""
    required_dirs = [
        "memory",
        "data",
        "memory/logs"
    ]
    
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")

def check_faiss():
    """Check if FAISS is installed correctly"""
    try:
        import faiss
        logger.info(f"FAISS version: {faiss.__version__}")
        
        # Check if GPU support is available
        if not hasattr(faiss, "GpuIndexFlatL2"):
            logger.warning("FAISS GPU support not available - using CPU version")
        else:
            logger.info("FAISS GPU support is available")
            
        return True
    except ImportError:
        logger.error("FAISS not installed")
        logger.info("Installing FAISS...")
        
        run_command("pip install faiss-cpu")
        return False

def check_missing_files():
    """Check for crucial missing files and create them"""
    required_files = [
        ("ai_studio_package/infra/db.py", "Basic database connection module"),
        ("ai_studio_package/infra/models.py", "Model loading utilities")
    ]
    
    for file_path, description in required_files:
        if not os.path.exists(file_path):
            logger.warning(f"Missing file: {file_path} ({description})")

def main():
    logger.info("Starting environment fix script...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Check and fix NumPy version
    numpy_fixed = fix_numpy_version()
    
    # Check for missing files
    check_missing_files()
    
    # Check FAISS installation
    faiss_ok = check_faiss()
    
    if numpy_fixed:
        logger.info("NumPy was downgraded. Please restart your application.")
        sys.exit(0)
    
    logger.info("Environment fix script completed.")
    logger.info("You can now run 'python main.py' to start the application.")

if __name__ == "__main__":
    main() 