# VOLTRON Threat Model & Safety Enforcements

## 1. Safety Principles

VOLTRON is designed with multi-layered defensive safeguards to prevent unauthorized execution, hallucinated financial data, and unintended live order routing.

---

## 2. Identified Threats & Mitigations

### Threat 1: LLM Inventing Option Strikes or Arbitrary Orders
* **Risk:** An AI agent hallucinating non-existent option contracts or arbitrary strike combinations.
* **Mitigation:** The Strategy Analyst is strictly constrained to selecting candidates by existing `id` from the pre-computed array returned by the Quant Gateway. The `MlegOrderCompiler` verifies contract symbols and underlying consistency against live broker quotes.

### Threat 2: Unintended Live Order Transmission
* **Risk:** Sending live monetary orders to Alpaca during development or demonstration.
* **Mitigation:** Execution fails closed unless `settings.ALPACA_PAPER is True`. Any attempt to execute in live mode without explicit override throws a fatal safety exception.

### Threat 3: Double-Click / Duplicate Order Dispatch
* **Risk:** Rapid multiple clicks on "Approve" button creating duplicate broker orders.
* **Mitigation:** Server-side idempotency using deterministic client order IDs (`cl-{decisionId}`). If an order already exists or decision status is `APPROVED`, the backend returns the existing `OrderResult` without re-dispatching.

### Threat 4: Autonomous Unauthorized Execution
* **Risk:** The AI automatically routing orders without human verification.
* **Mitigation:** Strict Human-In-The-Loop architecture. All decisions default to `AWAITING_APPROVAL` and require explicit trader confirmation in the Decision Room modal.

### Threat 5: Bypassing Risk Gates
* **Risk:** An agent ignoring portfolio loss limits or liquidity constraints.
* **Mitigation:** The Risk Compiler is 100% deterministic pure code (0% LLM). Execution service re-validates `riskCompilerResult.isApproved` immediately prior to broker transmission.
