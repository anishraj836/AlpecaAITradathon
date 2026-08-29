from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.domain.models import (
    AccountInfo,
    PositionInfo,
    MarketContext,
    OptionLeg,
    OrderResult,
    OptionType,
    PositionSide,
)

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class AlpacaNormalizer:
    """
    Robust Normalization Layer preventing raw external Alpaca fields from leaking into domain logic.
    Provides bulletproof fallbacks and decimal parsing.
    """

    @staticmethod
    def _parse_float(val: Any, default: float = 0.0) -> float:
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _parse_int(val: Any, default: int = 0) -> int:
        if val is None:
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    @classmethod
    def normalize_account(cls, raw: Dict[str, Any], is_paper: bool = True) -> AccountInfo:
        return AccountInfo(
            accountId=str(raw.get("id", "demo-account")),
            status=str(raw.get("status", "ACTIVE")),
            currency=str(raw.get("currency", "USD")),
            cash=cls._parse_float(raw.get("cash"), 100000.0),
            portfolioValue=cls._parse_float(raw.get("portfolio_value", raw.get("equity")), 100000.0),
            equity=cls._parse_float(raw.get("equity"), 100000.0),
            buyingPower=cls._parse_float(raw.get("buying_power"), 200000.0),
            patternDayTrader=bool(raw.get("pattern_day_trader", False)),
            optionsTradingLevel=cls._parse_int(raw.get("options_trading_level"), 3),
            isPaper=is_paper,
        )

    @classmethod
    def normalize_positions(cls, raw_list: List[Dict[str, Any]]) -> List[PositionInfo]:
        results: List[PositionInfo] = []
        for p in raw_list:
            results.append(
                PositionInfo(
                    symbol=str(p.get("symbol", "")),
                    qty=cls._parse_float(p.get("qty"), 0.0),
                    side="long" if str(p.get("side")).lower() == "long" else "short",
                    marketValue=cls._parse_float(p.get("market_value"), 0.0),
                    avgEntryPrice=cls._parse_float(p.get("avg_entry_price"), 0.0),
                    unrealizedPl=cls._parse_float(p.get("unrealized_pl"), 0.0),
                    currentPrice=cls._parse_float(p.get("current_price"), 0.0),
                )
            )
        return results

    @classmethod
    def normalize_market_context(
        cls,
        symbol: str,
        price: float,
        change_pct: float,
        high: Optional[float] = None,
        low: Optional[float] = None,
        volume: Optional[int] = None,
        vwap: Optional[float] = None,
    ) -> MarketContext:
        high_val = high if high is not None else price * 1.008
        low_val = low if low is not None else price * 0.992
        vol_val = volume if volume is not None else 85000000

        return MarketContext(
            symbol=symbol.upper(),
            price=price,
            changePct=change_pct,
            high=high_val,
            low=low_val,
            volume=vol_val,
            vwap=vwap or round((high_val + low_val + price) / 3.0, 2),
            timestamp=_utc_now_iso(),
        )

    @classmethod
    def normalize_option_contract(
        cls,
        raw_contract: Dict[str, Any],
        raw_snapshot: Optional[Dict[str, Any]] = None,
    ) -> OptionLeg:
        symbol = str(raw_contract.get("symbol", ""))
        underlying = str(raw_contract.get("underlying_symbol", "SPY")).upper()
        strike = cls._parse_float(raw_contract.get("strike_price"), 645.0)
        exp_date = str(raw_contract.get("expiration_date", "2026-09-18"))
        opt_type: OptionType = "CALL" if str(raw_contract.get("type")).lower() == "call" else "PUT"
        side: PositionSide = "BUY"

        # Calculate DTE from expiration date
        try:
            exp_dt = datetime.strptime(exp_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            delta_days = (exp_dt - datetime.now(timezone.utc)).days
            dte = max(delta_days, 1)
        except Exception:
            dte = 30

        # Extract snapshot data if present
        bid = 1.35
        ask = 1.40
        mid = 1.38
        iv = 0.225
        delta = 0.50 if opt_type == "CALL" else -0.50
        gamma = 0.02
        theta = -0.05
        vega = 0.15

        if raw_snapshot:
            latest_quote = raw_snapshot.get("latestQuote", {})
            bid = cls._parse_float(latest_quote.get("bp"), bid)
            ask = cls._parse_float(latest_quote.get("ap"), ask)
            mid = round((bid + ask) / 2.0, 2)
            
            greeks = raw_snapshot.get("greeks", {})
            iv = cls._parse_float(raw_snapshot.get("impliedVolatility"), iv)
            delta = cls._parse_float(greeks.get("delta"), delta)
            gamma = cls._parse_float(greeks.get("gamma"), gamma)
            theta = cls._parse_float(greeks.get("theta"), theta)
            vega = cls._parse_float(greeks.get("vega"), vega)

        return OptionLeg(
            id=symbol or f"{underlying}-{exp_date}-{strike}-{opt_type}",
            symbol=symbol,
            underlying=underlying,
            expiration=exp_date,
            dte=dte,
            strike=strike,
            type=opt_type,
            side=side,
            ratio=1,
            bid=bid,
            ask=ask,
            mid=mid,
            iv=iv,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
        )

    @classmethod
    def normalize_order_result(
        cls,
        raw_order: Dict[str, Any],
        decision_id: str,
    ) -> OrderResult:
        now_ts = datetime.now(timezone.utc)
        order_id = str(raw_order.get("id", f"ALP-ORD-{now_ts.strftime('%M%S')}"))
        client_order_id = str(raw_order.get("client_order_id", f"cl-{decision_id}"))
        status_str = str(raw_order.get("status", "accepted")).lower()
        
        valid_status = "accepted"
        if status_str in ["filled", "partially_filled"]:
            valid_status = "filled"
        elif status_str in ["rejected", "canceled", "expired"]:
            valid_status = "rejected"
        elif status_str in ["pending_new", "accepted"]:
            valid_status = "accepted"

        avg_price = cls._parse_float(raw_order.get("filled_avg_price", raw_order.get("limit_price")), 1.38)
        qty = cls._parse_int(raw_order.get("qty", raw_order.get("filled_qty")), 1)

        return OrderResult(
            orderId=order_id,
            decisionId=decision_id,
            clientOrderId=client_order_id,
            status=valid_status,
            filledAt=str(raw_order.get("filled_at", now_ts.isoformat() + "Z")),
            avgPrice=avg_price,
            qty=qty,
            broker="ALPACA_PAPER",
            rawResponse=raw_order,
        )
