"""
Textbook Compression for Offline Storage
Location: backend/src/offline/compression.py
"""

import zlib
import json
import gzip
from typing import Dict, Any, Union
import numpy as np
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Compression:
    """
    Compress textbooks for efficient offline storage
    """
    
    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
        
    def compress_textbook(self, textbook: Dict[str, Any]) -> bytes:
        """
        Compress textbook for storage
        """
        # Convert to JSON string
        json_str = json.dumps(textbook)
        
        # Compress with zlib
        compressed = zlib.compress(json_str.encode(), level=self.compression_level)
        
        compression_ratio = len(compressed) / len(json_str) * 100
        logger.info(f"Compressed textbook: {len(json_str)} -> {len(compressed)} bytes "
                   f"({compression_ratio:.1f}% of original)")
        
        return compressed
    
    def decompress_textbook(self, compressed_data: bytes) -> Dict[str, Any]:
        """
        Decompress textbook
        """
        # Decompress
        json_str = zlib.decompress(compressed_data).decode()
        
        # Parse JSON
        return json.loads(json_str)
    
    def compress_embeddings(self, embeddings: np.ndarray) -> bytes:
        """
        Compress embeddings array
        """
        # Convert to bytes
        embedding_bytes = embeddings.astype(np.float32).tobytes()
        
        # Compress with gzip for better compression
        compressed = gzip.compress(embedding_bytes, compresslevel=self.compression_level)
        
        return compressed
    
    def decompress_embeddings(self, compressed_data: bytes, shape: tuple) -> np.ndarray:
        """
        Decompress embeddings array
        """
        # Decompress
        embedding_bytes = gzip.decompress(compressed_data)
        
        # Convert back to numpy array
        return np.frombuffer(embedding_bytes, dtype=np.float32).reshape(shape)
    
    def get_compression_stats(self, original: Union[str, bytes], compressed: bytes) -> Dict[str, Any]:
        """
        Get compression statistics
        """
        original_size = len(original) if isinstance(original, bytes) else len(original.encode())
        
        return {
            "original_size_bytes": original_size,
            "compressed_size_bytes": len(compressed),
            "compression_ratio": len(compressed) / original_size * 100,
            "space_saved_percentage": (1 - len(compressed) / original_size) * 100
        }