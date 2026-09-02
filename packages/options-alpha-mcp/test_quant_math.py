"""
VOLTRON Canonical Quantitative Intelligence Test Suite
Validates mathematical pricing, Black-Scholes Greeks, IV inversion,
volatility surface interpolation, 25-delta skew, 7 anomaly detectors,
defined-risk strategy generation, payoff arithmetic, analytical breakevens,
lognormal estimated POP, tournament scoring, 21-scenario stress engine,
and deterministic Risk Compiler.
"""

import math
import pytest
from typing import List, Dict, Any

# We will import the modules from packages.options-alpha-mcp
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pricing import (
    black_scholes_price,
    black_scholes_greeks,
    implied_volatility,
    calculate_liquidity_score,
    OptionType,
)
from surface import (
    select_atm_strike,
    calculate_dte,
    build_term_structure,
    calculate_skew_snapshot,
    build_volatility_surface,
)
from anomalies import (
    detect_volatility_anomalies,
    calculate_parkinson_volatility,
    calculate_iv_rank_and_percentile,
)
from strategies import (
    generate_put_credit_spread,
    generate_call_credit_spread,
    generate_iron_condor,
    generate_all_candidate_structures,
    calculate_terminal_payoff,
    calculate_max_profit_loss,
    calculate_breakevens,
    estimate_probability_of_profit,
    score_strategy_candidate,
)
from stress import (
    generate_stress_matrix,
    calculate_max_profit_zone,
    evaluate_strategy_stress,
)
from risk import (
    compile_deterministic_risk,
    calculate_max_contracts,
)


class TestBlackScholesAndGreeks:
    """Mathematical verification of analytical option pricing and Greeks."""

    def test_put_call_parity(self):
        """Verify C - P = S - K * exp(-r * T) within floating precision."""
        S = 645.0
        K = 645.0
        T = 45.0 / 365.25
        r = 0.045
        sigma = 0.20

        call_price = black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        put_price = black_scholes_price(S, K, T, r, sigma, OptionType.PUT)

        lhs = call_price - put_price
        rhs = S - K * math.exp(-r * T)
        assert math.isclose(lhs, rhs, rel_tol=1e-4, abs_tol=1e-4)

    def test_greeks_signs_and_bounds(self):
        """Verify delta, gamma, theta, vega, rho bounds and signs."""
        S = 645.0
        K = 645.0
        T = 30.0 / 365.25
        r = 0.045
        sigma = 0.22

        call_greeks = black_scholes_greeks(S, K, T, r, sigma, OptionType.CALL)
        put_greeks = black_scholes_greeks(S, K, T, r, sigma, OptionType.PUT)

        # Call delta in (0, 1), Put delta in (-1, 0)
        assert 0.0 < call_greeks["delta"] < 1.0
        assert -1.0 < put_greeks["delta"] < 0.0
        # Delta parity: Delta_Call - Delta_Put = 1.0 (for non-dividend stock)
        assert math.isclose(call_greeks["delta"] - put_greeks["delta"], 1.0, rel_tol=1e-3)

        # Gamma must be positive and equal for Call and Put
        assert call_greeks["gamma"] > 0
        assert math.isclose(call_greeks["gamma"], put_greeks["gamma"], rel_tol=1e-4)

        # Vega must be positive and equal for Call and Put
        assert call_greeks["vega"] > 0
        assert math.isclose(call_greeks["vega"], put_greeks["vega"], rel_tol=1e-4)

        # Theta is typically negative for long options
        assert call_greeks["theta"] < 0
        assert put_greeks["theta"] < 0

    def test_implied_volatility_inversion(self):
        """Invert market prices back to exact implied volatility via Brent's method."""
        S = 645.0
        K = 650.0
        T = 45.0 / 365.25
        r = 0.045
        true_iv = 0.265

        call_mkt = black_scholes_price(S, K, T, r, true_iv, OptionType.CALL)
        recovered_iv = implied_volatility(call_mkt, S, K, T, r, OptionType.CALL)
        assert math.isclose(recovered_iv, true_iv, rel_tol=1e-3)

        put_mkt = black_scholes_price(S, K, T, r, true_iv, OptionType.PUT)
        recovered_put_iv = implied_volatility(put_mkt, S, K, T, r, OptionType.PUT)
        assert math.isclose(recovered_put_iv, true_iv, rel_tol=1e-3)

    def test_strike_from_delta_accuracy(self):
        """Verify analytical strike inversion from target delta matches Black-Scholes Greeks."""
        from pricing import strike_from_delta
        S = 645.31
        T = 45.0 / 365.25
        r = 0.045
        vol = 0.22
        target_delta = 0.15

        # 15-delta Call
        k_call = strike_from_delta(S, target_delta, T, vol, r, is_call=True)
        g_call = black_scholes_greeks(S, k_call, T, r, vol, OptionType.CALL)
        assert math.isclose(g_call["delta"], target_delta, abs_tol=0.005)

        # 15-delta Put (delta is -0.15)
        k_put = strike_from_delta(S, target_delta, T, vol, r, is_call=False)
        g_put = black_scholes_greeks(S, k_put, T, r, vol, OptionType.PUT)
        assert math.isclose(abs(g_put["delta"]), target_delta, abs_tol=0.005)

        # Wing monotonicity
        assert k_put < S < k_call

    def test_liquidity_scoring_composite(self):
        """Verify liquidity score composite weighting and edge cases."""
        # Perfect liquidity (tight spread, high OI, high volume)
        score_high = calculate_liquidity_score(bid=5.00, ask=5.02, volume=10000, open_interest=50000)
        assert score_high >= 90

        # Poor liquidity (wide spread, low volume, zero OI)
        score_low = calculate_liquidity_score(bid=1.00, ask=2.50, volume=5, open_interest=10)
        assert score_low < 50

        # Zero bid/ask handling (must return 0, no crash)
        score_zero = calculate_liquidity_score(bid=0.0, ask=0.0, volume=0, open_interest=0)
        assert score_zero == 0


