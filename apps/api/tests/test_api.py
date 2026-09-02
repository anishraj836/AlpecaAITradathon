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
        assert any(n in data["strategy"]["name"] for n in ("Iron Condor", "Jade Lizard", "Iron Butterfly", "Put Credit Spread", "Call Credit Spread"))
        assert data["status"] in ("APPROVED", "AWAITING_APPROVAL")

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

@pytest.mark.asyncio
async def test_settings_endpoints_and_autonomy_modes():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Get Settings
        resp = await client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "llmProvider" in data
        assert "availableProviders" in data

        # 2. Update Autonomy to COPILOT
        update_resp = await client.post("/api/settings", json={"autonomyLevel": "COPILOT"})
        assert update_resp.status_code == 200
        assert update_resp.json()["autonomyLevel"] == "COPILOT"

        # 3. Verify scan under COPILOT halts at AWAITING_APPROVAL
        scan_resp = await client.post("/api/scan", json={"mandate": "Test copilot mode", "underlying": "SPY", "autonomyLevel": "COPILOT"})
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()
        assert scan_data["status"] == "AWAITING_APPROVAL"
        assert scan_data["autonomyLevel"] == "COPILOT"

        # 4. Test connection endpoint with dummy test
        test_resp = await client.post("/api/settings/test", json={"provider": "ollama", "model": "llama3.2:3b"})
        assert test_resp.status_code == 200

@pytest.mark.asyncio
async def test_portfolio_history_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/portfolio/history?period=1M&timeframe=1D")
        assert resp.status_code == 200
        data = resp.json()
        assert "timestamp" in data
        assert "equity" in data
        assert "base_value" in data
        assert len(data["equity"]) > 0
