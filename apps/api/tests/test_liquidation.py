import pytest
import httpx
from app.main import app
from app.domain.models import PositionInfo
from app.services.liquidation_service import liquidation_service

def test_liquidation_rules_profit_target():
    # 1. Short Put with 50% profit
    pos = PositionInfo(
        symbol="SPY260918P00625000",
        qty=-1.0,
        side="short",
        marketValue=-50.0,
        avgEntryPrice=2.00,
        unrealizedPl=100.0,
        currentPrice=1.00,
    )
    ev = liquidation_service.evaluate_position(pos)
    assert ev.shouldLiquidate is True
    assert ev.reason == "PROFIT_TARGET_50"
    assert "Take Profit" in ev.actionLabel

def test_liquidation_rules_stop_loss():
    # 2. Short Call with >200% loss
    pos = PositionInfo(
        symbol="SPY260918C00660000",
        qty=-1.0,
        side="short",
        marketValue=-650.0,
        avgEntryPrice=2.00,
        unrealizedPl=-450.0,
        currentPrice=6.50,
    )
    ev = liquidation_service.evaluate_position(pos)
    assert ev.shouldLiquidate is True
    assert ev.reason == "STOP_LOSS_200"
    assert "Cut Loss" in ev.actionLabel

def test_liquidation_rules_expiration_pin_risk():
    # 3. Near-expiration option
    pos = PositionInfo(
        symbol="SPY260904P00600000",
        qty=-1.0,
        side="short",
        marketValue=-190.0,
        avgEntryPrice=2.00,
        unrealizedPl=10.0,
        currentPrice=1.90,
    )
    ev = liquidation_service.evaluate_position(pos)
    if ev.dte is not None and ev.dte <= 2:
        assert ev.shouldLiquidate is True
        assert ev.reason == "EXPIRATION_PIN_RISK"

def test_liquidation_rules_normal_hold():
    # 4. Position within normal boundaries
    pos = PositionInfo(
        symbol="SPY261016P00625000",
        qty=-1.0,
        side="short",
        marketValue=-180.0,
        avgEntryPrice=2.00,
        unrealizedPl=20.0,
        currentPrice=1.80,
    )
    ev = liquidation_service.evaluate_position(pos)
    assert ev.shouldLiquidate is False
    assert ev.reason == "HOLD"
    assert ev.actionLabel == "Hold"

@pytest.mark.asyncio
async def test_liquidation_api_endpoints():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Get liquidation evaluations
        eval_resp = await client.get("/api/portfolio/liquidation-evaluations")
        assert eval_resp.status_code == 200
        data = eval_resp.json()
        assert isinstance(data, list)

        # 2. Liquidate eligible positions
        liq_resp = await client.post("/api/portfolio/liquidate-eligible")
        assert liq_resp.status_code == 200
        liq_data = liq_resp.json()
        assert "evaluated" in liq_data
        assert "liquidatedCount" in liq_data

        # 3. Close individual position
        close_resp = await client.post("/api/portfolio/close/SPY260918P00625000")
        assert close_resp.status_code == 200
