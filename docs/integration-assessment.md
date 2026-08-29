# VOLTRON Integration Assessment & Quantitative Architecture Plan

**Document Version:** 1.0.0  
**Phase:** Phase A Deliverable (Repository Assessment & Architecture Alignment)  
**Date:** 2026-08-29  
**Authors:** Lead Orchestrator, Quant Lead (Agent A), Integration Lead (Agent B), Independent Watchdog (Agent C)

---

## 1. Executive Summary

VOLTRON is an AI-native options structuring desk designed for the **Alpaca AI Trading Agents Hackathon**. The platform identifies volatility dislocations and statistical skew anomalies across the US equity options market, deterministically generates defined-risk multi-leg structures, rigorously stress-tests them across 21 market scenarios, subjects candidates to an adversarial multi-agent critique, enforces deterministic risk compilation, and submits human-approved multi-leg (MLEG) orders to Alpaca Paper Trading.

The application side (FastAPI backend, Next.js 14 frontend, database persistence, SSE event bus, and runtime agent harnesses) was implemented by **Person 2**. The quantitative options intelligence core (`packages/options-alpha-mcp/`) currently operates with fixture mocks and dummy JSON-RPC responses.

This document presents the complete codebase audit, identifies the exact missing mathematical and quantitative capabilities, establishes stable typed contracts, and details the vertical slice integration plan approved by the **Independent Watchdog Agent (Checkpoint 1: PASS)**.

---

## 2. Current System Architecture

```
                                  +---------------------------------------+
                                  |            TRADER / USER              |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |         NEXT.JS 14 FRONTEND           |
                                  |  (Terminal, Surface 3D, Tournament,   |
                                  |   Stress Matrix, Multi-Agent Trace,   |
                                  |   Counterfactual, Portfolio, Replay)  |
                                  +---------------------------------------+
                                           | HTTP (REST)   ^ SSE (Events)
                                           v               |
                                  +---------------------------------------+
                                  |       FASTAPI BACKEND RUNTIME         |
                                  |      (app.agents.orchestrator)        |
                                  +---------------------------------------+
                                     /                                 \
                                    /                                   \
                                   v                                     v
+------------------------------------------+    +------------------------------------------+
|          ALPACA BROKER GATEWAY           |    |       OPTIONS INTELLIGENCE GATEWAY       |
|    (app.infrastructure.alpaca.gateway)   |    |    (app.infrastructure.options.gateway)  |
|                                          |    |                                          |
| - Account & Balances (/v2/account)       |    | - Volatility Surface (Cubic/SVI)         |
| - Positions (/v2/positions)              |    | - 25-Delta Skew & Term Structure         |
| - Option Chains & Greeks                 |    | - 7 Statistical Anomaly Detectors        |
| - Spot Market Data & VWAP                |    | - Multi-Leg Defined-Risk Generator       |
| - Multi-Leg Paper Execution (/v2/orders) |    | - Black-Scholes Pricing & Exact Payoff   |
|                                          |    | - Lognormal Estimated POP Engine         |
|   Connected to:                          |    | - 21-Scenario Spot/IV Stress Engine      |
|   Alpaca Paper REST / MCP Server         |    | - Deterministic Pure-Code Risk Compiler  |
+------------------------------------------+    |                                          |
                                                |   Connected to:                          |
                                                |   packages/options-alpha-mcp/ (Port 8001)|
                                                +------------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |        RUNTIME MULTI-AGENT DESK       |
                                  |                                       |
                                  | 1. Researcher (Regime & Context)      |
                                  | 2. Volatility Analyst (Skew/Term)     |
                                  | 3. Strategy Analyst (Selects Candidate|
                                  |    ID from pre-computed quant pool)   |
                                  | 4. Adversarial Critic (Failure Modes) |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |   DETERMINISTIC RISK COMPILER GATE    |
                                  |   [PURE PYTHON CODE - 0% LLM MATH]    |
                                  | - Max Loss <= 5% Account Equity       |
                                  | - Liquidity Score >= 70/100           |
                                  | - Concentration <= 20% Margin Limit   |
                                  | - Tail Risk Bounded Verification      |
                                  +---------------------------------------+
                                                      |
                                             PASS / FAIL GATE
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |        HUMAN TRADER APPROVAL          |
                                  |     (Interactive UI Decision Room)    |
                                  +---------------------------------------+
                                                      | (Trader Approves)
                                                      v
                                  +---------------------------------------+
                                  |         MLEG ORDER COMPILER           |
                                  |  - OCC Symbol Construction            |
                                  |  - buy_to_open / sell_to_open Intents |
                                  |  - Net Credit Limit Price Locking     |
                                  |  - Idempotency Client Order ID Hash   |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |      ALPACA PAPER API EXECUTION       |
                                  |    POST https://paper-api.alpaca...   |
                                  +---------------------------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |         SQLITE / POSTGRESQL DB        |
                                  |  (Decisions, Agent Runs, Risk Checks, |
                                  |   Candidates, Orders, Snapshots)      |
                                  +---------------------------------------+
```

