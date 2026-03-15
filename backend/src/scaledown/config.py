"""
ScaleDown Configuration
Location: backend/src/scaledown/config.py
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ScaleDownConfig:
    """Configuration for ScaleDown integration"""
    
    # API Settings
    api_key: str
    api_url: str = "https://api.scaledown.ai/v1"
    timeout: int = 2
    max_retries: int = 3
    
    # Compression Settings
    default_compression: str = "aggressive"
    preserve_semantics: bool = True
    
    # Model-specific settings
    model_configs: Dict[str, Dict[str, Any]] = None
    
    # Cache Settings
    cache_enabled: bool = True
    cache_max_size: int = 10000
    cache_ttl: int = 3600  # 1 hour
    
    # Tier Settings
    tier_compression: Dict[str, str] = None
    
    def __post_init__(self):
        if self.model_configs is None:
            self.model_configs = {
                "gpt-4": {
                    "compression": "conservative",
                    "max_tokens": 4000,
                    "min_savings": 0.3
                },
                "gpt-3.5-turbo": {
                    "compression": "aggressive",
                    "max_tokens": 2000,
                    "min_savings": 0.5
                },
                "claude-instant": {
                    "compression": "balanced",
                    "max_tokens": 3000,
                    "min_savings": 0.4
                }
            }
        
        if self.tier_compression is None:
            self.tier_compression = {
                "free": "maximum",
                "basic": "aggressive",
                "premium": "balanced",
                "enterprise": "light"
            }