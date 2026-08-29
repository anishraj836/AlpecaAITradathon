import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["environment"] == "paper"

@pytest.mark.asyncio
async def test_telemetry_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/telemetry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["underlying"] == "SPY"
        assert data["accountEquity"] > 0
        assert data["alpacaConnected"] is True

@pytest.mark.asyncio
async def test_scan_mandate_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {"mandate": "Harvest elevated put skew with defined risk", "underlying": "SPY"}
        resp = await client.post("/api/scan", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"].startswith("DEC-SPY-")
        assert data["underlying"] == "SPY"
        assert data["strategy"]["name"] == "Iron Condor"
        assert data["status"] == "AWAITING_APPROVAL"

@pytest.mark.asyncio
async def test_decision_endpoints():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Get Decision
        resp = await client.get("/api/decisions/DEC-SPY-9942")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "DEC-SPY-9942"
        assert data["underlying"] == "SPY"
        assert data["status"] == "AWAITING_APPROVAL"

        # 2. Approve Decision
        approve_resp = await client.post("/api/decisions/DEC-SPY-9942/approve")
        assert approve_resp.status_code == 200
        order_data = approve_resp.json()
        assert order_data["decisionId"] == "DEC-SPY-9942"
        assert order_data["status"] in ["accepted", "filled"]
        assert order_data["broker"] == "ALPACA_PAPER"

@pytest.mark.asyncio
async def test_quant_endpoints():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Surface
        surf_resp = await client.get("/api/quant/surface?symbol=SPY")
        assert surf_resp.status_code == 200
        assert surf_resp.json()["underlying"] == "SPY"

        # Strategies
        strat_resp = await client.get("/api/quant/strategies?symbol=SPY")
        assert strat_resp.status_code == 200
        assert len(strat_resp.json()) >= 3

        # Stress
        stress_resp = await client.get("/api/quant/stress?strategy_id=strat-condor-01")
        assert stress_resp.status_code == 200
        assert len(stress_resp.json()["matrix"]) == 21
