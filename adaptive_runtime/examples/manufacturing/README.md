# Manufacturing Line Recovery

> A real-world use case: adaptive state recovery for industrial production line systems.

---

## The Problem

Manufacturing lines face a brutal production reality:

```
Sensor detects anomaly
  ↓
Quality drops below threshold
  ↓
Machine stops — state lost
  ↓
Operator restarts manually
  ↓
Batch context gone
  ↓
Production resumes from wrong state
```

Traditional factory software has **no runtime resilience**.  
When a machine stops, state is lost. When power returns, the system starts fresh — with no memory of the last batch, quality score, or machine state.

This is not a hardware problem. This is a **runtime problem**.

---

## What Adaptive Runtime Does

```
Conveyor failure detected
  ↓
Context Engine  →  risk=critical, stability=low
  ↓
Confidence Engine  →  confidence=0.71 (adjusted for fault context)
  ↓
Decision Engine  →  ACTION: isolate_line + save_state
  ↓
State Engine  →  State persisted to SQLite before shutdown
  ↓
Recovery Engine  →  Checkpoint saved, restored in 4ms after restart
```

The system **remembers** the production line before failure.  
It **recovers** to the last known stable state automatically.  
No manual restart. No lost batch context. No wrong decisions.

---

## Architecture

```
Factory Floor Sensors
        │
        ▼
┌───────────────────┐
│   Event Stream    │  temperature_high, conveyor_failure, quality_alert...
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Adaptive Runtime │
│                   │
│  Context Engine   │  → Local fault or cascading line failure?
│  Confidence Engine│  → How certain are we about this reading?
│  Decision Engine  │  → inspect / isolate / recover / resume
│  State Engine     │  → Persist line state (survives power loss)
│  Recovery Engine  │  → Restore last stable state after restart
└───────────────────┘
         │
         ▼
┌───────────────────┐
│  Line Actions     │  isolate_line / verify_machine / resume_production
└───────────────────┘
```

---

## Run the Demo

<p align="center">
  <img src="manufacturing-demo.png" width="860" alt="Manufacturing Line Recovery Demo" />
</p>

```bash
# From the adaptive-runtime root:
pip install pydantic aiosqlite psutil

python examples/manufacturing/manufacturing_demo.py
```

Expected output:
```
============================================================
  ADAPTIVE RUNTIME — Manufacturing Line Recovery Demo
============================================================

[LINE] Phase 1: Normal production running...

  [LOW     ] temperature_normal       → log_telemetry                conf=0.690
  [LOW     ] pressure_normal          → log_telemetry                conf=0.690
  [LOW     ] product_detected         → log_telemetry                conf=0.690

[LINE] Phase 2: Quality risk detected...

  ⚠  [WARN] Product quality deviation detected
  [NORMAL  ] temperature_high         → monitor_voltage              conf=0.594
  [NORMAL  ] pressure_spike           → monitor_voltage              conf=0.594
  [HIGH    ] quality_alert            → isolate_segment              conf=0.424

[LINE] Phase 3: Machine failure — conveyor stopped...

  ⚠  [ALERT] Conveyor failure detected!
  [HIGH    ] conveyor_failure         → isolate_segment              conf=0.424
  [HIGH    ] motor_fault              → isolate_segment              conf=0.424

  💾  Saving production state before shutdown...
  ✓   Checkpoint created
        last_product_batch  : 125
        last_quality_score  : 0.61
        last_machine_state  : conveyor_failure

[LINE] Phase 4: Simulating power outage...

  [OUTAGE] System offline... (simulating 2s outage)

[LINE] Phase 5: Power restored — initiating recovery...

  ✅  State restored in 4ms

  Restored:
    - Last product batch  : 125 units
    - Last quality score  : 0.61
    - Last machine state  : conveyor_failure

[LINE] Phase 6: Resuming production...

  [NORMAL  ] sensor_reconnect         → verify_sensor_integrity      conf=0.594
  [LOW     ] line_ready               → optimize_resources           conf=0.690

  ✅  Production resumed — batch context intact

============================================================
  RECOVERY SUMMARY
============================================================
  State loss           : ZERO
  Manual intervention  : NOT REQUIRED
  Recovery time        : 4 ms
  Events handled       : 9
  Products processed   : 125

  Current memory       : 0.13 MB
  Peak memory          : 0.18 MB
  Process RSS          : 31.00 MB
  GPU required         : Never
============================================================

  The runtime remembers the production line before failure.
  Recovers automatically. No manual restart.
  No lost batch context.
```

---

## Benchmark (real numbers, mid-range laptop)

| Metric | Result |
|---|---|
| State recovery time | **4 ms** |
| Current memory | **0.13 MB** |
| Peak memory | **0.18 MB** |
| SQLite state persistence | **36.5 ms** |
| Event processing | **109 ms** |
| GPU required | **Never** |
| Works offline | **Yes** |

Memory is measured live at runtime using `tracemalloc` and `psutil` — not hardcoded.

This makes it suitable for:
- Factory floor edge controllers
- Low-power embedded PLC systems
- Air-gapped industrial networks
- Any environment where cloud dependency is unacceptable

---

## Why This Matters

Manufacturing failures follow a pattern:

1. Sensor detects anomaly
2. Machine stops — state lost on restart
3. Operator has no memory of last batch or quality score
4. Production resumes from wrong state
5. Defective products pass through undetected

Adaptive Runtime breaks this chain at step 2.  
State is **always persisted**. Recovery is **automatic**.  
The line returns to operation with full batch context intact.

---

## Extending This Example

The manufacturing demo uses the same 5 engines as any other Adaptive Runtime deployment.  
You can extend it by:

```python
# Add custom manufacturing-specific decision rules
custom_rules = [
    ("conveyor_failure", "critical", 0.0, "emergency_stop_line",   "conveyor_failure_critical"),
    ("quality_alert",    "high",     0.0, "isolate_line",           "quality_threshold_breached"),
    ("temperature_high", "medium",   0.0, "inspect_product",        "temperature_deviation"),
    ("line_ready",       "low",      0.0, "resume_production",      "line_cleared_for_restart"),
]

runtime = Runtime(agent_id="manufacturing-line")
runtime._decision = DecisionEngine(custom_rules=custom_rules)
```

---

## Related Industries

The same pattern applies to:

| Industry | Runtime Problem |
|---|---|
| Manufacturing | Machine fault, production state lost |
| Power Grid | Sensor offline, state lost, cascading failure |
| Trading Bot | VPS crash, positions lost, wrong exit |
| Healthcare | Device disconnect, patient state lost |
| Telecom | Node failure, routing state lost |

Same runtime layer. Different event types.
