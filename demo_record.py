"""
demo_record.py — Script khusus untuk direkam sebagai GIF terminal.

Letakkan file ini di ROOT repo (sejajar folder adaptive_runtime/):

    adaptive_runtime/
    ├── core/
    ├── runtime/
    ├── examples/
    └── ...
    demo_record.py   <-- taruh di sini

Jalankan dari root repo:
    python demo_record.py
"""

import asyncio
import sys
import os

# Tambah root repo ke path agar import runtime/ bisa jalan
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime.runtime_manager import Runtime

# ── ANSI colors ────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
MAGENTA = "\033[35m"
WHITE   = "\033[97m"
GREY    = "\033[90m"

def tag(name: str, color: str) -> str:
    return f"{DIM}[{RESET}{color}{BOLD}{name}{RESET}{DIM}]{RESET}"

async def slow_print(line: str, delay: float = 0.0):
    if delay:
        await asyncio.sleep(delay)
    print(line)
    sys.stdout.flush()

# ── SECTION 1: agent_demo ──────────────────────────────────
async def run_agent_demo():
    await slow_print(f"\n{BOLD}{WHITE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    await slow_print(f"  {BOLD}{WHITE}  DEMO 1 — Basic Agent{RESET}  {DIM}(agent_demo.py){RESET}")
    await slow_print(f"{BOLD}{WHITE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    await asyncio.sleep(0.4)

    runtime = Runtime(agent_id="demo-agent", persist=False)
    await runtime.start()

    await slow_print(f"  {tag('RUNTIME', CYAN)}  {GREEN}✓{RESET} Agent started: {BOLD}demo-agent{RESET}\n")
    await asyncio.sleep(0.3)

    events = [
        {"type": "service_overload", "severity": 0.82, "cpu": 94, "memory": 88},
        {"type": "anomaly_detected", "severity": 0.65, "error_rate": 0.6},
        {"type": "timeout",          "severity": 0.45, "latency_ms": 3200},
        {"type": "degraded_service", "severity": 0.55, "cpu": 70},
        {"type": "recovery_needed",  "severity": 0.30},
    ]

    priority_color = {"high": RED, "normal": YELLOW, "low": GREEN}

    for ev in events:
        result = await runtime.process(ev)
        pc = priority_color.get(result.priority, WHITE)
        await slow_print(
            f"  {tag('EVENT', MAGENTA)}  {WHITE}{ev['type']:<25}{RESET}"
            f"→ {BOLD}{result.action:<28}{RESET}"
            f"conf={GREEN}{result.confidence:.3f}{RESET}  "
            f"[{pc}{result.priority.upper()}{RESET}]"
        )
        await asyncio.sleep(0.35)

    await slow_print(f"\n  {tag('METRICS', CYAN)}  Summary:")
    for k, v in runtime.metrics_summary().items():
        await slow_print(f"  {DIM}  {k}: {v}{RESET}")
        await asyncio.sleep(0.08)

    await runtime.stop()
    await asyncio.sleep(0.8)

# ── SECTION 2: monitoring_demo ─────────────────────────────
async def run_monitoring_demo():
    await slow_print(f"\n{BOLD}{WHITE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    await slow_print(f"  {BOLD}{WHITE}  DEMO 2 — Monitoring + Event Bus{RESET}  {DIM}(monitoring_demo.py){RESET}")
    await slow_print(f"{BOLD}{WHITE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    await asyncio.sleep(0.4)

    runtime = Runtime(agent_id="prod-monitor", persist=False, checkpoint_every=5)

    @runtime.bus.subscribe("anomaly_detected")
    async def on_anomaly(event):
        await slow_print(
            f"  {tag('BUS', YELLOW)}  "
            f"{YELLOW}⚡ anomaly_detected handler fired{RESET}  "
            f"severity={event.get('severity')}"
        )

    await runtime.start()
    await slow_print(f"  {tag('RUNTIME', CYAN)}  {GREEN}✓{RESET} Monitoring agent started\n")
    await asyncio.sleep(0.3)

    events = [
        {"type": "service_overload", "severity": 0.91, "cpu": 96, "memory": 92},
        {"type": "anomaly_detected",  "severity": 0.74, "error_rate": 0.6},
        {"type": "auth_failure",      "severity": 0.55},
        {"type": "timeout",           "severity": 0.45, "latency_ms": 4200},
        {"type": "degraded_service",  "severity": 0.60, "cpu": 75},
        {"type": "recovery_needed",   "severity": 0.30},
        {"type": "anomaly_detected",  "severity": 0.80},
        {"type": "timeout",           "severity": 0.38, "latency_ms": 2100},
    ]

    priority_color = {"high": RED, "normal": YELLOW, "low": GREEN}

    for i, ev in enumerate(events):
        result = await runtime.process(ev)
        pc = priority_color.get(result.priority, WHITE)
        await slow_print(
            f"  {GREY}[{i+1}/8]{RESET}  "
            f"{WHITE}{ev['type']:<25}{RESET}"
            f"→ {BOLD}{result.action:<28}{RESET}"
            f"[{pc}{result.priority.upper()}{RESET}]"
        )
        await asyncio.sleep(0.4)

    await runtime.stop()
    await asyncio.sleep(0.8)

# ── SECTION 3: automation_demo ─────────────────────────────
async def run_automation_demo():
    await slow_print(f"\n{BOLD}{WHITE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    await slow_print(f"  {BOLD}{WHITE}  DEMO 3 — Retry + Crash Recovery{RESET}  {DIM}(automation_demo.py){RESET}")
    await slow_print(f"{BOLD}{WHITE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    await asyncio.sleep(0.4)

    runtime = Runtime(agent_id="auto-recover", persist=False, checkpoint_every=3)
    await runtime.start()

    await slow_print(f"  {tag('RUNTIME', CYAN)}  {GREEN}✓{RESET} Recovery agent started\n")
    await asyncio.sleep(0.3)

    for ev in [
        {"type": "service_overload", "severity": 0.80, "cpu": 91},
        {"type": "anomaly_detected", "severity": 0.70},
        {"type": "degraded_service", "severity": 0.60},
    ]:
        result = await runtime.process(ev)
        await slow_print(
            f"  {tag('EVENT', MAGENTA)}  {WHITE}{ev['type']:<25}{RESET}"
            f"→ {BOLD}{result.action}{RESET}"
        )
        await asyncio.sleep(0.3)

    await slow_print(f"\n  {tag('RECOVERY', RED)}  Simulating crash...")
    await asyncio.sleep(0.6)
    recovered = await runtime.recover()
    await slow_print(f"  {tag('RECOVERY', RED)}  {GREEN}✓{RESET} State restored: {list(recovered.keys())}\n")
    await asyncio.sleep(0.5)

    attempt = [0]

    async def flaky_task():
        attempt[0] += 1
        if attempt[0] < 3:
            raise RuntimeError(f"Simulated failure #{attempt[0]}")
        return f"Success on attempt #{attempt[0]}"

    async def fallback_task():
        return "Fallback result"

    await slow_print(f"  {tag('RETRY', YELLOW)}  Running flaky task with exponential back-off...")
    await asyncio.sleep(0.3)

    for i in range(1, 3):
        await slow_print(f"  {tag('RETRY', YELLOW)}  {RED}✗{RESET} Attempt {i} failed — retrying...")
        await asyncio.sleep(0.5)

    result = await runtime._recovery.retry(flaky_task, fallback=fallback_task)
    await slow_print(f"  {tag('RETRY', YELLOW)}  {GREEN}✓{RESET} {result}\n")

    await runtime.stop()
    await asyncio.sleep(0.8)

# ── MAIN ───────────────────────────────────────────────────
async def main():
    print(f"\n{BOLD}{WHITE}  Adaptive Runtime{RESET}  "
          f"{DIM}Runtime Intelligence Layer — Full Demo{RESET}\n")
    await asyncio.sleep(0.5)

    await run_agent_demo()
    await run_monitoring_demo()
    await run_automation_demo()

    print(f"  {'─' * 54}")
    print(f"  {tag('DONE', GREEN)}  All 3 demos complete.")
    print(f"  {DIM}No GPU. No cloud. Just Python + asyncio + SQLite.{RESET}\n")

if __name__ == "__main__":
    asyncio.run(main())
