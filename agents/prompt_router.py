"""
Prompt Router Module for AI Studio

This module handles routing of schizoprompts to appropriate AI models, including:
- Parsing intent from raw schizoprompts
- Routing to appropriate AI models (Grok, Claude, GPT-4o, Manus)
- Generating prompt variations when BUMP_PROMPTS is enabled
- Logging routing decisions and results
"""

import os
import re
import json
import logging
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import openai
import anthropic
from dotenv import load_dotenv

# Import our modules
from infra.db import store_prompt, update_prompt, log_action

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class PromptRouter:
    """
    Prompt Router for AI Studio.
    
    This class parses intent from raw schizoprompts and routes them to the
    appropriate AI models (Grok, Claude, GPT-4o, Manus).
    """
    
    def __init__(self):
        """
        Initialize the prompt router.
        """
        # Load configuration from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.claude_api_key = os.getenv('CLAUDE_API_KEY', '')
        self.grok_api_key = os.getenv('GROK_API_KEY', '')
        
        self.bump_prompts = os.getenv('BUMP_PROMPTS', 'false').lower() == 'true'
        
        # Initialize API clients
        if self.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        
        if self.claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
        else:
            self.claude_client = None
        
        # Intent keywords (temporarily routing everything to GPT-4o)
        self.intent_keywords = {
            'gpt4o': ['ui', 'interface', 'design', 'reasoning', 'logic', 'analyze', 'visualization',
                     'write', 'essay', 'article', 'content', 'creative', 'story', 'summarize',
                     'code', 'program', 'develop', 'implement', 'script', 'function', 'algorithm',
                     'infra', 'infrastructure', 'system', 'architecture', 'deploy', 'setup', 'configure']
        }
        
        logger.info(f"Prompt router initialized with BUMP_PROMPTS={self.bump_prompts}")
    
    def _parse_intent(self, prompt: str) -> str:
        """
        Parse intent from a schizoprompt.
        
        Args:
            prompt (str): The schizoprompt
            
        Returns:
            str: The detected intent ('grok', 'claude', 'gpt4o', 'manus')
        """
        prompt_lower = prompt.lower()
        
        # Count keyword matches for each intent
        intent_scores = {intent: 0 for intent in self.intent_keywords}
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword.lower() in prompt_lower:
                    intent_scores[intent] += 1
        
        # Get the intent with the highest score
        max_score = max(intent_scores.values())
        
        # If there's a tie or no matches, default to gpt4o
        if max_score == 0 or list(intent_scores.values()).count(max_score) > 1:
            return 'gpt4o'
        
        # Return the intent with the highest score
        return max(intent_scores, key=intent_scores.get)
    
    async def _generate_variations(self, prompt: str, intent: str) -> List[str]:
        """
        Generate variations of a prompt.
        
        Args:
            prompt (str): The original prompt
            intent (str): The detected intent
            
        Returns:
            list: List of prompt variations
        """
        variations = [prompt]  # Start with the original prompt
        
        try:
            if self.openai_api_key:
                # Use GPT-4o to generate variations
                system_message = "You are a prompt engineer. Generate 2 variations of the given prompt that maintain the original intent but use different wording, structure, or emphasis. Return ONLY the variations, one per line, with no additional text."
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Original prompt: {prompt}\nIntent: {intent}"}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                # Extract variations from response
                if response.choices and response.choices[0].message.content:
                    new_variations = response.choices[0].message.content.strip().split('\n')
                    new_variations = [v.strip() for v in new_variations if v.strip()]
                    variations.extend(new_variations)
            
            # Ensure we have at least 3 variations (or as many as we could generate)
            while len(variations) < 3:
                variations.append(prompt)
            
            return variations
        
        except Exception as e:
            logger.error(f"Error generating prompt variations: {e}")
            return [prompt]  # Return original prompt if generation fails
    
    def _select_best_variation(self, variations: List[str]) -> str:
        """
        Select the best variation from a list of prompt variations.
        
        Args:
            variations (list): List of prompt variations
            
        Returns:
            str: The selected variation
        """
        # For now, simply select the longest variation as a heuristic
        return max(variations, key=len)
    
    async def _route_to_grok(self, prompt: str) -> str:
        """
        Route a prompt to Grok.
        
        Args:
            prompt (str): The prompt
            
        Returns:
            str: The response
        """
        if not self.grok_api_key:
            return "Grok API key not configured. Please add your Grok API key to the .env file."
        
        # Placeholder for Grok API integration
        # In a real implementation, this would use the Grok API
        return f"[Grok would process: {prompt}]"
    
    async def _route_to_claude(self, prompt: str) -> str:
        """
        Route a prompt to Claude.
        
        Args:
            prompt (str): The prompt
            
        Returns:
            str: The response
        """
        if not self.claude_client:
            return "Claude API key not configured. Please add your Claude API key to the .env file."
        
        try:
            response = await self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Error routing to Claude: {e}")
            return f"Error processing with Claude: {e}"
    
    async def _route_to_gpt4o(self, prompt: str) -> str:
        """
        Route a prompt to GPT-4o.
        
        Args:
            prompt (str): The prompt
            
        Returns:
            str: The response
        """
        if not self.openai_api_key:
            return "OpenAI API key not configured. Please add your OpenAI API key to the .env file."
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error routing to GPT-4o: {e}")
            return f"Error processing with GPT-4o: {e}"
    
    async def _route_to_manus(self, prompt: str) -> str:
        """
        Route a prompt to Manus (save for manual execution).
        
        Args:
            prompt (str): The prompt
            
        Returns:
            str: The response
        """
        try:
            # Create a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create the prompt outputs directory if it doesn't exist
            os.makedirs(os.path.join("memory", "prompt_outputs"), exist_ok=True)
            
            # Save the prompt to a file
            filename = os.path.join("memory", "prompt_outputs", f"manus_prompt_{timestamp}.txt")
            with open(filename, 'w') as f:
                f.write(prompt)
            
            return f"Prompt saved for manual execution with Manus: {filename}"
        
        except Exception as e:
            logger.error(f"Error saving prompt for Manus: {e}")
            return f"Error saving prompt for Manus: {e}"
    
    async def process(self, prompt: str) -> Dict[str, Any]:
        """
        Process a schizoprompt.
        
        Args:
            prompt (str): The schizoprompt
            
        Returns:
            dict: Processing result
        """
        logger.info(f"Processing prompt: {prompt[:50]}...")
        
        # Parse intent
        intent = self._parse_intent(prompt)
        logger.info(f"Detected intent: {intent}")
        
        # Store prompt in database
        prompt_id = store_prompt(prompt, intent)
        
        # Generate variations if BUMP_PROMPTS is enabled
        final_prompt = prompt
        if self.bump_prompts:
            logger.info("Generating prompt variations")
            variations = await self._generate_variations(prompt, intent)
            final_prompt = self._select_best_variation(variations)
            logger.info(f"Selected variation: {final_prompt[:50]}...")
        
        # Route to appropriate model
        response = ""
        if intent == 'grok':
            response = await self._route_to_grok(final_prompt)
        elif intent == 'claude':
            response = await self._route_to_claude(final_prompt)
        elif intent == 'gpt4o':
            response = await self._route_to_gpt4o(final_prompt)
        elif intent == 'manus':
            response = await self._route_to_manus(final_prompt)
        
        # Update prompt in database
        update_prompt(prompt_id, response)
        
        # Log action
        log_action('prompt_router', 'process_prompt', f"Processed prompt with intent {intent}")
        
        # Return result
        result = {
            'prompt_id': prompt_id,
            'original_prompt': prompt,
            'final_prompt': final_prompt,
            'intent': intent,
            'response': response
        }
        
        return result

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create prompt router
    router = PromptRouter()
    
    # Process a prompt
    test_prompt = "Build a bot to track crypto scams on Twitter"
    result = asyncio.run(router.process(test_prompt))
    
    print(f"Intent: {result['intent']}")
    print(f"Response: {result['response']}")
