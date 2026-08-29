import pytest
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer
from app.domain.models import AccountInfo, OptionLeg, MarketContext, OrderResult

def test_normalize_account():
    raw = {
        "id": "ACC-12345",
        "status": "ACTIVE",
        "currency": "USD",
        "cash": "250000.50",
        "equity": "1245892.12",
        "buying_power": "4821000.00",
        "pattern_day_trader": True,
        "options_approved_level": 3,
    }
    account = AlpacaNormalizer.normalize_account(raw, is_paper=True)
    assert isinstance(account, AccountInfo)
    assert account.accountId == "ACC-12345"
    assert account.cash == 250000.50
    assert account.equity == 1245892.12
    assert account.buyingPower == 4821000.00
    assert account.isPaper is True

def test_normalize_account_fallbacks_on_empty():
    account = AlpacaNormalizer.normalize_account({}, is_paper=True)
    assert account.equity == 100000.0
    assert account.currency == "USD"

def test_normalize_market_context():
    ctx = AlpacaNormalizer.normalize_market_context(
        symbol="SPY",
        price=645.31,
        change_pct=0.82,
        high=647.0,
        low=643.0,
        volume=90000000,
    )
    assert isinstance(ctx, MarketContext)
    assert ctx.symbol == "SPY"
    assert ctx.price == 645.31
    assert ctx.changePct == 0.82

def test_normalize_option_contract():
    raw_contract = {
        "symbol": "SPY260918P00625000",
        "underlying_symbol": "SPY",
        "strike_price": "625.00",
        "expiration_date": "2026-09-18",
        "type": "put",
    }
    raw_snapshot = {
        "impliedVolatility": "0.284",
        "latestQuote": {"bp": "1.08", "ap": "1.12"},
        "greeks": {"delta": "-0.12", "gamma": "0.015", "theta": "-0.04", "vega": "0.18"},
    }
    leg = AlpacaNormalizer.normalize_option_contract(raw_contract, raw_snapshot)
    assert isinstance(leg, OptionLeg)
    assert leg.symbol == "SPY260918P00625000"
    assert leg.strike == 625.0
    assert leg.type == "PUT"
    assert leg.bid == 1.08
    assert leg.ask == 1.12
    assert leg.mid == 1.10
    assert leg.iv == 0.284
    assert leg.delta == -0.12

def test_normalize_order_result():
    raw_order = {
        "id": "ALP-998877",
        "client_order_id": "cl-DEC-SPY-9942",
        "status": "accepted",
        "filled_avg_price": "1.38",
        "qty": "1",
    }
    result = AlpacaNormalizer.normalize_order_result(raw_order, "DEC-SPY-9942")
    assert isinstance(result, OrderResult)
    assert result.orderId == "ALP-998877"
    assert result.decisionId == "DEC-SPY-9942"
    assert result.status == "accepted"
    assert result.avgPrice == 1.38
    assert result.broker == "ALPACA_PAPER"
