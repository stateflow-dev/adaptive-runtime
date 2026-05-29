"""
Async event bus — pub/sub within a single runtime process.
"""

import asyncio
from collections import defaultdict
from typing import Callable, Awaitable

from observability.logger import get_logger

logger = get_logger("event_bus")

Handler = Callable[[dict], Awaitable[None]]


class EventBus:
    """
    Lightweight in-process async event bus.

    Usage:
        bus = EventBus()

        @bus.subscribe("anomaly_detected")
        async def on_anomaly(event):
            ...

        await bus.publish({"type": "anomaly_detected", "severity": 0.9})
    """

    def __init__(self):
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._wildcard: list[Handler] = []

    def subscribe(self, event_type: str):
        """Decorator — registers a handler for a specific event type."""
        def decorator(fn: Handler) -> Handler:
            self._handlers[event_type].append(fn)
            logger.debug("Subscribed handler '%s' to event '%s'", fn.__name__, event_type)
            return fn
        return decorator

    def subscribe_all(self, fn: Handler) -> None:
        """Register a wildcard handler that receives every event."""
        self._wildcard.append(fn)

    async def publish(self, event: dict) -> int:
        """
        Fire an event and await all matching handlers concurrently.
        Returns the number of handlers invoked.
        """
        etype = event.get("type", "__unknown__")
        handlers = self._handlers.get(etype, []) + self._wildcard
        if not handlers:
            logger.debug("No handlers for event '%s'", etype)
            return 0

        await asyncio.gather(*[h(event) for h in handlers], return_exceptions=True)
        return len(handlers)
