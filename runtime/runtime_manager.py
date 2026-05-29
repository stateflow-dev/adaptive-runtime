"""
Runtime Manager — central orchestrator of all engines.

Usage:
    from adaptive_runtime import Runtime

    runtime = Runtime()
    await runtime.start()
    result = await runtime.process({"type": "service_overload", "severity": 0.82})
    await runtime.stop()
"""

import asyncio
import sys
import os

# Make sure sibling packages are importable when run from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel

from core.state_engine import StateEngine
from core.context_engine import ContextEngine
from core.confidence_engine import ConfidenceEngine
from core.decision_engine import DecisionEngine
from core.recovery_engine import RecoveryEngine
from runtime.event_bus import EventBus
from runtime.cache import TTLCache
from storage.sqlite_store import SQLiteStore
from storage.memory_store import MemoryStore
from observability.logger import get_logger
from observability.metrics import metrics

logger = get_logger("runtime")


class RuntimeResult(BaseModel):
    event_type: str
    context: dict
    confidence: float
    action: str
    reason: str
    priority: str
    state_persisted: bool
    checkpoint_created: bool


class Runtime:
    """
    Adaptive Runtime — wires all engines together into a single
    event-driven processing loop.

    Args:
        agent_id: Logical identity of the running agent.
        persist:  If True (default) use SQLiteStore, else MemoryStore.
        checkpoint_every: Create a snapshot every N processed events.
    """

    def __init__(
        self,
        agent_id: str = "default",
        persist: bool = True,
        checkpoint_every: int = 10,
    ):
        self.agent_id = agent_id
        self._checkpoint_every = checkpoint_every
        self._event_count = 0
        self._started = False

        # Storage
        self._store = SQLiteStore() if persist else MemoryStore()

        # Engines
        self._state     = StateEngine(self._store, agent_id)
        self._context   = ContextEngine()
        self._confidence = ConfidenceEngine()
        self._decision  = DecisionEngine()
        self._recovery  = RecoveryEngine(self._store, agent_id)

        # Supporting components
        self.bus   = EventBus()
        self._cache = TTLCache(default_ttl=30.0)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Connect storage and restore any previous state."""
        await self._store.connect()
        await self._state.load_state()
        self._started = True
        logger.info("Runtime started  agent_id='%s'", self.agent_id)

    async def stop(self) -> None:
        await self._store.close()
        self._started = False
        logger.info("Runtime stopped  agent_id='%s'", self.agent_id)

    # ── Main processing API ────────────────────────────────────────────────

    async def process(self, event: dict) -> RuntimeResult:
        """
        Full pipeline:
          Event → Context → Confidence → Decision → State → Recovery
        """
        if not self._started:
            await self.start()

        etype = event.get("type", "unknown")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("Event received: %s", etype)

        self._event_count += 1
        metrics.record("runtime.events", 1)

        # 1. Context analysis
        ctx_result = self._context.analyze(event)
        logger.info(
            "[Context Engine] risk=%s  stability=%s  pressure=%.2f",
            ctx_result.risk, ctx_result.stability, ctx_result.pressure_score,
        )

        # 2. Confidence evaluation
        conf_result = self._confidence.calculate(event, ctx_result.risk)
        logger.info("[Confidence Engine] confidence=%.4f", conf_result.final)

        # 3. Decision
        decision = self._decision.decide(
            event,
            ctx_result.context,
            ctx_result.risk,
            conf_result.final,
        )
        logger.info("[Decision Engine] ACTION: %s", decision.action.upper())

        # 4. State persistence
        patch = {
            "last_event": etype,
            "last_action": decision.action,
            "last_risk": ctx_result.risk,
            "last_confidence": conf_result.final,
        }
        await self._state.patch_state(patch)
        logger.info("[State Engine] State persisted")

        # Log event to store
        await self._store.log_event(
            self.agent_id, etype, event,
            outcome={"action": decision.action, "confidence": conf_result.final},
        )

        # 5. Checkpoint (periodic)
        checkpoint_created = False
        if self._event_count % self._checkpoint_every == 0:
            await self._recovery.create_checkpoint(self._state.current)
            checkpoint_created = True
            logger.info("[Recovery Engine] Checkpoint created (#%d)", self._event_count)

        # Publish to bus (non-blocking, best-effort)
        asyncio.create_task(
            self.bus.publish({**event, "_decision": decision.model_dump()})
        )

        result = RuntimeResult(
            event_type=etype,
            context=ctx_result.model_dump(),
            confidence=conf_result.final,
            action=decision.action,
            reason=decision.reason,
            priority=decision.priority,
            state_persisted=True,
            checkpoint_created=checkpoint_created,
        )
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return result

    # ── Recovery helpers ───────────────────────────────────────────────────

    async def recover(self) -> dict:
        """Manually trigger crash recovery."""
        return await self._recovery.crash_recovery(self._state)

    # ── Observability ──────────────────────────────────────────────────────

    def metrics_summary(self) -> dict:
        return metrics.summary()

    async def event_history(self, limit: int = 20) -> list[dict]:
        return await self._store.recent_events(self.agent_id, limit)
