import pytest
import httpx
from app.main import app
from app.services.news_discovery_service import news_discovery_service
from app.api.deps import get_broker_gateway

@pytest.mark.asyncio
async def test_news_discovery_service_candidates():
    broker = get_broker_gateway()
    current_watchlist = ["SPY", "QQQ"]
    discovered = await news_discovery_service.discover_candidates(broker, current_watchlist, limit=15)
    assert isinstance(discovered, list)
    # If live/mock articles return symbols, verify fields
    for d in discovered:
        assert d.symbol.isalpha()
        assert 1 <= len(d.symbol) <= 5
        assert d.optionContractsCount >= 10
        assert d.symbol not in current_watchlist

@pytest.mark.asyncio
async def test_news_discovery_api_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/agents/discover-tickers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
