import httpx
from typing import List, Optional, Dict, Any
from app.config import settings
from app.domain.models import OptionLeg
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

class AlpacaOptionsService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client
        self.headers = {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json",
        }

    async def get_option_chain(
        self,
        symbol: str,
        expiration_gte: Optional[str] = None,
        expiration_lte: Optional[str] = None,
    ) -> List[OptionLeg]:
        symbol = symbol.upper()
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic fallback option contracts
            dummy_contracts = [
                {"symbol": f"{symbol}260918P00625000", "underlying_symbol": symbol, "type": "put", "strike_price": 625, "expiration_date": "2026-09-18"},
                {"symbol": f"{symbol}260918P00630000", "underlying_symbol": symbol, "type": "put", "strike_price": 630, "expiration_date": "2026-09-18"},
                {"symbol": f"{symbol}260918C00660000", "underlying_symbol": symbol, "type": "call", "strike_price": 660, "expiration_date": "2026-09-18"},
                {"symbol": f"{symbol}260918C00665000", "underlying_symbol": symbol, "type": "call", "strike_price": 665, "expiration_date": "2026-09-18"},
            ]
            return [AlpacaNormalizer.normalize_option_contract(c) for c in dummy_contracts]

        async with httpx.AsyncClient() as client:
            params: Dict[str, Any] = {"underlying_symbols": symbol, "status": "active"}
            if expiration_gte:
                params["expiration_date_gte"] = expiration_gte
            if expiration_lte:
                params["expiration_date_lte"] = expiration_lte

            # 1. Fetch Option Contracts
            resp = await client.get(
                f"{settings.ALPACA_BASE_URL}/v2/options/contracts",
                headers=self.headers,
                params=params,
                timeout=15.0,
            )
            resp.raise_for_status()
            contracts_data = resp.json().get("option_contracts", [])

            # 2. Fetch Snapshots (Greeks, Bid/Ask, IV) if available
            snapshots: Dict[str, Any] = {}
            try:
                snap_resp = await client.get(
                    f"{settings.ALPACA_DATA_URL}/v1beta1/options/snapshots/{symbol}",
                    headers=self.headers,
                    timeout=15.0,
                )
                if snap_resp.status_code == 200:
                    snapshots = snap_resp.json().get("snapshots", {})
            except Exception:
                pass

            # 3. Normalize into domain OptionLeg list
            results: List[OptionLeg] = []
            for c in contracts_data:
                contract_symbol = c.get("symbol", "")
                snap = snapshots.get(contract_symbol)
                results.append(AlpacaNormalizer.normalize_option_contract(c, snap))

            return results
