"""
Fallback Handler for ScaleDown API Failures
Location: backend/src/scaledown/fallback.py
"""

import re
from typing import Dict, Any, Optional
from ..utils.logger import get_logger
from ..utils.text_utils import count_tokens

logger = get_logger(__name__)

class FallbackHandler:
    """
    Handles cases when ScaleDown API fails
    Provides local compression strategies
    """
    
    def __init__(self):
        self.fallback_count = 0
        
    def optimize(self, 
                base_prompt: str,
                model: str = "gpt-3.5-turbo",
                compression_level: str = "aggressive") -> Dict[str, Any]:
        """
        Local fallback optimization when API fails
        """
        self.fallback_count += 1
        logger.warning(f"Using fallback optimization #{self.fallback_count}")
        
        original_tokens = count_tokens(base_prompt)
        
        # Apply different compression strategies based on level
        if compression_level == "aggressive":
            optimized = self._aggressive_compress(base_prompt)
        elif compression_level == "balanced":
            optimized = self._balanced_compress(base_prompt)
        else:
            optimized = self._light_compress(base_prompt)
        
        optimized_tokens = count_tokens(optimized)
        savings = ((original_tokens - optimized_tokens) / original_tokens * 100) if original_tokens > 0 else 0
        
        return {
            "optimized_prompt": optimized,
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "savings_percentage": savings,
            "processing_time_ms": 10,  # Local processing is fast
            "model_used": model,
            "compression_level": compression_level,
            "success": True,
            "fallback": True
        }
    
    def _aggressive_compress(self, prompt: str) -> str:
        """
        Aggressive compression (target 60-80% savings)
        """
        # Remove all comments and extra whitespace
        lines = prompt.split('\n')
        compressed = []
        
        for line in lines:
            # Remove lines that are just instructions
            if any(word in line.lower() for word in ['context:', 'question:', 'answer:']):
                # Keep structure but compress
                line = re.sub(r'\s+', ' ', line.strip())
                if line:
                    compressed.append(line)
            elif len(line.strip()) > 20:  # Keep substantive lines
                line = re.sub(r'\s+', ' ', line.strip())
                compressed.append(line)
        
        # Join with single newlines
        result = '\n'.join(compressed)
        
        # Remove redundant words
        result = re.sub(r'\b(?:the|a|an|this|that|these|those)\s+', '', result)
        
        return result
    
    def _balanced_compress(self, prompt: str) -> str:
        """
        Balanced compression (target 40-60% savings)
        """
        # Remove extra whitespace
        lines = prompt.split('\n')
        compressed = [re.sub(r'\s+', ' ', line.strip()) for line in lines if line.strip()]
        return '\n'.join(compressed)
    
    def _light_compress(self, prompt: str) -> str:
        """
        Light compression (target 20-40% savings)
        """
        # Just remove extra whitespace and empty lines
        lines = prompt.split('\n')
        compressed = [line.strip() for line in lines if line.strip()]
        return '\n'.join(compressed)
    
    def get_fallback_count(self) -> int:
        """Get number of fallback operations"""
        return self.fallback_count