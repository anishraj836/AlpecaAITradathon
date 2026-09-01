from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.api.deps import get_broker_gateway, get_quant_gateway
from app.agents.orchestrator import VoltronOrchestrator
from app.infrastructure.database.repositories.agents import AgentRepository
from app.domain.models import (
    StrategyCandidate,
    VolatilitySurface,
    StressReport,
    CounterfactualComparison,
    AgentTraceStep,
    MandateRequest,
    DecisionPacket,
    AnomalyReport,
)

router = APIRouter(prefix="/quant", tags=["Quantitative Analysis"])

@router.post("/scan", response_model=DecisionPacket)
async def run_scan_mandate(
    req: MandateRequest,
    session: AsyncSession = Depends(get_db_session),
    broker_gw = Depends(get_broker_gateway),
    quant_gw = Depends(get_quant_gateway),
):
    from app.main import extract_symbol_from_mandate
    orchestrator = VoltronOrchestrator(broker_gw, quant_gw, session)
    try:
        target_symbol = extract_symbol_from_mandate(req.mandate, req.underlying)
        packet = await orchestrator.execute_mandate(
            mandate=req.mandate,
            symbol=target_symbol,
            autonomy_level=req.autonomyLevel,
        )
        return packet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies", response_model=List[StrategyCandidate])
async def get_strategies(
    symbol: str = "SPY",
    target_delta: float = 0.15,
    budget: float = 50000.0,
    quant_gw = Depends(get_quant_gateway),
    broker_gw = Depends(get_broker_gateway),
):
    symbol = symbol.strip().upper()
    try:
        ctx = await broker_gw.get_market_context(symbol)
        spot = ctx.price
    except Exception:
        spot = None

    try:
        chain = await broker_gw.get_option_chain(symbol)
        raw_contracts = [leg.model_dump() for leg in chain] if chain else None
    except Exception:
        raw_contracts = None

    return await quant_gw.generate_candidates(
        symbol, target_delta, budget, spot=spot, chain=raw_contracts
    )

@router.get("/surface", response_model=VolatilitySurface)
async def get_volatility_surface(
    symbol: str = "SPY",
    quant_gw = Depends(get_quant_gateway),
    broker_gw = Depends(get_broker_gateway),
):
    symbol = symbol.strip().upper()
    try:
        ctx = await broker_gw.get_market_context(symbol)
        spot = ctx.price
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{symbol}' not found on US exchanges or Alpaca Paper Broker. Please enter a valid symbol (e.g. SPY, PLTR, NVDA, TSLA, AAPL, QQQ)."
        )

    try:
        chain = await broker_gw.get_option_chain(symbol)
        raw_contracts = [leg.model_dump() for leg in chain] if chain else None
    except Exception:
        raw_contracts = None

    try:
        return await quant_gw.get_surface(symbol=symbol, spot=spot, chain=raw_contracts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/anomalies", response_model=List[AnomalyReport])
async def get_market_anomalies(
    symbol: str = "SPY",
    quant_gw = Depends(get_quant_gateway),
    broker_gw = Depends(get_broker_gateway),
):
    symbol = symbol.strip().upper()
    try:
        ctx = await broker_gw.get_market_context(symbol)
        spot = ctx.price
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{symbol}' not found on US exchanges or Alpaca Paper Broker. Please enter a valid symbol (e.g. SPY, PLTR, NVDA, TSLA, AAPL, QQQ)."
        )

    try:
        chain = await broker_gw.get_option_chain(symbol)
        raw_contracts = [leg.model_dump() for leg in chain] if chain else None
    except Exception:
        raw_contracts = None

    try:
        surface = await quant_gw.get_surface(symbol=symbol, spot=spot, chain=raw_contracts)
        return surface.anomalies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stress", response_model=StressReport)
async def get_stress_report(
    strategy_id: str = "strat-condor-01",
    symbol: str = "SPY",
    quant_gw = Depends(get_quant_gateway),
    broker_gw = Depends(get_broker_gateway),
):
    symbol = symbol.strip().upper()
    try:
        ctx = await broker_gw.get_market_context(symbol)
        spot = ctx.price
    except Exception:
        spot = None

    return await quant_gw.stress_test(strategy_id, spot=spot)

@router.post("/counterfactual", response_model=CounterfactualComparison)
async def get_counterfactual(
    params: Optional[dict] = None,
    quant_gw = Depends(get_quant_gateway),
    broker_gw = Depends(get_broker_gateway),
):
    p = dict(params) if params else {}
    symbol = p.get("symbol", "SPY").strip().upper()
    try:
        ctx = await broker_gw.get_market_context(symbol)
        p["spotPrice"] = ctx.price
    except Exception:
        pass
    return await quant_gw.get_counterfactual(p)

@router.get("/agents/trace/{decision_id}", response_model=List[AgentTraceStep])
async def get_agent_trace(
    decision_id: str,
    session: AsyncSession = Depends(get_db_session),
    quant_gw = Depends(get_quant_gateway),
):
    agent_repo = AgentRepository(session)
    runs = await agent_repo.get_by_decision(decision_id)
    if runs:
        steps = []
        for r in runs:
            if r.details_json:
                steps.append(AgentTraceStep.model_validate(r.details_json))
        if steps:
            return steps

    return await quant_gw.get_agent_trace(decision_id)
