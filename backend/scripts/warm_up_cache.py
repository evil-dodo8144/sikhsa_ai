#!/usr/bin/env python
"""
Cache Warming Script
Location: backend/scripts/warm_up_cache.py
"""

import asyncio
import argparse
from pathlib import Path
import sys
import random

sys.path.append(str(Path(__file__).parent.parent))

from src.cache.redis_client import RedisClient
from src.cache.response_cache import ResponseCache
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Sample common questions by subject
SAMPLE_QUESTIONS = {
    "mathematics": [
        "What is the quadratic formula?",
        "How do you calculate area of a circle?",
        "What is the Pythagorean theorem?",
        "How do you solve linear equations?",
        "What are prime numbers?"
    ],
    "science": [
        "What is photosynthesis?",
        "How do plants grow?",
        "What is the water cycle?",
        "What are the states of matter?",
        "How does gravity work?"
    ],
    "history": [
        "Who was Mahatma Gandhi?",
        "When did World War 2 end?",
        "What is the Indus Valley Civilization?",
        "Who invented the telephone?",
        "What was the Industrial Revolution?"
    ]
}

async def warm_up_cache(subject: str, grade: int, num_queries: int = 10):
    """
    Warm up cache with sample queries
    """
    logger.info(f"Warming up cache for {subject} grade {grade}")
    
    cache = ResponseCache()
    
    questions = SAMPLE_QUESTIONS.get(subject, SAMPLE_QUESTIONS["mathematics"])
    
    # Generate sample queries
    for i in range(min(num_queries, len(questions))):
        query = questions[i]
        
        # Create sample response
        sample_response = {
            "response": f"This is a sample response for: {query}",
            "model": "gpt-3.5-turbo",
            "tokens_saved": random.randint(100, 500),
            "optimization": {
                "savings_percentage": random.randint(40, 80)
            }
        }
        
        # Cache it
        cache_key = cache.generate_key(query, f"student_{i}", grade)
        await cache.set(cache_key, sample_response)
        
        logger.debug(f"Cached: {query[:50]}...")
    
    logger.info(f"Cached {num_queries} sample queries for {subject}")

async def main():
    parser = argparse.ArgumentParser(description="Warm up cache")
    parser.add_argument("--subject", type=str, default="mathematics", help="Subject")
    parser.add_argument("--grade", type=int, default=7, help="Grade level")
    parser.add_argument("--num-queries", type=int, default=10, help="Number of queries")
    
    args = parser.parse_args()
    
    await warm_up_cache(args.subject, args.grade, args.num_queries)

if __name__ == "__main__":
    asyncio.run(main())