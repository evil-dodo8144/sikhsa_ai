"""
Main Configuration
Location: backend/config/settings.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""
    
    # ScaleDown API
    SCALEDOWN_API_KEY = os.getenv("SCALEDOWN_API_KEY", "")
    SCALEDOWN_API_URL = os.getenv("SCALEDOWN_API_URL", "https://api.scaledown.ai/v1")
    SCALEDOWN_TIMEOUT = int(os.getenv("SCALEDOWN_TIMEOUT", "2"))
    SCALEDOWN_COMPRESSION_LEVEL = os.getenv("SCALEDOWN_COMPRESSION_LEVEL", "aggressive")
    SCALEDOWN_TIER = os.getenv("SCALEDOWN_TIER", "free")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tutor.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # LLM API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Application
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
    
    # Performance
    MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "1000"))
    DEFAULT_STUDENT_TIER = os.getenv("DEFAULT_STUDENT_TIER", "free")
    MAX_TOKENS_PER_QUERY = int(os.getenv("MAX_TOKENS_PER_QUERY", "2000"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # File Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    TEXTBOOK_DIR = Path(os.getenv("TEXTBOOK_DIR", str(DATA_DIR / "textbooks")))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", str(DATA_DIR / "cache")))
    MODEL_DIR = Path(os.getenv("MODEL_DIR", str(DATA_DIR / "models")))
    LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
    
    # Pruning Settings
    SEMANTIC_THRESHOLD = 0.3
    GRADE_TOLERANCE = 1
    MAX_CONTEXT_TOKENS = 2000
    RECENCY_DECAY = 0.1
    
    # Create directories
    for path in [DATA_DIR, TEXTBOOK_DIR, CACHE_DIR, MODEL_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)

config = Config()