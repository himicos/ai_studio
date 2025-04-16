
"""
Memory Handler for AI Studio.

Handles deduplication, insight aggregation, and efficient storage of processed content.
"""

import json
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

class MemoryHandler:
    def __init__(self, memory_dir: str = "memory/insights"):
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.content_hashes = set()
        self.insights_cache = {}
        self.last_aggregation = None
        self.AGGREGATION_INTERVAL = 3600  # Aggregate insights every hour
        self.MEMORY_WINDOW = 86400  # Keep 24 hours of memory
        
        self.logger.info(f"Memory handler initialized at {memory_dir}")

    def get_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate a hash for content to detect duplicates"""
        # Extract key fields for hashing
        key_fields = {
            'content': content.get('content', ''),
            'author': content.get('author', ''),
            'platform': content.get('metadata', {}).get('platform', '')
        }
        return hashlib.sha256(json.dumps(key_fields, sort_keys=True).encode()).hexdigest()

    def is_duplicate(self, content: Dict[str, Any]) -> bool:
        """Check if content is a duplicate"""
        content_hash = self.get_content_hash(content)
        if content_hash in self.content_hashes:
            self.logger.debug(f"Duplicate content detected: {content.get('id', 'unknown')}")
            return True
        self.content_hashes.add(content_hash)
        self.logger.debug(f"New unique content added: {content.get('id', 'unknown')}")
        return False

    def add_insight(self, insight: Dict[str, Any]) -> None:
        """Add a new insight to the cache"""
        timestamp = int(time.time())
        topic = insight.get('topic', 'general')
        
        if topic not in self.insights_cache:
            self.insights_cache[topic] = []
            
        self.insights_cache[topic].append({
            'timestamp': timestamp,
            'data': insight
        })
        
        self.logger.info(
            f"Added insight to cache - Topic: {topic}, "
            f"Items in topic: {len(self.insights_cache[topic])}"
        )

    def cleanup_old_insights(self) -> None:
        """Remove insights older than MEMORY_WINDOW"""
        cutoff = int(time.time()) - self.MEMORY_WINDOW
        total_removed = 0
        
        for topic in self.insights_cache:
            before_count = len(self.insights_cache[topic])
            self.insights_cache[topic] = [
                insight for insight in self.insights_cache[topic]
                if insight['timestamp'] > cutoff
            ]
            after_count = len(self.insights_cache[topic])
            removed = before_count - after_count
            total_removed += removed
            
            if removed > 0:
                self.logger.info(f"Removed {removed} old insights from topic {topic}")
        
        if total_removed > 0:
            self.logger.info(f"Total old insights removed: {total_removed}")

    async def aggregate_insights(self, openai_client) -> Optional[Dict[str, Any]]:
        """Aggregate insights and generate summary"""
        current_time = int(time.time())
        
        # Check if it's time to aggregate
        if (self.last_aggregation and 
            current_time - self.last_aggregation < self.AGGREGATION_INTERVAL):
            return None

        self.cleanup_old_insights()
        
        if not any(self.insights_cache.values()):
            return None

        # Prepare insights for analysis
        insights_summary = {}
        for topic, insights in self.insights_cache.items():
            if not insights:
                continue
                
            # Group insights by subtopics
            grouped_insights = self._group_insights(insights)
            
            try:
                # Generate summary for each topic
                response = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": (
                            "You are an AI crypto analyst. Analyze these insights and identify:\n"
                            "1. Key trends and patterns\n"
                            "2. Potential opportunities\n"
                            "3. Risk factors\n"
                            "4. Community sentiment\n"
                            "Provide a concise, actionable summary."
                        )},
                        {"role": "user", "content": json.dumps(grouped_insights, indent=2)}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                insights_summary[topic] = {
                    'summary': response.choices[0].message.content,
                    'timestamp': current_time,
                    'data_points': len(insights),
                    'subtopics': list(grouped_insights.keys())
                }
                
            except Exception as e:
                logger.error(f"Error aggregating insights for {topic}: {e}")
                continue

        # Save aggregated insights
        if insights_summary:
            output_file = self.memory_dir / f"insights_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(output_file, 'w') as f:
                json.dump(insights_summary, f, indent=2)

        self.last_aggregation = current_time
        return insights_summary

    def _group_insights(self, insights: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group insights by subtopics for better analysis"""
        grouped = {}
        
        for insight in insights:
            data = insight['data']
            subtopics = data.get('subtopics', ['general'])
            
            for subtopic in subtopics:
                if subtopic not in grouped:
                    grouped[subtopic] = []
                grouped[subtopic].append(data)
        
        return grouped

    def get_opportunity_analysis(self, insights_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Extract potential opportunities and risks from aggregated insights"""
        opportunities = []
        risks = []
        
        for topic, summary in insights_summary.items():
            topic_summary = summary.get('summary', '')
            
            # Extract opportunities (indicated by positive language)
            opp_indicators = ['potential', 'opportunity', 'growing', 'bullish', 'undervalued']
            for indicator in opp_indicators:
                if indicator in topic_summary.lower():
                    opportunities.append({
                        'topic': topic,
                        'indicator': indicator,
                        'context': topic_summary
                    })
            
            # Extract risks (indicated by cautionary language)
            risk_indicators = ['risk', 'warning', 'bearish', 'concern', 'volatile']
            for indicator in risk_indicators:
                if indicator in topic_summary.lower():
                    risks.append({
                        'topic': topic,
                        'indicator': indicator,
                        'context': topic_summary
                    })
        
        return {
            'opportunities': opportunities,
            'risks': risks,
            'timestamp': int(time.time())
        }