class TestSurfaceAndSkew:
    """Verification of ATM strike selection, term structure, and skew snapshot."""

    def test_select_atm_strike(self):
        strikes = [620.0, 625.0, 630.0, 635.0, 640.0, 645.0, 650.0, 655.0]
        # Exact match
        assert select_atm_strike(645.0, strikes) == 645.0
        # Between strikes (closer to 645)
        assert select_atm_strike(646.2, strikes) == 645.0
        # Between strikes (closer to 650)
        assert select_atm_strike(648.1, strikes) == 650.0

    def test_skew_snapshot_calculations(self):
        """Verify 25D Put, ATM, 25D Call IV and skew ratio."""
        put_25d_iv = 0.245
        atm_iv = 0.198
        call_25d_iv = 0.182

        skew = calculate_skew_snapshot(put_25d_iv, atm_iv, call_25d_iv)
        expected_ratio = round(put_25d_iv / call_25d_iv, 2)
        assert skew["skewRatio"] == expected_ratio
        assert skew["put25DeltaIV"] == round(put_25d_iv * 100.0, 1)
        assert skew["call25DeltaIV"] == round(call_25d_iv * 100.0, 1)
        assert skew["atmIV"] == round(atm_iv * 100.0, 1)


class TestDefinedRiskStrategiesAndPayoffs:
    """Verification of Put Credit Spread, Call Credit Spread, Iron Condor, Payoff, and Breakevens."""

    def test_put_credit_spread_payoff_and_breakeven(self):
        """
        Put Credit Spread:
        Sell 630 Put @ 3.43 (mid)
        Buy 625 Put @ 1.27 (mid)
        Net Credit = 2.16 ($216.00)
        Spread Width = 5.0 ($500.00)
        Max Profit = $216.00
        Max Loss = 500 - 216 = $284.00
        Breakeven = 630 - 2.16 = 628.84 (or 635 - 2.16 = 632.84 if strikes 635/630)
        """
        short_strike = 635.0
        long_strike = 630.0
        net_credit = 2.16

        bounds = calculate_max_profit_loss(
            strategy_name="Put Credit Spread",
            short_strike_1=short_strike,
            long_strike_1=long_strike,
            net_credit=net_credit,
        )
        assert bounds["maxProfit"] == 216.0
        assert bounds["maxLoss"] == 284.0

        be = calculate_breakevens(
            strategy_name="Put Credit Spread",
            short_strike_1=short_strike,
            long_strike_1=long_strike,
            net_credit=net_credit,
        )
        assert len(be) == 1
        assert math.isclose(be[0], 632.84, abs_tol=1e-2)

        # Terminal payoff tests across price points
        # Above short strike -> Full max profit
        assert math.isclose(calculate_terminal_payoff(645.0, "Put Credit Spread", [long_strike, short_strike], net_credit), 216.0)
        # Below long strike -> Full max loss (-$284.00)
        assert math.isclose(calculate_terminal_payoff(620.0, "Put Credit Spread", [long_strike, short_strike], net_credit), -284.0)
        # Exactly at breakeven -> PnL is 0.0
        assert math.isclose(calculate_terminal_payoff(632.84, "Put Credit Spread", [long_strike, short_strike], net_credit), 0.0, abs_tol=1e-1)

    def test_iron_condor_payoff_and_breakevens(self):
        """
        Iron Condor:
        Put Wing: Buy 625P @ 1.10, Sell 630P @ 1.85 (Credit = 0.75)
        Call Wing: Sell 660C @ 1.45, Buy 665C @ 0.82 (Credit = 0.63)
        Total Net Credit = 1.38 ($138.00)
        Wing Width = 5.0 ($500.00)
        Max Profit = $138.00
        Max Loss = 500 - 138 = $362.00
        Lower Breakeven = 630 - 1.38 = 628.62
        Upper Breakeven = 660 + 1.38 = 661.38
        """
        lp, sp, sc, lc = 625.0, 630.0, 660.0, 665.0
        net_credit = 1.38

        bounds = calculate_max_profit_loss(
            strategy_name="Iron Condor",
            short_strike_1=sp,
            long_strike_1=lp,
            short_strike_2=sc,
            long_strike_2=lc,
            net_credit=net_credit,
        )
        assert bounds["maxProfit"] == 138.0
        assert bounds["maxLoss"] == 362.0

        bes = calculate_breakevens(
            strategy_name="Iron Condor",
            short_strike_1=sp,
            long_strike_1=lp,
            short_strike_2=sc,
            long_strike_2=lc,
            net_credit=net_credit,
        )
        assert len(bes) == 2
        assert math.isclose(bes[0], 628.62, abs_tol=1e-2)
        assert math.isclose(bes[1], 661.38, abs_tol=1e-2)

        # Payoff between short strikes -> Full profit ($138.00)
        assert math.isclose(calculate_terminal_payoff(645.0, "Iron Condor", [lp, sp, sc, lc], net_credit), 138.0)
        # Deep downside -> Max loss (-$362.00)
        assert math.isclose(calculate_terminal_payoff(610.0, "Iron Condor", [lp, sp, sc, lc], net_credit), -362.0)
        # Deep upside -> Max loss (-$362.00)
        assert math.isclose(calculate_terminal_payoff(680.0, "Iron Condor", [lp, sp, sc, lc], net_credit), -362.0)
        # At lower breakeven -> PnL 0
        assert math.isclose(calculate_terminal_payoff(628.62, "Iron Condor", [lp, sp, sc, lc], net_credit), 0.0, abs_tol=1e-1)
        # At upper breakeven -> PnL 0
        assert math.isclose(calculate_terminal_payoff(661.38, "Iron Condor", [lp, sp, sc, lc], net_credit), 0.0, abs_tol=1e-1)

    def test_lognormal_pop_model(self):
        """Verify POP calculation produces valid probability in (0, 1) and behaves monotonically."""
        S = 645.0
        sigma = 0.20
        T = 45.0 / 365.25
        r = 0.045

        # Wide breakevens should have higher POP than narrow breakevens
        pop_wide = estimate_probability_of_profit(S, [620.0, 670.0], sigma, T, r)
        pop_narrow = estimate_probability_of_profit(S, [635.0, 655.0], sigma, T, r)

        assert 0.0 < pop_wide < 1.0
        assert 0.0 < pop_narrow < 1.0
        assert pop_wide > pop_narrow


