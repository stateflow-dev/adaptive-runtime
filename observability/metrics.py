"""
In-memory lightweight metrics collector.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque


@dataclass
class MetricPoint:
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """Collects and summarises runtime metrics in memory (no external deps)."""

    def __init__(self, max_history: int = 500):
        self._max = max_history
        self._data: dict[str, Deque[MetricPoint]] = defaultdict(
            lambda: deque(maxlen=self._max)
        )

    def record(self, key: str, value: float) -> None:
        self._data[key].append(MetricPoint(value=value))

    def last(self, key: str) -> float | None:
        pts = self._data.get(key)
        return pts[-1].value if pts else None

    def average(self, key: str) -> float | None:
        pts = self._data.get(key)
        if not pts:
            return None
        return sum(p.value for p in pts) / len(pts)

    def summary(self) -> dict[str, dict]:
        return {
            k: {
                "last": self.last(k),
                "avg": round(self.average(k), 4),
                "count": len(v),
            }
            for k, v in self._data.items()
        }


# Module-level singleton
metrics = MetricsCollector()
