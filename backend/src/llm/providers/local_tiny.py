"""
Local Tiny Model Provider (Free)
Location: backend/src/llm/providers/local_tiny.py
"""

from typing import Dict, Any, Optional
import random
from ...utils.logger import get_logger

logger = get_logger(__name__)

class LocalTinyModel:
    """
    Tiny local model for simple queries
    Completely free, runs offline
    """
    
    def __init__(self):
        self.model_name = "local-tiny"
        self.is_loaded = False
        
    async def load(self):
        """Load the model (simplified)"""
        if not self.is_loaded:
            logger.info("Loading local tiny model...")
            # In production, load actual model here
            self.is_loaded = True
    
    async def generate(self, prompt: str) -> Dict[str, Any]:
        """
        Generate response using local model
        """
        await self.load()
        
        # Simple response generation for demo
        # In production, use actual model inference
        prompt_lower = prompt.lower()
        
        # Very simple pattern matching for demo
        if "what is" in prompt_lower:
            topic = prompt_lower.replace("what is", "").strip()
            response = f"{topic.capitalize()} is a concept in your textbook. For a complete answer, please connect to the internet."
        elif "how to" in prompt_lower:
            response = "I can help with that when you're online. For now, check your textbook chapter."
        elif "hello" in prompt_lower or "hi" in prompt_lower:
            response = "Hello! I'm your AI tutor. I can answer questions when you're online."
        else:
            response = "I understand your question. Please connect to the internet for a detailed answer."
        
        return {
            "text": response,
            "model": self.model_name,
            "confidence": 0.6,
            "sources": []
        }