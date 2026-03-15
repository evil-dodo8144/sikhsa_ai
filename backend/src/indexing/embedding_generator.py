"""
Local Embedding Generator
Location: backend/src/indexing/embedding_generator.py
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Union, List
import asyncio
from functools import lru_cache
from ..utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingGenerator:
    """Generate embeddings locally using sentence-transformers"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._model = None
        self.embedding_dim = 384  # For all-MiniLM-L6-v2
        
    @property
    def model(self):
        """Lazy load model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    async def generate(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embedding for text
        """
        if isinstance(text, str):
            if not text.strip():
                return np.zeros(self.embedding_dim)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.model.encode, 
                text
            )
            return embedding
        else:
            # Batch processing
            texts = [t for t in text if t.strip()]
            if not texts:
                return np.zeros((0, self.embedding_dim))
            
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.model.encode,
                texts
            )
            return embeddings
    
    @lru_cache(maxsize=1000)
    def generate_sync(self, text: str) -> np.ndarray:
        """Synchronous version with caching"""
        if not text.strip():
            return np.zeros(self.embedding_dim)
        return self.model.encode(text)
    
    async def generate_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = await self.generate(batch)
            results.extend(batch_embeddings)
            
        return results