"""
Text Processing Utilities
Location: backend/src/utils/text_utils.py
"""

import re
from typing import List, Set
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def count_tokens(text: str) -> int:
    """
    Approximate token count (1 token ≈ 4 chars for English)
    """
    return len(text) // 4

def normalize_text(text: str) -> str:
    """
    Normalize text: lowercase, remove extra spaces, etc.
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\?\-,]', '', text)
    
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text
    """
    # Tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    keywords = [t for t in tokens if t.isalnum() and t not in stop_words and len(t) > 2]
    
    # Count frequencies
    freq = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1
    
    # Sort by frequency
    sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in sorted_keywords[:max_keywords]]

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
    """
    Truncate text to max length
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length].rsplit(' ', 1)[0]
    if add_ellipsis:
        truncated += '...'
    
    return truncated