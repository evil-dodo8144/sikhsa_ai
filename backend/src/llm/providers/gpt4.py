"""
GPT-4 Provider (Premium)
Location: backend/src/llm/providers/gpt4.py
"""

from typing import Dict, Any, Optional
import openai
from ...utils.logger import get_logger
from ...config.settings import config

logger = get_logger(__name__)

class GPT4:
    """
    GPT-4 provider (premium, fallback only)
    """
    
    def __init__(self):
        self.model_name = "gpt-4"
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using GPT-4
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert tutor for students. Provide detailed, accurate explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            
            return {
                "text": response.choices[0].message.content,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "confidence": 0.95
            }
            
        except Exception as e:
            logger.error(f"GPT-4 error: {str(e)}")
            raise