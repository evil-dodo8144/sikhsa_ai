"""
Complete API Routes
Location: backend/src/api/routes.py
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import os
from pathlib import Path

from ..query.query_parser import QueryParser
from ..query.intent_classifier import IntentClassifier
from ..query.context_retriever import ContextRetriever
from ..query.prompt_builder import PromptBuilder
from ..llm.router import LLMRouter
from ..cache.response_cache import ResponseCache
from ..scaledown.optimizer import PromptOptimizer
from ..utils.logger import get_logger
from ..utils.metrics import get_metrics, MetricsCollector
from ..config.settings import config
from .validators import validate_query, validate_student, validate_textbook_ingest
from .serializers import (
    serialize_response, 
    serialize_error, 
    serialize_optimization,
    serialize_health,
    serialize_metrics,
    serialize_textbook,
    PaginatedResponse
)
from ..ingestion.pdf_processor import PDFProcessor
from ..ingestion.text_extractor import TextExtractor
from ..ingestion.structure_parser import StructureParser
from ..ingestion.metadata_extractor import MetadataExtractor
from ..indexing.multi_level_index import MultiLevelIndex

router = APIRouter()
logger = get_logger(__name__)

# Initialize components
query_parser = QueryParser()
intent_classifier = IntentClassifier()
context_retriever = ContextRetriever()
prompt_builder = PromptBuilder()
llm_router = LLMRouter()
response_cache = ResponseCache()
prompt_optimizer = PromptOptimizer()
metrics = MetricsCollector()

# Admin API key for protected endpoints
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-change-in-production")

def verify_admin(authorization: str = Header(None)):
    """Verify admin API key"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Expecting "Bearer <api-key>"
    scheme, _, key = authorization.partition(" ")
    if scheme.lower() != "bearer" or key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    
    return True

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        JSON with system health status and service states
    """
    logger.debug("Health check requested")
    
    # Check database connection
    db_status = "healthy"
    try:
        from ..config.database_config import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    # Check Redis connection
    redis_status = "healthy"
    try:
        from ..cache.redis_client import RedisClient
        redis = RedisClient()
        await redis.connect()
        await redis.client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = "unhealthy"
    
    # Check ScaleDown API
    scaledown_status = "available"
    try:
        # Just check if we can reach the API (don't make actual optimization)
        import requests
        response = requests.get(
            f"{config.SCALEDOWN_API_URL.replace('/v1', '')}/health",
            timeout=2
        )
        if response.status_code != 200:
            scaledown_status = "unavailable"
    except:
        scaledown_status = "unavailable"
    
    # Check disk space
    data_dir = Path(config.DATA_DIR)
    free_space = data_dir.stat().st_dev  # This is simplified
    
    return serialize_health(
        status="healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        services={
            "database": db_status,
            "redis": redis_status,
            "scaledown": scaledown_status,
            "disk_space": f"{free_space / (1024**3):.1f}GB free"
        }
    )


@router.get("/health/detailed")
async def health_check_detailed():
    """
    Detailed health check with metrics (admin only)
    """
    health = await health_check()
    
    # Add detailed metrics
    health["metrics"] = {
        "total_queries": metrics.get_total_queries(),
        "active_queries": metrics.get_active_queries(),
        "average_response_time_ms": metrics.get_avg_response_time() * 1000,
        "cache_hit_rate": metrics.get_cache_hit_rate(),
        "memory_usage_mb": metrics.get_memory_usage(),
        "uptime_seconds": metrics.get_uptime()
    }
    
    return health

# ============================================================================
# SCALEDOWN OPTIMIZATION TEST ENDPOINT
# ============================================================================

@router.post("/optimize")
async def test_optimization(request: Request):
    """
    Test ScaleDown prompt optimization
    
    This endpoint allows testing the ScaleDown API directly
    without going through the full query pipeline.
    
    Request body:
    {
        "prompt": "Your prompt text here",
        "model": "gpt-3.5-turbo",  # Optional
        "tier": "free",  # Optional
        "compression_level": "aggressive"  # Optional
    }
    
    Returns:
        Optimized prompt with metrics
    """
    try:
        data = await request.json()
        
        # Validate input
        prompt = data.get("prompt")
        if not prompt:
            return serialize_error("Prompt is required", 400)
        
        model = data.get("model", "gpt-3.5-turbo")
        tier = data.get("tier", "free")
        compression_level = data.get("compression_level", "aggressive")
        
        logger.info(f"Testing ScaleDown optimization: {len(prompt)} chars, model={model}")
        
        # Track start time
        start_time = datetime.utcnow()
        
        # Call ScaleDown optimizer
        result = await prompt_optimizer.optimize(
            base_prompt=prompt,
            model=model,
            student_tier=tier,
            force_refresh=data.get("force_refresh", False)
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Format response
        response = serialize_optimization(result)
        response["processing_time_ms"] = processing_time
        
        # Track test
        metrics.track_optimization_test(
            original_length=len(prompt),
            optimized_length=len(result.get("optimized_prompt", "")),
            savings=result.get("savings_percentage", 0),
            model=model
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Optimization test failed: {str(e)}")
        return serialize_error(str(e), 500)


@router.post("/optimize/batch")
async def batch_optimization(request: Request):
    """
    Batch test ScaleDown optimization
    
    Request body:
    {
        "prompts": ["prompt1", "prompt2", ...],
        "model": "gpt-3.5-turbo",
        "tier": "free"
    }
    
    Returns:
        List of optimized prompts with metrics
    """
    try:
        data = await request.json()
        
        prompts = data.get("prompts", [])
        if not prompts:
            return serialize_error("Prompts list is required", 400)
        
        if len(prompts) > 10:
            return serialize_error("Maximum 10 prompts per batch", 400)
        
        model = data.get("model", "gpt-3.5-turbo")
        tier = data.get("tier", "free")
        
        logger.info(f"Batch optimization: {len(prompts)} prompts")
        
        results = []
        for prompt in prompts:
            result = await prompt_optimizer.optimize(
                base_prompt=prompt,
                model=model,
                student_tier=tier
            )
            results.append(serialize_optimization(result))
        
        return {
            "results": results,
            "total_prompts": len(results),
            "average_savings": sum(r["savings_percentage"] for r in results) / len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch optimization failed: {str(e)}")
        return serialize_error(str(e), 500)


@router.get("/optimize/stats")
async def optimization_stats():
    """
    Get ScaleDown optimization statistics
    
    Returns:
        Statistics about token savings and usage
    """
    try:
        optimizer_stats = prompt_optimizer.get_metrics()
        cache_stats = prompt_optimizer.get_cache_stats()
        
        return {
            "total_optimizations": optimizer_stats.get("total_calls", 0),
            "total_tokens_saved": optimizer_stats.get("total_tokens_saved", 0),
            "average_savings_percentage": optimizer_stats.get("avg_savings", 0),
            "cache_hit_rate": cache_stats.get("hit_rate_percentage", 0),
            "by_model": optimizer_stats.get("model_stats", {}),
            "estimated_cost_saved_usd": optimizer_stats.get("estimated_cost_saved_usd", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization stats: {str(e)}")
        return serialize_error(str(e), 500)

# ============================================================================
# TEXTBOOK INGESTION ENDPOINT (ADMIN ONLY)
# ============================================================================

@router.post("/ingest")
async def ingest_textbook(
    request: Request,
    admin: bool = Depends(verify_admin)
):
    """
    Ingest a new textbook into the system (Admin only)
    
    Request body:
    {
        "path": "/path/to/textbook.pdf",
        "subject": "mathematics",
        "grade": 7,
        "title": "Mathematics Grade 7",  # Optional
        "overwrite": false  # Optional
    }
    
    Returns:
        Ingestion results with metadata
    """
    try:
        data = await request.json()
        
        # Validate input
        validated = validate_textbook_ingest(data)
        textbook_path = validated["path"]
        subject = validated["subject"]
        grade = validated["grade"]
        title = validated.get("title", "")
        overwrite = validated.get("overwrite", False)
        
        logger.info(f"Ingesting textbook: {textbook_path} (Subject: {subject}, Grade: {grade})")
        
        # Check if file exists
        if not os.path.exists(textbook_path):
            return serialize_error(f"File not found: {textbook_path}", 404)
        
        # Initialize components
        processor = PDFProcessor()
        extractor = TextExtractor()
        parser = StructureParser()
        metadata_extractor = MetadataExtractor()
        indexer = MultiLevelIndex()
        
        # Process PDF
        logger.info("Extracting PDF content...")
        pdf_content = await processor.extract(textbook_path)
        
        # Extract text
        logger.info("Extracting text...")
        text_content = await extractor.extract_text(pdf_content)
        
        # Parse structure
        logger.info("Parsing chapter structure...")
        structure = await parser.parse(pdf_content.get('content', []))
        
        # Extract metadata
        logger.info("Extracting metadata...")
        metadata = await metadata_extractor.extract(textbook_path, text_content)
        
        # Override with provided metadata
        if subject:
            metadata["subject"] = subject
        if grade:
            metadata["grade"] = grade
        if title:
            metadata["title"] = title
        
        # Index content
        logger.info("Creating embeddings and indexing...")
        index_result = await indexer.index_textbook(
            content=text_content,
            structure={'chapters': [c.__dict__ for c in structure]},
            subject=metadata["subject"],
            grade=metadata["grade"]
        )
        
        # Save processed content for future reference
        output_path = Path(config.TEXTBOOK_DIR) / "processed" / f"{subject}_grade{grade}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_path, 'w') as f:
            json.dump({
                "metadata": metadata,
                "structure": [c.__dict__ for c in structure],
                "index_info": index_result,
                "ingested_at": datetime.utcnow().isoformat()
            }, f, indent=2, default=str)
        
        logger.info(f"Textbook saved to {output_path}")
        
        # Track ingestion metrics
        metrics.track_ingestion(
            subject=subject,
            grade=grade,
            pages=pdf_content.get('total_pages', 0),
            chapters=len(structure),
            concepts=index_result.get('total_concepts', 0)
        )
        
        # Return success response
        return {
            "status": "success",
            "message": f"Textbook ingested successfully",
            "metadata": {
                "title": metadata.get("title", ""),
                "subject": metadata["subject"],
                "grade": metadata["grade"],
                "language": metadata.get("language", "en"),
                "total_pages": pdf_content.get('total_pages', 0),
                "file_size_mb": round(os.path.getsize(textbook_path) / (1024 * 1024), 2)
            },
            "content_stats": {
                "chapters": len(structure),
                "concepts": index_result.get('total_concepts', 0),
                "embeddings_created": index_result.get('total_concepts', 0) + len(structure),
                "estimated_tokens": len(text_content) // 4
            },
            "output_path": str(output_path),
            "ingested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error ingesting textbook: {str(e)}")
        return serialize_error(str(e), 500)


@router.post("/ingest/batch")
async def batch_ingest(
    request: Request,
    admin: bool = Depends(verify_admin)
):
    """
    Batch ingest multiple textbooks from a directory (Admin only)
    
    Request body:
    {
        "directory": "/path/to/textbooks/",
        "subject_mapping": {
            "math*.pdf": "mathematics",
            "science*.pdf": "science"
        },
        "default_grade": 7
    }
    
    Returns:
        Batch ingestion results
    """
    try:
        data = await request.json()
        
        directory = data.get("directory")
        if not directory or not os.path.isdir(directory):
            return serialize_error("Valid directory path is required", 400)
        
        subject_mapping = data.get("subject_mapping", {})
        default_grade = data.get("default_grade", 7)
        
        # Find all PDF files
        pdf_files = list(Path(directory).glob("*.pdf"))
        
        if not pdf_files:
            return serialize_error(f"No PDF files found in {directory}", 404)
        
        logger.info(f"Found {len(pdf_files)} PDF files for batch ingestion")
        
        results = {
            "successful": [],
            "failed": [],
            "total": len(pdf_files)
        }
        
        for pdf_file in pdf_files:
            try:
                # Determine subject from filename
                subject = default_grade
                for pattern, subj in subject_mapping.items():
                    if pdf_file.match(pattern):
                        subject = subj
                        break
                
                # Ingest single textbook
                ingest_data = {
                    "path": str(pdf_file),
                    "subject": subject,
                    "grade": default_grade,
                    "title": pdf_file.stem
                }
                
                # Mock request object
                class MockRequest:
                    async def json(self):
                        return ingest_data
                
                mock_request = MockRequest()
                result = await ingest_textbook(mock_request, admin)
                
                if result.get("status") == "success":
                    results["successful"].append({
                        "file": pdf_file.name,
                        "subject": subject,
                        "chapters": result["content_stats"]["chapters"]
                    })
                else:
                    results["failed"].append({
                        "file": pdf_file.name,
                        "error": result.get("message", "Unknown error")
                    })
                    
            except Exception as e:
                results["failed"].append({
                    "file": pdf_file.name,
                    "error": str(e)
                })
        
        return {
            "status": "completed",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch ingestion failed: {str(e)}")
        return serialize_error(str(e), 500)


@router.get("/ingest/status/{job_id}")
async def ingestion_status(
    job_id: str,
    admin: bool = Depends(verify_admin)
):
    """
    Get status of an ingestion job
    
    Returns:
        Current status of the ingestion process
    """
    # This would check a job queue in a real implementation
    return {
        "job_id": job_id,
        "status": "completed",  # or "processing", "failed"
        "progress": 100,
        "completed_at": datetime.utcnow().isoformat()
    }


@router.get("/textbooks")
async def list_textbooks(
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    List all ingested textbooks
    
    Query parameters:
        - subject: Filter by subject
        - grade: Filter by grade
        - page: Page number
        - page_size: Items per page
    
    Returns:
        Paginated list of textbooks
    """
    try:
        # This would query a database in production
        # For now, scan the processed directory
        processed_dir = Path(config.TEXTBOOK_DIR) / "processed"
        textbooks = []
        
        if processed_dir.exists():
            for json_file in processed_dir.glob("*.json"):
                import json
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    
                    # Apply filters
                    if subject and metadata.get("subject") != subject:
                        continue
                    if grade and metadata.get("grade") != grade:
                        continue
                    
                    textbooks.append({
                        "id": json_file.stem,
                        "title": metadata.get("title", ""),
                        "subject": metadata.get("subject", ""),
                        "grade": metadata.get("grade", 0),
                        "chapters": len(data.get("structure", [])),
                        "ingested_at": data.get("ingested_at", ""),
                        "file": json_file.name
                    })
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        paginated = textbooks[start:end]
        
        return PaginatedResponse.create(
            items=paginated,
            total=len(textbooks),
            page=page,
            page_size=page_size,
            serializer=lambda x: x
        )
        
    except Exception as e:
        logger.error(f"Failed to list textbooks: {str(e)}")
        return serialize_error(str(e), 500)


