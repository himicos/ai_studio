"""
Execution logging module for the Self-Improvement Loop (SIL)

This module provides functionality to track and record execution metrics for various tasks,
allowing the system to learn from its own operations and improve over time.
"""

import time
import json
import sqlite3
import uuid
import logging
import functools
import traceback
from typing import Dict, Any, Optional, Callable, List, TypeVar, cast
from datetime import datetime

# Import database functions
from ai_studio_package.infra.db import get_db_connection, DB_PATH

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for decorator
F = TypeVar('F', bound=Callable[..., Any])

def init_execution_logs_table():
    """
    Initialize the execution_logs table in the database.
    This should be called during application startup.
    """
    logger.info("Initializing execution_logs table...")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create execution_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_logs (
            id TEXT PRIMARY KEY,
            task TEXT NOT NULL,           -- Name of the task/function/endpoint
            status TEXT NOT NULL,          -- success, error, timeout
            start_time INTEGER NOT NULL,   -- Unix timestamp (ms)
            end_time INTEGER NOT NULL,     -- Unix timestamp (ms)
            latency REAL NOT NULL,         -- Execution time in seconds
            cost REAL,                     -- Estimated cost (e.g. token cost)
            token_count INTEGER,           -- Number of tokens processed
            quality REAL,                  -- Quality score (0-1)
            error TEXT,                    -- Error message if status is 'error'
            trace JSON,                    -- JSON record of memory nodes accessed
            metadata JSON,                 -- Additional context data
            created_at INTEGER NOT NULL    -- Record creation time
        )
        ''')
        
        # Create index for faster lookups by task
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_execution_logs_task 
        ON execution_logs(task)
        ''')
        
        # Create index for faster lookups by status
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_execution_logs_status 
        ON execution_logs(status)
        ''')
        
        conn.commit()
        logger.info("Execution logs table initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing execution_logs table: {e}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def log_execution(
    task: str,
    status: str,
    start_time: int,
    end_time: int,
    latency: float,
    cost: Optional[float] = None,
    token_count: Optional[int] = None,
    quality: Optional[float] = None,
    error: Optional[str] = None,
    trace: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Log an execution record to the database.
    
    Args:
        task: Name of the task/function/endpoint
        status: Status of execution (success, error, timeout)
        start_time: Start time as Unix timestamp (ms)
        end_time: End time as Unix timestamp (ms)
        latency: Execution time in seconds
        cost: Estimated cost (e.g. token cost)
        token_count: Number of tokens processed
        quality: Quality score (0-1)
        error: Error message if status is 'error'
        trace: JSON record of memory nodes accessed
        metadata: Additional context data
        
    Returns:
        Optional[str]: The ID of the created log entry, or None if failed
    """
    log_id = str(uuid.uuid4())
    created_at = int(time.time() * 1000)
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO execution_logs (
            id, task, status, start_time, end_time, latency, 
            cost, token_count, quality, error, trace, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id, task, status, start_time, end_time, latency,
            cost, token_count, quality, error,
            json.dumps(trace) if trace else None,
            json.dumps(metadata) if metadata else None,
            created_at
        ))
        
        conn.commit()
        logger.debug(f"Execution log created with ID: {log_id}")
        return log_id
        
    except Exception as e:
        logger.error(f"Error logging execution: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def track_execution(task_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator to track execution of a function and log metrics.
    
    Args:
        task_name: Optional custom name for the task. If not provided, the function name is used.
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Record start time
            start_time = int(time.time() * 1000)
            
            # Initialize metrics
            status = "success"
            error_msg = None
            result = None
            trace_data = {}
            
            # Track trace data if available in kwargs
            if 'trace_context' in kwargs:
                trace_data = kwargs.pop('trace_context')
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Get quality score if result has it
                quality_score = None
                if hasattr(result, 'quality_score'):
                    quality_score = getattr(result, 'quality_score')
                elif isinstance(result, dict) and 'quality_score' in result:
                    quality_score = result['quality_score']
                
                # Get token count if result has it
                token_count = None
                if hasattr(result, 'token_count'):
                    token_count = getattr(result, 'token_count')
                elif isinstance(result, dict) and 'token_count' in result:
                    token_count = result['token_count']
                
                # Calculate cost if we have token count
                cost = None
                if token_count:
                    # Simple cost estimate based on standard GPT rates
                    # This should be replaced with actual cost calculation
                    cost = token_count * 0.0001  # $0.0001 per token is a placeholder
                
                return result
                
            except Exception as e:
                status = "error"
                error_msg = str(e)
                logger.error(f"Error in tracked function {func.__name__}: {e}", exc_info=True)
                # Re-raise the exception
                raise
                
            finally:
                # Record end time
                end_time = int(time.time() * 1000)
                latency = (end_time - start_time) / 1000  # Convert to seconds
                
                # Prepare metadata
                metadata = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Get actual task name
                actual_task_name = task_name or func.__name__
                
                # Log execution
                log_execution(
                    task=actual_task_name,
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                    latency=latency,
                    error=error_msg,
                    trace=trace_data,
                    metadata=metadata
                )
        
        return cast(F, wrapper)
    
    return decorator

def get_execution_logs(
    task: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve execution logs from the database with optional filtering.
    
    Args:
        task: Filter by task name
        status: Filter by status
        limit: Maximum number of logs to return
        offset: Offset for pagination
        start_date: Start date as Unix timestamp (ms)
        end_date: End date as Unix timestamp (ms)
        
    Returns:
        List[Dict[str, Any]]: List of execution log records
    """
    conn = None
    logs = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query conditionally
        query = "SELECT * FROM execution_logs WHERE 1=1"
        params = []
        
        if task:
            query += " AND task = ?"
            params.append(task)
            
        if status:
            query += " AND status = ?"
            params.append(status)
            
        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND end_time <= ?"
            params.append(end_date)
            
        query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for row in rows:
            log = dict(row)
            
            # Parse JSON fields
            if log.get('trace'):
                try:
                    log['trace'] = json.loads(log['trace'])
                except:
                    log['trace'] = {}
                    
            if log.get('metadata'):
                try:
                    log['metadata'] = json.loads(log['metadata'])
                except:
                    log['metadata'] = {}
                    
            logs.append(log)
            
        return logs
        
    except Exception as e:
        logger.error(f"Error retrieving execution logs: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()

def get_execution_stats(
    task: Optional[str] = None,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get statistics on execution logs.
    
    Args:
        task: Filter by task name
        start_date: Start date as Unix timestamp (ms)
        end_date: End date as Unix timestamp (ms)
        
    Returns:
        Dict[str, Any]: Statistics including counts, average latency, etc.
    """
    conn = None
    stats = {
        "total_count": 0,
        "success_count": 0,
        "error_count": 0,
        "avg_latency": 0,
        "total_cost": 0,
        "avg_quality": 0
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query conditionally
        query_base = "FROM execution_logs WHERE 1=1"
        params = []
        
        if task:
            query_base += " AND task = ?"
            params.append(task)
            
        if start_date:
            query_base += " AND start_time >= ?"
            params.append(start_date)
            
        if end_date:
            query_base += " AND end_time <= ?"
            params.append(end_date)
        
        # Total count
        cursor.execute(f"SELECT COUNT(*) {query_base}", params)
        stats["total_count"] = cursor.fetchone()[0]
        
        # Success count
        cursor.execute(f"SELECT COUNT(*) {query_base} AND status = 'success'", params)
        stats["success_count"] = cursor.fetchone()[0]
        
        # Error count
        cursor.execute(f"SELECT COUNT(*) {query_base} AND status = 'error'", params)
        stats["error_count"] = cursor.fetchone()[0]
        
        # Average latency
        cursor.execute(f"SELECT AVG(latency) {query_base}", params)
        avg_latency = cursor.fetchone()[0]
        stats["avg_latency"] = avg_latency if avg_latency else 0
        
        # Total cost
        cursor.execute(f"SELECT SUM(cost) {query_base}", params)
        total_cost = cursor.fetchone()[0]
        stats["total_cost"] = total_cost if total_cost else 0
        
        # Average quality
        cursor.execute(f"SELECT AVG(quality) {query_base} AND quality IS NOT NULL", params)
        avg_quality = cursor.fetchone()[0]
        stats["avg_quality"] = avg_quality if avg_quality else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving execution stats: {e}", exc_info=True)
        return stats
    finally:
        if conn:
            conn.close()

# Initialize the execution_logs table if this module is imported
# This is commented out to prevent automatic initialization when imported
# init_execution_logs_table() 