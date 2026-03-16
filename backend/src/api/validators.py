"""
Input Validation
Location: backend/src/api/validators.py
"""

from typing import Dict, Any, Optional, List
from fastapi import HTTPException
import re
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_query(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate query input from student
    """
    errors = []
    
    # Check required fields
    if "query" not in data:
        errors.append("Query is required")
    
    query = data.get("query", "").strip()
    
    # Validate query length
    if len(query) < 3:
        errors.append("Query too short (minimum 3 characters)")
    
    if len(query) > 1000:
        errors.append("Query too long (maximum 1000 characters)")
    
    # Sanitize query - remove dangerous characters
    query = re.sub(r'[<>{}()\[\]\\]', '', query)
    
    # Validate grade
    grade = data.get("grade", 7)
    if grade is not None:
        try:
            grade = int(grade)
            if grade < 1 or grade > 12:
                errors.append("Grade must be between 1 and 12")
        except (ValueError, TypeError):
            errors.append("Grade must be a number")
    
    # Validate subject
    subject = data.get("subject", "general")
    valid_subjects = [
        "mathematics", "science", "english", "history", 
        "geography", "computer_science", "general"
    ]
    if subject not in valid_subjects:
        errors.append(f"Subject must be one of: {', '.join(valid_subjects)}")
    
    # Validate student tier
    tier = data.get("tier", "free")
    valid_tiers = ["free", "basic", "premium", "enterprise"]
    if tier not in valid_tiers:
        errors.append(f"Tier must be one of: {', '.join(valid_tiers)}")
    
    # Validate student ID if provided
    student_id = data.get("student_id")
    if student_id and not re.match(r'^[a-zA-Z0-9_-]{5,50}$', student_id):
        errors.append("Student ID must be alphanumeric, 5-50 characters")
    
    # Raise error if any validation failed
    if errors:
        logger.warning(f"Validation errors: {errors}")
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # Return validated data
    return {
        "query": query,
        "grade": grade,
        "subject": subject,
        "student_id": student_id or f"anonymous_{int(datetime.utcnow().timestamp())}",
        "tier": tier,
        "metadata": data.get("metadata", {})
    }


def validate_student(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate student registration data
    """
    errors = []
    
    # Required fields
    required_fields = ["student_id", "grade"]
    for field in required_fields:
        if field not in data:
            errors.append(f"{field} is required")
    
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # Validate student ID
    student_id = data["student_id"]
    if not re.match(r'^[a-zA-Z0-9_-]{5,50}$', student_id):
        errors.append("Student ID must be alphanumeric, 5-50 characters")
    
    # Validate grade
    try:
        grade = int(data["grade"])
        if grade < 1 or grade > 12:
            errors.append("Grade must be between 1 and 12")
    except (ValueError, TypeError):
        errors.append("Grade must be a number")
    
    # Validate name if provided
    name = data.get("name", "")
    if name and len(name) > 100:
        errors.append("Name too long (maximum 100 characters)")
    
    # Validate email if provided
    email = data.get("email")
    if email and not validate_email(email):
        errors.append("Invalid email format")
    
    # Validate preferences
    preferences = data.get("preferences", {})
    valid_prefs = validate_preferences(preferences)
    
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    return {
        "student_id": student_id,
        "grade": grade,
        "name": name or f"Student_{student_id}",
        "email": email,
        "school": data.get("school", ""),
        "preferences": valid_prefs,
        "created_at": datetime.utcnow().isoformat()
    }


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_preferences(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user preferences"""
    valid_prefs = {}
    
    # Theme
    theme = prefs.get("theme", "light")
    if theme in ["light", "dark", "auto"]:
        valid_prefs["theme"] = theme
    
    # Font size
    font_size = prefs.get("font_size", "medium")
    if font_size in ["small", "medium", "large"]:
        valid_prefs["font_size"] = font_size
    
    # Language
    language = prefs.get("language", "en")
    if language in ["en", "hi", "te", "ta", "bn", "mr"]:
        valid_prefs["language"] = language
    
    # Notifications
    if "notifications" in prefs:
        valid_prefs["notifications"] = bool(prefs["notifications"])
    
    return valid_prefs


def validate_textbook_ingest(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate textbook ingestion request"""
    errors = []
    
    # Required fields
    required = ["path", "subject", "grade"]
    for field in required:
        if field not in data:
            errors.append(f"{field} is required")
    
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # Validate path
    path = data["path"]
    if not path.endswith('.pdf'):
        errors.append("File must be a PDF")
    
    # Validate subject
    subject = data["subject"]
    valid_subjects = [
        "mathematics", "science", "english", "history", 
        "geography", "computer_science"
    ]
    if subject not in valid_subjects:
        errors.append(f"Subject must be one of: {', '.join(valid_subjects)}")
    
    # Validate grade
    try:
        grade = int(data["grade"])
        if grade < 1 or grade > 12:
            errors.append("Grade must be between 1 and 12")
    except (ValueError, TypeError):
        errors.append("Grade must be a number")
    
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    return {
        "path": path,
        "subject": subject,
        "grade": grade,
        "title": data.get("title", ""),
        "overwrite": data.get("overwrite", False)
    }


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    
    # Remove dangerous characters
    text = re.sub(r'[<>{}()\[\]\\]', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_pagination(page: int, page_size: int) -> tuple:
    """Validate pagination parameters"""
    if page < 1:
        page = 1
    
    if page_size < 1:
        page_size = 10
    elif page_size > 100:
        page_size = 100
    
    return page, page_size