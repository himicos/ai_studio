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
from ai_studio_package.infra.db_enhanced import create_memory_node, get_memory_node
from ai_studio_package.infra.vector_adapter import generate_embedding_for_node_faiss
from ai_studio_package.infra.execution_logs import get_execution_logs, get_execution_stats
from ai_studio_package.infra.db import get_db_connection

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
    Analyze execution logs for a specific task or all tasks
    
    Args:
        task: Optional task name to filter logs
        limit: Maximum number of logs to analyze
        days: Number of days to look back
        min_entries: Minimum number of entries required for analysis
        
    Returns:
        Dict with analysis results
    """
    logger.info(f"Analyzing execution logs for {'task: ' + task if task else 'all tasks'}")
    
    # Calculate start date
    start_date = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    # Get execution logs
    logs = get_execution_logs(
        task=task,
        limit=limit,
        start_date=start_date
    )
    
    # Check if we have enough logs
    if len(logs) < min_entries:
        logger.info(f"Not enough logs for analysis. Found {len(logs)}, need at least {min_entries}")
        return {
            "status": "insufficient_data",
            "message": f"Need at least {min_entries} logs for meaningful analysis",
            "logs_found": len(logs)
        }
    
    # Get statistics
    stats = get_execution_stats(task=task, start_date=start_date)
    
    # Extract key metrics
    success_rate = (stats["success_count"] / stats["total_count"]) * 100 if stats["total_count"] > 0 else 0
    avg_latency = stats["avg_latency"]
    
    # Identify slow executions (>2x average)
    slow_executions = [log for log in logs if log.get("latency", 0) > (avg_latency * 2)]
    
    # Identify error patterns
    error_logs = [log for log in logs if log.get("status") == "error"]
    error_types = {}
    
    for log in error_logs:
        error_msg = log.get("error", "Unknown error")
        # Extract just the error type, not the whole message
        error_type = error_msg.split(":", 1)[0] if ":" in error_msg else error_msg
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    # Sort error types by frequency
    error_patterns = [
        {"type": error_type, "count": count}
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Prepare sample logs for analysis
    # Include some successful logs and some error logs for a balanced view
    sample_success = [log for log in logs if log.get("status") == "success"][:3]
    sample_errors = error_logs[:3]
    sample_logs = sample_success + sample_errors
    
    # Format samples for analysis
    formatted_samples = []
    for i, log in enumerate(sample_logs):
        formatted_samples.append(
            f"Log {i+1} [status: {log.get('status', 'unknown')}]:\n"
            f"  Task: {log.get('task', 'unknown')}\n"
            f"  Latency: {log.get('latency', 0):.2f}s\n"
            f"  Error: {log.get('error', 'None')}\n"
            f"  Metadata: {json.dumps(log.get('metadata', {}), indent=2)}"
        )
    
    # Combine samples for analysis
    analysis_text = (
        f"Task Analysis: {task or 'All Tasks'}\n"
        f"Period: Last {days} days\n"
        f"Sample Logs:\n" + "\n\n".join(formatted_samples) + "\n\n"
        f"Statistics:\n"
        f"  Total Executions: {stats['total_count']}\n"
        f"  Success Rate: {success_rate:.1f}%\n"
        f"  Average Latency: {avg_latency:.2f}s\n"
        f"  Error Patterns: {json.dumps(error_patterns, indent=2)}\n"
    )
    
    # Generate analysis (in a real implementation, this would use an LLM)
    analysis = generate_critique(analysis_text, task)
    
    return {
        "status": "success",
        "statistics": stats,
        "success_rate": success_rate,
        "avg_latency": avg_latency,
        "error_patterns": error_patterns,
        "slow_executions_count": len(slow_executions),
        "analysis": analysis
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
        "tags": json.dumps(["critique", "self_improvement", task_label]),
        "created_at": created_at,
        "updated_at": created_at,
        "source_type": "critic_agent",
        "metadata": json.dumps({
            "task_name": task_name,
            "success_rate": analysis_result["success_rate"],
            "avg_latency": analysis_result["avg_latency"],
            "error_patterns": analysis_result["error_patterns"],
            "generated_by": "critic_agent",
            "analysis_timestamp": datetime.now().isoformat()
        })
    }
    
    try:
        # Create the memory node
        create_memory_node(node_data)
        logger.info(f"Created critique node with ID: {node_id}")
        
        # Generate embedding for the node
        content = node_data["content"]
        generate_embedding_for_node_faiss(node_id, content, None)  # None will cause it to generate the embedding
        logger.info(f"Generated embedding for critique node: {node_id}")
        
        return node_id
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
        logger.error(f"Error running critic agent: {e}", exc_info=True)
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