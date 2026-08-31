import sys
import pytest
from pathlib import Path

# Add apps/api and packages/options-alpha-mcp to PYTHONPATH
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(repo_root / "packages" / "options-alpha-mcp"))

from app.config import settings
from app.infrastructure.database.session import init_db, engine, Base
from app.infrastructure.llm import llm_client

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    # Ensure test environment uses deterministic test mode
    monkeypatch.setattr(settings, "ALPACA_API_KEY", "PKTEST_DUMMY_KEY")
    monkeypatch.setattr(settings, "ALPACA_SECRET_KEY", "SKTEST_DUMMY_SECRET")
    monkeypatch.setattr(settings, "USE_MOCK_QUANT", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "LLM_API_KEY", None)
    
    # Reload llm_client with unconfigured key for tests
    llm_client.reload_provider(api_key=None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
