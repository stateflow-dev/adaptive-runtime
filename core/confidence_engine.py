"""
Confidence Engine — adaptive probabilistic confidence scoring.
"""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from pydantic import BaseModel
from observability.logger import get_logger
from observability.metrics import metrics

logger = get_logger("confidence_engine")


@dataclass
class OutcomeRecord:
    success: bool
    confidence_at_time: float
    context_risk: str


class ConfidenceResult(BaseModel):
    confidence: float
    decay_factor: float
    history_weight: float
    context_adjustment: float
    final: float


class ConfidenceEngine:
    """
    Calculates adaptive confidence using:
      - base score from event severity
      - contextual adjustment from risk level
      - historical outcome weighting (exponential decay)
      - configurable decay over time
    """

    RISK_WEIGHTS = {
        "low":      1.00,
        "medium":   0.90,
        "high":     0.75,
        "critical": 0.55,
    }

    def __init__(
        self,
        base_confidence: float = 0.75,
        decay_rate: float = 0.05,
        history_window: int = 50,
    ):
        self._base = base_confidence
        self._decay_rate = decay_rate
        self._history: Deque[OutcomeRecord] = deque(maxlen=history_window)
        self._call_count = 0

    # ── Public API ─────────────────────────────────────────────────────────

    def calculate(self, event: dict, context_risk: str) -> ConfidenceResult:
        self._call_count += 1

        severity = float(event.get("severity", 0.5))
        base = max(0.1, self._base - severity * 0.2)

        decay = self._decay_factor()
        hist_weight = self._history_weight(context_risk)
        ctx_adj = self.RISK_WEIGHTS.get(context_risk, 0.8)

        raw = base * decay * hist_weight * ctx_adj
        final = round(min(max(raw, 0.05), 0.99), 4)

        result = ConfidenceResult(
            confidence=round(base, 4),
            decay_factor=round(decay, 4),
            history_weight=round(hist_weight, 4),
            context_adjustment=round(ctx_adj, 4),
            final=final,
        )
        metrics.record("confidence.final", final)
        logger.info(
            "Confidence → base=%.2f  decay=%.2f  hist=%.2f  ctx=%.2f  final=%.4f",
            base, decay, hist_weight, ctx_adj, final,
        )
        return result

    def record_outcome(self, success: bool, confidence: float, context_risk: str) -> None:
        """Feed outcome back for adaptive weighting."""
        self._history.append(OutcomeRecord(
            success=success,
            confidence_at_time=confidence,
            context_risk=context_risk,
        ))
        logger.debug("Outcome recorded: success=%s  conf=%.3f", success, confidence)

    # ── Internals ──────────────────────────────────────────────────────────

    def _decay_factor(self) -> float:
        """Confidence decays slightly as call volume grows (simulate drift)."""
        return math.exp(-self._decay_rate * (self._call_count // 20))

    def _history_weight(self, context_risk: str) -> float:
        """Adjust weight based on past success rate for the same risk tier."""
        relevant = [r for r in self._history if r.context_risk == context_risk]
        if len(relevant) < 3:
            return 1.0
        success_rate = sum(1 for r in relevant if r.success) / len(relevant)
        # Map [0, 1] success rate → [0.6, 1.1] weight
        return 0.6 + success_rate * 0.5
