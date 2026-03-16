#!/usr/bin/env python
"""
Pre-compute Embeddings Script
Location: backend/scripts/generate_embeddings.py
"""

import asyncio
import argparse
from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).parent.parent))

from src.indexing.embedding_generator import EmbeddingGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def generate_embeddings(input_file: str, output_file: str, batch_size: int = 32):
    """
    Generate embeddings for text chunks
    """
    logger.info(f"Generating embeddings from {input_file}")
    
    # Load text chunks
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    chunks = data.get('chunks', [])
    if not chunks:
        logger.error("No text chunks found")
        return False
    
    logger.info(f"Loaded {len(chunks)} text chunks")
    
    # Initialize generator
    generator = EmbeddingGenerator()
    
    # Generate embeddings in batches
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_texts = [chunk['text'] for chunk in batch]
        
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
        
        embeddings = await generator.generate_batch(batch_texts)
        
        for j, embedding in enumerate(embeddings):
            all_embeddings.append({
                'id': batch[j]['id'],
                'embedding': embedding.tolist()
            })
    
    # Save embeddings
    output = {
        'embeddings': all_embeddings,
        'metadata': {
            'total_chunks': len(chunks),
            'embedding_dim': len(all_embeddings[0]['embedding']) if all_embeddings else 0,
            'model': 'all-MiniLM-L6-v2'
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved {len(all_embeddings)} embeddings to {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate embeddings")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with text chunks")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file for embeddings")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    
    args = parser.parse_args()
    
    success = asyncio.run(generate_embeddings(args.input, args.output, args.batch_size))
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()