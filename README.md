<p align="center">
  <h1 align="center">Adaptive Runtime</h1>
  <p align="center"><b>Runtime Intelligence Layer for Long-Running Systems</b></p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" />
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
    <img src="https://img.shields.io/badge/tests-12%20passing-brightgreen?style=flat-square" />
    <img src="https://img.shields.io/badge/GPU-not%20required-orange?style=flat-square" />
    <img src="https://img.shields.io/badge/runs%20on-%245%20VPS-lightgrey?style=flat-square" />
    <img src="https://img.shields.io/badge/cold%20start-~30ms-blue?style=flat-square" />
    <img src="https://img.shields.io/badge/idle%20memory-30MB-green?style=flat-square" />
    <a href="https://github.com/stateflow-dev/adaptive-runtime/actions/workflows/ci.yml"><img src="https://github.com/stateflow-dev/adaptive-runtime/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  </p>
  <p align="center">
    <a href="https://stateflow-dev.github.io/stateflowlabs/">Part of the Stateflow Labs Runtime Intelligence Ecosystem</a>
  </p>
</p>

---

> **Not** a chatbot framework. **Not** an LLM wrapper. **Not** a workflow builder.
>
> An **adaptive runtime intelligence layer** — the missing piece between your application logic and production reality.

---

## The Problem

Most frameworks solve the *logic* problem.  
Nobody solves the *runtime* problem.

```
Your service in development:   Works perfectly.
Your service in production:    Crashes. Loses state. Retries blindly. Dies silently.
```

Long-running systems fail in production because of:

- 💥 **No crash recovery** — state lost on restart
- 🧠 **No memory** — service forgets context between sessions
- 🔁 **Retry chaos** — blind retries with no back-off
- 📉 **No confidence scoring** — decisions made without certainty
- 🌊 **No contextual awareness** — can't adapt to changing conditions

**Adaptive Runtime fixes this.**

---

## Why Adaptive Runtime Exists

Most frameworks focus on *what* a system should do.

Adaptive Runtime focuses on *what happens* when the system has already been running for hours, days, or weeks — and something goes wrong.

It provides:

- **state persistence** — runtime memory that survives crashes and restarts
- **contextual awareness** — understanding of current operating conditions
- **confidence-aware decisions** — actions weighted by certainty, not just rules
- **recovery workflows** — automatic restoration from checkpoints after failure

All of this without requiring a cloud service, LLM, or external orchestration platform.

---

## See It Running

<p align="center">
  <img src="render1779972984877.gif" width="860" alt="Adaptive Runtime Demo" />
</p>

```
[16:08:13][RUNTIME]          Event received: service_overload
[16:08:13][CONTEXT_ENGINE]   risk=high  stability=low  pressure=0.65
[16:08:13][CONFIDENCE_ENGINE] confidence=0.84
[16:08:13][DECISION_ENGINE]  ACTION: RESTART_SERVICE
[16:08:13][STATE_ENGINE]     State persisted
[16:08:13][RECOVERY_ENGINE]  Checkpoint #3 created

  → restart_service  [high]  conf=0.840

[16:08:14][RUNTIME]          Event received: anomaly_detected
[16:08:14][CONTEXT_ENGINE]   risk=low   stability=stable  pressure=0.32
[16:08:14][CONFIDENCE_ENGINE] confidence=0.62
[16:08:14][DECISION_ENGINE]  ACTION: FLAG_FOR_REVIEW
[16:08:14][STATE_ENGINE]     State persisted

  → flag_for_review  [low]   conf=0.620
```

The runtime **evaluates conditions**, **selects actions**, **remembers state**, and **recovers** — automatically.

---

## How It Works

```
Event (CPU spike, anomaly, timeout, auth failure...)
  │
  ▼
┌─────────────────┐
│  Context Engine │  → Analyzes conditions: risk, stability, pressure score
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│  Confidence Engine   │  → Calculates adaptive confidence (with decay + history)
└────────┬─────────────┘
         │
         ▼
┌──────────────────┐
│  Decision Engine │  → Selects action: restart / throttle / rollback / recover...
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   State Engine   │  → Persists state to SQLite (survives crashes)
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│   Recovery Engine    │  → Creates checkpoint, handles retry with back-off
└──────────────────────┘
```

---

## Quick Start

```bash
# Install from package
pip install adaptive-runtime

# Or for local development
pip install -e .
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

    print(result.action)      # "restart_service"
    print(result.confidence)  # 0.7831
    print(result.reason)      # "high_resource_pressure"
    print(result.priority)    # "high"

    await runtime.stop()

asyncio.run(main())
```

**That's it.** No API keys. No cloud setup. No GPU. Runs on a $5 VPS.

---

## Where Does Adaptive Runtime Fit?

Adaptive Runtime is **not** something you run *instead of* your application.

