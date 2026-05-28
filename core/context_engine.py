"""
Context Engine — transforms raw events into contextual understanding.
"""

from pydantic import BaseModel, Field
from observability.logger import get_logger
from observability.metrics import metrics

logger = get_logger("context_engine")


# ── Models ─────────────────────────────────────────────────────────────────

class RawEvent(BaseModel):
    type: str
    severity: float = 0.0
    cpu: float = 0.0
    memory: float = 0.0
    error_rate: float = 0.0
    latency_ms: float = 0.0
    extra: dict = Field(default_factory=dict)


class ContextResult(BaseModel):
    risk: str           # low | medium | high | critical
    stability: str      # stable | degraded | low | critical
    context: str        # symbolic label
    pressure_score: float
    tags: list[str]


# ── Thresholds ─────────────────────────────────────────────────────────────

_RISK_RULES: list[tuple[float, str]] = [
    (0.85, "critical"),
    (0.60, "high"),
    (0.35, "medium"),
    (0.00, "low"),
]

_STABILITY_RULES: list[tuple[float, str]] = [
    (0.85, "critical"),
    (0.65, "low"),
    (0.40, "degraded"),
    (0.00, "stable"),
]

_CONTEXT_MAP: dict[str, str] = {
    "service_overload":  "resource_pressure",
    "anomaly_detected":  "anomaly_signal",
    "memory_leak":       "resource_pressure",
    "timeout":           "latency_issue",
    "auth_failure":      "security_signal",
    "recovery_needed":   "self_healing",
    "degraded_service":  "service_degradation",
}


# ── Engine ─────────────────────────────────────────────────────────────────

class ContextEngine:
    """
    Classifies events and scores runtime context.

    Uses lightweight rule-based scoring — no ML dependencies.
    """

    def __init__(self, custom_context_map: dict[str, str] | None = None):
        self._ctx_map = {**_CONTEXT_MAP, **(custom_context_map or {})}

    def analyze(self, event: dict) -> ContextResult:
        raw = RawEvent(**{k: v for k, v in event.items() if k in RawEvent.model_fields or k == "extra"}, 
                        extra={k: v for k, v in event.items() if k not in RawEvent.model_fields})

        pressure = self._pressure_score(raw)
        risk = self._classify(pressure, _RISK_RULES)
        stability = self._classify(pressure, _STABILITY_RULES)
        context_label = self._ctx_map.get(raw.type, f"unknown_{raw.type}")
        tags = self._build_tags(raw, risk)

        result = ContextResult(
            risk=risk,
            stability=stability,
            context=context_label,
            pressure_score=round(pressure, 4),
            tags=tags,
        )

        metrics.record("context.pressure", pressure)
        logger.info(
            "Context → risk=%s  stability=%s  ctx=%s  pressure=%.2f",
            risk, stability, context_label, pressure,
        )
        return result

    # ── Internals ──────────────────────────────────────────────────────────

    def _pressure_score(self, raw: RawEvent) -> float:
        """Weighted composite score in [0, 1]."""
        weights = {
            "severity":   0.35,
            "cpu":        0.20,
            "memory":     0.20,
            "error_rate": 0.15,
            "latency_ms": 0.10,
        }
        score = (
            raw.severity   * weights["severity"]
            + (raw.cpu / 100)   * weights["cpu"]
            + (raw.memory / 100) * weights["memory"]
            + raw.error_rate    * weights["error_rate"]
            + min(raw.latency_ms / 5000, 1.0) * weights["latency_ms"]
        )
        return min(score, 1.0)

    @staticmethod
    def _classify(score: float, rules: list[tuple[float, str]]) -> str:
        for threshold, label in rules:
            if score >= threshold:
                return label
        return rules[-1][1]

    @staticmethod
    def _build_tags(raw: RawEvent, risk: str) -> list[str]:
        tags = [f"risk:{risk}", f"event:{raw.type}"]
        if raw.cpu > 80:
            tags.append("cpu:high")
        if raw.memory > 80:
            tags.append("memory:high")
        if raw.error_rate > 0.5:
            tags.append("errors:elevated")
        if raw.latency_ms > 2000:
            tags.append("latency:high")
        return tags
