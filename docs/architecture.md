# VOLTRON System Architecture & Implementation Guide

## 1. Overview & Ownership Model

VOLTRON is an AI-native options structuring, adversarial validation, and trading decision system designed for the Alpaca AI Trading Agents Hackathon.

### Division of Responsibility
* **PERSON 1 (Canonical Quant Engine):** Independently owns `packages/options-alpha-mcp/`. Responsible for volatility surface fitting, term structure calculation, skew dislocations, anomaly detection, strategy generation, payoff curves, breakevens, POP, stress testing, and deterministic risk checks.
* **PERSON 2 (Application & AI Orchestration):** Owns `apps/api/`, `apps/worker/`, `apps/web/`, Alpaca broker integration, runtime multi-agent orchestration, human-in-the-loop approval, execution pipeline, database persistence, and real-time SSE streaming.

---

## 2. Multi-Agent Reasoning Architecture

```
                                  Trader Mandate
                                        │
                                        ▼
                               VoltronOrchestrator
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
      Broker Gateway                                 Options Intelligence Gateway
   (Single Account/Price)                            (Mock or Voltron Quant MCP)
             │                                                     │
             ├──────────────────────────┬──────────────────────────┤
             │                          │                          │
             ▼                          ▼                          ▼
    1. Researcher Agent        2. Volatility Analyst       Candidate Generation
     (Regime Identification)    (Skew/Term Dislocation)    (Pre-computed Structures)
             │                          │                          │
             └──────────────────────────┼──────────────────────────┘
                                        │
                                        ▼
                              3. Strategy Analyst
                           (Selects Candidate by ID)
                                        │
                                        ▼
                                  Stress Matrix
                              (Price Shift vs IV Shift)
                                        │
                                        ▼
                                 4. Critic Agent
                            (Adversarial Invalidation)
                                        │
                                        ▼
                         5. Deterministic Risk Compiler
                           (Pure-Code Gate: 0% LLM)
                                        │
                                        ▼
                                  DecisionPacket
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                  PostgreSQL DB                   SSE Stream
              (Complete Audit Graph)          (Live Telemetry)
```

---

## 3. Options Intelligence Gateway & Mock Boundary

* **Interface (`OptionsIntelligenceGateway`):** Defines async methods: `get_surface`, `detect_anomalies`, `generate_candidates`, `stress_test`, `compile_risk`, `get_agent_trace`, `get_counterfactual`.
* **Mock Implementation (`MockOptionsIntelligenceGateway`):** Provides deterministic test fixtures matching domain DTOs without duplicating quant math.
* **Future MCP Integration (`VoltronOptionsMCPClient`):** Switches via `.env` setting `USE_MOCK_QUANT=false` with zero application refactoring.

---

## 4. Execution Pipeline & Safety Gates

1. **Human Approval Gate:** Decisions start in `AWAITING_APPROVAL`. Orders are never dispatched without explicit user confirmation.
2. **Server-Side Idempotency:** Duplicate approval requests for the same `decisionId` return the existing `OrderResult` without placing multiple broker orders.
3. **Deterministic Risk Re-validation:** The execution service re-evaluates `riskCompilerResult.isApproved` before compiling order payloads.
4. **Paper Trading Hard Lock:** Enforces `settings.ALPACA_PAPER is True`. If live trading configuration is detected, execution fails closed.
