"""
System Constants
Location: backend/config/constants.py
"""

class Constants:
    """System-wide constants"""
    
    # Student tiers
    TIERS = ["free", "basic", "premium", "enterprise"]
    
    # Subjects
    SUBJECTS = [
        "mathematics", "science", "english", "history", 
        "geography", "computer_science", "general"
    ]
    
    # Grade levels
    MIN_GRADE = 1
    MAX_GRADE = 12
    
    # HTTP Status codes
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_429_TOO_MANY_REQUESTS = 429
    HTTP_500_INTERNAL_ERROR = 500
    
    # Cache TTLs (seconds)
    CACHE_TTL_SHORT = 300  # 5 minutes
    CACHE_TTL_MEDIUM = 3600  # 1 hour
    CACHE_TTL_LONG = 86400  # 24 hours
    
    # Rate limits (requests per minute)
    RATE_LIMIT_FREE = 5
    RATE_LIMIT_BASIC = 20
    RATE_LIMIT_PREMIUM = 60
    RATE_LIMIT_ENTERPRISE = 200
    
    # Token limits
    MAX_TOKENS_LOCAL = 500
    MAX_TOKENS_GPT3 = 2000
    MAX_TOKENS_GPT4 = 4000
    MAX_TOKENS_CLAUDE = 3000
    
    # File size limits
    MAX_TEXTBOOK_SIZE_MB = 100
    MAX_EMBEDDING_SIZE_MB = 10