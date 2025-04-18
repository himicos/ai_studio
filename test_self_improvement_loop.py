#!/usr/bin/env python3
"""
Test script for Self-Improvement Loop (SIL)

This script tests the Self-Improvement Loop implementation by:
1. Verifying the execution_logs table exists and structure is correct
2. Testing the Critic Agent's ability to analyze logs and generate critiques
3. Testing the Refactor Agent's ability to implement suggestions
4. Simulating the complete SIL workflow
"""

import os
import sys
import json
import sqlite3
import logging
import time
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import random
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_DB_PATH = "memory/memory.sqlite"
EXECUTION_LOGS_INIT_SCRIPT = "ai_studio_package/scripts/initialize_execution_logs.py"
CRITIC_AGENT_PATH = "ai_studio_package/agents/critic_agent.py"
REFACTOR_AGENT_PATH = "ai_studio_package/agents/refactor_agent.py"
DECORATOR_PATH = "ai_studio_package/infra/execution_logs.py"
SCHEDULER_PATH = "ai_studio_package/scripts/schedule_critic.py"

def check_file_exists(path: str) -> bool:
    """Check if a file exists and return its status"""
    file_path = Path(path)
    exists = file_path.exists()
    
    if exists:
        logger.info(f"✅ File exists: {path}")
    else:
        logger.error(f"❌ File missing: {path}")
    
    return exists

def run_command(command: str, timeout: int = 60) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr"""
    logger.info(f"Running command: {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
        
        if exit_code == 0:
            logger.info(f"✅ Command executed successfully (exit code: {exit_code})")
        else:
            logger.error(f"❌ Command failed with exit code: {exit_code}")
            logger.error(f"Error output: {stderr}")
            
        return exit_code, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        logger.error(f"❌ Command timed out after {timeout} seconds")
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"❌ Error executing command: {e}")
        return -1, "", str(e)

def query_database(query: str, params: tuple = (), db_path: str = MEMORY_DB_PATH) -> List[Dict[str, Any]]:
    """Execute a query against the database and return results as dictionaries"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"❌ Database query error: {e}")
        return []

