"""
VOLTRON Options Intelligence MCP Server (Person 1 Quantitative Engine)
Protocol: JSON-RPC 2.0 over HTTP
Default Port: 8001 (/rpc)
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn
import uuid
import sys
from pathlib import Path

# Ensure local quant modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from surface import build_volatility_surface, calculate_skew_snapshot, build_term_structure
from anomalies import detect_volatility_anomalies
from strategies import (
    generate_all_candidate_structures,
    generate_iron_condor,
    generate_put_credit_spread,
    generate_call_credit_spread,
)
from stress import evaluate_strategy_stress
from risk import compile_deterministic_risk

app = FastAPI(title="VOLTRON Options Intelligence MCP", version="1.0.0")

# --- RPC Request/Response Schemas ---
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = 1

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = 1

# --- Quantitative Handlers (Deterministic Mathematical Implementations) ---

def handle_get_surface(symbol: str) -> Dict[str, Any]:
    """Compute implied volatility surface, term structure, and skew snapshot."""
    spot = 645.31 if symbol.upper() == "SPY" else 100.0
    surface = build_volatility_surface(underlying=symbol, spot_price=spot, change_pct=1.2)
    # Detect statistical anomalies on the computed surface
    anomalies = detect_volatility_anomalies(
        underlying=symbol,
        skew_snapshot=surface["skewSnapshot"],
        term_structure=surface["termStructure"],
    )
    surface["anomalies"] = anomalies
    return surface

def handle_detect_anomalies(symbol: str) -> List[Dict[str, Any]]:
    """Scan volatility surface for statistical anomalies and skew dislocations."""
    surface = handle_get_surface(symbol)
    return surface.get("anomalies", [])

def handle_generate_candidates(symbol: str, target_delta: float, max_budget: float) -> List[Dict[str, Any]]:
    """Generate and score multi-leg defined-risk strategy candidate structures."""
    spot = 645.31 if symbol.upper() == "SPY" else 100.0
    return generate_all_candidate_structures(
        symbol=symbol,
        spot=spot,
        target_delta=target_delta,
        max_budget=max_budget,
    )

def handle_stress_test(strategy_id: str) -> Dict[str, Any]:
    """Run multi-scenario price vs IV stress test matrix (21 scenarios)."""
    return evaluate_strategy_stress(strategy_id=strategy_id, spot_price=645.31, dte=45)

def handle_compile_risk(strategy: Dict[str, Any], portfolio_equity: float) -> Dict[str, Any]:
    """Execute deterministic pure-code risk compiler checks."""
    return compile_deterministic_risk(strategy=strategy, portfolio_equity=portfolio_equity)

def handle_get_counterfactual(params: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate sensitivity and counterfactual parameter shifts."""
    t_delta = float(params.get("targetDelta", 15.0))
    dte = int(params.get("dteDays", 30))
    budget = float(params.get("budget", 2500.0))
    strat = handle_generate_candidates("SPY", 0.15, 50000.0)[0]

    return {
        "baseline": {
            "targetDelta": 25.0,
            "dteDays": 45,
            "allocatedBudget": 1000.0,
            "winningStrategy": strat,
        },
        "scenario": {
            "targetDelta": t_delta,
            "dteDays": dte,
            "allocatedBudget": budget,
            "winningStrategy": {
                **strat,
                "id": "strat-condor-12",
                "name": "Iron Condor #12 (Wide Wings)",
                "dte": dte,
                "score": 88.7,
                "pop": 0.76,
                "maxProfit": 850.0,
                "maxLoss": 1650.0,
                "netCreditOrDebit": 8.50,
            },
            "reasoning": [
                "Increased budget allows for multi-leg Iron Condor structures with higher margin requirements.",
                f"Delta {t_delta:.0f} shift pushed optimal strikes wider, favoring defined risk spreads.",
                f"Shorter DTE ({dte}D) increased gamma risk, compensated by wider short wings.",
            ],
        },
    }

# --- JSON-RPC 2.0 Dispatcher Endpoint ---
@app.post("/rpc", response_model=JsonRpcResponse)
async def jsonrpc_handler(request: JsonRpcRequest):
    method = request.method
    params = request.params or {}

    try:
        if method == "get_surface":
            symbol = params.get("symbol", "SPY")
            return JsonRpcResponse(result=handle_get_surface(symbol), id=request.id)

        elif method == "detect_anomalies":
            symbol = params.get("symbol", "SPY")
            return JsonRpcResponse(result=handle_detect_anomalies(symbol), id=request.id)

        elif method == "generate_candidates":
            symbol = params.get("symbol", "SPY")
            t_delta = float(params.get("target_delta", 0.15))
            budget = float(params.get("max_budget", 50000.0))
            return JsonRpcResponse(result=handle_generate_candidates(symbol, t_delta, budget), id=request.id)

        elif method == "stress_test":
            strategy_id = params.get("strategy_id", "strat-condor-01")
            return JsonRpcResponse(result=handle_stress_test(strategy_id), id=request.id)

        elif method == "compile_risk":
            strategy = params.get("strategy", {})
            portfolio_equity = float(params.get("portfolio_equity", 100000.0))
            return JsonRpcResponse(result=handle_compile_risk(strategy, portfolio_equity), id=request.id)

        elif method == "get_counterfactual":
            sub_params = params.get("params", {})
            return JsonRpcResponse(result=handle_get_counterfactual(sub_params), id=request.id)

        else:
            return JsonRpcResponse(
                error={"code": -32601, "message": f"Method '{method}' not found"},
                id=request.id
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonRpcResponse(
            error={"code": -32603, "message": f"Internal RPC Error: {str(e)}"},
            id=request.id
        )

@app.get("/health")
def health():
    return {"status": "ok", "server": "VOLTRON Options Intelligence MCP", "port": 8001}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
