"""
State Engine — manages runtime persistence and state memory.
"""

from datetime import datetime
from typing import Any

from observability.logger import get_logger
from observability.metrics import metrics

logger = get_logger("state_engine")


class StateEngine:
    """
    Manages agent state lifecycle: load, merge, persist.

    Compatible with any store that implements the async store API
    (SQLiteStore or MemoryStore).
    """

    def __init__(self, store, agent_id: str):
        self.store = store
        self.agent_id = agent_id
        self._state: dict[str, Any] = {}

    # ── Public API ─────────────────────────────────────────────────────────

    async def save_state(self, state: dict) -> None:
        self._state.update(state)
        self._state["_updated"] = datetime.utcnow().isoformat()
        await self.store.save_state(self.agent_id, self._state)
        metrics.record("state.saves", 1)
        logger.info("State persisted for agent '%s'", self.agent_id)

    async def load_state(self) -> dict:
        stored = await self.store.load_state(self.agent_id)
        if stored:
            self._state = stored
            logger.info("State loaded for agent '%s' (keys: %s)", self.agent_id, list(stored.keys()))
        else:
            logger.info("No prior state found for agent '%s'", self.agent_id)
        return dict(self._state)

    async def patch_state(self, patch: dict) -> dict:
        """Merge a partial patch into current state."""
        self._state.update(patch)
        await self.save_state(self._state)
        return dict(self._state)

    async def reset_state(self) -> None:
        self._state = {}
        await self.store.save_state(self.agent_id, self._state)
        logger.warning("State RESET for agent '%s'", self.agent_id)

    @property
    def current(self) -> dict:
        return dict(self._state)
