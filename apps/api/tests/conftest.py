import sys
import pytest
from pathlib import Path

# Add apps/api to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.database.session import init_db, engine, Base

@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
