# VOLTRON Deterministic Risk Compiler & Safety Envelope Specification

**Document Version:** 1.0.0  
**Ownership:** Quantitative Risk & Safety Architect  
**Principle:** 0% LLM Math, 100% Deterministic Pure-Code Enforcement, Strict Paper Trading Lock

---

## 1. Safety Invariants & Threat Model

The VOLTRON Risk Compiler is a non-bypassable, fail-closed pure Python code gate situated between the AI multi-agent reasoning layer and the Human Approval Decision Room.

```
+--------------------------+
|  AI Multi-Agent Desk     |
|  (Researcher, Volatility,|
|   Strategist, Critic)    |
+--------------------------+
             |
             v
+--------------------------+
| DETERMINISTIC RISK GATE  | <--- 100% Pure Code Checks (0% LLM Bypass)
| 1. Max Loss <= 5% Equity |
| 2. Liquidity >= 70/100   |
| 3. Margin <= 20% Limit   |
| 4. Defined Tail Risk     |
| 5. Integer Contract Size |
+--------------------------+
             |
     [ PASS / FAIL ]
             |
             v
+--------------------------+
| HUMAN TRADER APPROVAL    |
| (Interactive Modal)      |
+--------------------------+
             | (Trader Approves)
             v
+--------------------------+
| MLEG ORDER COMPILER      |
| - OCC Symbol Validation  |
| - Limit Price Locking    |
| - Client Order ID Hash   |
+--------------------------+
             |
             v
+--------------------------+
| ALPACA PAPER BROKER API  |
| (Hard-locked to Paper)   |
+--------------------------+
```

---

## 2. Deterministic Risk Rules & Limits

### 2.1 Risk Budget Allocation Gate
- **Rule:** $\text{MaxLoss} \le \text{PortfolioEquity} \times 0.05$ (Max 5.0% single-structure risk).
- **Enforcement:** If a proposed structure has maximum defined loss exceeding 5% of current equity, the gate returns `status="FAIL"` and `isApproved=False`.
- **LLM Override:** Strictly prohibited.

### 2.2 Contract Liquidity Gate
- **Rule:** Composite Liquidity Score $L \ge 70 / 100$.
- **Enforcement:** Prevents execution in wide, illiquid, or stale options chains where slippage degrades net credit collection.

### 2.3 Portfolio Margin Concentration Gate
- **Rule:** Total risk on a single underlying must not exceed $20.0\%$ of total account margin.

### 2.4 Defined-Risk Invariant Verification
- **Rule:** Max loss must be finite, strictly positive, and bounded ($\text{MaxLoss} < \$50,000.00$).
- **Enforcement:** Undefined-risk structures (e.g. naked short straddles, naked short puts/calls) are rejected deterministically before reaching trader approval.

### 2.5 Position Sizing Calculator
$$N_{\text{max}} = \left\lfloor \frac{\text{PortfolioEquity} \times 0.05}{\text{MaxLossPerContract}} \right\rfloor$$

Bounded to a hard maximum of 50 contracts per order.

---

## 3. Quadruple-Gate Execution Defense

VOLTRON implements four independent, layered defense gates to prevent unauthorized or malformed order execution:

1. **Gate 1 — Orchestrator Decision Status Gate:** Only decisions with `status="AWAITING_APPROVAL"` can enter the execution queue. Decisions marked `REJECTED`, `FAILED`, or `NO_TRADE` are immediately blocked.
2. **Gate 2 — Pre-Dispatch Deterministic Re-Validation:** `ExecutionService.approve_and_execute` re-runs `packet.riskCompilerResult.isApproved` verification from stored database state immediately before building the broker payload.
3. **Gate 3 — MLEG Order Compiler OCC Validation:** `MlegOrderCompiler` verifies symbol OCC format, ensures $\ge 2$ legs, locks net credit limit prices, and validates underlying consistency.
4. **Gate 4 — Paper Environment Hard-Lock:** `settings.ALPACA_PAPER` is validated in `trading.py` and `execution_service.py`. Any attempt to execute in live mode without explicit multi-signature configuration raises a fatal safety exception.

---

## 4. Concurrency, Locking & Idempotency

- **Process-Level Mutex Locks:** Each `decision_id` is protected by a dedicated `asyncio.Lock` in `ExecutionService` to prevent double-click or race condition duplicate orders.
- **Client Order ID Hashing:** Every order is tagged with `client_order_id = "cl-{decision_id}"`. If an order with that client ID already exists in the database or broker ledger, the service returns the existing order record without dispatching a new broker order.
- **Database Transaction Atomicity:** Decision status updates and order records are committed in a single database transaction with automatic rollback on collision.
