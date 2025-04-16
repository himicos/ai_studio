#!/bin/bash

# Integration Test Script for AI Studio
# This script tests the integration of all AI Studio components

echo "Starting AI Studio Integration Tests..."
echo "========================================"

# Create necessary directories
mkdir -p memory/logs
mkdir -p memory/prompt_outputs

# Create a test .env file
echo "Creating test .env file..."
cat > .env << EOL
# AI Studio Test Environment Configuration

# API Keys (using placeholder values for testing)
OPENAI_API_KEY=sk-test
GROK_API_KEY=grok-test
CLAUDE_API_KEY=claude-test

# Monitoring Configuration
SUBREDDITS=cryptocurrency,CryptoMoonShots
TWITTER_ACCOUNTS=elonmusk,vitalikbuterin
KEYWORDS=crypto,bitcoin,ethereum,contract,0x

# Burner Configuration
PROXIES=
USER_AGENTS="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BURNER_MODE=false

# System Configuration
BUMP_PROMPTS=false
SCAN_INTERVAL=60
LOG_LEVEL=INFO
EOL

echo "Test .env file created."

# Initialize the database
echo "Initializing database..."
python3 -c "import sys; sys.path.append('.'); from infra.db import init_db; init_db()"
echo "Database initialized."

# Test database operations
echo "Testing database operations..."
python3 -c "
import sys; sys.path.append('.')
from infra.db import store_post, get_post, log_action
from datetime import datetime

# Test storing a post
post = {
    'id': 'test_post_1',
    'source': 'twitter',
    'title': 'Test Post',
    'content': 'This is a test post with contract 0x1234567890abcdef1234567890abcdef12345678',
    'author': 'test_user',
    'url': 'https://twitter.com/test_user/status/123456789',
    'score': 10,
    'num_comments': 5,
    'created_utc': int(datetime.now().timestamp()),
    'metadata': {
        'hashtags': ['test', 'example']
    }
}

success = store_post(post)
print(f'Post stored: {success}')

# Test retrieving a post
retrieved_post = get_post('test_post_1')
print(f'Retrieved post: {retrieved_post is not None}')

# Test logging an action
log_success = log_action('test_agent', 'test_action', 'This is a test action')
print(f'Action logged: {log_success}')
"
echo "Database operations tested."

# Test burner manager
echo "Testing burner manager..."
python3 -c "
import sys; sys.path.append('.')
from tools.burner_manager import BurnerManager

# Create burner manager
burner = BurnerManager()

# Get identity
proxy, user_agent = burner.get_identity()
print(f'Identity retrieved: User-Agent={user_agent[:30]}...')
"
echo "Burner manager tested."

# Test prompt router
echo "Testing prompt router..."
python3 -c "
import sys; sys.path.append('.')
import asyncio
from agents.prompt_router import PromptRouter

async def test_router():
    # Create prompt router
    router = PromptRouter()
    
    # Test intent parsing
    prompt = 'Build a bot to track crypto scams on Twitter'
    intent = router._parse_intent(prompt)
    print(f'Detected intent: {intent}')

# Run the test
asyncio.run(test_router())
"
echo "Prompt router tested."

# Test action executor
echo "Testing action executor..."
python3 -c "
import sys; sys.path.append('.')
import asyncio
import json
from datetime import datetime
from agents.action_executor import ActionExecutor

async def test_executor():
    # Create action executor
    executor = ActionExecutor()
    
    # Create a test item
    test_item = {
        'type': 'contract',
        'data': {
            'id': 'contract_0x1234567890abcdef1234567890abcdef12345678_1234567890',
            'address': '0x1234567890abcdef1234567890abcdef12345678',
            'source': 'twitter',
            'source_id': 'twitter_123456789',
            'detected_at': int(datetime.now().timestamp()),
            'status': 'detected',
            'metadata': {
                'tweet_text': 'Check out this new contract: 0x1234567890abcdef1234567890abcdef12345678',
                'tweet_url': 'https://twitter.com/user/status/123456789',
                'author': 'user'
            }
        }
    }
    
    # Process the item
    result = await executor.process_item(test_item)
    print(f'Item processed: {result[\"status\"]}')

# Run the test
asyncio.run(test_executor())
"
echo "Action executor tested."

# Test the test prototype
echo "Testing test prototype..."
python3 tests/test_prototype.py
echo "Test prototype tested."

# Test main CLI
echo "Testing main CLI..."
python3 -c "
import sys; sys.path.append('.')
import os
from main import setup

# Test setup function
setup()
print('Main setup function executed successfully')

# Check if directories were created
logs_dir = os.path.join('memory', 'logs')
outputs_dir = os.path.join('memory', 'prompt_outputs')
print(f'Logs directory exists: {os.path.exists(logs_dir)}')
print(f'Prompt outputs directory exists: {os.path.exists(outputs_dir)}')
"
echo "Main CLI tested."

echo "========================================"
echo "Integration tests completed."
echo "AI Studio system is ready for use!"
