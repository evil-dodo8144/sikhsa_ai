"""
PDF Textbook Processor
Location: backend/src/ingestion/pdf_processor.py
"""

import PyPDF2
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PDFProcessor:
    """Extract text and structure from PDF textbooks"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        
    async def extract(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract all content from PDF textbook
        """
        logger.info(f"Extracting text from: {pdf_path}")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            # Use pdfplumber for better text extraction
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                content = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        content.append({
                            'page_num': page_num,
                            'text': text,
                            'tables': page.extract_tables() if page.extract_tables() else []
                        })
                    
                    if page_num % 10 == 0:
                        logger.debug(f"Processed {page_num}/{total_pages} pages")
                
                return {
                    'file_name': Path(pdf_path).name,
                    'total_pages': total_pages,
                    'content': content,
                    'metadata': self._extract_metadata(pdf)
                }
                
        except Exception as e:
            logger.error(f"Error extracting PDF: {str(e)}")
            raise
    
    def _extract_metadata(self, pdf) -> Dict[str, Any]:
        """Extract PDF metadata"""
        metadata = pdf.metadata or {}
        return {
            'title': metadata.get('/Title', ''),
            'author': metadata.get('/Author', ''),
            'subject': metadata.get('/Subject', ''),
            'keywords': metadata.get('/Keywords', ''),
            'creator': metadata.get('/Creator', '')
        }
    
    async def extract_structure(self, content: List[Dict]) -> Dict[str, Any]:
        """
        Extract chapter/section structure from content
        """
        structure = {
            'chapters': [],
            'sections': [],
            'subsections': []
        }
        
        # Common chapter patterns
        chapter_patterns = [
            r'chapter\s+\d+',
            r'unit\s+\d+',
            r'lesson\s+\d+',
            r'module\s+\d+'
        ]
        
        import re
        current_chapter = None
        
        for page in content:
            text = page['text']
            lines = text.split('\n')
            
            for line in lines[:10]:  # Check first 10 lines of each page
                line = line.strip().lower()
                
                for pattern in chapter_patterns:
                    if re.match(pattern, line):
                        current_chapter = {
                            'title': line,
                            'page': page['page_num'],
                            'sections': []
                        }
                        structure['chapters'].append(current_chapter)
                        break
        
        logger.info(f"Found {len(structure['chapters'])} chapters")
        return structure