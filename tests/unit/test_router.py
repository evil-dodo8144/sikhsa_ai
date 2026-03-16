import pytest
from backend.src.llm.router import LLMRouter

@pytest.mark.asyncio
async def test_router():
    router = LLMRouter()
    result = await router.route_and_generate(
        prompt="What is 2+2?",
        intent={"type": "factual", "complexity": "simple"},
        student_tier="free"
    )
    
    assert result is not None
    assert "text" in result