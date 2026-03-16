import pytest
from backend.src.query.context_pruner import ContextPruner

@pytest.mark.asyncio
async def test_context_pruner():
    pruner = ContextPruner()
    result = await pruner.prune(
        query="What is photosynthesis?",
        grade=7,
        subject="science",
        intent={"type": "factual"}
    )
    
    assert result is not None
    assert "token_count" in result
    assert "pruning_stats" in result