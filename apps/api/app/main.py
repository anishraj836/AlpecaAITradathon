from contextlib import asynccontextmanager
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
        target_symbol = req.underlying or "SPY"
        if target_symbol == "SPY" and req.mandate:
            import re
            m = re.search(r"\b(QQQ|NVDA|AAPL|TSLA|IWM|MSFT|AMZN|META|AMD|SPY)\b", req.mandate, re.IGNORECASE)
            if m:
                target_symbol = m.group(1).upper()

        return await orchestrator.execute_mandate(
            mandate=req.mandate,
            symbol=target_symbol,
            autonomy_level=req.autonomyLevel,
        )
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
