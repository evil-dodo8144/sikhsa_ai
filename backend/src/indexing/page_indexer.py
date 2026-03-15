"""
Page-Level Indexer
Location: backend/src/indexing/page_indexer.py
"""

import numpy as np
from typing import List, Dict, Any, Optional
import hashlib
from .embedding_generator import EmbeddingGenerator
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PageIndexer:
    """Create page-level mappings and embeddings"""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        
    async def index(self,
                   content: str,
                   structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create page-level index
        """
        pages = []
        
        # Split into pages (simplified - in reality would use actual page breaks)
        page_size = 2000  # Approximate characters per page
        num_pages = len(content) // page_size + 1
        
        for i in range(num_pages):
            start = i * page_size
            end = min((i + 1) * page_size, len(content))
            page_text = content[start:end]
            
            if not page_text.strip():
                continue
            
            # Generate embedding for page
            embedding = await self.embedding_generator.generate(page_text)
            
            page_id = hashlib.md5(f"page{i}".encode()).hexdigest()[:16]
            
            pages.append({
                'id': page_id,
                'page_num': i + 1,
                'embedding': embedding.tolist(),
                'preview': page_text[:200],
                'token_count': len(page_text.split()),
                'type': 'page'
            })
        
        logger.info(f"Indexed {len(pages)} pages")
        return pages
    
    async def search(self,
                    query_embedding: np.ndarray,
                    pages: List[Dict],
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search pages by similarity
        """
        results = []
        
        for page in pages:
            page_emb = np.array(page.get('embedding', []))
            if page_emb.size == 0:
                continue
            
            similarity = np.dot(query_embedding, page_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(page_emb) + 1e-8
            )
            
            results.append({
                **page,
                'similarity': float(similarity),
                'type': 'page'
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]