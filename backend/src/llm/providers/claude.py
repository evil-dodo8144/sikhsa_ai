"""
Claude Provider (Backup)
Location: backend/src/llm/providers/claude.py
"""

from typing import Dict, Any, Optional
import anthropic
from ...utils.logger import get_logger
from ...config.settings import config

logger = get_logger(__name__)

class ClaudeProvider:
    """
    Claude provider (backup for when OpenAI is unavailable)
    """
    
    def __init__(self):
        self.model_name = "claude-instant"
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using Claude
        """
        try:
            response = self.client.messages.create(
                model="claude-instant-1",
                max_tokens=kwargs.get("max_tokens", 1000),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "text": response.content[0].text,
                "model": self.model_name,
                "usage": {
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Claude error: {str(e)}")
            raise