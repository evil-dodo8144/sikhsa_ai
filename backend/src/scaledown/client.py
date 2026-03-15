"""
ScaleDown API Client
Location: backend/src/scaledown/client.py
"""

import requests
import hashlib
import hmac
import time
import json
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ScaleDownClient:
    """
    Client for ScaleDown API - reduces token usage by 40-80%
    Features:
    - Smart prompt compression using NLP
    - Model-specific tuning (GPT-4, Claude, GPT-3.5)
    - Real-time optimization with 5x faster processing
    - Token-aware compression for maximum savings
    """
    
    def __init__(self, api_key: str, api_url: str = "https://api.scaledown.ai/v1", timeout: int = 2):
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ScaleDown-Tutor/1.0",
            "Accept": "application/json"
        })
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def optimize_prompt(self, 
                        prompt: str, 
                        model: str = "gpt-3.5-turbo",
                        compression_level: str = "aggressive",
                        max_tokens: Optional[int] = None,
                        preserve_semantics: bool = True,
                        request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send prompt to ScaleDown for optimization (synchronous version)
        
        Args:
            prompt: Original prompt to optimize
            model: Target model (gpt-4, gpt-3.5-turbo, claude-instant)
            compression_level: aggressive, balanced, conservative
            max_tokens: Maximum tokens in output
            preserve_semantics: Ensure educational quality
            request_id: Optional request ID for tracking
            
        Returns:
            Dict with optimized prompt and metrics
        """
        # Generate request ID if not provided
        if not request_id:
            request_id = hashlib.md5(f"{prompt}{time.time()}".encode()).hexdigest()[:16]
        
        # Generate signature for request validation
        signature = self._generate_signature(prompt, request_id)
        
        payload = {
            "prompt": prompt,
            "target_model": model,
            "compression_level": compression_level,
            "preserve_semantics": preserve_semantics,
            "max_tokens": max_tokens,
            "timestamp": int(time.time()),
            "request_id": request_id
        }
        
        headers = {
            "X-Signature": signature,
            "X-Request-ID": request_id
        }
        
        try:
            logger.debug(f"Sending prompt to ScaleDown API. Length: {len(prompt)} chars, Model: {model}")
            
            response = self.session.post(
                f"{self.api_url}/optimize",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate savings
                original_tokens = data.get("original_tokens", len(prompt) // 4)
                optimized_tokens = data.get("optimized_tokens", len(data.get("optimized_prompt", "")) // 4)
                savings = ((original_tokens - optimized_tokens) / original_tokens * 100) if original_tokens > 0 else 0
                
                logger.info(f"ScaleDown optimization complete. Saved {savings:.1f}% tokens")
                
                return {
                    "optimized_prompt": data.get("optimized_prompt", prompt),
                    "original_tokens": original_tokens,
                    "optimized_tokens": optimized_tokens,
                    "savings_percentage": savings,
                    "processing_time_ms": data.get("processing_time_ms", 0),
                    "model_used": model,
                    "compression_level": compression_level,
                    "request_id": request_id,
                    "success": True,
                    "cached": data.get("cached", False)
                }
            else:
                error_msg = f"ScaleDown API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                logger.error(error_msg)
                return {
                    "optimized_prompt": prompt,  # Fallback to original
                    "error": error_msg,
                    "success": False,
                    "savings_percentage": 0,
                    "request_id": request_id
                }
                
        except requests.exceptions.Timeout:
            logger.warning(f"ScaleDown API timeout after {self.timeout}s")
            return {
                "optimized_prompt": prompt,
                "error": "timeout",
                "success": False,
                "savings_percentage": 0,
                "request_id": request_id
            }
        except requests.exceptions.ConnectionError:
            logger.warning("ScaleDown API connection error")
            return {
                "optimized_prompt": prompt,
                "error": "connection_error",
                "success": False,
                "savings_percentage": 0,
                "request_id": request_id
            }
        except Exception as e:
            logger.error(f"ScaleDown API exception: {str(e)}")
            return {
                "optimized_prompt": prompt,
                "error": str(e),
                "success": False,
                "savings_percentage": 0,
                "request_id": request_id
            }
    
    async def optimize_prompt_async(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Async wrapper for optimize_prompt
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.optimize_prompt, *args, **kwargs)
    
    def _generate_signature(self, prompt: str, request_id: str) -> str:
        """Generate HMAC signature for request validation"""
        timestamp = str(int(time.time()))
        message = f"{prompt[:100]}{request_id}{timestamp}".encode()
        signature = hmac.new(
            self.api_key.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}.{signature[:16]}"
    
    def batch_optimize(self, 
                       prompts: List[str],
                       model: str = "gpt-3.5-turbo",
                       compression_level: str = "aggressive") -> List[Dict[str, Any]]:
        """
        Optimize multiple prompts in batch
        """
        results = []
        for prompt in prompts:
            result = self.optimize_prompt(prompt, model, compression_level)
            results.append(result)
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        try:
            response = self.session.get(
                f"{self.api_url}/usage",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            return {"error": "Unable to fetch usage stats"}
        except Exception as e:
            logger.error(f"Error fetching usage stats: {str(e)}")
            return {"error": str(e)}