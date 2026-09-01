import time
import asyncio
import httpx
from typing import List, Optional, Dict, Any, Tuple
from app.config import settings
from app.domain.models import OptionLeg
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

_OPTION_CHAIN_CACHE: Dict[str, Tuple[float, List[OptionLeg]]] = {}
CACHE_TTL_SECONDS = 45.0

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
        cache_key = f"{symbol}:{expiration_gte}:{expiration_lte}"
        now_ts = time.time()
        if cache_key in _OPTION_CHAIN_CACHE:
            ts, cached_data = _OPTION_CHAIN_CACHE[cache_key]
            if now_ts - ts < CACHE_TTL_SECONDS:
                return cached_data

        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic fallback option contracts
            dummy_contracts = [
                {"symbol": f"{symbol}260918P00625000", "underlying_symbol": symbol, "type": "put", "strike_price": 625, "expiration_date": "2026-09-18"},
                {"symbol": f"{symbol}260918P00630000", "underlying_symbol": symbol, "type": "put", "strike_price": 630, "expiration_date": "2026-09-18"},
                {"symbol": f"{symbol}260918C00660000", "underlying_symbol": symbol, "type": "call", "strike_price": 660, "expiration_date": "2026-09-18"},
                {"symbol": f"{symbol}260918C00665000", "underlying_symbol": symbol, "type": "call", "strike_price": 665, "expiration_date": "2026-09-18"},
            ]
            res = [AlpacaNormalizer.normalize_option_contract(c) for c in dummy_contracts]
            _OPTION_CHAIN_CACHE[cache_key] = (now_ts, res)
            return res

        async with httpx.AsyncClient() as client:
            params: Dict[str, Any] = {"underlying_symbols": symbol, "status": "active", "limit": 60}
            if expiration_gte:
                params["expiration_date_gte"] = expiration_gte
            if expiration_lte:
                params["expiration_date_lte"] = expiration_lte

            # 1 & 2. Concurrently fetch Option Contracts and Snapshots
            contracts_task = client.get(
                f"{settings.ALPACA_BASE_URL}/v2/options/contracts",
                headers=self.headers,
                params=params,
                timeout=8.0,
            )
            snapshot_task = client.get(
                f"{settings.ALPACA_DATA_URL}/v1beta1/options/snapshots/{symbol}",
                headers=self.headers,
                timeout=8.0,
            )

            contracts_res, snap_res = await asyncio.gather(contracts_task, snapshot_task, return_exceptions=True)

            contracts_data = []
            if not isinstance(contracts_res, Exception) and hasattr(contracts_res, "status_code") and contracts_res.status_code == 200:
                contracts_data = contracts_res.json().get("option_contracts", [])

            snapshots: Dict[str, Any] = {}
            if not isinstance(snap_res, Exception) and hasattr(snap_res, "status_code") and snap_res.status_code == 200:
                snapshots = snap_res.json().get("snapshots", {})

            # 3. Normalize into domain OptionLeg list
            results: List[OptionLeg] = []
            for c in contracts_data:
                contract_symbol = c.get("symbol", "")
                snap = snapshots.get(contract_symbol)
                results.append(AlpacaNormalizer.normalize_option_contract(c, snap))

            if results:
                _OPTION_CHAIN_CACHE[cache_key] = (now_ts, results)
            return results