---

## 3. Existing Application Components (Person 2 Implementation)

### 3.1 Backend Architecture (`apps/api/`)
* **FastAPI Application (`app/main.py`):** Configures lifespan database initialization, CORS for Next.js endpoints, and routes under `/api`.
* **API Routers (`app/api/routes/`):**
  * `scan.py` & `main.py:run_mandate_scan`: Triggers synchronous multi-agent orchestration for a symbol and mandate.
  * `decisions.py`: Lists recent decisions, fetches full `DecisionPacket` by ID, handles human trader approvals (`POST /decisions/{id}/approve`), and handles trader rejections (`POST /decisions/{id}/reject`).
  * `orders.py`: Queries order statuses, retrieves execution history, and allows direct order dispatch.
  * `events.py`: Server-Sent Events (SSE) broadcaster stream (`GET /api/events`) pushing real-time agent thoughts, status transitions, and execution telemetry to the frontend.
  * `telemetry.py`: Returns broker connection status, paper trading flag, account equity, and buying power.
  * `portfolio.py`: Provides normalized account balances, Greeks summary ($\Delta, \Theta, \nu, \Gamma$), and open positions.
  * `history.py`: Lists past decision summaries and profit/loss outcomes.
  * `replay.py`: Fetches time-stamped multi-agent deliberation traces for auditability.
* **Services Layer (`app/services/`):**
  * `execution_service.py`: Contains `MlegOrderCompiler` and `ExecutionService`. Enforces async process-level locks (`_decision_locks`), idempotency checks against `orders` table, lifecycle state machines (`AWAITING_APPROVAL` $\rightarrow$ `APPROVED`), risk re-validation, broker dispatch, and database transaction commits.
  * `event_broadcaster.py`: In-memory `asyncio.Queue` event bus broadcasting `OrchestratorEvent` payloads over SSE.
  * `decision_service.py`: CRUD operations for decisions and trace steps.
  * `market_service.py` & `order_service.py`: High-level broker aggregation helpers.
* **Database & Persistence (`app/infrastructure/database/`):**
  * Async SQLAlchemy 2.0 with aiosqlite / asyncpg.
  * Tables: `decisions`, `agent_runs`, `risk_checks`, `strategy_candidates`, `orders`, `fills`, `market_snapshots`, `option_snapshots`.
  * Alembic migration revision `e4fe8a45245d_initial_schema_decisions_market_.py` verified.

### 3.2 Frontend Architecture (`apps/web/`)
* Next.js 14 App Router with Tailwind CSS, Lucide icons, and Three.js / Canvas 3D surface rendering.
* **Dedicated UI Pages:**
  1. `/terminal`: Main mission control with real-time mandate input, market telemetry, multi-agent stage timeline, winning strategy card, and one-click execution drawer.
  2. `/surface`: Interactive 3D/2D Volatility Surface visualizer, strike vs. DTE grid, term structure curve, and skew anomaly callouts.
  3. `/tournament`: Strategy Candidate Tournament comparing 6–12 structures, multi-factor scores, POP, reward/risk, and rejection reasons.
  4. `/stress`: Interactive $7 \times 3$ Price Shift vs. IV Shift Stress Matrix, max-profit corridor, and worst-case scenario callouts.
  5. `/decision/[id]`: Formal Human-in-the-Loop Decision Room presenting the full `DecisionPacket`, Why This Trade thesis, Critic failure modes, Risk Gate results, and Approve/Reject buttons.
  6. `/trace/[id]`: Step-by-step multi-agent deliberation transcript with confidence scores, key drivers, and latency telemetry.
  7. `/counterfactual`: Sensitivity analysis simulator exploring parameter shifts (target delta, DTE, risk budget).
  8. `/portfolio`: Real-time portfolio Greeks, open options positions, margin utilization, and PnL metrics.
  9. `/history`: Historical log of all evaluated decisions, executed trades, and performance outcomes.
  10. `/replay/[id]`: Historical playback of decision execution timeline.

