# VOLTRON Quantitative Options Intelligence Engine Specification

**Document Version:** 1.0.0  
**Ownership:** Quantitative Engine Lead (Person 1 / `packages/options-alpha-mcp/`)  
**Protocol:** JSON-RPC 2.0 over HTTP (Port 8001)

---

## 1. Overview & Theoretical Foundation

The VOLTRON Options Intelligence Engine provides pure deterministic mathematical computation and quantitative market intelligence for US equity options. The engine adheres to strict engineering invariants:

- **100% Deterministic Code:** All financial formulas, options pricing, Greeks, terminal payoffs, breakevens, max-profit/loss bounds, lognormal POP distributions, 21-scenario stress testing, and risk limits are executed in pure Python code.
- **Zero LLM Arithmetic:** LLMs are reserved exclusively for contextual synthesis, thesis generation, and adversarial critique. LLMs cannot modify strikes, calculate breakevens, or alter broker payloads.
- **Defined-Risk Enforcement:** Only strictly defined-risk multi-leg structures are generated and evaluated.

---

## 2. Core Mathematical Models

### 2.1 Black-Scholes-Merton Pricing
For European options under continuous compounding:

$$d_1 = \frac{\ln(S / K) + (r + \frac{1}{2}\sigma^2)T}{\sigma \sqrt{T}}$$
$$d_2 = d_1 - \sigma \sqrt{T}$$

$$C(S, K, T, r, \sigma) = S \Phi(d_1) - K e^{-rT} \Phi(d_2)$$
$$P(S, K, T, r, \sigma) = K e^{-rT} \Phi(-d_2) - S \Phi(-d_1)$$

Where:
- $S$: Underlying spot price
- $K$: Strike price
- $T$: Annualized time to expiration ($T = \text{DTE} / 365.25$, pegged to 16:00 ET close)
- $r$: Risk-free interest rate ($4.5\% = 0.045$)
- $\sigma$: Implied volatility
- $\Phi(x)$: Cumulative standard normal distribution function

### 2.2 Analytical Greeks
Exact closed-form Greeks calculated per contract:

| Greek | Formula | Financial Interpretation |
|---|---|---|
| **Delta ($\Delta$)** | Call: $\Phi(d_1)$, Put: $\Phi(d_1) - 1$ | Directional spot price sensitivity $\frac{\partial V}{\partial S}$ |
| **Gamma ($\Gamma$)** | $\frac{\phi(d_1)}{S \sigma \sqrt{T}}$ | Curvature / rate of delta change $\frac{\partial^2 V}{\partial S^2}$ |
| **Vega ($\nu$)** | $S \phi(d_1) \sqrt{T} \times 0.01$ | Sensitivity to $1\%$ change in volatility $\frac{\partial V}{\partial \sigma}$ |
| **Theta ($\Theta$)** | Call: $\frac{-S \phi(d_1) \sigma}{2\sqrt{T}} - r K e^{-rT} \Phi(d_2)$, Put: $\frac{-S \phi(d_1) \sigma}{2\sqrt{T}} + r K e^{-rT} \Phi(-d_2)$ | Daily calendar time decay $\frac{\partial V}{\partial t}$ ($/ 365.25$) |
| **Rho ($\rho$)** | Call: $K T e^{-rT} \Phi(d_2) \times 0.01$, Put: $-K T e^{-rT} \Phi(-d_2) \times 0.01$ | Sensitivity to $1\%$ change in interest rates $\frac{\partial V}{\partial r}$ |

### 2.3 Implied Volatility Inversion
Recovered from market mid-prices via a hybrid Brent-Dekker / Newton-Raphson root-finding algorithm:

$$\sigma^* = \arg\min_{\sigma} |V_{\text{BS}}(S, K, T, r, \sigma) - V_{\text{market}}|$$

Bounded within $\sigma \in [0.001, 5.000]$ with tolerance $\epsilon = 10^{-5}$.

### 2.4 Multi-Factor Liquidity Score ($L \in [0, 100]$)
$$L = 50 \cdot S_{\text{spread}} + 30 \cdot S_{\text{oi}} + 20 \cdot S_{\text{vol}}$$

- $S_{\text{spread}} = \max\left(0, \frac{0.10 - \text{SpreadPct}}{0.09}\right)$ (Tight $\le 1\%$ spread receives $1.0$; $\ge 10\%$ receives $0.0$)
- $S_{\text{oi}} = \min\left(1.0, \frac{\text{OpenInterest}}{5000}\right)$
- $S_{\text{vol}} = \min\left(1.0, \frac{\text{Volume}}{1000}\right)$

---

## 3. Volatility Surface, Skew & Term Structure

### 3.1 ATM Strike Selection
$$K_{\text{ATM}} = \arg\min_{K_i} |K_i - S_{\text{spot}}|$$

### 3.2 25-Delta Skew Analysis
Evaluates the implied volatility ratio between downside protection ($25\Delta$ Put) and upside speculation ($25\Delta$ Call):

