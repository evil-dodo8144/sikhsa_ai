"""
Query Parser - Parse and normalize student queries
Location: backend/src/query/query_parser.py
"""

import re
from typing import Dict, Any, List
from ..utils.logger import get_logger
from ..utils.text_utils import normalize_text

logger = get_logger(__name__)

class QueryParser:
    """Parse and normalize student queries"""
    
    def __init__(self):
        self.question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'which']
        self.stop_words = ['a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at']
        
    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parse query into structured format
        """
        # Normalize text
        normalized = normalize_text(query)
        
        # Extract basic info
        words = normalized.split()
        word_count = len(words)
        
        # Detect question type
        question_type = self._detect_question_type(normalized)
        
        # Extract keywords (remove stop words)
        keywords = [w for w in words if w.lower() not in self.stop_words and len(w) > 2]
        
        # Check for mathematical expressions
        has_math = self._detect_math(normalized)
        
        # Check for code (for CS subjects)
        has_code = self._detect_code(normalized)
        
        parsed = {
            'original': query,
            'normalized': normalized,
            'words': words,
            'word_count': word_count,
            'question_type': question_type,
            'keywords': keywords,
            'has_math': has_math,
            'has_code': has_code,
            'complexity': self._calculate_complexity(word_count, keywords)
        }
        
        logger.debug(f"Parsed query: {parsed['question_type']} - {word_count} words")
        return parsed
    
    def _detect_question_type(self, text: str) -> str:
        """Detect if query is a question and what type"""
        text_lower = text.lower()
        
        # Check if it's a question
        if text_lower.startswith(tuple(self.question_words)) or text_lower.endswith('?'):
            for q_word in self.question_words:
                if text_lower.startswith(q_word):
                    return f"question_{q_word}"
            return "question_general"
        return "statement"
    
    def _detect_math(self, text: str) -> bool:
        """Detect mathematical expressions"""
        math_patterns = [
            r'\d+\s*[+\-*/]\s*\d+',  # Basic operations
            r'=',                       # Equals sign
            r'\b(solve|calculate|compute|find)\b',  # Math verbs
            r'\b(equation|formula|theorem)\b'  # Math terms
        ]
        
        for pattern in math_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _detect_code(self, text: str) -> bool:
        """Detect code-related queries"""
        code_patterns = [
            r'\b(print|if|else|for|while|function|class|import)\b',
            r'[{}()\[\]=<>]',  # Code symbols
            r'\b(code|program|function|method)\b'
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _calculate_complexity(self, word_count: int, keywords: List[str]) -> str:
        """Calculate query complexity"""
        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "medium"
        else:
            return "complex"