#!/usr/bin/env python
"""
Batch Textbook Ingestion Script
Location: backend/scripts/ingest_textbooks.py
"""

import asyncio
import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ingestion.pdf_processor import PDFProcessor
from src.ingestion.text_extractor import TextExtractor
from src.ingestion.structure_parser import StructureParser
from src.ingestion.metadata_extractor import MetadataExtractor
from src.indexing.multi_level_index import MultiLevelIndex
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def ingest_textbook(pdf_path: str, subject: str, grade: int):
    """
    Ingest a single textbook
    """
    logger.info(f"Ingesting {pdf_path}...")
    
    # Initialize components
    processor = PDFProcessor()
    extractor = TextExtractor()
    parser = StructureParser()
    metadata_extractor = MetadataExtractor()
    indexer = MultiLevelIndex()
    
    try:
        # Process PDF
        pdf_content = await processor.extract(pdf_path)
        
        # Extract text
        text_content = await extractor.extract_text(pdf_content)
        
        # Parse structure
        structure = await parser.parse(pdf_content.get('content', []))
        
        # Extract metadata
        metadata = await metadata_extractor.extract(pdf_path, text_content)
        
        # Index content
        index_result = await indexer.index_textbook(
            content=text_content,
            structure={'chapters': [c.__dict__ for c in structure]},
            subject=subject,
            grade=grade
        )
        
        logger.info(f"Successfully ingested {pdf_path}")
        logger.info(f"  - Chapters: {len(structure)}")
        logger.info(f"  - Concepts: {index_result.get('total_concepts', 0)}")
        logger.info(f"  - Pages: {metadata.get('estimated_pages', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to ingest {pdf_path}: {str(e)}")
        return False

async def main():
    parser = argparse.ArgumentParser(description="Ingest textbooks")
    parser.add_argument("--dir", type=str, help="Directory containing PDFs")
    parser.add_argument("--file", type=str, help="Single PDF file")
    parser.add_argument("--subject", type=str, required=True, help="Subject")
    parser.add_argument("--grade", type=int, required=True, help="Grade level")
    
    args = parser.parse_args()
    
    if args.file:
        # Ingest single file
        success = await ingest_textbook(args.file, args.subject, args.grade)
        if not success:
            sys.exit(1)
            
    elif args.dir:
        # Ingest all PDFs in directory
        pdf_dir = Path(args.dir)
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.error(f"No PDF files found in {args.dir}")
            sys.exit(1)
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        successes = 0
        for pdf_file in pdf_files:
            if await ingest_textbook(str(pdf_file), args.subject, args.grade):
                successes += 1
        
        logger.info(f"Ingestion complete: {successes}/{len(pdf_files)} successful")
        
        if successes == 0:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())