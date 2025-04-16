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
import time
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
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        
        # Initialize memory handler
        from tools.memory_handler import MemoryHandler
        self.memory_handler = MemoryHandler()
        
        # Initialize prompt router for advanced processing
        self.prompt_router = PromptRouter()
        
        # Initialize API cost tracking
        self.api_costs = {
            'total_tokens': 0,
            'total_cost': 0.0,
            'last_reset': time.time()
        }
        
        logger.info("Action executor initialized")
    
    async def process_item(self, item: Dict[str, Any], batch_context: str = None) -> Dict[str, Any]:
        """
        Process a detected item.
        
        Args:
            item (dict): The detected item
            batch_context (str, optional): Context from batch summary
            
        Returns:
            dict: Processing result
        """
        item_type = item.get('type', '')
        item_data = item.get('data', {})
        
        logger.info(f"Processing {item_type} item")
        
        # Add batch context to item data if available
        if batch_context:
            item_data['batch_context'] = batch_context
        
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
    
    async def generate_batch_summary(self, items: List[Dict[str, Any]]) -> str:
        """
        Generate a summary for a batch of items using AI.
        
        Args:
            items (list): List of items to summarize
            
        Returns:
            str: The batch summary
        """
        try:
            if not self.openai_api_key:
                return "OpenAI API key not configured. Summary generation skipped."
            
            # Prepare batch content
            batch_content = []
            for item in items:
                platform = item.get('metadata', {}).get('platform', 'unknown')
                author = item.get('author', 'unknown')
                content = item.get('content', '')
                batch_content.append(f"{platform} by {author}: {content}")
            
            batch_str = "\n---\n".join(batch_content)
            
            # Use GPT-4o to generate batch summary
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI analyst specializing in crypto and blockchain content. Create a concise summary of related content items, identifying key themes and important information."},
                    {"role": "user", "content": f"Please analyze and summarize these related items:\n\n{batch_str}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            # Track API usage
            if hasattr(response, 'usage'):
                tokens = response.usage.total_tokens
                # Estimate cost: $0.01 per 1K tokens for gpt-4o
                cost = (tokens / 1000) * 0.01
                self.api_costs['total_tokens'] += tokens
                self.api_costs['total_cost'] += cost
                logger.debug(f"Batch summary API usage: {tokens} tokens, ${cost:.4f}")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating batch summary: {e}")
            return f"Error generating batch summary: {e}"
            
    async def generate_summary(self, content: Dict[str, Any], batch_context: str = None) -> str:
        """
        Generate a summary of content using AI, optionally with batch context.
        
        Args:
            content (dict): The content to summarize
            batch_context (str, optional): Context from batch summary
            
        Returns:
            str: The summary
        """
        try:
            if not self.openai_api_key:
                return "OpenAI API key not configured. Summary generation skipped."
            
            # Convert content to string representation
            content_str = json.dumps(content, indent=2)
            
            # Prepare system message with batch context if available
            system_message = "You are a summarization assistant specializing in crypto and blockchain content."
            if batch_context:
                system_message += f"\n\nBatch Context: {batch_context}"
            
            # Use GPT-4o to generate summary
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Please summarize the following content in the context of related items:\n\n{content_str}"}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            # Track API usage
            if hasattr(response, 'usage'):
                tokens = response.usage.total_tokens
                # Estimate cost: $0.01 per 1K tokens for gpt-4o
                cost = (tokens / 1000) * 0.01
                self.api_costs['total_tokens'] += tokens
                self.api_costs['total_cost'] += cost
                logger.debug(f"Summary API usage: {tokens} tokens, ${cost:.4f}")
            
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
        Process multiple detected items using the batching system and memory handler.
        
        Args:
            items (list): List of detected items
            
        Returns:
            list: List of processing results
        """
        from tools.content_scorer import ContentBatcher
        
        # Initialize batcher if not exists
        if not hasattr(self, 'content_batcher'):
            self.content_batcher = ContentBatcher()
        
        # Filter out duplicates using memory handler
        unique_items = [item for item in items if not self.memory_handler.is_duplicate(item)]
        if len(unique_items) < len(items):
            logger.info(f"Filtered out {len(items) - len(unique_items)} duplicate items")
        
        # Add unique items to batcher
        self.content_batcher.add_items(unique_items)
        
        # Get batches ready for processing
        ready_batches = self.content_batcher.get_ready_batches()
        results = []
        
        # Process each ready batch
        for priority, batch_items in ready_batches.items():
            logger.info(f"Processing {priority} batch with {len(batch_items)} items")
            
            if not batch_items:
                continue
                
            # Process items in the batch together
            try:
                # Generate combined summary for the batch
                batch_summary = await self.generate_batch_summary(batch_items)
                
                # Add batch insights to memory handler
                self.memory_handler.add_insight({
                    'type': 'batch_summary',
                    'topic': priority,
                    'content': batch_summary,
                    'items_count': len(batch_items),
                    'subtopics': [item.get('type', 'unknown') for item in batch_items]
                })
                
                # Process individual items with the context of the batch
                for item in batch_items:
                    result = await self.process_item(item, batch_context=batch_summary)
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error processing {priority} batch: {e}")
                results.extend([
                    {
                        'status': 'error',
                        'message': str(e),
                        'item': item
                    } for item in batch_items
                ])
        
        # Try to aggregate insights if enough time has passed
        try:
            insights_summary = await self.memory_handler.aggregate_insights(self.openai_client)
            if insights_summary:
                # Analyze for opportunities
                opportunities = self.memory_handler.get_opportunity_analysis(insights_summary)
                
                # Save opportunities analysis
                await self.save_to_prompt_outputs(
                    f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    opportunities
                )
                
                logger.info(f"Generated insights summary with {len(opportunities['opportunities'])} opportunities")
        except Exception as e:
            logger.error(f"Error aggregating insights: {e}")
        
        # Track API costs
        current_time = time.time()
        if current_time - self.api_costs['last_reset'] >= 3600:  # Reset every hour
            logger.info(
                f"API usage in the last hour: {self.api_costs['total_tokens']} tokens, "
                f"estimated cost: ${self.api_costs['total_cost']:.2f}"
            )
            self.api_costs.update({
                'total_tokens': 0,
                'total_cost': 0.0,
                'last_reset': current_time
            })
        
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
