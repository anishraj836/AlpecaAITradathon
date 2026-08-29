import sys
import pytest
from pathlib import Path

# Add apps/api to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.infrastructure.database.session import init_db, engine, Base

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    # Ensure test environment uses deterministic test mode
    monkeypatch.setattr(settings, "ALPACA_API_KEY", "PKTEST_DUMMY_KEY")
    monkeypatch.setattr(settings, "ALPACA_SECRET_KEY", "SKTEST_DUMMY_SECRET")
    monkeypatch.setattr(settings, "USE_MOCK_QUANT", True)
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
