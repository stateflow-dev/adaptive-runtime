# Adaptive Runtime — Tier 1 Core

> Adaptive Runtime Layer for Stateful AI Systems

A lightweight, async-first, event-driven runtime intelligence layer for stateful AI agents and autonomous systems.

---

## What this is

**Not** a chatbot framework. **Not** an LLM wrapper. **Not** a drag-drop workflow builder.

This is an **adaptive runtime intelligence layer** — a small operating layer for AI behavior that:

- processes events
- maintains adaptive state
- evaluates contextual conditions
- calculates probabilistic confidence
- makes adaptive decisions
- supports recovery and resilience

Runs comfortably on a low-end laptop or a $5 VPS. No GPU, no PyTorch, no cloud lock-in.

---

## Architecture

```
Event
  ↓
Context Analysis      ← ContextEngine
  ↓
Confidence Evaluation ← ConfidenceEngine
  ↓
Adaptive Decision     ← DecisionEngine
  ↓
State Persistence     ← StateEngine
  ↓
Recovery Snapshot     ← RecoveryEngine
```

---

## Quick Start

```bash
pip install pydantic aiosqlite
```

```python
import asyncio
from adaptive_runtime import Runtime

async def main():
    runtime = Runtime(agent_id="my-agent")
    await runtime.start()

    result = await runtime.process({
        "type": "service_overload",
        "severity": 0.82,
        "cpu": 94,
        "memory": 88,
    })

    print(result.action)      # e.g. "restart_service"
    print(result.confidence)  # e.g. 0.7831
    print(result.reason)      # e.g. "high_resource_pressure"

    await runtime.stop()

asyncio.run(main())
```

---

## Project Structure

```
adaptive_runtime/
│
├── core/
│   ├── state_engine.py      # State persistence and memory
│   ├── context_engine.py    # Event → contextual classification
│   ├── confidence_engine.py # Adaptive probabilistic confidence
│   ├── decision_engine.py   # Rule-based action selection
│   └── recovery_engine.py   # Crash recovery + retry orchestration
│
├── runtime/
│   ├── runtime_manager.py   # Main orchestrator (Runtime class)
│   ├── event_bus.py         # Async pub/sub event bus
│   └── cache.py             # TTL-based in-memory cache
│
├── storage/
│   ├── sqlite_store.py      # Async SQLite persistence
│   └── memory_store.py      # In-process ephemeral store (testing)
│
├── observability/
│   ├── logger.py            # Structured color logger
│   └── metrics.py           # Lightweight in-memory metrics
│
├── examples/
│   ├── agent_demo.py        # Basic event processing demo
│   ├── monitoring_demo.py   # Continuous monitoring + event bus
│   └── automation_demo.py   # Retry + crash recovery demo
│
└── tests/
    └── test_engines.py      # 12 unit tests (all 5 engines)
```

---

## The 5 Core Engines

### 1. State Engine
Manages agent state lifecycle — save, load, patch, reset. Backed by SQLite (default) or in-memory store.

```python
await state_engine.save_state({"health": "ok", "version": "1.2"})
state = await state_engine.load_state()
await state_engine.patch_state({"last_action": "restart"})
```

### 2. Context Engine
Transforms raw events into contextual understanding using weighted pressure scoring and rule-based classification.

```python
ctx = context_engine.analyze({
    "type": "service_overload",
    "cpu": 94,
    "memory": 88,
    "severity": 0.82,
})
# → risk="high", stability="low", context="resource_pressure"
```

### 3. Confidence Engine
Calculates adaptive probabilistic confidence with historical outcome weighting and decay.

```python
conf = confidence_engine.calculate(event, context_risk="high")
# → conf.final = 0.7831

confidence_engine.record_outcome(success=True, confidence=0.78, context_risk="high")
```

### 4. Decision Engine
Matches context + risk + confidence against a rule table to produce an explainable action.

```python
decision = decision_engine.decide(event, "resource_pressure", "high", 0.78)
# → action="restart_service", reason="high_resource_pressure", priority="high"
```

Extend with custom rules:

```python
custom_rules = [
    ("my_context", "high", 0.70, "my_custom_action", "my_reason"),
]
engine = DecisionEngine(custom_rules=custom_rules)
```

### 5. Recovery Engine
Crash recovery, checkpoint snapshots, and retry orchestration with exponential back-off.

```python
# Create periodic checkpoint
await recovery_engine.create_checkpoint(state)

# Restore after crash
state = await recovery_engine.restore_latest()

# Retry with fallback
result = await recovery_engine.retry(flaky_fn, fallback=fallback_fn)
```

---

## Event Bus

Subscribe to specific events or all events:

```python
@runtime.bus.subscribe("anomaly_detected")
async def on_anomaly(event):
    print(f"Anomaly! severity={event['severity']}")

runtime.bus.subscribe_all(my_logger)
```

---

## Storage Backends

| Backend      | Use case                        |
|--------------|---------------------------------|
| SQLiteStore  | Default — persistent, async-safe |
| MemoryStore  | Testing, ephemeral agents        |

Switch with `persist=False`:
```python
runtime = Runtime(persist=False)  # uses MemoryStore
```

---

## Observability

```python
# Metrics summary
print(runtime.metrics_summary())

# Event history
history = await runtime.event_history(limit=20)
```

---

## Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

12 tests covering all 5 engines.

---

## Design Principles

1. **Lightweight cognition** — probabilistic scoring, adaptive weighting, no neural models
2. **Async-first** — asyncio throughout
3. **Modular** — each engine is independently importable and reusable
4. **Minimal dependencies** — pydantic, aiosqlite, nothing else required
5. **Production-oriented** — stable, resilient, explainable

---

## License

MIT
