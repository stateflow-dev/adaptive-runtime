"""
Recovery Engine — self-healing runtime resilience.
"""

import asyncio
from datetime import datetime
from typing import Callable, Awaitable

from pydantic import BaseModel
from observability.logger import get_logger
from observability.metrics import metrics

logger = get_logger("recovery_engine")


class CheckpointMeta(BaseModel):
    snapshot_id: int
    agent_id: str
    created: str
    state_keys: list[str]


class RecoveryEngine:
    """
    Manages:
      - automatic checkpoint snapshots
      - crash recovery / restore
      - retry orchestration with exponential back-off
      - fallback handlers
    """

    def __init__(self, store, agent_id: str, max_retries: int = 3, base_delay: float = 1.0):
        self.store = store
        self.agent_id = agent_id
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._last_checkpoint: CheckpointMeta | None = None

    # ── Checkpointing ──────────────────────────────────────────────────────

    async def create_checkpoint(self, state: dict) -> CheckpointMeta:
        snap_id = await self.store.save_snapshot(
            self.agent_id,
            {"state": state, "checkpoint_at": datetime.utcnow().isoformat()},
        )
        meta = CheckpointMeta(
            snapshot_id=snap_id,
            agent_id=self.agent_id,
            created=datetime.utcnow().isoformat(),
            state_keys=list(state.keys()),
        )
        self._last_checkpoint = meta
        metrics.record("recovery.checkpoints", 1)
        logger.info("Checkpoint #%d created (keys: %s)", snap_id, meta.state_keys)
        return meta

    async def restore_latest(self) -> dict | None:
        snap = await self.store.load_latest_snapshot(self.agent_id)
        if snap:
            state = snap.get("state", snap)
            logger.info("State restored from snapshot (keys: %s)", list(state.keys()))
            metrics.record("recovery.restores", 1)
            return state
        logger.warning("No snapshot found for agent '%s'", self.agent_id)
        return None

    # ── Retry orchestration ────────────────────────────────────────────────

    async def retry(
        self,
        fn: Callable[[], Awaitable],
        fallback: Callable[[], Awaitable] | None = None,
    ):
        """
        Execute `fn` with exponential back-off retries.
        On total failure, call `fallback` if provided, else re-raise.
        """
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await fn()
                if attempt > 1:
                    logger.info("Retry succeeded on attempt %d", attempt)
                    metrics.record("recovery.retry_success", 1)
                return result
            except Exception as exc:
                last_exc = exc
                delay = self.base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt, self.max_retries, exc, delay,
                )
                metrics.record("recovery.retry_fail", 1)
                await asyncio.sleep(delay)

        logger.error("All %d retries exhausted.", self.max_retries)
        metrics.record("recovery.exhausted", 1)

        if fallback:
            logger.info("Executing fallback handler.")
            return await fallback()
        raise last_exc

    # ── Crash recovery ─────────────────────────────────────────────────────

    async def crash_recovery(self, state_engine) -> dict:
        """
        Attempt to restore state after an unexpected crash.
        1. Try load from state store.
        2. Fall back to latest snapshot.
        3. Return empty dict if both fail.
        """
        logger.warning("[Recovery] Crash recovery initiated for '%s'", self.agent_id)
        state = await state_engine.load_state()
        if state:
            logger.info("[Recovery] State recovered from persistent store.")
            return state

        snap = await self.restore_latest()
        if snap:
            await state_engine.save_state(snap)
            logger.info("[Recovery] State recovered from snapshot.")
            return snap

        logger.error("[Recovery] No recoverable state found — starting fresh.")
        return {}
