# VOLTRON Decision & Execution Lifecycle

## 1. Lifecycle State Machine

```
CREATED
   │
   ▼
ANALYZING ────► [Agent Failure / Invalid Candidate] ────► FAILED
   │
   ▼
DECISION_READY
   │
   ▼
AWAITING_APPROVAL ────► [Risk Gate Failed / Critic REJECTED] ────► REJECTED / NO_TRADE
   │
   ├──────────────────────────────┐
   ▼                              ▼
Trader Clicks Approve          Trader Clicks Reject
   │                              │
   ▼                              ▼
APPROVED / EXECUTED            REJECTED
(Idempotent no-op on re-click)
```

## 2. 13-Stage Reasoning & Persistence Sequence

1. **Init (`INIT`):** Initialize `decision_id` (`DEC-SPY-HHMMSS`), emit `analysis_created`.
2. **Data Fetch (`DATA_FETCH`):** Single call to `BrokerGateway.get_account()` and `get_market_context(symbol)`.
3. **Quantitative Surfaces (`DATA_FETCH`):** Single call to `OptionsIntelligenceGateway.get_surface()` and `detect_anomalies()`.
4. **Candidate Generation (`QUANT_GEN`):** Retrieve pre-computed candidates from `OptionsIntelligenceGateway.generate_candidates()`.
5. **Researcher Agent (`RESEARCH`):** Output `MarketResearch` (price velocity, regime classification).
6. **Volatility Analyst Agent (`VOLATILITY`):** Output `VolatilityAnalysis` (skew ratio interpretation, anomaly focus).
7. **Strategy Analyst Agent (`STRATEGY`):** Output `StrategySelection` (verifies winner exists in candidate list).
8. **Stress Simulation (`STRESS`):** Retrieve 5x3 price/IV stress matrix for the selected candidate.
9. **Adversarial Critic Agent (`CRITIC`):** Output `Critique` (adversarial failure modes, severity rating).
10. **Deterministic Risk Compiler (`RISK`):** Pure-code gate evaluates budget ($\le 1.0\%$), liquidity ($\ge 70$), and concentration limits.
11. **State Resolution:** Sets status to `REJECTED` if risk checks fail; otherwise `AWAITING_APPROVAL`.
12. **Database Persistence:** Persists complete decision graph (`decisions`, `agent_runs`, `risk_checks`, `strategy_candidates`).
13. **Final SSE Emission:** Emits `decision_completed` with full `DecisionPacket` payload.
