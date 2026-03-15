"""
GPT-3.5 Turbo Provider
Location: backend/src/llm/providers/gpt3_turbo.py
"""

from typing import Dict, Any, Optional
import openai
from ...utils.logger import get_logger
from ...config.settings import config

logger = get_logger(__name__)

class GPT3Turbo:
    """
    GPT-3.5 Turbo provider (cost-effective)
    """
    
    def __init__(self):
        self.model_name = "gpt-3.5-turbo"
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using GPT-3.5 Turbo
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful tutor for students in rural India. Provide clear, concise answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=kwargs.get("max_tokens", 500)
            )
            
            return {
                "text": response.choices[0].message.content,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"GPT-3.5 error: {str(e)}")
            raise