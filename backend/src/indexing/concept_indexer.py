"""
Concept-Level Indexer
Location: backend/src/indexing/concept_indexer.py
"""

import numpy as np
from typing import List, Dict, Any, Optional
import re
import hashlib
from .embedding_generator import EmbeddingGenerator
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ConceptIndexer:
    """Extract and index key concepts from textbook"""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        
        # Common educational concepts by subject
        self.concept_patterns = {
            'mathematics': [r'\b(?:equation|formula|theorem|proof|function)\b'],
            'science': [r'\b(?:cell|atom|molecule|force|energy|reaction)\b'],
            'general': [r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b']  # Proper nouns
        }
        
    async def index(self,
                   content: str,
                   structure: Dict[str, Any],
                   subject: str,
                   grade: int) -> List[Dict[str, Any]]:
        """
        Extract and index key concepts
        """
        concepts = []
        
        # Extract potential concepts
        patterns = self.concept_patterns.get(subject, self.concept_patterns['general'])
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches[:50]:  # Limit per pattern
                if len(match) < 3 or len(match) > 100:
                    continue
                    
                # Find context around concept
                context = self._extract_context(content, match)
                
                # Generate embedding
                embedding = await self.embedding_generator.generate(context)
                
                concept_id = hashlib.md5(f"{subject}{match}".encode()).hexdigest()[:16]
                
                concepts.append({
                    'id': concept_id,
                    'name': match,
                    'embedding': embedding.tolist(),
                    'context': context,
                    'subject': subject,
                    'grade_level': grade,
                    'frequency': content.lower().count(match.lower()),
                    'type': 'concept'
                })
        
        # Remove duplicates
        unique_concepts = {}
        for concept in concepts:
            name = concept['name'].lower()
            if name not in unique_concepts or concept['frequency'] > unique_concepts[name]['frequency']:
                unique_concepts[name] = concept
        
        logger.info(f"Indexed {len(unique_concepts)} concepts")
        return list(unique_concepts.values())
    
    def _extract_context(self, content: str, concept: str, window: int = 100) -> str:
        """Extract text surrounding concept"""
        pos = content.lower().find(concept.lower())
        if pos == -1:
            return concept
        
        start = max(0, pos - window)
        end = min(len(content), pos + len(concept) + window)
        
        return content[start:end]
    
    async def search(self,
                    query_embedding: np.ndarray,
                    concepts: List[Dict],
                    limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search concepts by similarity
        """
        results = []
        
        for concept in concepts:
            concept_emb = np.array(concept.get('embedding', []))
            if concept_emb.size == 0:
                continue
            
            similarity = np.dot(query_embedding, concept_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(concept_emb) + 1e-8
            )
            
            results.append({
                **concept,
                'similarity': float(similarity),
                'type': 'concept'
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]