It runs **alongside** your application — as a runtime intelligence layer between your business logic and real-world operating conditions.

**Before Adaptive Runtime** — your monitoring loop runs, but has no runtime awareness:

```python
while True:
    run_api_test_case(...)
```

**After Adaptive Runtime** — the same loop runs, now with context, confidence, and recovery:

```python
runtime = Runtime(agent_id="api-watchdog")
await runtime.start()

# Runtime observes the signal before your logic runs
result = await runtime.process({
    "type": "timeout",
    "severity": 0.72,
    "latency_ms": 4200
})

# Your original logic remains completely unchanged
run_api_test_case(...)
```

The watchdog still performs API monitoring. Adaptive Runtime does not replace it — it provides runtime intelligence *around* it.

```
Your Application
        │
        ▼
Adaptive Runtime
        │
 ├─ Context Engine
 ├─ Confidence Engine
 ├─ Decision Engine
 ├─ State Engine
 └─ Recovery Engine
        │
        ▼
Runtime Actions
```

What it adds — without touching your application logic:

- **Contextual awareness** — understands the operating environment
- **Confidence scoring** — knows how certain a decision is before acting
- **State persistence** — remembers across restarts and crashes
- **Recovery workflows** — restores from checkpoints automatically
- **Runtime observability** — structured metrics and logging built-in

---

## Example: Adding Runtime Intelligence to API Watchdog