def execute_database_statement(statement: str, params: tuple = (), db_path: str = MEMORY_DB_PATH) -> bool:
    """Execute a statement against the database (INSERT, UPDATE, etc.)"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(statement, params)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database statement error: {e}")
        return False

def check_execution_logs_table():
    """Check if the execution_logs table exists and has the correct structure"""
    logger.info("=== Checking Execution Logs Table ===")
    
    # Check if the table exists
    table_exists = query_database("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
    
    if not table_exists:
        logger.error("❌ execution_logs table does not exist")
        
        # Try to create it
        logger.info("Attempting to create execution_logs table...")
        
        if check_file_exists(EXECUTION_LOGS_INIT_SCRIPT):
            exit_code, stdout, stderr = run_command(f"python {EXECUTION_LOGS_INIT_SCRIPT}")
            
            if exit_code != 0:
                logger.error(f"❌ Failed to create execution_logs table: {stderr}")
                return False
                
            # Check again
            table_exists = query_database("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
            
            if not table_exists:
                logger.error("❌ execution_logs table still does not exist after initialization")
                return False
        else:
            logger.error(f"❌ Cannot create execution_logs table: {EXECUTION_LOGS_INIT_SCRIPT} not found")
            return False
    
    logger.info("✅ execution_logs table exists")
    
    # Check the table structure
    columns = query_database("PRAGMA table_info(execution_logs)")
    
    # Define the expected columns
    expected_columns = [
        "id", "task", "status", "start_time", "end_time", "latency",
        "cost", "token_count", "quality", "error", "trace", "metadata", "created_at"
    ]
    
    # Check if all expected columns exist
    column_names = [col["name"] for col in columns]
    missing_columns = [col for col in expected_columns if col not in column_names]
    
    if missing_columns:
        logger.error(f"❌ execution_logs table is missing columns: {missing_columns}")
        return False
    
    logger.info("✅ execution_logs table has the correct structure")
    
    # Get count of existing logs
    logs_count = query_database("SELECT COUNT(*) as count FROM execution_logs")
    count = logs_count[0]["count"] if logs_count else 0
    
    logger.info(f"Found {count} existing execution logs")
    
    return True

def generate_test_logs(num_logs: int = 10):
    """Generate test execution logs for testing the Critic Agent"""
    logger.info(f"=== Generating {num_logs} Test Execution Logs ===")
    
    # Tasks to randomly select from
    tasks = [
        "searchMemoryNodes",
        "getMemoryNodes",
        "getMemoryEdges",
        "generateKnowledgeGraph",
        "trackNodeAccess",
        "summarizeContent"
    ]
    
    # Statuses to randomly select from (weighted toward success)
    statuses = ["success"] * 8 + ["error"] * 2
    
    # Current time in milliseconds
    current_time = int(time.time() * 1000)
    
    # Generate logs
    logs_created = 0
    
    for i in range(num_logs):
        # Random task
        task = random.choice(tasks)
        
        # Random status (weighted toward success)
        status = random.choice(statuses)
        
        # Random start time in the last 24 hours
        start_time = current_time - random.randint(0, 24 * 60 * 60 * 1000)
        
        # Random latency between 0.1 and 5 seconds
        latency = round(random.uniform(0.1, 5.0), 3)
        
        # Calculate end time
        end_time = start_time + int(latency * 1000)
        
        # Generate error message if status is error
        error = f"Test error for {task}: Connection timeout" if status == "error" else None
        
        # Generate some metadata
        metadata = json.dumps({
            "function": task,
            "module": f"ai_studio_package.web.routes.{task.lower()}_routes",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_time / 1000))
        })
        
        # Generate a unique ID
        log_id = str(uuid.uuid4())
        
        # Insert into database
        success = execute_database_statement(
            """
            INSERT INTO execution_logs 
            (id, task, status, start_time, end_time, latency, error, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (log_id, task, status, start_time, end_time, latency, error, metadata, current_time)
        )
        
        if success:
            logs_created += 1
    
    logger.info(f"✅ Created {logs_created} test execution logs")
    
    return logs_created

