import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Tuple
from datetime import datetime, timezone
from app.domain.models import OrchestratorEvent

logger = logging.getLogger("VoltronBroadcaster")

class EventBroadcaster:
    """
    In-memory asynchronous SSE event broadcaster.
    Enables real-time streaming of multi-agent reasoning tokens and orchestrator state
    to connected frontend web clients with filtered subscriptions and history buffers.
    """

    def __init__(self):
        # List of (queue, optional_decision_id_filter)
        self._subscribers: List[Tuple[asyncio.Queue, Optional[str]]] = []
        self._history: Dict[str, List[OrchestratorEvent]] = {}
        self._lock = asyncio.Lock()

    async def broadcast(self, event: OrchestratorEvent):
        async with self._lock:
            # Store in history buffer for reconnection support
            if event.decisionId not in self._history:
                self._history[event.decisionId] = []
            self._history[event.decisionId].append(event)

            # Keep last 50 events per decision
            if len(self._history[event.decisionId]) > 50:
                self._history[event.decisionId].pop(0)

            # Dispatch only to matching queues
            dead_entries = []
            for queue, filter_id in self._subscribers:
                if filter_id and filter_id != event.decisionId:
                    continue  # Do not push unrelated events to filtered queues

                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead_entries.append((queue, filter_id))

            for item in dead_entries:
                if item in self._subscribers:
                    self._subscribers.remove(item)

    async def subscribe(self, decision_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        subscription_entry = (queue, decision_id)

        async with self._lock:
            self._subscribers.append(subscription_entry)
            # Replay historical events for this decision if available
            if decision_id and decision_id in self._history:
                for past_event in self._history[decision_id]:
                    queue.put_nowait(past_event)

        try:
            while True:
                event: OrchestratorEvent = await queue.get()
                data_json = json.dumps(event.model_dump())
                yield f"event: {event.eventType}\ndata: {data_json}\n\n"
        finally:
            async with self._lock:
                if subscription_entry in self._subscribers:
                    self._subscribers.remove(subscription_entry)

# Global Broadcaster Singleton
broadcaster = EventBroadcaster()