### 3.3 Alpaca Broker Gateway (`apps/api/app/infrastructure/alpaca/`)
* `AlpacaBrokerGateway` implementing `BrokerGateway` interface:
  * `get_account()`: Fetches cash, equity, buying power, and options trading level (Level 3).
  * `get_positions()`: Fetches open stock and option contracts.
  * `get_market_context(symbol)`: Retrieves spot price, day change, high, low, volume, and VWAP.
  * `get_option_chain(symbol)`: Queries options contracts and snapshots with fallback.
  * `place_multileg_order(decision, payload)`: Enforces `ALPACA_PAPER=true` safety gate, constructs MLEG payload, and dispatches to `POST /v2/orders`.
  * `get_order(order_id)`: Queries order fill status.
* `AlpacaNormalizer`: Robust parsing layer protecting domain models from raw broker field anomalies.

---

## 4. Quantitative Gaps & Required Implementations

Currently, `packages/options-alpha-mcp/server.py` and `mock_gateway.py` return static hardcoded dictionaries. The following 17 canonical quantitative components must be fully implemented in `packages/options-alpha-mcp/`:

| # | Quantitative Component | Requirement & Formula | Owner Module |
|---|---|---|---|
| 1 | **Data Normalization & Greeks** | Black-Scholes analytical Greeks ($\Delta, \Gamma, \Theta, \nu, \rho$) and Brent's method numerical IV inversion. Explicit missing-data handling (no fake values). | `pricing.py` |
| 2 | **DTE Convention** | Fractional annualized time $T = \text{DTE}/365.25$ pegged to 16:00 ET expiration close. Distinct handling for calendar vs. trading days. | `surface.py` |
| 3 | **ATM Strike Selection** | Deterministic selection: $K_{\text{ATM}} = \arg\min |K - S_{\text{spot}}|$ and $\Delta$-neutral ATM $K = \arg\min |\Delta_C - 0.50|$. Tested for exact match and sparse strikes. | `surface.py` |
| 4 | **Volatility Surface** | Normalized surface over strike, DTE, IV, Delta, volume, and open interest. SVI / cubic spline curve interpolation. | `surface.py` |
| 5 | **Term Structure** | ATM IV by expiration / DTE across 7D, 14D, 30D, 45D, 60D, 90D. Explicit `INSUFFICIENT_DATA` handling when sparse. | `surface.py` |
| 6 | **Skew Analysis** | Dynamic $25\Delta$ Put selection and $25\Delta$ Call selection. Skew ratio $\sigma_{25P}/\sigma_{25C}$ and skew spread $\sigma_{25P} - \sigma_{25C}$. | `surface.py` |
| 7 | **Liquidity Scoring** | Multi-factor composite $L \in [0, 100]$: Spread (50%), Open Interest (30%), Volume (20%). Configurable thresholds. | `pricing.py` |
| 8 | **Historical Baseline** | Parkinson & Garman-Klass realized volatility, 252-day IV Rank, IV Percentile, 60-day skew z-score. Explicit `INSUFFICIENT_HISTORY` state. | `anomalies.py` |
| 9 | **Anomaly Engine** | 7 deterministic anomaly detectors: Put Skew Rich, Call Skew Rich, Front-End IV Elevated, Term Structure Inversion, Relative IV Expansion, Smile Curvature, Liquidity Dislocation. | `anomalies.py` |
| 10 | **3 Defined-Risk Strategies** | Algorithmic generation for Put Credit Spread, Call Credit Spread, and Iron Condor (6–12 candidates total). Strict wing ordering and strike validation. | `strategies.py` |
| 11 | **Payoff Engine** | Pure deterministic terminal payoff $\Pi(S_T) = \sum w_i \max(\phi_i(S_T - K_i), 0) + C_{\text{net}}$ and Black-Scholes intraday curve. Zero LLM math. | `strategies.py` |
| 12 | **Max Profit / Max Loss** | Exact mathematical bounds: $MaxProfit = C_{\text{net}} \times 100$, $MaxLoss = (\text{Width} - C_{\text{net}}) \times 100$. Verified against payoff curve. | `strategies.py` |
| 13 | **Breakevens** | Exact analytical formulas: Put Spread ($K_{sp} - C$), Call Spread ($K_{sc} + C$), Iron Condor ($K_{sp} - C$ and $K_{sc} + C$). Validated against payoff roots. | `strategies.py` |
| 14 | **Estimated POP Model** | Documented lognormal cumulative probability distribution $N(d_2)$ evaluated over profitable terminal price regions. Clearly labeled "ESTIMATED POP". | `strategies.py` |
| 15 | **Strategy Tournament Scoring** | Transparent multi-factor objective function: $40\% \text{POP} + 25\% \text{Reward/Risk} + 20\% \text{Liquidity} + 15\% \text{Skew Capture}$ with tail risk penalties. | `strategies.py` |
| 16 | **Stress Engine** | Complete 21-scenario matrix ($7 \text{ Spot shifts: } \pm 10\%, \pm 5\%, \pm 3\%, 0\% \times 3 \text{ IV shifts: } \pm 20\%, 0\%$). Computes modeled PnL, best case, worst case. | `stress.py` |
| 17 | **Deterministic Risk Compiler** | Fail-closed pure-code risk gate: Max Loss $\le 5\%$ Equity, Liquidity Score $\ge 70$, Margin Concentration $\le 20\%$, Tail Risk Bounded check, and contract sizing. | `risk.py` |

