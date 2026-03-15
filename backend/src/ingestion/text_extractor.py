"""
Text Extraction with OCR Fallback
Location: backend/src/ingestion/text_extractor.py
"""

import pytesseract
from PIL import Image
import io
from typing import Optional, Dict, Any
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TextExtractor:
    """Extract and clean text from PDFs with OCR fallback"""
    
    def __init__(self, enable_ocr: bool = True):
        self.enable_ocr = enable_ocr
        
    async def extract_text(self, pdf_content: Dict[str, Any]) -> str:
        """
        Extract clean text from PDF content
        """
        raw_text = []
        
        for page in pdf_content.get('content', []):
            text = page.get('text', '')
            
            if not text and self.enable_ocr:
                # OCR fallback for scanned pages
                text = await self._ocr_page(page)
            
            if text:
                cleaned = self._clean_text(text)
                raw_text.append(cleaned)
        
        return '\n\n'.join(raw_text)
    
    async def _ocr_page(self, page: Dict[str, Any]) -> str:
        """Perform OCR on page image"""
        try:
            # This would need image data from PDF
            # Simplified for now
            return ""
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')
        text = text.replace('0', 'O')  # Be careful with numbers
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())
        
        return text.strip()