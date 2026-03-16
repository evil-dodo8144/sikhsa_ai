import pytest
from backend.src.indexing.multi_level_index import MultiLevelIndex

@pytest.mark.asyncio
async def test_indexer():
    indexer = MultiLevelIndex()
    result = await indexer.index_textbook(
        content="Sample textbook content",
        structure={"chapters": []},
        subject="science",
        grade=7
    )
    
    assert result is not None
    assert "total_chapters" in result