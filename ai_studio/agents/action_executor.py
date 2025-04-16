"""
Action Executor Module for AI Studio

This module handles execution of actions based on scanner outputs, including:
- Processing detected items from Twitter and Reddit trackers
- Logging detected items to the database
- Summarizing content using AI models
- Saving outputs to prompt_outputs directory
- Optionally triggering prototypes in the tests directory
"""

import os
import re
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import openai
from dotenv import load_dotenv

# Import our modules
from infra.db import log_action, get_post, store_post
from agents.prompt_router import PromptRouter

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class ActionExecutor:
    """
    Action Executor for AI Studio.
    
    This class processes detected items from the Twitter and Reddit trackers,
    logs them to the database, summarizes content, and executes appropriate actions.
    """
    
    def __init__(self):
        """
        Initialize the action executor.
        """
        # Load configuration from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        
        # Initialize API clients
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Initialize prompt router for advanced processing
        self.prompt_router = PromptRouter()
        
        logger.info("Action executor initialized")
    
    async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a detected item.
        
        Args:
            item (dict): The detected item
            
        Returns:
            dict: Processing result
        """
        item_type = item.get('type', '')
        item_data = item.get('data', {})
        
        logger.info(f"Processing {item_type} item")
        
        if item_type == 'contract':
            return await self.process_contract(item_data)
        elif item_type == 'keyword':
            return await self.process_keyword(item_data)
        else:
            logger.warning(f"Unknown item type: {item_type}")
            return {
                'status': 'error',
                'message': f"Unknown item type: {item_type}",
                'item': item
            }
    
    async def process_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a detected contract.
        
        Args:
            contract (dict): The contract data
            
        Returns:
            dict: Processing result
        """
        logger.info(f"Processing contract: {contract['address']}")
        
        try:
            # Log action
            log_action('action_executor', 'process_contract', f"Processing contract {contract['address']}")
            
            # Generate summary
            summary = await self.generate_summary(contract)
            
            # Save to prompt outputs
            output_path = await self.save_to_prompt_outputs(
                f"contract_{contract['address']}",
                {
                    'contract': contract,
                    'summary': summary,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return result
            return {
                'status': 'success',
                'contract': contract,
                'summary': summary,
                'output_path': output_path
            }
        
        except Exception as e:
            logger.error(f"Error processing contract: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'contract': contract
            }
    
    async def process_keyword(self, keyword_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a detected keyword.
        
        Args:
            keyword_data (dict): The keyword data
            
        Returns:
            dict: Processing result
        """
        keyword = keyword_data.get('keyword', '')
        content = keyword_data.get('tweet', {}) or keyword_data.get('post', {})
        
        logger.info(f"Processing keyword: {keyword}")
        
        try:
            # Log action
            log_action('action_executor', 'process_keyword', f"Processing keyword {keyword}")
            
            # Generate summary
            summary = await self.generate_summary(content)
            
            # Save to prompt outputs
            output_path = await self.save_to_prompt_outputs(
                f"keyword_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                {
                    'keyword': keyword,
                    'content': content,
                    'summary': summary,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Return result
            return {
                'status': 'success',
                'keyword': keyword,
                'content': content,
                'summary': summary,
                'output_path': output_path
            }
        
        except Exception as e:
            logger.error(f"Error processing keyword: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'keyword': keyword,
                'content': content
            }
    
    async def generate_summary(self, content: Dict[str, Any]) -> str:
        """
        Generate a summary of content using AI.
        
        Args:
            content (dict): The content to summarize
            
        Returns:
            str: The summary
        """
        try:
            if not self.openai_api_key:
                return "OpenAI API key not configured. Summary generation skipped."
            
            # Convert content to string representation
            content_str = json.dumps(content, indent=2)
            
            # Use GPT-4o to generate summary
            response = await openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a summarization assistant. Create a concise 50-word summary of the provided content, focusing on the most important information."},
                    {"role": "user", "content": f"Please summarize the following content:\n\n{content_str}"}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {e}"
    
    async def save_to_prompt_outputs(self, base_name: str, data: Dict[str, Any]) -> str:
        """
        Save data to the prompt outputs directory.
        
        Args:
            base_name (str): Base name for the file
            data (dict): Data to save
            
        Returns:
            str: Path to the saved file
        """
        try:
            # Create the prompt outputs directory if it doesn't exist
            os.makedirs(os.path.join("memory", "prompt_outputs"), exist_ok=True)
            
            # Create the file path
            file_path = os.path.join("memory", "prompt_outputs", f"{base_name}.json")
            
            # Save the data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Saved data to {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error saving to prompt outputs: {e}")
            return f"Error: {e}"
    
    async def trigger_prototype(self, prototype_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a prototype in the tests directory.
        
        Args:
            prototype_name (str): Name of the prototype
            data (dict): Data to pass to the prototype
            
        Returns:
            dict: Prototype result
        """
        try:
            # Check if prototype exists
            prototype_path = os.path.join("tests", f"{prototype_name}.py")
            if not os.path.exists(prototype_path):
                logger.error(f"Prototype {prototype_name} not found")
                return {
                    'status': 'error',
                    'message': f"Prototype {prototype_name} not found"
                }
            
            # Save data to temporary file
            temp_data_path = os.path.join("memory", "prompt_outputs", f"temp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(temp_data_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Execute prototype
            # In a real implementation, this would use subprocess or importlib
            # to execute the prototype script
            logger.info(f"Triggering prototype {prototype_name}")
            
            # Placeholder for prototype execution
            return {
                'status': 'success',
                'message': f"Prototype {prototype_name} triggered",
                'data_path': temp_data_path
            }
        
        except Exception as e:
            logger.error(f"Error triggering prototype: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def process_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple detected items.
        
        Args:
            items (list): List of detected items
            
        Returns:
            list: List of processing results
        """
        results = []
        
        for item in items:
            result = await self.process_item(item)
            results.append(result)
        
        return results

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create action executor
    executor = ActionExecutor()
    
    # Process a sample item
    sample_item = {
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
    
    result = asyncio.run(executor.process_item(sample_item))
    print(json.dumps(result, indent=2, default=str))
