import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("VoltronRateLimiter")

class RateLimitGuard:
    """
    Intelligent rate-limiting and quota-preservation guard.
    Protects Google Free Tier API keys (15 RPM / 500 RPD) from 429 quota exhaustion.
    Includes sliding-window RPM throttling, inter-agent pacing, and in-memory TTL caching.
    """

    def __init__(self, rpm_limit: int = 12, enabled: bool = True):
        self._enabled = enabled
        self._rpm_limit = rpm_limit
        self._timestamps: List[float] = []
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()
        
        # TTL Cache: key -> (timestamp, value)
        self._cache: Dict[str, Tuple[float, Any]] = {}

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        logger.info(f"RateLimitGuard enabled state set to: {enabled}")

    @property
    def rpm_limit(self) -> int:
        return self._rpm_limit

    def set_rpm_limit(self, limit: int):
        self._rpm_limit = limit

    def get_current_rpm(self) -> float:
        """Returns the number of requests sent in the rolling 60-second window."""
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < 60.0]
        return float(len(self._timestamps))

    async def acquire_slot(self):
        """
        Paces execution to ensure strict compliance with the RPM limit.
        If current rolling RPM >= limit, asynchronously sleeps until an older request expires.
        """
        if not self._enabled:
            return

        async with self._lock:
            now = time.time()
            self._timestamps = [t for t in self._timestamps if now - t < 60.0]

            # 1. Enforce rolling RPM ceiling
            while len(self._timestamps) >= self._rpm_limit:
                oldest = self._timestamps[0]
                sleep_duration = max(0.5, 60.0 - (now - oldest) + 0.1)
                logger.info(f"RateLimitGuard: Rolling RPM at ceiling ({len(self._timestamps)}/{self._rpm_limit}). Pacing for {sleep_duration:.1f}s...")
                await asyncio.sleep(sleep_duration)
                now = time.time()
                self._timestamps = [t for t in self._timestamps if now - t < 60.0]

            # 2. Inter-agent spacing (minimum 2.5s between calls to prevent burst rate limits)
            elapsed_since_last = now - self._last_request_time
            if elapsed_since_last < 2.5:
                spacing = 2.5 - elapsed_since_last
                await asyncio.sleep(spacing)
                now = time.time()

            self._timestamps.append(now)
            self._last_request_time = now

    def get_cached(self, key: str) -> Optional[Any]:
        """Retrieve cached structured object if TTL has not expired."""
        if not self._enabled:
            return None
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < 180.0:  # 3 minutes TTL
                logger.debug(f"RateLimitGuard: Cache HIT for {key} (age: {time.time() - ts:.1f}s)")
                return val
            else:
                del self._cache[key]
        return None

    def set_cached(self, key: str, value: Any):
        """Cache structured response with current timestamp."""
        if self._enabled:
            self._cache[key] = (time.time(), value)

    def clear_cache(self):
        self._cache.clear()

# Global singleton
quota_guard = RateLimitGuard()