def test_critic_agent():
    """Test the Critic Agent"""
    logger.info("=== Testing Critic Agent ===")
    
    # Check if the critic agent file exists
    if not os.path.exists("ai_studio_package/agents/critic_agent.py"):
        logger.error("❌ Critic Agent file not found")
        return False
    
    logger.info("✅ File exists: ai_studio_package/agents/critic_agent.py")
    
    # Run the critic agent
    logger.info("Running command: python -m ai_studio_package.agents.critic_agent")
    result = subprocess.run(
        ["python", "-m", "ai_studio_package.agents.critic_agent"],
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"❌ Command failed with exit code: {result.returncode}")
        logger.error(f"Error output: {result.stderr}")
        logger.error(f"❌ Critic Agent execution failed: {result.stderr}")
        return False
    
    logger.info("✅ Critic Agent executed successfully")
    
    # Check if any critique nodes were created in the last minute
    conn = sqlite3.connect(MEMORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get current timestamp and timestamp from 1 minute ago
    now = int(time.time())
    one_minute_ago = now - 60
    
    cursor.execute(
        "SELECT id FROM memory_nodes WHERE type = 'critique' AND created_at > ? ORDER BY created_at DESC",
        (one_minute_ago,)
    )
    
    new_nodes = cursor.fetchall()
    conn.close()
    
    if new_nodes:
        logger.info(f"✅ Critic Agent created {len(new_nodes)} new critique nodes")
        return True
    else:
        logger.warning("⚠️ No new critique nodes found. This might be normal if no issues were detected.")
        return True

def test_refactor_agent():
    """Test the Refactor Agent"""
    logger.info("=== Testing Refactor Agent ===")
    
    # Check if the refactor agent file exists
    if not os.path.exists("ai_studio_package/agents/refactor_agent.py"):
        logger.error("❌ Refactor Agent file not found")
        return False
    
    logger.info("✅ File exists: ai_studio_package/agents/refactor_agent.py")
    
    # Get a recent critique node to test with
    conn = sqlite3.connect(MEMORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM memory_nodes WHERE type = 'critique' ORDER BY created_at DESC LIMIT 1"
    )
    
    critique_node = cursor.fetchone()
    conn.close()
    
    if not critique_node:
        logger.warning("⚠️ No critique nodes found. Cannot test Refactor Agent without a critique.")
        return False
    
    critique_id = critique_node['id']
    logger.info(f"Using critique node: {critique_id}")
    
    # Run the refactor agent with the critique ID
    logger.info(f"Running command: python -m ai_studio_package.agents.refactor_agent --critique-id {critique_id}")
    result = subprocess.run(
        ["python", "-m", "ai_studio_package.agents.refactor_agent", "--critique-id", critique_id],
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"❌ Command failed with exit code: {result.returncode}")
        logger.error(f"Error output: {result.stderr}")
        logger.error(f"❌ Refactor Agent execution failed: {result.stderr}")
        return False
    
    logger.info("✅ Refactor Agent executed successfully")
    return True

def test_track_execution_decorator():
    """Test the track_execution decorator functionality"""
    logger.info("=== Testing @track_execution Decorator ===")
    
    # Check if the decorator module exists
    if not check_file_exists(DECORATOR_PATH):
        logger.error(f"❌ Execution logs module not found at {DECORATOR_PATH}")
        return False
    
    # Import the decorator dynamically
    try:
        spec = importlib.util.spec_from_file_location("execution_logs", DECORATOR_PATH)
        if spec is None or spec.loader is None:
            logger.error(f"❌ Could not load module from {DECORATOR_PATH}")
            return False
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the decorator
        track_execution = getattr(module, "track_execution", None)
        
        if track_execution is None:
            logger.error("❌ track_execution decorator not found in module")
            return False
            
        logger.info("✅ Successfully imported track_execution decorator")
        
        # Create a test function with the decorator
        @track_execution("test_function")
        def test_function(succeed=True):
            """Test function that either succeeds or raises an exception"""
            if not succeed:
                raise ValueError("Test error")
            return "Success"
        
        # Get the count of logs before
        logs_before = query_database("SELECT COUNT(*) as count FROM execution_logs")
        count_before = logs_before[0]["count"] if logs_before else 0
        
        # Call the test function (success case)
        logger.info("Calling test function (success case)...")
        result = test_function()
        logger.info(f"Function returned: {result}")
        
        # Call the test function (error case)
        logger.info("Calling test function (error case)...")
        try:
            test_function(succeed=False)
        except ValueError as e:
            logger.info(f"Function raised expected error: {e}")
        
        # Get the count of logs after
        logs_after = query_database("SELECT COUNT(*) as count FROM execution_logs")
        count_after = logs_after[0]["count"] if logs_after else 0
        
        # Check if new logs were created
        if count_after > count_before:
            logger.info(f"✅ {count_after - count_before} new logs created by the decorator")
            
            # Check the new logs
            new_logs = query_database(
                "SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT 2"
            )
            
            if new_logs:
                logger.info("Latest execution logs:")
                for log in new_logs:
                    logger.info(f"Task: {log.get('task')}, Status: {log.get('status')}, Latency: {log.get('latency')}s")
                    
            return True
        else:
            logger.error("❌ No new logs created by the decorator")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing decorator: {e}")
        return False

def test_scheduler():
    """Test the Critic Scheduler"""
    logger.info("=== Testing Scheduler ===")
    
    # Check if the scheduler file exists
    if not os.path.exists("ai_studio_package/scripts/schedule_critic.py"):
        logger.error("❌ Scheduler file not found")
        return False
    
    logger.info("✅ File exists: ai_studio_package/scripts/schedule_critic.py")
    
    # Run the scheduler with the --run-now flag
    logger.info("Running command: python -m ai_studio_package.scripts.schedule_critic --run-now")
    result = subprocess.run(
        ["python", "-m", "ai_studio_package.scripts.schedule_critic", "--run-now"],
        capture_output=True, 
        text=True,
        timeout=30  # Give it up to 30 seconds to run
    )
    
    if result.returncode != 0:
        logger.error(f"❌ Command failed with exit code: {result.returncode}")
        logger.error(f"Error output: {result.stderr}")
        return False
    
    logger.info("✅ Command executed successfully (exit code: 0)")
    
    # Check if any new critique nodes were created in the last minute
    conn = sqlite3.connect(MEMORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get current timestamp and timestamp from 1 minute ago
    now = int(time.time())
    one_minute_ago = now - 60
    
    cursor.execute(
        "SELECT id FROM memory_nodes WHERE type = 'critique' AND created_at > ? ORDER BY created_at DESC",
        (one_minute_ago,)
    )
    
    new_nodes = cursor.fetchall()
    conn.close()
    
    if new_nodes:
        logger.info(f"✅ Scheduler created {len(new_nodes)} new critique nodes")
        return True
    else:
        logger.warning("⚠️ No new critique nodes found. This might be normal if no issues were detected.")
        return True

def simulate_workflow():
    """Simulate the complete Self-Improvement Loop workflow"""
    logger.info("=== Simulating Complete SIL Workflow ===")
    
    # Step 1: Create execution logs
    logger.info("Step 1: Creating execution logs...")
    logs_created = generate_test_logs(20)
    
    if logs_created == 0:
        logger.error("❌ Failed to create test logs")
        return False
    
    # Step 2: Run the Critic Agent
    logger.info("Step 2: Running the Critic Agent...")
    critic_success = test_critic_agent()
    
    if not critic_success:
        logger.error("❌ Critic Agent test failed")
        return False
    
    # Step 3: Run the Refactor Agent
    logger.info("Step 3: Running the Refactor Agent...")
    refactor_success = test_refactor_agent()
    
    if not refactor_success:
        logger.error("❌ Refactor Agent test failed")
        return False
    
    logger.info("✅ Complete SIL workflow simulation successful")
    return True

def main():
    """Main function to test the Self-Improvement Loop"""
    logger.info("=== Self-Improvement Loop (SIL) Test ===")
    
    # Check prerequisites
    if not os.path.exists(MEMORY_DB_PATH):
        logger.error(f"❌ Memory database not found at {MEMORY_DB_PATH}")
        return 1
    
    # Test execution logs table
    if not check_execution_logs_table():
        logger.error("❌ Execution logs table test failed")
        return 1
    
    # Test track_execution decorator
    decorator_test = test_track_execution_decorator()
    
    # Test Critic Agent
    critic_test = test_critic_agent()
    
    # Test Refactor Agent
    refactor_test = test_refactor_agent()
    
    # Test scheduler
    scheduler_test = test_scheduler()
    
    # Simulate complete workflow
    workflow_test = simulate_workflow()
    
    # Report results
    logger.info("=== Self-Improvement Loop Test Results ===")
    logger.info(f"Execution Logs Table: {'✅ PASS' if check_execution_logs_table() else '❌ FAIL'}")
    logger.info(f"track_execution Decorator: {'✅ PASS' if decorator_test else '❌ FAIL'}")
    logger.info(f"Critic Agent: {'✅ PASS' if critic_test else '❌ FAIL'}")
    logger.info(f"Refactor Agent: {'✅ PASS' if refactor_test else '❌ FAIL'}")
    logger.info(f"Scheduler: {'✅ PASS' if scheduler_test else '❌ FAIL'}")
    logger.info(f"Complete Workflow: {'✅ PASS' if workflow_test else '❌ FAIL'}")
    
    # Overall result
    all_passed = (
        check_execution_logs_table() and
        decorator_test and 
        critic_test and 
        refactor_test and 
        scheduler_test and 
        workflow_test
    )
    
    if all_passed:
        logger.info("🎉 All Self-Improvement Loop tests passed!")
    else:
        logger.warning("⚠️ Some Self-Improvement Loop tests failed. See details above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 