> **API Watchdog is an independent open-source project created by Jose Fondrej. The project is referenced here solely as an integration example.**  
> GitHub: [github.com/josefondrej/api-watchdog](https://github.com/josefondrej/api-watchdog)

Adaptive Runtime is not a monitoring tool. It is not a watchdog. It is a runtime intelligence layer that can be added to monitoring tools like API Watchdog — without changing any of their existing logic.

API Watchdog continuously monitors endpoints. Failures produce runtime events:

```
API Watchdog
      │
      ▼
API Failure Event
(timeout / degraded_service / anomaly_detected / recovery_needed)
      │
      ▼
Adaptive Runtime
      │
 ├─ Context Engine
 ├─ Confidence Engine
 ├─ Decision Engine
 ├─ State Engine
 └─ Recovery Engine
      │
      ▼
Runtime Action
```

Here is what the original API Watchdog loop looks like:

### Before

```python
while True:
    config = Config.from_file(config_file_path)

    for api_test_case in config.api_test_cases:
        api_test_case_record = run_api_test_case(api_test_case)
        database.insert_api_test_case_record(api_test_case_record)

        if api_test_case_record.result.status != PASSED:
            logger.error(...)
```

### After

```python
runtime = Runtime(agent_id="api-watchdog")
await runtime.start()

while True:
    config = Config.from_file(config_file_path)

    for api_test_case in config.api_test_cases:
        api_test_case_record = run_api_test_case(api_test_case)
        database.insert_api_test_case_record(api_test_case_record)

        if api_test_case_record.result.status != PASSED:

            result = await runtime.process({
                "type": "timeout",
                "severity": 0.72,
                "latency_ms": 4200
            })

            logger.error(
                f"Decision={result.action} "
                f"Confidence={result.confidence:.2f}"
            )
```

Notice what did **not** change:

- API Watchdog still performs API testing
- API Watchdog still stores results
- API Watchdog still controls monitoring logic

Adaptive Runtime only:

- analyzes runtime context
- calculates confidence
- selects recovery actions
- persists runtime state
- records event history

**The application remains the same. The runtime becomes smarter.**

Runtime output for a timeout event:

```
Context:     degraded_network
Confidence:  0.68
Decision:    cache_warmup
Priority:    normal
```

---

## Where Adaptive Runtime Adds Value

### API Monitoring Platforms

Examples: API Watchdog, uptime monitoring, health-check services, synthetic monitoring.

Adaptive Runtime adds:

- confidence scoring on failure events
- contextual failure classification (timeout vs degradation vs anomaly)
- checkpoint recovery after crashes
- runtime observability across long monitoring sessions

### Long-Running Services

Examples: customer support systems, AI workers, automation daemons.

Adaptive Runtime adds:

- persistence across restarts
- event history for replay and debugging
- recovery workflows that resume automatically after failure

### Edge and Infrastructure Systems

Examples: Raspberry Pi monitoring, edge gateways, industrial monitoring nodes.

Adaptive Runtime adds:

- lightweight resilience with no GPU or cloud dependency
- SQLite persistence with minimal memory footprint
- recovery after unexpected interruption or power loss

---

## Example Included

See `examples/agent_demo.py` for a complete walkthrough of the Adaptive Runtime lifecycle.

Events enter the runtime. The **Context Engine** analyzes conditions. The **Confidence Engine** calculates certainty. The **Decision Engine** selects an action. The **State Engine** persists runtime state. The **Recovery Engine** manages checkpoints.

```
service_overload  → throttle_requests
anomaly_detected  → flag_for_review
timeout           → cache_warmup
degraded_service  → health_check
recovery_needed   → run_recovery
```

In a production system such as API Watchdog, these events would originate from real monitoring data rather than a demo event list.

---

## When Should I Use Adaptive Runtime?

**Use Adaptive Runtime if:**

- your application runs for hours or days
- you need runtime resilience
- you need checkpointing
- you need state persistence
- you need recovery workflows
- you need confidence-aware decisions
- you need runtime observability
- you need contextual runtime behavior

**Do not use Adaptive Runtime if:**

- your script runs once and exits
- you only need automation scripts
- you only need API calls
- you only need lightweight workflows

For those scenarios, **ALGOgent Runtime** is usually the better choice.

---

## How Adaptive Runtime Differs from LLM Frameworks

LLM frameworks focus on model orchestration — prompt chains, RAG pipelines, agent loops.

Adaptive Runtime focuses on a different layer entirely: runtime behavior, state persistence, recovery, and operational resilience. It does not use a language model internally. It does not require one to function.

| | LLM Frameworks | **Adaptive Runtime** |
|---|---|---|
| **Purpose** | Model orchestration | Runtime behavior |
| **Core abstraction** | Prompt chains | Stateful events |
| **Intelligence source** | Language model | Probabilistic rule engine |
| **Dependencies** | Heavy (model SDKs, tokenizers) | Minimal (pydantic, aiosqlite) |
| **GPU required** | Sometimes | **Never** |
| **Crash recovery** | ❌ | ✅ Built-in |
| **State persistence** | External setup required | ✅ Built-in SQLite |
| **Confidence scoring** | ❌ | ✅ Adaptive |
| **Runs on $5 VPS** | Rarely | ✅ Designed for it |
| **Use case** | Chat, RAG, agents | **Runtime resilience** |

They solve different layers of the stack and can be used together. Adaptive Runtime does not replace LLM frameworks — it handles the operational layer they leave unaddressed.

---

## Runtime Philosophy

> Most AI problems in production are not model problems.  
> They are **runtime problems**.

Adaptive Runtime is built around the belief that future AI systems need:

- **Memory** — state that survives crashes and restarts
- **Resilience** — self-healing with checkpoints and retry logic  
- **Contextual behavior** — decisions that adapt to real conditions
- **Confidence awareness** — knowing *how certain* a decision is
- **Lightweight cognition** — intelligence without neural dependency

Not just prompts. Not just workflows. **Runtime intelligence.**

---

## The 5 Core Engines

### 1. State Engine
Persistent agent memory. Survives crashes. SQLite by default.

```python
await state_engine.save_state({"health": "ok", "version": "1.2"})
state = await state_engine.load_state()          # Restored after restart
await state_engine.patch_state({"last": "ok"})   # Partial update
```

### 2. Context Engine
Transforms raw signals into contextual understanding — no ML needed.

```python
ctx = context_engine.analyze({
    "type": "service_overload", "cpu": 94, "memory": 88, "severity": 0.82
})
# → risk="high", stability="low", context="resource_pressure", pressure=0.65
```

### 3. Confidence Engine
Adaptive probabilistic scoring with historical weighting and decay.

```python
conf = confidence_engine.calculate(event, context_risk="high")
# → conf.final = 0.7831  (lower when risk is high, adapts from history)

confidence_engine.record_outcome(success=True, confidence=0.78, context_risk="high")
```

### 4. Decision Engine
Explainable rule-based action selection. Extensible with custom rules.

```python
decision = decision_engine.decide(event, "resource_pressure", "high", 0.78)
# → action="restart_service", reason="high_resource_pressure", priority="high"

# Add your own rules:
custom_rules = [("my_context", "high", 0.70, "my_action", "my_reason")]
engine = DecisionEngine(custom_rules=custom_rules)
```

### 5. Recovery Engine
Crash recovery, checkpoint snapshots, exponential back-off retry.

```python
await recovery_engine.create_checkpoint(state)    # Save checkpoint
state = await recovery_engine.restore_latest()    # Restore after crash
result = await recovery_engine.retry(fn, fallback=fallback_fn)  # Retry with back-off
```

---

## Designed for Constrained Environments

```
✅ Raspberry Pi
✅ $5 VPS (512MB RAM)  
✅ Old laptop
✅ Edge devices
✅ Offline / air-gapped systems
✅ Serverless (cold start friendly)
```

No GPU. No cloud lock-in. No heavy ML frameworks.  
Just Python + asyncio + SQLite.

---

## Project Structure

```
adaptive_runtime/
│
├── core/
│   ├── __init__.py
│   ├── confidence_engine.py  # Adaptive probabilistic confidence
│   ├── context_engine.py     # Event → contextual classification
│   ├── decision_engine.py    # Rule-based action selection
│   ├── recovery_engine.py    # Crash recovery + retry orchestration
│   └── state_engine.py       # State persistence and memory
│
├── observability/
│   ├── __init__.py
│   ├── logger.py             # Structured color logger
│   └── metrics.py            # Lightweight in-memory metrics
│
├── runtime/
│   ├── __init__.py
│   ├── benchmark.py          # Performance benchmarking
│   ├── cache.py              # TTL-based in-memory cache
│   ├── event_bus.py          # Async pub/sub event bus
│   └── runtime_manager.py    # Main orchestrator (Runtime class)
│
├── storage/
│   ├── __init__.py
│   ├── memory_store.py       # In-process ephemeral store (testing)
│   └── sqlite_store.py       # Async SQLite persistence
│
└── __init__.py
│
examples/
├── agent_demo.py             # Basic event processing
├── automation_demo.py        # Retry + crash recovery
├── demo.yml                  # Demo configuration
├── demo_record.py            # Demo record helper
└── monitoring_demo.py        # Continuous monitoring + event bus
│
tests/
├── __init__.py
└── test_engines.py           # 12 unit tests — all engines
```

---

## Run the Examples

```bash
# Clone
git clone https://github.com/stateflow-dev/adaptive-runtime.git
cd adaptive-runtime

# Install
pip install adaptive-runtime

# Run demos
python examples/agent_demo.py
python examples/monitoring_demo.py
python examples/automation_demo.py

# Run tests
pip install pytest pytest-asyncio
pytest tests/ -v
# → 12 passed
```

---

## Roadmap

| | Feature | Status |
|---|---|---|
| ✅ | 5 Core Engines | Tier 1 — Released |
| ✅ | SQLite + Memory store | Tier 1 — Released |
| ✅ | Async event bus | Tier 1 — Released |
| ✅ | Retry + crash recovery | Tier 1 — Released |
| 🔜 | REST API adapter (FastAPI) | Tier 2 |
| 🔜 | Multi-agent orchestration | Tier 2 |
| 🔜 | Plugin system | Tier 2 |
| 🔜 | Real-time dashboard | Tier 2 |
| 🔜 | Distributed runtime | Tier 3 |

---

## Benchmarks

Measured on a mid-range Windows laptop (Python 3.11, SQLite, no GPU).

| Metric | Result |
|---|---|
| Cold start | ~0 ms (warm import) |
| Idle memory | 30 MB |
| CPU idle usage | <0% |
| SQLite save latency | 81.3 ms avg (n=50) |
| SQLite load latency | 2.7 ms avg (n=50) |
| Event processing | 197.6 ms avg (n=50) |
| GPU required | ❌ Never |

> Runs comfortably on a $5 VPS (512MB RAM). No GPU. No cloud lock-in.

---

## Stateflow Labs Ecosystem

Adaptive Runtime is part of the **Stateflow Labs runtime intelligence ecosystem**.

🌐 [https://stateflow-dev.github.io/stateflowlabs/](https://stateflow-dev.github.io/stateflowlabs/)

### Related Project: ALGOgent Runtime

The two projects are often confused. Here is the clearest way to think about them:

| | ALGOgent Runtime | Adaptive Runtime |
|---|---|---|
| **Best for** | Scripts, automation, task execution | Long-running services, stateful systems |
| **Runtime model** | Run once, exit cleanly | Runs for hours or days without stopping |
| **State** | Lightweight, per-run | Persistent across restarts and crashes |
| **Recovery** | Basic retry | Full checkpoint + restore workflows |
| **Decisions** | Task-driven | Context-aware, confidence-scored |
| **Core abstraction** | Task / workflow | Runtime event |
| **Typical use** | AI pipelines, tool execution, automation | Monitoring daemons, AI workers, edge systems |

**Rule of thumb:**
- Your script runs once and exits → **ALGOgent Runtime**
- Your service runs continuously and must survive failure → **Adaptive Runtime**

Neither project is positioned as AGI, autonomous AI, or chatbot infrastructure. Both are **runtime tools** — reliable, observable, and production-ready.

---

## Keywords

Adaptive Runtime is a Python runtime framework for:

- stateful services and long-running daemons
- fault-tolerant systems and resilience engineering
- event-driven applications and runtime event processing
- recovery-oriented architectures and checkpoint management
- runtime resilience and operational observability
- edge computing workloads and constrained environments
- confidence-aware decision systems without ML dependencies

---

## Contributing

Issues and PRs welcome. Please open an issue first for major changes.

---

## License

MIT © [Stateflow Labs](https://github.com/stateflow-dev)

---

<p align="center">
  <b>"The biggest AI problems in production are not model problems.<br>They are runtime problems."</b>
</p>
