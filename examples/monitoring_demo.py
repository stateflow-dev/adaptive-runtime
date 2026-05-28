"""
Demo: Continuous monitoring loop with event bus subscription.
"""

import asyncio
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.runtime_manager import Runtime


async def main():
    runtime = Runtime(agent_id="monitor", persist=False, checkpoint_every=5)

    @runtime.bus.subscribe("anomaly_detected")
    async def on_anomaly(event):
        print(f"  [BUS] anomaly_detected handler fired! severity={event.get('severity')}")

    await runtime.start()

    EVENT_TYPES = [
        "service_overload", "anomaly_detected", "timeout",
        "degraded_service", "recovery_needed", "auth_failure",
    ]

    for i in range(8):
        event = {
            "type": random.choice(EVENT_TYPES),
            "severity": round(random.uniform(0.3, 0.95), 2),
            "cpu": random.randint(40, 98),
            "memory": random.randint(30, 95),
        }
        result = await runtime.process(event)
        print(f"  [{i+1}] {event['type']:25s} → {result.action}")

    await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
