"""
Demo: Basic agent processing a sequence of events.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.runtime_manager import Runtime


EVENTS = [
    {"type": "service_overload", "severity": 0.82, "cpu": 94, "memory": 88},
    {"type": "anomaly_detected", "severity": 0.65, "error_rate": 0.6},
    {"type": "timeout",          "severity": 0.45, "latency_ms": 3200},
    {"type": "degraded_service", "severity": 0.55, "cpu": 70},
    {"type": "recovery_needed",  "severity": 0.30},
]


async def main():
    runtime = Runtime(agent_id="demo-agent", persist=False)
    await runtime.start()

    for event in EVENTS:
        result = await runtime.process(event)
        print(f"  → {result.action}  [{result.priority}]  conf={result.confidence:.3f}\n")

    print("=== Metrics Summary ===")
    for k, v in runtime.metrics_summary().items():
        print(f"  {k}: {v}")

    await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