$$\text{SkewRatio} = \frac{\sigma_{25\Delta \text{Put}}}{\sigma_{25\Delta \text{Call}}}$$
$$\text{SkewSpread} = \sigma_{25\Delta \text{Put}} - \sigma_{25\Delta \text{Call}}$$

### 3.3 Term Structure Nodes
Constructs normalized ATM volatility curves across 6 standardized DTE horizons:
- `7D` (Near-term event risk)
- `14D` (Front-month buffer)
- `30D` (Standard benchmark 30-day IV)
- `45D` (Optimal decay window for Iron Condors)
- `60D` (Intermediate horizon)
- `90D` (Back-end term baseline)

---

## 4. 7 Canonical Anomaly Detectors

1. **`PUT_SKEW_RICH`:** Triggered when $\text{SkewRatio} \ge 1.20$ or 60-day historical z-score $\ge 2.0\sigma$. Identifies rich downside put wings for credit collection.
2. **`CALL_SKEW_RICH`:** Triggered when Call IV exceeds Put IV or trades at elevated upside percentile.
3. **`FRONT_END_IV_ELEV`:** Triggered when $7D\text{ IV} - 45D\text{ IV} \ge 2.0$ vols (term structure backwardation).
4. **`TERM_STRUCTURE_INVERSION`:** Inverted volatility slope indicating near-term catalyst demand.
5. **`VOL_PREMIUM_EXPANSION`:** Triggered when $\text{IV}_{30} - \text{RV}_{20} \ge 3.0$ vols (implied volatility trading at wide premium above Parkinson realized volatility).
6. **`SMILE_CURVATURE`:** Excessive wing convexity across both call and put strikes.
7. **`LIQUIDITY_DISLOCATION`:** Bid-ask spread anomalies across the chain.

---

## 5. Defined-Risk Strategies & Payoff Engine

### 5.1 Iron Condor (4 Legs)
- **Structure:** Buy $K_{lp}$, Sell $K_{sp}$, Sell $K_{sc}$, Buy $K_{lc}$ where $K_{lp} < K_{sp} < K_{sc} < K_{lc}$.
- **Net Credit:** $C_{\text{net}} = (P_{\text{sell}} - P_{\text{buy}}) + (C_{\text{sell}} - C_{\text{buy}})$
- **Max Profit:** $C_{\text{net}} \times 100$
- **Max Loss:** $(\text{WingWidth} - C_{\text{net}}) \times 100$
- **Breakevens:** Lower: $K_{sp} - C_{\text{net}}$, Upper: $K_{sc} + C_{\text{net}}$

### 5.2 Put Credit Spread (Bull Put)
- **Structure:** Buy $K_{lp}$, Sell $K_{sp}$ where $K_{lp} < K_{sp}$.
- **Net Credit:** $C_{\text{net}} = P_{\text{sell}} - P_{\text{buy}}$
- **Max Profit:** $C_{\text{net}} \times 100$
- **Max Loss:** $((K_{sp} - K_{lp}) - C_{\text{net}}) \times 100$
- **Breakeven:** $K_{sp} - C_{\text{net}}$

### 5.3 Call Credit Spread (Bear Call)
- **Structure:** Sell $K_{sc}$, Buy $K_{lc}$ where $K_{sc} < K_{lc}$.
- **Net Credit:** $C_{\text{net}} = C_{\text{sell}} - C_{\text{buy}}$
- **Max Profit:** $C_{\text{net}} \times 100$
- **Max Loss:** $((K_{lc} - K_{sc}) - C_{\text{net}}) \times 100$
- **Breakeven:** $K_{sc} + C_{\text{net}}$

### 5.4 Estimated Probability of Profit (POP)
Modeled via lognormal terminal distribution at breakeven roots:

$$\text{POP}_{\text{Condor}} = \Phi\left(\frac{\ln(K_{\text{upper}} / S_0) - \mu T}{\sigma \sqrt{T}}\right) - \Phi\left(\frac{\ln(K_{\text{lower}} / S_0) - \mu T}{\sigma \sqrt{T}}\right)$$

### 5.5 Tournament Scoring Objective Function
$$\text{Score} = 40 \cdot \text{POP} + 25 \cdot \min(100, \text{RR} \times 250) + 20 \cdot \text{Liquidity} + 15 \cdot \min(100, \frac{\text{SkewAdvantage}}{1.30} \times 100)$$

---

## 6. Multi-Scenario Stress Engine (21 Scenarios)

Evaluates positions across a complete grid of 7 price shifts $\times$ 3 IV shifts:
- **Spot Price Shifts:** $[-10.0\%, -5.0\%, -3.0\%, 0.0\%, +3.0\%, +5.0\%, +10.0\%]$
- **IV Shifts:** $[-20.0\%, 0.0\%, +20.0\%]$

Calculates half-life mark-to-market Black-Scholes repricing, worst-case drawdown, best-case profit, and maximum profit corridor.