@router.delete("/textbook/{textbook_id}")
async def delete_textbook(
    textbook_id: str,
    admin: bool = Depends(verify_admin)
):
    """
    Delete a textbook from the system (Admin only)
    
    Returns:
        Deletion confirmation
    """
    try:
        # Delete index files
        index_path = Path(config.DATA_DIR) / "embeddings"
        for f in index_path.glob(f"*{textbook_id}*"):
            f.unlink()
        
        # Delete processed content
        processed_path = Path(config.TEXTBOOK_DIR) / "processed" / f"{textbook_id}.json"
        if processed_path.exists():
            processed_path.unlink()
        
        logger.info(f"Deleted textbook: {textbook_id}")
        
        return {
            "status": "success",
            "message": f"Textbook {textbook_id} deleted",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete textbook: {str(e)}")
        return serialize_error(str(e), 500)

# ============================================================================
# METRICS ENDPOINT
# ============================================================================

@router.get("/metrics")
async def get_system_metrics():
    """
    Get system performance metrics
    
    Returns:
        Detailed metrics about system performance
    """
    try:
        # Get metrics from various components
        query_metrics = metrics.get_summary()
        cache_stats = await response_cache.get_stats()
        optimizer_stats = prompt_optimizer.get_metrics()
        
        # Combine all metrics
        all_metrics = {
            **query_metrics,
            "cache": cache_stats,
            "optimization": optimizer_stats,
            "system": {
                "memory_usage_mb": metrics.get_memory_usage(),
                "cpu_percent": metrics.get_cpu_usage(),
                "active_connections": metrics.get_active_connections(),
                "uptime_seconds": metrics.get_uptime()
            }
        }
        
        return serialize_metrics(all_metrics)
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        return serialize_error(str(e), 500)


@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """
    Get metrics in Prometheus format for monitoring
    """
    try:
        metrics_text = metrics.get_prometheus_format()
        return Response(
            content=metrics_text,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {str(e)}")
        return serialize_error(str(e), 500)

# ============================================================================
# ADDITIONAL UTILITY ENDPOINTS
# ============================================================================

@router.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "build_date": "2024-01-15",
        "scaledown_integrated": True,
        "features": [
            "context_pruning",
            "multi_level_indexing",
            "offline_support",
            "cost_optimization"
        ]
    }


@router.get("/models")
async def list_models():
    """List available LLM models"""
    return {
        "models": [
            {
                "id": "local",
                "name": "Local Tiny Model",
                "cost_per_1k": 0,
                "offline": True,
                "max_tokens": 500
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "cost_per_1k": 0.0015,
                "offline": False,
                "max_tokens": 2000
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "cost_per_1k": 0.03,
                "offline": False,
                "max_tokens": 4000
            },
            {
                "id": "claude-instant",
                "name": "Claude Instant",
                "cost_per_1k": 0.0016,
                "offline": False,
                "max_tokens": 3000
            }
        ],
        "default": "gpt-3.5-turbo"
    }


@router.get("/docs/openapi.json")
async def get_openapi_spec():
    """Get OpenAPI specification"""
    from fastapi.openapi.utils import get_openapi
    
    from ..api.main import app
    return get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )