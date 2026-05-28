"""
Demo: Retry + crash-recovery pattern using RecoveryEngine directly.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.runtime_manager import Runtime


async def main():
    runtime = Runtime(agent_id="auto-recover", persist=False, checkpoint_every=3)
    await runtime.start()

    # Process a few events to build state and checkpoints
    for event in [
        {"type": "service_overload", "severity": 0.80, "cpu": 91},
        {"type": "anomaly_detected", "severity": 0.70},
        {"type": "degraded_service", "severity": 0.60},
    ]:
        await runtime.process(event)

    print("\n=== Simulating crash recovery ===")
    recovered = await runtime.recover()
    print(f"Recovered state keys: {list(recovered.keys())}\n")

    # Retry demo — fails first 2 calls, succeeds on 3rd
    attempt = [0]

    async def flaky_task():
        attempt[0] += 1
        if attempt[0] < 3:
            raise RuntimeError(f"Simulated failure #{attempt[0]}")
        return f"Success on attempt #{attempt[0]}"

    async def fallback_task():
        return "Fallback result"

    result = await runtime._recovery.retry(flaky_task, fallback=fallback_task)
    print(f"Retry result: {result}")

    await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
