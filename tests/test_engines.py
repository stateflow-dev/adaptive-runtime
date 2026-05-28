"""
Unit tests for all 5 core engines.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from storage.memory_store import MemoryStore
from core.state_engine import StateEngine
from core.context_engine import ContextEngine
from core.confidence_engine import ConfidenceEngine
from core.decision_engine import DecisionEngine
from core.recovery_engine import RecoveryEngine


# ── State Engine ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_state_save_load():
    store = MemoryStore()
    engine = StateEngine(store, "test-agent")
    await engine.save_state({"foo": "bar", "score": 0.9})
    loaded = await engine.load_state()
    assert loaded["foo"] == "bar"
    assert loaded["score"] == 0.9


@pytest.mark.asyncio
async def test_state_patch():
    store = MemoryStore()
    engine = StateEngine(store, "test-agent")
    await engine.save_state({"x": 1})
    patched = await engine.patch_state({"y": 2})
    assert patched["x"] == 1
    assert patched["y"] == 2


# ── Context Engine ─────────────────────────────────────────────────────────

def test_context_high_risk():
    engine = ContextEngine()
    result = engine.analyze({"type": "service_overload", "severity": 0.9, "cpu": 95, "memory": 90})
    assert result.risk in ("high", "critical")
    assert "resource_pressure" in result.context


def test_context_low_risk():
    engine = ContextEngine()
    result = engine.analyze({"type": "service_overload", "severity": 0.1, "cpu": 20, "memory": 20})
    assert result.risk == "low"


# ── Confidence Engine ──────────────────────────────────────────────────────

def test_confidence_output_range():
    engine = ConfidenceEngine()
    for risk in ("low", "medium", "high", "critical"):
        res = engine.calculate({"severity": 0.5}, risk)
        assert 0.0 < res.final <= 1.0


def test_confidence_higher_for_lower_risk():
    engine = ConfidenceEngine()
    low  = engine.calculate({"severity": 0.3}, "low").final
    high = engine.calculate({"severity": 0.3}, "high").final
    assert low > high


# ── Decision Engine ────────────────────────────────────────────────────────

def test_decision_resource_pressure_critical():
    engine = DecisionEngine()
    result = engine.decide({"type": "service_overload"}, "resource_pressure", "critical", 0.5)
    assert result.action == "scale_up_immediate"
    assert result.priority == "critical"


def test_decision_anomaly_fallback():
    engine = DecisionEngine()
    result = engine.decide({"type": "anomaly_detected"}, "anomaly_signal", "low", 0.99)
    assert result.action == "flag_for_review"


def test_decision_no_match():
    engine = DecisionEngine()
    result = engine.decide({"type": "unknown_xyz"}, "unknown_xyz", "low", 0.5)
    assert result.action == "monitor_and_wait"


# ── Recovery Engine ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_checkpoint_and_restore():
    store = MemoryStore()
    await store.connect()
    engine = RecoveryEngine(store, "test-recovery")
    state = {"health": "ok", "version": "1.2.3"}
    meta = await engine.create_checkpoint(state)
    assert meta.snapshot_id >= 1
    restored = await engine.restore_latest()
    # MemoryStore merges the snapshot dict inline; check state key exists
    assert restored is not None
    # state is nested under "state" key in the snapshot
    state_data = restored.get("state", restored)
    assert state_data.get("health") == "ok"


@pytest.mark.asyncio
async def test_retry_success():
    store = MemoryStore()
    engine = RecoveryEngine(store, "retry-test", max_retries=3, base_delay=0.01)
    calls = [0]

    async def flaky():
        calls[0] += 1
        if calls[0] < 2:
            raise ValueError("fail")
        return "ok"

    result = await engine.retry(flaky)
    assert result == "ok"
    assert calls[0] == 2


@pytest.mark.asyncio
async def test_retry_fallback():
    store = MemoryStore()
    engine = RecoveryEngine(store, "fallback-test", max_retries=2, base_delay=0.01)

    async def always_fail():
        raise RuntimeError("always")

    async def fallback():
        return "fallback_result"

    result = await engine.retry(always_fail, fallback=fallback)
    assert result == "fallback_result"
