"""
Multi-Level Indexing System
Location: backend/src/indexing/multi_level_index.py
"""

import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import json

from .chapter_indexer import ChapterIndexer
from .concept_indexer import ConceptIndexer
from .page_indexer import PageIndexer
from .embedding_generator import EmbeddingGenerator
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class MultiLevelIndex:
    """
    Creates hierarchical embeddings at chapter/concept/page levels
    Enables efficient context retrieval
    """
    
    def __init__(self):
        self.chapter_indexer = ChapterIndexer()
        self.concept_indexer = ConceptIndexer()
        self.page_indexer = PageIndexer()
        self.embedding_generator = EmbeddingGenerator()
        
        self.index_path = Path(config.DATA_DIR) / "embeddings"
        self.index_path.mkdir(parents=True, exist_ok=True)
        
    async def index_textbook(self, 
                            content: str,
                            structure: Dict[str, Any],
                            subject: str,
                            grade: int) -> Dict[str, Any]:
        """
        Index textbook at multiple levels
        """
        logger.info(f"Indexing textbook: {subject} Grade {grade}")
        
        # Generate embeddings at different granularities
        chapter_embeddings = await self.chapter_indexer.index(
            structure.get('chapters', []),
            subject,
            grade
        )
        
        concept_embeddings = await self.concept_indexer.index(
            content,
            structure,
            subject,
            grade
        )
        
        page_embeddings = await self.page_indexer.index(
            content,
            structure
        )
        
        # Save indices
        index_data = {
            'subject': subject,
            'grade': grade,
            'timestamp': str(asyncio.get_event_loop().time()),
            'chapters': chapter_embeddings,
            'concepts': concept_embeddings,
            'pages': page_embeddings,
            'total_chapters': len(chapter_embeddings),
            'total_concepts': len(concept_embeddings),
            'total_pages': len(page_embeddings)
        }
        
        # Save to disk
        filename = self.index_path / f"{subject}_grade{grade}.json"
        with open(filename, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"Indexing complete. {len(chapter_embeddings)} chapters, "
                   f"{len(concept_embeddings)} concepts")
        
        return index_data
    
    async def retrieve_candidates(self,
                                 query: str,
                                 query_embedding: np.ndarray,
                                 subject: str,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve candidate passages for query
        """
        candidates = []
        
        # Load index for subject
        index_file = self.index_path / f"{subject}.json"
        if not index_file.exists():
            logger.warning(f"No index found for subject: {subject}")
            return []
        
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        # Search at all levels
        chapter_results = await self.chapter_indexer.search(
            query_embedding,
            index.get('chapters', []),
            limit=limit//3
        )
        
        concept_results = await self.concept_indexer.search(
            query_embedding,
            index.get('concepts', []),
            limit=limit//3
        )
        
        page_results = await self.page_indexer.search(
            query_embedding,
            index.get('pages', []),
            limit=limit//3
        )
        
        # Combine and rank
        all_results = chapter_results + concept_results + page_results
        all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return all_results[:limit]