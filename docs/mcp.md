# VOLTRON MCP & Broker Integration Specification

**Document Version:** 1.1.0  
**Ownership:** Integration Architect & Broker Gateway Lead  
**Protocol:** JSON-RPC 2.0 over HTTP (Port 8001 / `packages/options-alpha-mcp/`) & Alpaca REST API

---

## 1. Alpaca MCP & REST Interface Verification

VOLTRON connects to Alpaca via both direct REST API (`BrokerGateway`) and JSON-RPC 2.0 Model Context Protocol (`Alpaca MCP Client`).

### Authentication & Environments
* **Paper Trading Base URL:** `https://paper-api.alpaca.markets`
* **Live Trading Base URL:** `https://api.alpaca.markets`
* **Market Data Base URL:** `https://data.alpaca.markets`
* **Required Authentication Headers:**
  * `APCA-API-KEY-ID`: Alpaca API Key
  * `APCA-API-SECRET-KEY`: Alpaca Secret Key

### Verified Account & Portfolio Capabilities
* `GET /v2/account`
  * Response fields: `id`, `status`, `currency`, `buying_power`, `regt_buying_power`, `cash`, `portfolio_value`, `equity`, `last_equity`, `multiplier`, `pattern_day_trader`, `options_trading_level`, `options_approved_level`.
* `GET /v2/positions`
  * Response fields: `asset_id`, `symbol`, `qty`, `avg_entry_price`, `side`, `market_value`, `cost_basis`, `unrealized_pl`, `current_price`.

### Verified Options Data Access
* `GET /v2/options/contracts`
  * Query parameters: `underlying_symbols`, `status=active`, `expiration_date_gte`, `expiration_date_lte`, `root_symbol`, `type` (`call`/`put`), `strike_price_gte`, `strike_price_lte`.
  * Response fields: `id`, `symbol`, `name`, `status`, `tradable`, `expiration_date`, `root_symbol`, `underlying_symbol`, `type`, `style` (`american`/`european`), `strike_price`, `size`, `open_interest`, `close_price`.
* `GET /v1beta1/options/snapshots/{underlying_symbol}`
  * Returns full implied volatility surface snapshot, greeks (delta, gamma, theta, vega), bid/ask quotes, and latest trade prints per contract.
* `GET /v1beta1/options/bars`
  * Historical option candlestick series.

### Verified Multi-Leg (MLEG) Order Structure
* `POST /v2/orders`
  * **Payload Structure for Defined-Risk Multi-Leg Orders:**
    ```json
    {
      "symbol": "SPY",
      "qty": "1",
      "side": "buy",
      "type": "limit",
      "time_in_force": "day",
      "limit_price": "1.38",
      "order_class": "mleg",
      "client_order_id": "cl-DEC-SPY-9942",
      "legs": [
        {
          "symbol": "SPY260918P00625000",
          "ratio_qty": "1",
          "side": "buy",
          "position_intent": "buy_to_open"
        },
        {
          "symbol": "SPY260918P00630000",
          "ratio_qty": "1",
          "side": "sell",
          "position_intent": "sell_to_open"
        },
        {
          "symbol": "SPY260918C00660000",
          "ratio_qty": "1",
          "side": "sell",
          "position_intent": "sell_to_open"
        },
        {
          "symbol": "SPY260918C00665000",
          "ratio_qty": "1",
          "side": "buy",
          "position_intent": "buy_to_open"
        }
      ]
    }
    ```
* **Order Statuses:** `pending_new`, `accepted`, `partially_filled`, `filled`, `done_for_day`, `canceled`, `expired`, `replaced`, `rejected`.

---

## 2. VOLTRON Options Intelligence MCP (Person 1 Ownership)

Person 1 owns `packages/options-alpha-mcp/` listening on `http://localhost:8001/rpc`. The gateway boundary exposed to the backend orchestrator conforms to the `OptionsIntelligenceGateway` interface:

### JSON-RPC 2.0 Tools Exposed:
1. `get_surface`
   * **Params:** `{"symbol": "SPY"}`
   * **Result:** `VolatilitySurface` (Surface points, 6-node term structure, 25Δ skew snapshot, 7 anomaly detectors).
2. `detect_anomalies`
   * **Params:** `{"symbol": "SPY"}`
   * **Result:** `List[AnomalyReport]` (Classified anomalies with percentile and confidence).
3. `generate_candidates`
   * **Params:** `{"symbol": "SPY", "target_delta": 0.15, "max_budget": 50000.0}`
   * **Result:** `List[StrategyCandidate]` (Tournament set of 5+ defined-risk candidates).
4. `stress_test`
   * **Params:** `{"strategy_id": "strat-condor-01"}`
   * **Result:** `StressReport` (21-scenario Price $\times$ IV matrix, max profit zone, baseline PnL).
5. `compile_risk`
   * **Params:** `{"strategy": {...}, "portfolio_equity": 100000.0}`
   * **Result:** `RiskCheckResult` (Budget, liquidity, concentration checks, approved status, max contracts).
6. `get_counterfactual`
   * **Params:** `{"params": {"targetDelta": 15.0, "dteDays": 30, "budget": 2500.0}}`
   * **Result:** `CounterfactualComparison` (Baseline vs. shifted scenario comparison).

---

## 3. Normalization Boundary

Raw broker responses and external MCP JSON-RPC payloads are strictly isolated in `app/infrastructure/alpaca/normalizer.py`.
Application services and API routers consume only canonical Pydantic domain models:
* `OptionLeg`
* `StrategyCandidate`
* `VolatilitySurface`
* `StressReport`
* `AgentTraceStep`
* `RiskCheckResult`
* `DecisionPacket`
* `OrderResult`