class TestStressAndRiskCompiler:
    """Verification of 21-scenario stress engine and deterministic risk compiler."""

    def test_21_stress_matrix_scenarios(self):
        """Stress matrix must contain exactly 21 scenarios (7 price shifts x 3 IV shifts)."""
        spot = 645.0
        legs = [
            {"strike": 625.0, "type": "PUT", "side": "BUY", "ratio": 1, "bid": 1.08, "ask": 1.12, "mid": 1.10, "iv": 0.284},
            {"strike": 630.0, "type": "PUT", "side": "SELL", "ratio": 1, "bid": 1.83, "ask": 1.87, "mid": 1.85, "iv": 0.265},
            {"strike": 660.0, "type": "CALL", "side": "SELL", "ratio": 1, "bid": 1.43, "ask": 1.47, "mid": 1.45, "iv": 0.224},
            {"strike": 665.0, "type": "CALL", "side": "BUY", "ratio": 1, "bid": 0.80, "ask": 0.84, "mid": 0.82, "iv": 0.218},
        ]
        dte = 45
        net_credit = 1.38

        matrix = generate_stress_matrix(spot, dte, legs, net_credit)
        assert len(matrix) == 21, f"Expected 21 stress scenarios, got {len(matrix)}"

        # Check that spot shifts are -10%, -5%, -3%, 0%, +3%, +5%, +10% (or standard 7 shifts)
        price_shifts = sorted(list(set(m["priceShiftPct"] for m in matrix)))
        assert len(price_shifts) == 7
        iv_shifts = sorted(list(set(m["ivShiftPct"] for m in matrix)))
        assert len(iv_shifts) == 3
        assert iv_shifts == [-20.0, 0.0, 20.0]

    def test_deterministic_risk_compiler_rules(self):
        """Verify hard limits: budget (5%), liquidity (>=70), tail risk verification."""
        equity = 100000.0

        # 1. Compliant Strategy -> Approved
        valid_strat = {
            "id": "strat-1",
            "name": "Iron Condor",
            "maxLoss": 362.0,
            "liquidityScore": 92,
            "underlying": "SPY",
        }
        res = compile_deterministic_risk(valid_strat, equity)
        assert res["isApproved"] is True
        assert res["budgetCheck"]["passed"] is True
        assert res["liquidityCheck"]["passed"] is True

        # 2. Oversized Max Loss (> 5% of equity = $5,000) -> Rejected
        oversized_strat = {
            "id": "strat-2",
            "name": "Oversized Spread",
            "maxLoss": 7500.0,
            "liquidityScore": 85,
            "underlying": "SPY",
        }
        res_oversized = compile_deterministic_risk(oversized_strat, equity)
        assert res_oversized["isApproved"] is False
        assert res_oversized["budgetCheck"]["status"] == "FAIL"

        # 3. Poor Liquidity (< 70) -> Rejected
        illiquid_strat = {
            "id": "strat-3",
            "name": "Illiquid Condor",
            "maxLoss": 300.0,
            "liquidityScore": 55,
            "underlying": "SPY",
        }
        res_illiquid = compile_deterministic_risk(illiquid_strat, equity)
        assert res_illiquid["isApproved"] is False
        assert res_illiquid["liquidityCheck"]["status"] == "FAIL"

        # 4. Undefined Risk (Max loss = 99999 or unbounded) -> Rejected
        unbounded_strat = {
            "id": "strat-4",
            "name": "Short Straddle",
            "maxLoss": 99999.0,
            "liquidityScore": 95,
            "underlying": "SPY",
        }
        res_unbounded = compile_deterministic_risk(unbounded_strat, equity)
        assert res_unbounded["isApproved"] is False

    def test_position_sizing_calculation(self):
        """Verify integer contract sizing: max_loss * qty <= budget."""
        equity = 100000.0
        max_loss_per_contract = 362.0
        # 5% budget limit = $5,000 / $362 = 13.8 -> 13 contracts
        qty = calculate_max_contracts(max_loss_per_contract, equity, max_budget_pct=0.05)
        assert qty == 13
        assert qty * max_loss_per_contract <= 5000.0