---

## 5. Watchdog Checkpoint 1 Audit & Resolutions

The **Independent Watchdog Agent** performed Checkpoint 1 (Repository Assessment) and issued a **PASS WITH OBSERVATIONS** verdict. Three minor refinements were identified and scheduled for Phase B/C:

1. **[Medium Severity] Directional Strategy Breakeven Handling in Critic Agent:**
   * *Finding:* `CriticAgent` assumed all strategies have two breakevens and evaluated upside breakout even on single-breakeven Put Credit Spreads where the primary vulnerability is downside drop.
   * *Resolution:* In Phase D/G, equip `CriticAgent` with strategy-type awareness (distinguishing 2-sided Iron Condors from 1-sided Put/Call Credit Spreads).
2. **[Low Severity] Inverted Delta Signs in Mock Gateway:**
   * *Finding:* In `mock_gateway.py`, short put/call legs used positive/negative position deltas rather than standard contract deltas (Calls $>0$, Puts $<0$).
   * *Resolution:* Align all delta conventions to standard contract deltas in `packages/options-alpha-mcp/` and `mock_gateway.py`.
3. **[Low Severity] Redundant Approval Method in DecisionService:**
   * *Finding:* `DecisionService.approve_decision` was redundant with `ExecutionService.approve_and_execute`.
   * *Resolution:* Deprecate `DecisionService.approve_decision` and standardize all approval routes through `ExecutionService`.

---

## 6. Target Shared Contracts (`packages/options-alpha-mcp` $\leftrightarrow$ `apps/api`)

The JSON-RPC 2.0 communication protocol on `http://localhost:8001/rpc` is verified and frozen:

```json
{
  "jsonrpc": "2.0",
  "method": "<method_name>",
  "params": { ... },
  "id": 1
}
```

### Supported RPC Methods:
1. `get_surface(symbol: str) -> VolatilitySurface`
2. `detect_anomalies(symbol: str) -> List[AnomalyReport]`
3. `generate_candidates(symbol: str, target_delta: float, max_budget: float) -> List[StrategyCandidate]`
4. `stress_test(strategy_id: str, candidate: Optional[StrategyCandidate]) -> StressReport`
5. `compile_risk(strategy: StrategyCandidate, portfolio_equity: float) -> RiskCheckResult`
6. `get_counterfactual(params: Dict[str, Any]) -> CounterfactualComparison`

---

## 7. Exact Vertical Slice Integration Sequence

To maintain continuous stability and 100% test coverage, implementation proceeds in incremental vertical slices:

