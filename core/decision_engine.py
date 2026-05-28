"""
Decision Engine — generates adaptive runtime decisions.
"""

from pydantic import BaseModel
from observability.logger import get_logger
from observability.metrics import metrics

logger = get_logger("decision_engine")


class DecisionResult(BaseModel):
    action: str
    confidence: float
    reason: str
    priority: str       # low | normal | high | critical
    metadata: dict = {}


# ── Action ruleset ─────────────────────────────────────────────────────────
# Each rule: (context_label, risk_level, min_confidence) → action
# Evaluated top-to-bottom; first match wins.

_RULES: list[tuple[str | None, str | None, float, str, str]] = [
    # (context,            risk,       min_conf, action,               reason)
    ("resource_pressure",  "critical", 0.0,      "scale_up_immediate",    "critical_resource_pressure"),
    ("resource_pressure",  "high",     0.70,     "restart_service",        "high_resource_pressure"),
    ("resource_pressure",  "high",     0.0,      "throttle_requests",      "resource_pressure_low_confidence"),
    ("resource_pressure",  "medium",   0.0,      "optimize_resources",     "medium_resource_pressure"),
    ("anomaly_signal",     "critical", 0.0,      "isolate_component",      "critical_anomaly"),
    ("anomaly_signal",     "high",     0.65,     "rollback_deployment",    "anomaly_with_confidence"),
    ("anomaly_signal",     "high",     0.0,      "increase_monitoring",    "anomaly_low_confidence"),
    ("anomaly_signal",     None,       0.0,      "flag_for_review",        "anomaly_detected"),
    ("latency_issue",      "high",     0.0,      "optimize_query",         "latency_degradation"),
    ("latency_issue",      None,       0.0,      "cache_warmup",           "latency_signal"),
    ("security_signal",    None,       0.0,      "trigger_security_audit", "security_event"),
    ("self_healing",       None,       0.0,      "run_recovery",           "recovery_requested"),
    ("service_degradation","high",     0.0,      "circuit_breaker_open",   "service_degraded_high"),
    ("service_degradation", None,      0.0,      "health_check",           "service_degraded"),
]

_PRIORITY_MAP = {
    "critical": "critical",
    "high":     "high",
    "medium":   "normal",
    "low":      "low",
}


class DecisionEngine:
    """
    Matches context + risk + confidence against a rule table to produce
    a ranked, explainable action.  No ML required.
    """

    def __init__(self, custom_rules: list | None = None):
        self._rules = (custom_rules or []) + _RULES

    def decide(
        self,
        event: dict,
        context_label: str,
        risk: str,
        confidence: float,
    ) -> DecisionResult:
        action, reason = self._match(context_label, risk, confidence)
        priority = _PRIORITY_MAP.get(risk, "normal")

        result = DecisionResult(
            action=action,
            confidence=round(confidence, 4),
            reason=reason,
            priority=priority,
            metadata={
                "event_type": event.get("type"),
                "context": context_label,
                "risk": risk,
            },
        )
        metrics.record("decision.confidence", confidence)
        logger.info(
            "Decision → action=%s  confidence=%.3f  reason=%s  priority=%s",
            action, confidence, reason, priority,
        )
        return result

    # ── Internals ──────────────────────────────────────────────────────────

    def _match(self, context: str, risk: str, confidence: float) -> tuple[str, str]:
        for ctx_rule, risk_rule, min_conf, action, reason in self._rules:
            ctx_ok  = ctx_rule  is None or ctx_rule  == context
            risk_ok = risk_rule is None or risk_rule == risk
            conf_ok = confidence >= min_conf
            if ctx_ok and risk_ok and conf_ok:
                return action, reason
        return "monitor_and_wait", "no_matching_rule"
