"""
Data Validation Utilities
Location: backend/src/utils/validators.py
"""

import re
from typing import Optional

def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_grade(grade: int) -> bool:
    """
    Validate grade level (1-12)
    """
    return 1 <= grade <= 12

def validate_student_id(student_id: str) -> bool:
    """
    Validate student ID format
    """
    # Alphanumeric, 5-20 chars
    return re.match(r'^[a-zA-Z0-9]{5,20}$', student_id) is not None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input
    """
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove any script tags
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_query_length(query: str, min_length: int = 3, max_length: int = 500) -> bool:
    """
    Validate query length
    """
    return min_length <= len(query.strip()) <= max_length