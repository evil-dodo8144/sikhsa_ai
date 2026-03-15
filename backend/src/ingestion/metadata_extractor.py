"""
Metadata Extractor for Textbooks
Location: backend/src/ingestion/metadata_extractor.py
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MetadataExtractor:
    """Extract grade, subject, and other metadata from textbooks"""
    
    def __init__(self):
        self.grade_patterns = [
            (r'grade\s*(\d+)', 1),
            (r'class\s*(\d+)', 1),
            (r'standard\s*(\d+)', 1),
            (r'(\d+)(?:st|nd|rd|th)\s+grade', 1)
        ]
        
        self.subject_keywords = {
            'mathematics': ['math', 'algebra', 'geometry', 'calculus', 'arithmetic'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'experiment'],
            'english': ['english', 'grammar', 'literature', 'writing'],
            'history': ['history', 'historical', 'civilization', 'world war'],
            'geography': ['geography', 'map', 'continent', 'country'],
            'computer_science': ['computer', 'programming', 'coding', 'algorithm']
        }
    
    async def extract(self, pdf_path: str, content: str) -> Dict[str, Any]:
        """
        Extract all metadata from textbook
        """
        metadata = {
            'file_name': pdf_path.split('/')[-1],
            'extracted_at': datetime.utcnow().isoformat(),
            'grade': await self._extract_grade(content),
            'subject': await self._extract_subject(content),
            'title': await self._extract_title(content),
            'estimated_pages': len(content) // 3000,  # Rough estimate
            'language': await self._detect_language(content)
        }
        
        logger.info(f"Extracted metadata: Grade {metadata['grade']}, Subject {metadata['subject']}")
        return metadata
    
    async def _extract_grade(self, content: str) -> Optional[int]:
        """Extract grade level from content"""
        first_500 = content[:5000].lower()
        
        for pattern, group in self.grade_patterns:
            match = re.search(pattern, first_500)
            if match:
                try:
                    return int(match.group(group))
                except:
                    pass
        
        # Default based on content complexity (simple heuristic)
        avg_word_length = len(content.split()) / max(len(content), 1)
        if avg_word_length < 5:
            return 6  # Elementary
        elif avg_word_length < 7:
            return 9  # Middle school
        else:
            return 11  # High school
    
    async def _extract_subject(self, content: str) -> str:
        """Extract subject area"""
        content_lower = content.lower()
        scores = {}
        
        for subject, keywords in self.subject_keywords.items():
            score = 0
            for keyword in keywords:
                score += content_lower.count(keyword) * len(keyword)
            scores[subject] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    async def _extract_title(self, content: str) -> str:
        """Extract textbook title"""
        first_line = content.split('\n')[0] if content else ''
        return first_line[:100].strip()
    
    async def _detect_language(self, content: str) -> str:
        """Detect language of content"""
        try:
            from langdetect import detect
            return detect(content[:1000])
        except:
            return 'en'  # Default to English