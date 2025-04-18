"""
Critic Agent for Self-Improvement Loop

This agent analyzes execution logs to identify patterns, bottlenecks,
and potential improvement areas, then generates critique nodes.
"""

import os
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import database and API functions
from ai_studio_package.infra.db_enhanced import create_memory_node, get_memory_node, get_db_connection
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss, create_node_with_embedding
from ai_studio_package.infra.execution_logs import get_execution_logs, get_execution_stats

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Helper function to get a model for summarizing (replace with your actual model)
def get_summarization_model():
    """Get a summarization model for text generation"""
    # In a real implementation, you would load your model here
    # from transformers import pipeline
    # return pipeline("summarization")
    
    # For now, we'll just use a mock function
    class MockModel:
        def generate(self, text, max_length=150):
            return f"Mock analysis: This is a placeholder for a real analysis of '{text[:30]}...'"
    
    return MockModel()

def analyze_execution_logs(
    task: Optional[str] = None,
    limit: int = 50,
    days: int = 1,
    min_entries: int = 5
) -> Dict[str, Any]:
    """
    Analyze execution logs to identify patterns and issues
    
    Args:
        task: Optional task name to filter logs
        limit: Maximum number of logs to analyze
        days: Number of days to look back
        min_entries: Minimum number of entries required for analysis
        
    Returns:
        Dict with analysis results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate time threshold
        time_threshold = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Build query
        query = """
        SELECT * FROM execution_logs 
        WHERE start_time >= ? 
        """
        params = [time_threshold]
        
        if task:
            query += " AND task = ?"
            params.append(task)
            
        query += f" ORDER BY start_time DESC LIMIT {limit}"
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if len(rows) < min_entries:
            return {
                "status": "insufficient_data",
                "message": f"Not enough data points ({len(rows)} < {min_entries})"
            }
            
        # Calculate metrics
        total_count = len(rows)
        success_count = sum(1 for row in rows if row['status'] == 'success')
        error_count = total_count - success_count
        success_rate = success_count / total_count
        
        # Calculate latency stats
        latencies = [row['latency'] for row in rows]
        avg_latency = sum(latencies) / len(latencies)
        
        # Analyze error patterns
        error_patterns = {}
        for row in rows:
            if row['status'] == 'error' and row['error']:
                error_type = row['error'].split(':')[0]
                error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
                
        # Generate analysis text
        analysis = f"""Performance Analysis for {task if task else 'all tasks'}:

Success Rate: {success_rate:.2%} ({success_count}/{total_count} successful)
Average Latency: {avg_latency:.2f} seconds

Error Distribution:
{json.dumps(error_patterns, indent=2)}

Recommendations:
"""

        # Add recommendations based on patterns
        if success_rate < 0.9:
            analysis += "- High error rate detected. Review error patterns and implement better error handling.\n"
            
        if avg_latency > 5.0:
            analysis += "- High average latency. Consider optimization or caching strategies.\n"
            
        for error_type, count in error_patterns.items():
            if count > total_count * 0.1:  # Error occurs in >10% of cases
                analysis += f"- Frequent {error_type} errors. Implement specific handling for this case.\n"
                
        return {
            "status": "success",
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "error_patterns": error_patterns,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing execution logs: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def generate_critique(analysis_text: str, task_name: Optional[str] = None) -> str:
    """
    Generate a critique based on the analysis text
    
    In a real implementation, this would use an LLM to generate
    thoughtful insights and suggestions
    
    Args:
        analysis_text: Text containing execution data for analysis
        task_name: Name of the task being analyzed
        
    Returns:
        str: Generated critique text
    """
    # In a real implementation, this would use an LLM
    # model = get_summarization_model()
    # return model.generate(analysis_text)
    
    # For now, return a mock critique
    task_str = f"task '{task_name}'" if task_name else "tasks"
    
    return (
        f"## Critique for {task_str}\n\n"
        f"### Observations\n"
        f"- This is a placeholder critique that would normally be generated by an LLM\n"
        f"- In a real implementation, we would analyze the patterns in the execution logs\n"
        f"- The analysis would identify common error patterns and performance bottlenecks\n\n"
        f"### Suggestions\n"
        f"1. Implement proper error handling for common failure patterns\n"
        f"2. Consider optimizing slow operations\n"
        f"3. Add more detailed logging to diagnose specific issues\n\n"
        f"### Code-Level Recommendations\n"
        f"- Add try/except blocks around external API calls\n"
        f"- Consider adding caching for frequently accessed data\n"
        f"- Review database query patterns for optimization opportunities"
    )

def create_critique_node(analysis_result: Dict[str, Any], task_name: Optional[str] = None) -> Optional[str]:
    """
    Create a memory node to store the critique
    
    Args:
        analysis_result: Result from analyze_execution_logs
        task_name: Name of the task being analyzed
        
    Returns:
        Optional[str]: ID of the created node, or None if failed
    """
    if analysis_result["status"] != "success":
        logger.info(f"Not creating critique node: {analysis_result['message']}")
        return None
    
    # Prepare node data
    node_id = str(uuid.uuid4())
    created_at = int(time.time() * 1000)
    
    task_label = task_name if task_name else "all_tasks"
    
    node_data = {
        "id": node_id,
        "type": "critique",
        "content": analysis_result["analysis"],
        "tags": ["critique", "self_improvement", task_label],
        "created_at": created_at,
        "updated_at": created_at,
        "source_type": "critic_agent",
        "metadata": {
            "task_name": task_name,
            "success_rate": analysis_result["success_rate"],
            "avg_latency": analysis_result["avg_latency"],
            "error_patterns": analysis_result["error_patterns"],
            "generated_by": "critic_agent",
            "analysis_timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        # Create the memory node with async embedding generation
        node_id = create_node_with_embedding(node_data, async_embedding=True)
        if node_id:
            logger.info(f"Created critique node with ID: {node_id}")
            return node_id
        return None
        
    except Exception as e:
        logger.error(f"Error creating critique node: {e}", exc_info=True)
        return None

def run_critic(
    task: Optional[str] = None,
    limit: int = 50,
    days: int = 1,
    min_entries: int = 5
) -> Dict[str, Any]:
    """
    Main function to run the critic agent
    
    Args:
        task: Optional task name to filter logs
        limit: Maximum number of logs to analyze
        days: Number of days to look back
        min_entries: Minimum number of entries required for analysis
        
    Returns:
        Dict with results
    """
    logger.info(f"Running critic agent for {'task: ' + task if task else 'all tasks'}")
    
    try:
        # Analyze execution logs
        analysis_result = analyze_execution_logs(
            task=task,
            limit=limit,
            days=days,
            min_entries=min_entries
        )
        
        # If we have a successful analysis, create a critique node
        node_id = None
        if analysis_result["status"] == "success":
            node_id = create_critique_node(analysis_result, task)
        
        return {
            "status": "success" if node_id else "no_action",
            "analysis": analysis_result,
            "node_id": node_id
        }
    except Exception as e:
        logger.error(f"Error running critic agent: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Critic Agent to analyze execution logs")
    parser.add_argument("--task", help="Filter by specific task name")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of logs to analyze")
    parser.add_argument("--days", type=int, default=1, help="Number of days to look back")
    parser.add_argument("--min-entries", type=int, default=5, help="Minimum entries needed for analysis")
    
    args = parser.parse_args()
    
    result = run_critic(
        task=args.task,
        limit=args.limit,
        days=args.days,
        min_entries=args.min_entries
    )
    
    print(json.dumps(result, indent=2)) 