from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Set
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database.session import init_db, get_db_session
from app.api.deps import get_broker_gateway, get_quant_gateway
from app.agents.orchestrator import VoltronOrchestrator
from app.domain.models import MandateRequest, DecisionPacket
from app.api.routes import health, telemetry, decisions, scan, orders, events, replay, history, portfolio
from app.api.routes import settings as settings_route

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trading stop words to filter out when extracting ticker symbols
TRADING_STOP_WORDS = {
    "BUY", "SELL", "CALL", "PUT", "WITH", "RISK", "FOR", "THE", "SCAN", "RUN", "MODE",
    "AUTO", "TRADE", "DELTA", "WING", "SKEW", "IRON", "SPREAD", "CONDOR", "CREDIT",
    "DEBIT", "HIGH", "LOW", "LONG", "SHORT", "AND", "OUT", "IN", "TO", "ON", "FIND",
    "LOOK", "OPEN", "CLOSE", "EXIT", "STOP", "LOSS", "TARGET", "MAX", "MIN", "RATE",
    "VOL", "DAYS", "DTE", "CASH", "BASKET", "STOCK", "STOCKS", "OPTION", "OPTIONS",
    "LEGS", "LEG", "ENTRY", "MARK", "TIME", "PRICE", "GAIN", "WIN", "DROP", "SHOCK",
    "CRASH", "AI", "MCP", "HARVEST", "SEEK", "BUILD", "NEUTRAL", "BETA", "ANALYZE"
}

def extract_symbol_from_mandate(mandate: str, explicit: Optional[str] = None) -> str:
    if explicit and explicit.upper() != "SPY":
        return explicit.strip().upper()
    if not mandate:
        return explicit.upper() if explicit else "SPY"
    import re
    # 1. Preposition match (e.g. 'on PLTR', 'for NVDA', 'symbol AMD')
    m_prep = re.search(r"\b(?:on|for|in|stock|symbol|ticker|analyze|harvest|trade)\s+([A-Za-z]{1,6})\b", mandate, re.IGNORECASE)
    if m_prep:
        candidate = m_prep.group(1).upper()
        if candidate not in TRADING_STOP_WORDS:
            return candidate
    # 2. Uppercase tokens
    for tok in re.findall(r"\b[A-Z]{2,6}\b", mandate):
        if tok not in TRADING_STOP_WORDS:
            return tok
    # 3. Known high-liquidity symbols (case-insensitive)
    known = {"PLTR", "COIN", "SMCI", "AMD", "NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "GOOGL", "GOOG", "QQQ", "IWM", "SPY", "ARM", "DIS", "NFLX", "AVGO", "UBER", "BABA", "BA", "GLD", "TLT"}
    for w in re.findall(r"\b[A-Za-z]{2,6}\b", mandate):
        if w.upper() in known:
            return w.upper()
    return explicit.upper() if explicit else "SPY"

# Direct root scan endpoint (/api/scan)
@app.post(f"{settings.API_PREFIX}/scan", response_model=DecisionPacket, tags=["Mandates"])
async def run_mandate_scan(
    req: MandateRequest,
    session: AsyncSession = Depends(get_db_session),
    broker_gw = Depends(get_broker_gateway),
    quant_gw = Depends(get_quant_gateway),
):
    orchestrator = VoltronOrchestrator(broker_gw, quant_gw, session)
    try:
        target_symbol = extract_symbol_from_mandate(req.mandate, req.underlying)
        try:
            await broker_gw.get_market_context(target_symbol)
        except Exception:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{target_symbol}' not found on US exchanges or Alpaca Paper Broker. Please provide a valid ticker (e.g. SPY, PLTR, NVDA, TSLA, AAPL, QQQ)."
            )
        return await orchestrator.execute_mandate(
            mandate=req.mandate,
            symbol=target_symbol,
            autonomy_level=req.autonomyLevel,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Register API Routers under settings.API_PREFIX (/api)
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(telemetry.router, prefix=settings.API_PREFIX)
app.include_router(decisions.router, prefix=settings.API_PREFIX)
app.include_router(scan.router, prefix=settings.API_PREFIX)
app.include_router(orders.router, prefix=settings.API_PREFIX)
app.include_router(events.router, prefix=settings.API_PREFIX)
app.include_router(replay.router, prefix=settings.API_PREFIX)
app.include_router(history.router, prefix=settings.API_PREFIX)
app.include_router(portfolio.router, prefix=settings.API_PREFIX)
app.include_router(settings_route.router)

@app.get("/")
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
