"""
Chapter-Level Indexer
Location: backend/src/indexing/chapter_indexer.py
"""

import numpy as np
from typing import List, Dict, Any, Optional
import hashlib
from .embedding_generator import EmbeddingGenerator
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ChapterIndexer:
    """Create and manage chapter-level embeddings"""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        
    async def index(self, 
                   chapters: List[Dict],
                   subject: str,
                   grade: int) -> List[Dict[str, Any]]:
        """
        Create embeddings for each chapter
        """
        indexed_chapters = []
        
        for i, chapter in enumerate(chapters):
            # Create embedding from chapter content
            chapter_text = f"{chapter.get('title', '')} {chapter.get('summary', '')}"
            
            if chapter.get('sections'):
                for section in chapter.get('sections', [])[:3]:
                    chapter_text += f" {section.get('title', '')}"
                    chapter_text += ' '.join(section.get('content', [])[:5])
            
            # Generate embedding
            embedding = await self.embedding_generator.generate(chapter_text)
            
            # Create index entry
            chapter_id = hashlib.md5(f"{subject}{grade}{i}".encode()).hexdigest()[:16]
            
            indexed_chapters.append({
                'id': chapter_id,
                'title': chapter.get('title', f'Chapter {i+1}'),
                'embedding': embedding.tolist(),
                'page_start': chapter.get('page_start', 1),
                'page_end': chapter.get('page_end', 1),
                'summary': chapter.get('summary', ''),
                'grade_level': grade,
                'subject': subject,
                'token_count': len(chapter_text.split())
            })
        
        logger.info(f"Indexed {len(indexed_chapters)} chapters")
        return indexed_chapters
    
    async def search(self,
                    query_embedding: np.ndarray,
                    chapters: List[Dict],
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search chapters by similarity
        """
        results = []
        
        for chapter in chapters:
            chapter_emb = np.array(chapter.get('embedding', []))
            if chapter_emb.size == 0:
                continue
            
            # Cosine similarity
            similarity = np.dot(query_embedding, chapter_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chapter_emb) + 1e-8
            )
            
            results.append({
                **chapter,
                'similarity': float(similarity),
                'type': 'chapter'
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]