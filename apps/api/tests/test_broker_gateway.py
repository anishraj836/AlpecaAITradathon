import pytest
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.domain.models import DecisionPacket, StrategyCandidate

@pytest.mark.asyncio
async def test_get_account_broker():
    broker = AlpacaBrokerGateway()
    account = await broker.get_account()
    assert account.equity > 0
    assert account.buyingPower > 0
    assert account.isPaper is True

@pytest.mark.asyncio
async def test_get_market_context_broker():
    broker = AlpacaBrokerGateway()
    market = await broker.get_market_context("SPY")
    assert market.symbol == "SPY"
    assert market.price > 0
    assert market.high >= market.low

@pytest.mark.asyncio
async def test_get_option_chain_broker():
    broker = AlpacaBrokerGateway()
    chain = await broker.get_option_chain("SPY")
    assert len(chain) > 0
    assert all(leg.underlying == "SPY" for leg in chain)

@pytest.mark.asyncio
async def test_place_multileg_order_broker():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]
    
    decision = DecisionPacket(
        id="DEC-TEST-01",
        createdAt="2026-08-29T10:00:00Z",
        underlying="SPY",
        spotPrice=645.31,
        marketRegime="Range-Bound",
        iv30=18.4,
        ivRank=72.1,
        aiConfidence=0.81,
        strategy=strategy,
        evidence={"description": "Test evidence", "putSkewElevated": True, "termStructureRich": True},
        whyThisTrade=["Testing"],
        criticAnalysis={"primaryFailureMode": "None", "details": "Test"},
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    result = await broker.place_multileg_order(decision)
    assert result.orderId.startswith("ALP-ORD-")
    assert result.decisionId == "DEC-TEST-01"
    assert result.status in ["accepted", "filled"]
    assert result.broker == "ALPACA_PAPER"