* **PHASE B — CONTRACT ALIGNMENT & TEST HARNESS:**
  * Freeze domain schemas in `models.py`.
  * Create `packages/options-alpha-mcp/test_quant_math.py` unit test suite covering pure mathematical pricing, payoff curves, breakevens, and POP.
  * Watchdog Review Checkpoint 2. Commit.

* **PHASE C — DATA NORMALIZATION & VOLATILITY SURFACE:**
  * Implement `packages/options-alpha-mcp/pricing.py` (Black-Scholes, Greeks, Brent IV inversion, Liquidity composite).
  * Implement `packages/options-alpha-mcp/surface.py` (ATM selection, DTE convention, SVI surface, term structure, 25-delta skew).
  * Watchdog Review Checkpoints 3 & 4. Commit.

* **PHASE D — ANOMALIES & STRATEGY TOURNAMENT:**
  * Implement `packages/options-alpha-mcp/anomalies.py` (7-anomaly engine, Parkinson realized vol, historical baseline).
  * Implement `packages/options-alpha-mcp/strategies.py` (Put Credit Spread, Call Credit Spread, Iron Condor, terminal/intraday payoff, breakevens, POP, tournament scoring for 6–12 candidates).
  * Watchdog Review Checkpoints 5 & 6. Commit.

* **PHASE E — STRESS ENGINE & DETERMINISTIC RISK COMPILER:**
  * Implement `packages/options-alpha-mcp/stress.py` (21-scenario spot vs. IV stress matrix, max profit zone).
  * Implement `packages/options-alpha-mcp/risk.py` (Deterministic risk compiler, 5% budget limit, liquidity gate, margin concentration limit, position sizing).
  * Watchdog Review Checkpoints 7 & 8 (including adversarial bypass tests). Commit.

* **PHASE F — VOLTRON MCP SERVER WIRE-UP:**
  * Wire all quantitative handlers into `packages/options-alpha-mcp/server.py` JSON-RPC dispatcher.
  * Connect `apps/api/app/infrastructure/options/mcp_client.py` to live MCP server.
  * Watchdog Review Checkpoint 9. Commit.

* **PHASE G — APPLICATION INTEGRATION & RUNTIME AGENT REASONING:**
  * Connect real MCP quant outputs to `MarketResearcherAgent`, `VolatilityAnalystAgent`, `StrategyAnalystAgent`, and `CriticAgent`.
  * Update `CriticAgent` directional spread evaluation.
  * Validate end-to-end `DecisionPacket` assembly and database persistence.
  * Watchdog Review Checkpoint 10. Commit.

* **PHASE H — END-TO-END PAPER EXECUTION & HARDENING:**
  * Run complete paper trading test: Mandate $\rightarrow$ Quant MCP $\rightarrow$ AI Agents $\rightarrow$ Risk Gate $\rightarrow$ UI Decision Room $\rightarrow$ Human Approval $\rightarrow$ Order Compiler $\rightarrow$ Alpaca MLEG Paper Order.
  * Run full backend and quant test suites.
  * Watchdog Review Checkpoint 11 (Final Gate). Commit.

---

## 8. Summary of Commit Milestones

Following the user's directive, each milestone will be accompanied by an immediate, clean git commit:
1. `docs: add comprehensive integration assessment and quant architecture plan` (Phase A)
2. `feat(quant): implement analytical black-scholes pricer, greeks, and iv inversion` (Phase C.1)
3. `feat(quant): implement volatility surface, term structure, and skew models` (Phase C.2)
4. `feat(quant): implement 7-factor anomaly detection and historical baseline engine` (Phase D.1)
5. `feat(quant): implement defined-risk strategy generator, payoff engine, pop, and tournament scoring` (Phase D.2)
6. `feat(quant): implement 21-scenario stress engine and deterministic risk compiler` (Phase E)
7. `feat(mcp): wire mathematical quantitative modules into voltron json-rpc mcp server` (Phase F)
8. `feat(integration): connect live quant mcp to orchestrator, runtime agents, and execution service` (Phase G)
9. `test(e2e): complete adversarial test suite and paper trading verification` (Phase H)

---
*Verified and approved by Lead Orchestrator and Independent Watchdog Agent.*
