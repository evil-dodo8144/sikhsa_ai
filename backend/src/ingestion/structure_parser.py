"""
Chapter/Section Structure Parser
Location: backend/src/ingestion/structure_parser.py
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Chapter:
    id: str
    title: str
    page_start: int
    page_end: int
    sections: List[Dict]
    summary: str = ""

class StructureParser:
    """Parse textbook structure into chapters and sections"""
    
    def __init__(self):
        self.chapter_patterns = [
            (r'chapter\s+(\d+)[:\s]+(.*)', 'chapter'),
            (r'unit\s+(\d+)[:\s]+(.*)', 'unit'),
            (r'lesson\s+(\d+)[:\s]+(.*)', 'lesson'),
            (r'module\s+(\d+)[:\s]+(.*)', 'module'),
            (r'^\d+\.\s+(.*)', 'numbered')  # 1. Title format
        ]
        
        self.section_patterns = [
            (r'^\d+\.\d+\s+(.*)', 'subsection'),
            (r'^[A-Z]\.\s+(.*)', 'lettered')
        ]
    
    async def parse(self, content: List[Dict]) -> List[Chapter]:
        """
        Parse full textbook content into chapters
        """
        chapters = []
        current_chapter = None
        current_section = None
        
        for page in content:
            text = page['text']
            lines = text.split('\n')
            page_num = page['page_num']
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check for chapter headers
                chapter_match = self._match_pattern(line, self.chapter_patterns)
                if chapter_match:
                    if current_chapter:
                        current_chapter.page_end = page_num - 1
                        chapters.append(current_chapter)
                    
                    current_chapter = Chapter(
                        id=f"ch{len(chapters)+1}",
                        title=chapter_match['title'],
                        page_start=page_num,
                        page_end=page_num,
                        sections=[]
                    )
                    continue
                
                # Check for sections within chapter
                if current_chapter:
                    section_match = self._match_pattern(line, self.section_patterns)
                    if section_match:
                        current_section = {
                            'title': section_match['title'],
                            'page': page_num,
                            'content': []
                        }
                        current_chapter.sections.append(current_section)
                    
                    # Add content to current section or chapter
                    if current_section:
                        current_section['content'].append(line)
                    else:
                        # Might be chapter intro text
                        if not hasattr(current_chapter, 'intro'):
                            current_chapter.intro = []
                        current_chapter.intro.append(line)
        
        # Add last chapter
        if current_chapter:
            current_chapter.page_end = content[-1]['page_num']
            chapters.append(current_chapter)
        
        # Generate summaries
        for chapter in chapters:
            chapter.summary = await self._generate_summary(chapter)
        
        logger.info(f"Parsed {len(chapters)} chapters")
        return chapters
    
    def _match_pattern(self, text: str, patterns: List) -> Optional[Dict]:
        """Match text against patterns"""
        text_lower = text.lower()
        
        for pattern, pattern_type in patterns:
            match = re.match(pattern, text_lower)
            if match:
                groups = match.groups()
                if pattern_type == 'numbered':
                    return {'title': groups[0], 'type': pattern_type}
                elif len(groups) == 2:
                    return {'number': groups[0], 'title': groups[1], 'type': pattern_type}
                else:
                    return {'title': groups[0], 'type': pattern_type}
        
        return None
    
    async def _generate_summary(self, chapter: Chapter) -> str:
        """Generate brief chapter summary"""
        # Simple extractive summary - first few sentences
        all_text = []
        if hasattr(chapter, 'intro'):
            all_text.extend(chapter.intro)
        
        for section in chapter.sections:
            all_text.extend(section.get('content', [])[:3])  # First 3 lines of each section
        
        summary = ' '.join(all_text)[:500]  # First 500 chars
        return summary + '...' if len(summary) == 500 else summary