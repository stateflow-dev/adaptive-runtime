import asyncio
import time
import os
import sys

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ── 1. Cold start time ─────────────────────────────────────────────
t0 = time.perf_counter()
from adaptive_runtime import Runtime
cold_start_ms = (time.perf_counter() - t0) * 1000
print(f"[cold_start]  {cold_start_ms:.1f} ms")

async def main():
    runtime = Runtime(agent_id="benchmark-agent")
    await runtime.start()

    # ── 2. Idle memory ────────────────────────────────────────────
    if HAS_PSUTIL:
        proc = psutil.Process(os.getpid())
        idle_mb = proc.memory_info().rss / 1024 / 1024
        print(f"[idle_memory] {idle_mb:.1f} MB")
    else:
        print("[idle_memory] install psutil: pip install psutil")

    # ── 3. SQLite save latency ────────────────────────────────────
    RUNS = 50
    t_save = []
    for i in range(RUNS):
        t = time.perf_counter()
        await runtime._state.save_state({"iter": i, "status": "ok"})
        t_save.append((time.perf_counter() - t) * 1000)
    avg_save = sum(t_save) / RUNS
    print(f"[sqlite_save] avg={avg_save:.2f} ms  min={min(t_save):.2f}  max={max(t_save):.2f}")

    # ── 4. SQLite load latency ────────────────────────────────────
    t_load = []
    for _ in range(RUNS):
        t = time.perf_counter()
        await runtime._state.load_state()
        t_load.append((time.perf_counter() - t) * 1000)
    avg_load = sum(t_load) / RUNS
    print(f"[sqlite_load] avg={avg_load:.2f} ms  min={min(t_load):.2f}  max={max(t_load):.2f}")

    # ── 5. Event processing latency ───────────────────────────────
    test_events = [
        {"type": "service_overload", "severity": 0.91, "cpu": 96, "memory": 92},
        {"type": "anomaly_detected", "severity": 0.74, "error_rate": 0.6},
        {"type": "auth_failure",     "severity": 0.55},
        {"type": "timeout",          "severity": 0.45, "latency_ms": 4200},
    ]
    t_evt = []
    for event in test_events * (RUNS // len(test_events) + 1):
        if len(t_evt) >= RUNS:
            break
        t = time.perf_counter()
        await runtime.process(event)
        t_evt.append((time.perf_counter() - t) * 1000)
    avg_evt = sum(t_evt) / RUNS
    print(f"[event_proc]  avg={avg_evt:.2f} ms  min={min(t_evt):.2f}  max={max(t_evt):.2f}")

    # ── 6. CPU idle ───────────────────────────────────────────────
    if HAS_PSUTIL:
        cpu = psutil.Process(os.getpid()).cpu_percent(interval=0.5)
        print(f"[cpu_idle]    {cpu:.1f}%")

    await runtime.stop()

    # ── Summary ───────────────────────────────────────────────────
    print()
    print("## Benchmarks")
    print(f"- Cold start:              {cold_start_ms:.0f} ms")
    if HAS_PSUTIL:
        print(f"- Idle memory:             {idle_mb:.0f} MB")
        print(f"- CPU idle usage:          <{cpu:.0f}%")
    print(f"- SQLite save latency:     {avg_save:.1f} ms (avg, n={RUNS})")
    print(f"- SQLite load latency:     {avg_load:.1f} ms (avg, n={RUNS})")
    print(f"- Event processing:        {avg_evt:.1f} ms (avg, n={RUNS})")
    print("- GPU required:            No")

asyncio.run(main())