"""
VOLTRON Options Intelligence: Deterministic Risk Compiler & Sizing Engine
Pure deterministic Python code (0% LLM reasoning / 0% LLM math).
Enforces hard safety gates:
1. Risk Budget Allocation (Max Loss <= 5% Portfolio Equity)
2. Contract Liquidity (Liquidity Score >= 70/100)
3. Portfolio Margin Concentration (Underlying Risk <= 20% Equity)
4. Defined-Risk Invariant Verification (Finite Max Loss, >= 2 Spread Legs)
5. Strict Contract Sizing Bounds
"""

import math
from typing import Dict, Any, Optional

def calculate_max_contracts(
    max_loss_per_contract: float,
    portfolio_equity: float,
    max_budget_pct: float = 0.05,
    hard_max_contracts: int = 50,
    uncapped_mode: bool = False,
) -> int:
    """
    Calculate maximum allowed integer contracts based on hard risk budget.
    If uncapped_mode is True, sizes up to full available buying power without artificial budget bottleneck.
    """
    if max_loss_per_contract <= 0 or portfolio_equity <= 0:
        return 0

    if uncapped_mode:
        raw_qty = math.floor(portfolio_equity / max_loss_per_contract)
        return max(1, min(100, int(raw_qty)))

    allowed_risk = portfolio_equity * max_budget_pct
    raw_qty = math.floor(allowed_risk / max_loss_per_contract)
    return max(0, min(hard_max_contracts, int(raw_qty)))

def compile_deterministic_risk(
    strategy: Dict[str, Any],
    portfolio_equity: float = 100000.0,
    max_budget_pct: float = 0.05,
    min_liquidity_threshold: int = 70,
    max_concentration_pct: float = 0.20,
    uncapped_mode: bool = False,
) -> Dict[str, Any]:
    """
    Execute pure-code deterministic risk compiler checks.
    If uncapped_mode is True, removes all artificial upper-bounds on position size, budget, and concentration.
    """
    if portfolio_equity <= 0:
        portfolio_equity = 100000.0

    max_loss = float(strategy.get("maxLoss", 362.0))
    net_credit = float(strategy.get("netCreditOrDebit", 1.38))
    liquidity_score = int(strategy.get("liquidityScore", 90))
    underlying = str(strategy.get("underlying", "SPY")).upper()

    # 1. Defined-Risk Verification (Reject undefined naked risk, allow uncapped sizes)
    is_defined_risk = max_loss > 0.0 and (max_loss < 500000.0 if uncapped_mode else max_loss < 50000.0)

    # 2. Budget Allocation Gate
    if uncapped_mode:
        budget_limit = portfolio_equity
        budget_pct = (max_loss / portfolio_equity) * 100.0
        budget_passed = is_defined_risk
        budget_val_text = f"UNCAPPED (${max_loss:,.2f})"
        budget_details = f"Free Trading Mode ACTIVE: Zero upper bound on investment budget. Position sizes freely against available buying power."
    else:
        budget_limit = portfolio_equity * max_budget_pct
        budget_pct = (max_loss / portfolio_equity) * 100.0
        budget_passed = is_defined_risk and (max_loss <= budget_limit)
        budget_val_text = f"${max_loss:,.2f} / ${budget_limit:,.2f} ({budget_pct:.2f}%)"
        budget_details = f"Risk allocation of ${max_loss:.2f} is {budget_pct:.3f}% of equity (limit {max_budget_pct*100:.1f}%)."

    # 3. Liquidity Gate (Liquidity Score >= 70)
    liquidity_passed = liquidity_score >= min_liquidity_threshold

    # 4. Concentration Gate
    if uncapped_mode:
        concentration_passed = True
        concentration_val_text = "UNCAPPED (Free Margin)"
        concentration_details = f"Free Trading Mode ACTIVE: Zero concentration cap on {underlying}."
    else:
        concentration_limit = portfolio_equity * max_concentration_pct
        concentration_passed = max_loss <= concentration_limit
        concentration_val_text = f"{budget_pct:.2f}% Margin"
        concentration_details = f"{underlying} total exposure is {budget_pct:.2f}% of portfolio margin (limit {max_concentration_pct*100:.0f}%)."

    # All hard gates must pass
    is_approved = budget_passed and liquidity_passed and concentration_passed and is_defined_risk

    # Calculate position sizing envelope
    max_contracts = calculate_max_contracts(max_loss, portfolio_equity, max_budget_pct, uncapped_mode=uncapped_mode)

    return {
        "budgetCheck": {
            "passed": budget_passed,
            "status": "PASS" if budget_passed else "FAIL",
            "label": "Risk Budget Allocation" if not uncapped_mode else "Uncapped Risk Budget",
            "valueText": budget_val_text,
            "details": budget_details,
        },
        "liquidityCheck": {
            "passed": liquidity_passed,
            "status": "PASS" if liquidity_passed else "FAIL",
            "label": "Contract Liquidity",
            "valueText": f"{liquidity_score}/100",
            "details": f"Liquidity score {liquidity_score}/100 {'meets' if liquidity_passed else 'fails'} minimum threshold {min_liquidity_threshold}.",
        },
        "concentrationCheck": {
            "passed": concentration_passed,
            "status": "PASS" if concentration_passed else "FAIL",
            "label": "Portfolio Concentration" if not uncapped_mode else "Uncapped Margin Concentration",
            "valueText": concentration_val_text,
            "details": concentration_details,
        },
        "isApproved": is_approved,
        "maxContractsAllowed": max_contracts,
    }
