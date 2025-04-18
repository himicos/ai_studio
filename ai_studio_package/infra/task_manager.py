"""
Task Manager Module

This module provides functionality for managing background tasks, particularly
embedding generation tasks.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
from queue import Queue, Empty
from threading import Thread, Event
import json
import threading

from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss
from ai_studio_package.infra.db_enhanced import get_db_connection, create_memory_node

logger = logging.getLogger(__name__)

# Global task queue
_task_queue = Queue()
_stop_event = Event()
_worker_thread: Optional[Thread] = None
_is_running = False

class EmbeddingTask:
    """Represents a task to generate embeddings for a node"""
    def __init__(self, node_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.text = text
        self.metadata = metadata or {}
        self.created_at = int(time.time() * 1000)
        self.attempts = 0
        self.max_attempts = 3
        self.last_error: Optional[str] = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "text": self.text,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "attempts": self.attempts,
            "last_error": self.last_error
        }

def _process_task(task: EmbeddingTask) -> bool:
    """Process a single embedding task"""
    try:
        task.attempts += 1
        logger.info(f"Processing embedding task for node {task.node_id} (attempt {task.attempts})")
        
        # Generate embedding
        success = generate_embedding_for_node_faiss(task.node_id, task.text)
        
        if success:
            logger.info(f"Successfully generated embedding for node {task.node_id}")
            
            # Log successful completion
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_logs (
                    task_id, task_type, status, created_at, completed_at, 
                    attempts, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task.node_id, 
                "embedding_generation",
                "success",
                task.created_at,
                int(time.time() * 1000),
                task.attempts,
                json.dumps(task.to_dict())
            ))
            conn.commit()
            return True
            
        task.last_error = "Failed to generate embedding"
        return False
        
    except Exception as e:
        task.last_error = str(e)
        logger.error(f"Error processing embedding task for node {task.node_id}: {e}")
        traceback.print_exc()
        return False

def _worker_loop():
    """Background worker loop for processing embedding tasks."""
    global _is_running
    
    logger.info("Starting embedding task worker loop")
    
    while _is_running:
        try:
            # Get task with timeout
            task = _task_queue.get(timeout=1.0)
            
            try:
                # Extract task data
                node_id = task.get('node_id')
                text = task.get('text')
                metadata = task.get('metadata', {})
                
                # Validate task data
                if not node_id:
                    logger.error("Task missing node_id")
                    continue
                if not text:
                    logger.error(f"Task for node {node_id} missing text content")
                    continue
                
                # Log task processing
                logger.info(f"Processing embedding task for node {node_id}")
                logger.debug(f"Text length: {len(text)}, metadata: {metadata}")
                
                # Import here to avoid circular imports
                from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss
                
                # Generate embedding
                success = generate_embedding_for_node_faiss(node_id, text)
                
                if success:
                    logger.info(f"Successfully generated embedding for node {node_id}")
                else:
                    logger.error(f"Failed to generate embedding for node {node_id}")
                    
            except Exception as e:
                logger.error(f"Error processing task for node {node_id if 'node_id' in locals() else 'unknown'}: {str(e)}")
                logger.debug("Full error details:", exc_info=True)
                
            finally:
                _task_queue.task_done()
                
        except Empty:
            # No tasks available, continue waiting
            continue
            
        except Exception as e:
            logger.error(f"Critical error in worker loop: {str(e)}")
            logger.debug("Full error details:", exc_info=True)
            time.sleep(1)  # Prevent tight loop on repeated errors

def init_task_manager():
    """Initialize the task manager and start the worker thread."""
    global _worker_thread, _is_running
    
    if _worker_thread and _worker_thread.is_alive():
        logger.info("Task manager worker thread already running")
        return
        
    _is_running = True
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
    _worker_thread.start()
    logger.info("Started embedding task worker thread")

def shutdown_task_manager():
    """Shutdown the task manager and stop the worker thread."""
    global _is_running, _worker_thread
    
    _is_running = False
    if _worker_thread:
        _worker_thread.join(timeout=5.0)
        _worker_thread = None
    logger.info("Embedding task worker thread stopped")

def create_embedding_task(node_id: str, text: str, metadata: dict = None) -> bool:
    """
    Create and queue a task to generate embeddings for a node.
    
    Args:
        node_id (str): Unique identifier for the node
        text (str): Text content to generate embeddings for
        metadata (dict, optional): Additional metadata for the task
        
    Returns:
        bool: True if task was successfully queued, False otherwise
    """
    try:
        if not _is_running:
            logger.error("Task manager is not running. Cannot create embedding task.")
            return False
            
        if not node_id:
            logger.error("Node ID is required for embedding task")
            return False
            
        if not text or not isinstance(text, str):
            logger.error(f"Invalid text content for node {node_id}")
            return False

        task = {
            'node_id': node_id,
            'text': text,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Creating embedding task for node {node_id} with {len(text)} chars")
        _task_queue.put(task)
        return True
        
    except Exception as e:
        logger.error(f"Failed to create embedding task for node {node_id}: {str(e)}")
        return False

# Initialize task manager on module import
init_task_manager() 