class TestJsonRpcMcpServer:
    """Verification of JSON-RPC 2.0 dispatch handlers on the Voltron Options MCP server."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_rpc_get_surface(self, client):
        resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "get_surface", "params": {"symbol": "SPY"}, "id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert "result" in data
        res = data["result"]
        assert res["underlying"] == "SPY"
        assert len(res["points"]) >= 4
        assert "skewSnapshot" in res
        assert "termStructure" in res

    def test_rpc_detect_anomalies(self, client):
        resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "detect_anomalies", "params": {"symbol": "SPY"}, "id": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["result"]) >= 1

    def test_rpc_generate_candidates(self, client):
        resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "generate_candidates", "params": {"symbol": "SPY", "target_delta": 0.15, "max_budget": 50000.0}, "id": 3})
        assert resp.status_code == 200
        candidates = resp.json()["result"]
        assert len(candidates) >= 3
        # First candidate is winning defined-risk structure
        assert candidates[0]["isWinner"] is True
        assert candidates[0]["maxLoss"] > 0
        assert len(candidates[0]["legs"]) >= 2

    def test_rpc_stress_test(self, client):
        resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "stress_test", "params": {"strategy_id": "strat-condor-01"}, "id": 4})
        assert resp.status_code == 200
        stress = resp.json()["result"]
        assert len(stress["matrix"]) == 21
        assert "maxProfitZone" in stress

    def test_rpc_compile_risk(self, client):
        strat = {"id": "strat-1", "name": "Iron Condor", "maxLoss": 362.0, "liquidityScore": 92, "underlying": "SPY"}
        resp = client.post("/rpc", json={"jsonrpc": "2.0", "method": "compile_risk", "params": {"strategy": strat, "portfolio_equity": 100000.0}, "id": 5})
        assert resp.status_code == 200
        risk = resp.json()["result"]
        assert risk["isApproved"] is True
        assert risk["budgetCheck"]["passed"] is True

    def test_jade_lizard_and_iron_butterfly(self):
        from strategies import generate_jade_lizard, generate_iron_butterfly, generate_all_candidate_structures, get_bandit_metrics
        # 1. Jade Lizard
        jl = generate_jade_lizard("SPY", 600.0, dte=30, wing_width=5.0)
        assert jl["name"].startswith("Jade Lizard")
        assert len(jl["legs"]) == 3
        assert jl["zeroUpsideRisk"] is True
        assert jl["pop"] >= 0.70
        assert len(jl["breakevens"]) == 1

        # 2. Iron Butterfly
        ib = generate_iron_butterfly("SPY", 600.0, dte=30, wing_width=5.0)
        assert ib["name"].startswith("Iron Butterfly")
        assert len(ib["legs"]) == 4
        assert ib["maxProfit"] > 0
        assert len(ib["breakevens"]) == 2

        # 3. Dynamic tournament candidates
        cands = generate_all_candidate_structures("SPY", 600.0)
        assert len(cands) >= 6
        winner = next(c for c in cands if c.get("isWinner"))
        assert winner["rank"] == 1
        assert winner["score"] > 50.0

        # 4. Bandit metrics
        meta = get_bandit_metrics("JADE_LIZARD")
        assert meta["expectedWinRate"] > 0.75
        assert meta["banditMultiplier"] > 1.0

