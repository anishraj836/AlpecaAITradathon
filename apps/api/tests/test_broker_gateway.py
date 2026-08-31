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

@pytest.mark.asyncio
async def test_place_multileg_order_via_mcp_success(monkeypatch):
    """
    Verify that when AlpacaOfficialMCPClient responds successfully,
    AlpacaBrokerGateway returns the MCP-sourced OrderResult rather than falling through to REST.
    """
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]

    decision = DecisionPacket(
        id="DEC-TEST-MCP-01",
        createdAt="2026-08-29T10:00:00Z",
        underlying="SPY",
        spotPrice=645.31,
        marketRegime="Range-Bound",
        iv30=18.4,
        ivRank=72.1,
        aiConfidence=0.81,
        strategy=strategy,
        evidence={"description": "MCP order test", "putSkewElevated": True, "termStructureRich": True},
        whyThisTrade=["MCP test"],
        criticAnalysis={"primaryFailureMode": "None", "details": "MCP test"},
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    mcp_tool_calls = []

    async def mock_call_mcp_tool(tool_name: str, arguments: dict):
        mcp_tool_calls.append({"tool": tool_name, "args": arguments})
        if tool_name == "alpaca_place_multileg_order":
            return {
                "id": "MCP-ORD-88888",
                "client_order_id": "cl-DEC-TEST-MCP-01",
                "status": "filled",
                "filled_avg_price": 1.42,
                "filled_qty": 1,
            }
        return {"error": "Unknown tool"}

    monkeypatch.setattr(broker.mcp_client, "call_mcp_tool", mock_call_mcp_tool)

    result = await broker.place_multileg_order(decision)

    # Must be the MCP-sourced order result
    assert result.orderId == "MCP-ORD-88888"
    assert result.decisionId == "DEC-TEST-MCP-01"
    assert result.status == "filled"
    assert result.avgPrice == 1.42
    assert len(mcp_tool_calls) == 1
    assert mcp_tool_calls[0]["tool"] == "alpaca_place_multileg_order"
    assert mcp_tool_calls[0]["args"]["order_class"] == "mleg"
    assert len(mcp_tool_calls[0]["args"]["legs"]) == len(strategy.legs)

@pytest.mark.asyncio
async def test_get_clock_broker():
    broker = AlpacaBrokerGateway()
    clock = await broker.get_clock()
    assert "is_open" in clock
    assert "market_status" in clock
    assert clock["market_status"] in ["OPEN", "CLOSED"]

@pytest.mark.asyncio
async def test_get_news_broker():
    broker = AlpacaBrokerGateway()
    news = await broker.get_news("SPY", limit=5)
    assert isinstance(news, list)
    assert len(news) > 0
    assert "headline" in news[0]
    assert "summary" in news[0]
