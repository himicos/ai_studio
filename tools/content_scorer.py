"""
Content Scoring and Batching Module for AI Studio.

This module provides sophisticated content scoring and batching mechanisms
for optimizing API usage and content processing.
"""

import time
import re
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Constants
VERIFIED_ACCOUNTS = set()  # TODO: Load from configuration
KNOWN_DEVELOPERS = set()   # TODO: Load from configuration
SPAM_ACCOUNTS = set()      # TODO: Load from configuration

class ContentScorer:
    def calculate_engagement_score(self, content: Dict[str, Any]) -> float:
        """
        Calculate an engagement score based on platform-specific metrics
        Returns a normalized score between 0-10
        """
        score = 0
        platform = content.get('metadata', {}).get('platform', '')
        
        if platform == 'reddit':
            # Reddit-specific scoring
            upvotes = content.get('score', 0)
            ratio = content.get('metadata', {}).get('upvote_ratio', 1.0)
            comments = content.get('num_comments', 0)
            age_hours = (time.time() - content.get('created_utc', time.time())) / 3600
            
            # Viral factor: high upvotes + high ratio
            if upvotes > 100 and ratio > 0.8:
                score += 5
            elif upvotes > 50 and ratio > 0.7:
                score += 3
            
            # Engagement quality
            engagement_score = (upvotes * ratio) + (comments * 2)
            
            # Time decay factor (reduce score for older posts)
            time_decay = max(0, 1 - (age_hours / 24))  # Decay over 24 hours
            
            # Normalized engagement score (0-10)
            score += min(5, (engagement_score / 1000) * 5) * time_decay

        elif platform == 'twitter':
            # Twitter-specific scoring
            likes = content.get('metadata', {}).get('likes', 0)
            retweets = content.get('metadata', {}).get('retweets', 0)
            replies = content.get('metadata', {}).get('replies', 0)
            verified = content.get('metadata', {}).get('verified', False)
            followers = content.get('metadata', {}).get('follower_count', 0)
            
            # Engagement rate (relative to follower count)
            if followers > 0:
                engagement_rate = (likes + retweets * 2 + replies * 3) / followers
                score += min(4, engagement_rate * 1000)  # Cap at 4 points
            
            # Absolute engagement metrics
            engagement_score = (likes * 0.5) + (retweets * 1.5) + (replies * 1)
            score += min(3, (engagement_score / 1000) * 3)
            
            # Verified account bonus
            if verified:
                score += 1
            
            # Viral tweet detection
            if retweets > likes * 0.4:  # High retweet-to-like ratio
                score += 2

        return min(10, score)  # Cap final score at 10

    def should_process_content(self, content: Dict[str, Any]) -> Tuple[float, bool]:
        """
        Enhanced content filtering with engagement metrics
        Returns (score, should_process)
        """
        base_score = 0
        engagement_score = self.calculate_engagement_score(content)
        
        # Engagement weight (30% of total score)
        base_score += engagement_score * 0.3
        
        # Content relevance (40% of total score)
        relevance_score = 0
        
        # High-priority keywords (technical, news, announcements)
        high_priority = ['announcement', 'launch', 'vulnerability', 'hack', 'protocol', 'update']
        if any(kw in content.get('content', '').lower() for kw in high_priority):
            relevance_score += 4
        
        # Medium-priority keywords
        medium_priority = ['defi', 'blockchain', 'crypto', 'web3', 'token']
        if any(kw in content.get('content', '').lower() for kw in medium_priority):
            relevance_score += 2
        
        # Technical indicators
        if re.search(r'0x[a-fA-F0-9]{40}', content.get('content', '')):  # Contains contract address
            relevance_score += 3
        
        base_score += min(10, relevance_score) * 0.4
        
        # Source credibility (30% of total score)
        credibility_score = 0
        
        # Check author history
        author = content.get('author', '')
        if author in VERIFIED_ACCOUNTS:
            credibility_score += 5
        elif author in KNOWN_DEVELOPERS:
            credibility_score += 7
        elif author in SPAM_ACCOUNTS:
            credibility_score -= 10
        
        # Account age and karma (Reddit) or followers (Twitter)
        if content.get('metadata', {}).get('platform') == 'reddit':
            author_karma = content.get('metadata', {}).get('author_karma', 0)
            credibility_score += min(5, (author_karma / 10000) * 5)
        else:  # Twitter
            followers = content.get('metadata', {}).get('follower_count', 0)
            credibility_score += min(5, (followers / 10000) * 5)
        
        base_score += min(10, credibility_score) * 0.3
        
        # Final score is out of 10
        return base_score, base_score >= 6

class ContentBatcher:
    def __init__(self):
        self.scorer = ContentScorer()
        self.batches = {
            'urgent': [],     # Score >= 8: Process immediately
            'high': [],       # Score >= 6: Process every 5 minutes
            'medium': [],     # Score >= 4: Process every 10 minutes
            'low': []         # Score < 4: Process every 15 minutes
        }
        self.last_processed = {
            'urgent': None,
            'high': None,
            'medium': None,
            'low': None
        }
        self.batch_intervals = {
            'urgent': 0,      # Process immediately
            'high': 300,      # 5 minutes
            'medium': 600,    # 10 minutes
            'low': 900        # 15 minutes
        }

    def add_items(self, items: List[Dict[str, Any]]) -> None:
        """Add new items to appropriate batches based on their scores"""
        for item in items:
            score, _ = self.scorer.should_process_content(item)
            if score >= 8:
                self.batches['urgent'].append((item, score))
            elif score >= 6:
                self.batches['high'].append((item, score))
            elif score >= 4:
                self.batches['medium'].append((item, score))
            else:
                self.batches['low'].append((item, score))

    def get_ready_batches(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get batches that are ready to be processed based on their intervals"""
        now = time.time()
        ready_batches = {}
        
        for priority, items in self.batches.items():
            last_time = self.last_processed[priority]
            interval = self.batch_intervals[priority]
            
            if not last_time or (now - last_time) >= interval:
                if items:
                    # Sort items by score and take top items
                    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
                    ready_batches[priority] = [item[0] for item in sorted_items]
                    self.batches[priority] = []  # Clear the batch
                    self.last_processed[priority] = now
        
        return ready_batches

    def get_stats(self) -> Dict[str, Any]:
        """Get current batching statistics"""
        return {
            'batch_sizes': {k: len(v) for k, v in self.batches.items()},
            'last_processed': self.last_processed.copy()
        }
