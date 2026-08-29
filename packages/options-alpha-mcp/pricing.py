"""
VOLTRON Options Intelligence: Core Pricing & Greeks Engine
Provides closed-form Black-Scholes-Merton European option pricing,
analytical Greeks (Delta, Gamma, Theta, Vega, Rho),
numerical Implied Volatility inversion (Brent's method),
and multi-factor contract liquidity scoring.
"""

import math
from enum import Enum
from typing import Dict, Any, Optional

class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"

def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function Phi(x)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_pdf(x: float) -> float:
    """Standard normal probability density function phi(x)."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def calculate_d1_d2(
    spot: float,
    strike: float,
    time_to_exp: float,
    rate: float,
    vol: float,
) -> tuple[float, float]:
    """Calculate d1 and d2 for Black-Scholes formulas."""
    if spot <= 0 or strike <= 0 or time_to_exp <= 0 or vol <= 0:
        return 0.0, 0.0
    vol_sqrt_t = vol * math.sqrt(time_to_exp)
    d1 = (math.log(spot / strike) + (rate + 0.5 * vol * vol) * time_to_exp) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2

def black_scholes_price(
    spot: float,
    strike: float,
    time_to_exp: float,
    rate: float,
    vol: float,
    option_type: OptionType = OptionType.CALL,
) -> float:
    """
    Compute analytical Black-Scholes European option price.
    
    Parameters:
    - spot (S): Current underlying spot price
    - strike (K): Option strike price
    - time_to_exp (T): Annualized time to expiration (DTE / 365.25)
    - rate (r): Annualized risk-free interest rate (e.g. 0.045 for 4.5%)
    - vol (sigma): Implied volatility (e.g. 0.22 for 22%)
    - option_type: OptionType.CALL or OptionType.PUT
    """
    if time_to_exp <= 0:
        # At expiration: pure intrinsic value
        if option_type == OptionType.CALL or str(option_type).upper() == "CALL":
            return max(0.0, spot - strike)
        else:
            return max(0.0, strike - spot)

    if vol <= 0 or spot <= 0 or strike <= 0:
        return max(0.0, spot - strike) if str(option_type).upper() == "CALL" else max(0.0, strike - spot)

    d1, d2 = calculate_d1_d2(spot, strike, time_to_exp, rate, vol)
    discount = math.exp(-rate * time_to_exp)

    if option_type == OptionType.CALL or str(option_type).upper() == "CALL":
        price = spot * _norm_cdf(d1) - strike * discount * _norm_cdf(d2)
    else:
        price = strike * discount * _norm_cdf(-d2) - spot * _norm_cdf(-d1)

    return max(0.0, price)

def black_scholes_greeks(
    spot: float,
    strike: float,
    time_to_exp: float,
    rate: float,
    vol: float,
    option_type: OptionType = OptionType.CALL,
) -> Dict[str, float]:
    """
    Compute exact analytical Greeks for European options.
    
    Returns dictionary with:
    - delta: Sensitivity to spot price
    - gamma: Second derivative w.r.t spot price (per $1 shift)
    - theta: Daily time decay ($ / day)
    - vega: Sensitivity to 1% (0.01) shift in volatility
    - rho: Sensitivity to 1% shift in interest rate
    """
    is_call = option_type == OptionType.CALL or str(option_type).upper() == "CALL"

    if time_to_exp <= 1e-6 or vol <= 1e-6 or spot <= 0 or strike <= 0:
        intrin_delta = (1.0 if spot > strike else 0.0) if is_call else (-1.0 if strike > spot else 0.0)
        return {"delta": intrin_delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

    d1, d2 = calculate_d1_d2(spot, strike, time_to_exp, rate, vol)
    sqrt_t = math.sqrt(time_to_exp)
    pdf_d1 = _norm_pdf(d1)
    discount = math.exp(-rate * time_to_exp)

    # 1. Delta
    if is_call:
        delta = _norm_cdf(d1)
    else:
        delta = _norm_cdf(d1) - 1.0

    # 2. Gamma (identical for Call and Put)
    gamma = pdf_d1 / (spot * vol * sqrt_t)

    # 3. Vega (per 1 percentage point shift in vol)
    vega = (spot * pdf_d1 * sqrt_t) * 0.01

    # 4. Theta (daily decay = annualized / 365.25)
    term1 = -(spot * pdf_d1 * vol) / (2.0 * sqrt_t)
    if is_call:
        term2 = -rate * strike * discount * _norm_cdf(d2)
        theta_annual = term1 + term2
    else:
        term2 = rate * strike * discount * _norm_cdf(-d2)
        theta_annual = term1 + term2
    theta_daily = theta_annual / 365.25

    # 5. Rho (per 1 percentage point shift in rate)
    if is_call:
        rho = (strike * time_to_exp * discount * _norm_cdf(d2)) * 0.01
    else:
        rho = (-strike * time_to_exp * discount * _norm_cdf(-d2)) * 0.01

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta_daily, 4),
        "vega": round(vega, 4),
        "rho": round(rho, 4),
    }

def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    time_to_exp: float,
    rate: float,
    option_type: OptionType = OptionType.CALL,
    initial_guess: float = 0.25,
    max_iterations: int = 100,
    tolerance: float = 1e-5,
) -> float:
    """
    Recover exact implied volatility from market price using Brent-Dekker / Newton root finding.
    Returns annualized volatility sigma in [0.001, 5.0].
    """
    is_call = option_type == OptionType.CALL or str(option_type).upper() == "CALL"
    intrinsic = max(0.0, spot - strike) if is_call else max(0.0, strike - spot)

    if market_price <= intrinsic + 1e-4:
        return 0.05

    # Bracket search [a, b]
    low_vol = 0.001
    high_vol = 5.000

    price_low = black_scholes_price(spot, strike, time_to_exp, rate, low_vol, option_type)
    if price_low >= market_price:
        return low_vol

    price_high = black_scholes_price(spot, strike, time_to_exp, rate, high_vol, option_type)
    if price_high <= market_price:
        return high_vol

    # Bisection / Newton-Raphson hybrid
    vol = initial_guess
    for _ in range(max_iterations):
        p = black_scholes_price(spot, strike, time_to_exp, rate, vol, option_type)
        diff = p - market_price

        if abs(diff) < tolerance:
            return round(vol, 4)

        greeks = black_scholes_greeks(spot, strike, time_to_exp, rate, vol, option_type)
        vega_total = greeks["vega"] * 100.0  # un-scale vega from 1% to 1.0

        if vega_total > 1e-4:
            new_vol = vol - diff / vega_total
            if low_vol < new_vol < high_vol:
                vol = new_vol
                continue

        # Fallback to Bisection if Newton steps out of bounds
        if diff > 0:
            high_vol = vol
        else:
            low_vol = vol
        vol = 0.5 * (low_vol + high_vol)

    return round(vol, 4)

def calculate_liquidity_score(
    bid: float,
    ask: float,
    volume: int = 0,
    open_interest: int = 0,
) -> int:
    """
    Multi-Factor Composite Liquidity Metric L in [0, 100].
    
    Formula:
    L = 50 * S_spread + 30 * S_oi + 20 * S_vol
    
    - S_spread = max(0, 1 - (ask - bid) / mid / 0.10) (0% spread = 1.0, >= 10% spread = 0.0)
    - S_oi = min(1.0, open_interest / 10000.0)
    - S_vol = min(1.0, volume / 2500.0)
    """
    if bid <= 0 or ask <= 0 or ask < bid:
        return 0

    mid = 0.5 * (bid + ask)
    if mid <= 0:
        return 0

    spread = ask - bid
    spread_pct = spread / mid

    # 1. Spread factor (50% weight): tight <= 1% is perfect, >= 10% is 0
    s_spread = max(0.0, min(1.0, (0.10 - spread_pct) / 0.09)) if spread_pct < 0.10 else 0.0

    # 2. Open Interest factor (30% weight): >= 5,000 contracts is perfect
    s_oi = min(1.0, open_interest / 5000.0)

    # 3. Volume factor (20% weight): >= 1,000 contracts is perfect
    s_vol = min(1.0, volume / 1000.0)

    raw_score = 50.0 * s_spread + 30.0 * s_oi + 20.0 * s_vol
    return int(round(max(0.0, min(100.0, raw_score))))
