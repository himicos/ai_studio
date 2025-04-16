"""
Telegram message handler with random sampling and AI analysis
"""
import os
import json
import random
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from telethon import TelegramClient, events
from telethon.tl.types import Message
from .memory_handler import MemoryHandler
from .content_scorer import ContentScorer
from .burner_manager import BurnerManager

class TelegramHandler:
    def __init__(
        self,
        api_id: str,
        api_hash: str,
        session_name: str = "ai_studio",
        sample_rate: float = 0.1,  # Analyze 10% of messages by default
        batch_size: int = 50,  # Process in batches of 50 messages
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.sample_rate = sample_rate
        self.batch_size = batch_size
        
        # Initialize components
        self.memory_handler = MemoryHandler()
        self.content_scorer = ContentScorer()
        self.burner_manager = BurnerManager()
        
        # Message queue for batching
        self.message_queue: List[Dict[str, Any]] = []
        
        # Initialize client
        self.client = TelegramClient(session_name, api_id, api_hash)
        
    async def start(self):
        """Start the Telegram client and message handlers"""
        await self.client.start()
        
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            if random.random() < self.sample_rate:  # Random sampling
                await self.process_message(event.message)
                
        print("Telegram handler started - listening for messages...")
        
    async def process_message(self, message: Message):
        """Process a single message"""
        msg_data = {
            "id": message.id,
            "chat_id": message.chat_id,
            "timestamp": datetime.now().timestamp(),
            "text": message.text,
            "from_id": message.from_id,
            "reply_to_msg_id": message.reply_to_msg_id
        }
        
        # Add to queue
        self.message_queue.append(msg_data)
        
        # Process batch if queue is full
        if len(self.message_queue) >= self.batch_size:
            await self.process_batch()
            
    async def process_batch(self):
        """Process a batch of messages with AI analysis"""
        if not self.message_queue:
            return
            
        try:
            # Get proxy for API calls
            proxy, user_agent = self.burner_manager.get_identity()
            
            # Score content
            scores = await self.content_scorer.score_batch([
                msg["text"] for msg in self.message_queue
            ])
            
            # Combine messages with scores
            for msg, score in zip(self.message_queue, scores):
                msg["ai_score"] = score
            
            # Save batch to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/telegram/batch_{timestamp}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.message_queue, f, indent=2)
            
            # Store insights in memory
            for msg in self.message_queue:
                if msg["ai_score"] > 0.7:  # Only store high-scoring insights
                    self.memory_handler.store_insight(
                        topic="telegram_messages",
                        content=msg["text"],
                        metadata={
                            "score": msg["ai_score"],
                            "chat_id": msg["chat_id"],
                            "timestamp": msg["timestamp"]
                        }
                    )
            
            # Clear queue
            self.message_queue = []
            
        except Exception as e:
            print(f"Error processing batch: {e}")
            
    async def get_chat_history(
        self,
        chat_id: int,
        limit: Optional[int] = None,
        sample_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history with optional sampling
        
        Args:
            chat_id: Telegram chat ID
            limit: Maximum number of messages to retrieve
            sample_size: Number of random messages to sample (if None, get all)
        """
        messages = []
        async for message in self.client.iter_messages(chat_id, limit=limit):
            msg_data = {
                "id": message.id,
                "timestamp": message.date.timestamp(),
                "text": message.text,
                "from_id": message.from_id,
                "reply_to_msg_id": message.reply_to_msg_id
            }
            messages.append(msg_data)
            
        if sample_size and len(messages) > sample_size:
            messages = random.sample(messages, sample_size)
            
        return messages
        
    def save_chat_history(self, chat_id: int, messages: List[Dict[str, Any]]):
        """Save chat history to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/telegram/history_{chat_id}_{timestamp}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
            
    async def stop(self):
        """Stop the Telegram client"""
        # Process any remaining messages
        if self.message_queue:
            await self.process_batch()
        await self.client.disconnect()
