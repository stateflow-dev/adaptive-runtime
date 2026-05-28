"""
In-process memory store — useful for testing or ephemeral agents.
Mirrors the SQLiteStore async API.
"""

import json
from collections import defaultdict
from datetime import datetime
from copy import deepcopy


class MemoryStore:
    def __init__(self):
        self._states: dict[str, dict] = {}
        self._snapshots: dict[str, list] = defaultdict(list)
        self._events: dict[str, list] = defaultdict(list)
        self._snap_counter = 0

    async def connect(self) -> None:
        pass  # nothing to do

    async def save_state(self, agent_id: str, state: dict) -> None:
        self._states[agent_id] = deepcopy(state)

    async def load_state(self, agent_id: str) -> dict | None:
        return deepcopy(self._states.get(agent_id))

    async def save_snapshot(self, agent_id: str, snapshot: dict) -> int:
        self._snap_counter += 1
        self._snapshots[agent_id].append(
            {"id": self._snap_counter, "created": datetime.utcnow().isoformat(), **deepcopy(snapshot)}
        )
        return self._snap_counter

    async def load_latest_snapshot(self, agent_id: str) -> dict | None:
        snaps = self._snapshots.get(agent_id, [])
        return deepcopy(snaps[-1]) if snaps else None

    async def list_snapshots(self, agent_id: str, limit: int = 10) -> list[dict]:
        snaps = self._snapshots.get(agent_id, [])
        return deepcopy(snaps[-limit:])

    async def log_event(self, agent_id: str, event_type: str, payload: dict, outcome: dict | None = None) -> None:
        self._events[agent_id].append({
            "type": event_type,
            "payload": deepcopy(payload),
            "outcome": deepcopy(outcome),
            "created": datetime.utcnow().isoformat(),
        })

    async def recent_events(self, agent_id: str, limit: int = 20) -> list[dict]:
        evts = self._events.get(agent_id, [])
        return deepcopy(evts[-limit:])

    async def close(self) -> None:
        pass
