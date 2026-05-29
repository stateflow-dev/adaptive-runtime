"""
Async SQLite persistence layer for runtime state and snapshots.
"""

import json
import aiosqlite
from pathlib import Path
from datetime import datetime


DB_PATH = Path("adaptive_runtime.db")


class SQLiteStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA journal_mode=WAL;")
        await self._create_tables()

    async def _create_tables(self) -> None:
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_id TEXT PRIMARY KEY,
                state     TEXT NOT NULL,
                updated   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id  TEXT    NOT NULL,
                snapshot  TEXT    NOT NULL,
                created   TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS event_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id   TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload    TEXT NOT NULL,
                outcome    TEXT,
                created    TEXT NOT NULL
            );
        """)
        await self._db.commit()

    # ── State ──────────────────────────────────────────────────────────────

    async def save_state(self, agent_id: str, state: dict) -> None:
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            """
            INSERT INTO agent_state (agent_id, state, updated)
            VALUES (?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET state=excluded.state, updated=excluded.updated
            """,
            (agent_id, json.dumps(state), now),
        )
        await self._db.commit()

    async def load_state(self, agent_id: str) -> dict | None:
        async with self._db.execute(
            "SELECT state FROM agent_state WHERE agent_id = ?", (agent_id,)
        ) as cur:
            row = await cur.fetchone()
        return json.loads(row[0]) if row else None

    # ── Snapshots ──────────────────────────────────────────────────────────

    async def save_snapshot(self, agent_id: str, snapshot: dict) -> int:
        now = datetime.utcnow().isoformat()
        cur = await self._db.execute(
            "INSERT INTO snapshots (agent_id, snapshot, created) VALUES (?, ?, ?)",
            (agent_id, json.dumps(snapshot), now),
        )
        await self._db.commit()
        return cur.lastrowid

    async def load_latest_snapshot(self, agent_id: str) -> dict | None:
        async with self._db.execute(
            "SELECT snapshot FROM snapshots WHERE agent_id = ? ORDER BY id DESC LIMIT 1",
            (agent_id,),
        ) as cur:
            row = await cur.fetchone()
        return json.loads(row[0]) if row else None

    async def list_snapshots(self, agent_id: str, limit: int = 10) -> list[dict]:
        async with self._db.execute(
            "SELECT id, created, snapshot FROM snapshots WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [{"id": r[0], "created": r[1], **json.loads(r[2])} for r in rows]

    # ── Event log ──────────────────────────────────────────────────────────

    async def log_event(
        self, agent_id: str, event_type: str, payload: dict, outcome: dict | None = None
    ) -> None:
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO event_log (agent_id, event_type, payload, outcome, created) VALUES (?, ?, ?, ?, ?)",
            (agent_id, event_type, json.dumps(payload), json.dumps(outcome) if outcome else None, now),
        )
        await self._db.commit()

    async def recent_events(self, agent_id: str, limit: int = 20) -> list[dict]:
        async with self._db.execute(
            "SELECT event_type, payload, outcome, created FROM event_log "
            "WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [
            {
                "type": r[0],
                "payload": json.loads(r[1]),
                "outcome": json.loads(r[2]) if r[2] else None,
                "created": r[3],
            }
            for r in rows
        ]

    async def close(self) -> None:
        if self._db:
            await self._db.close()
