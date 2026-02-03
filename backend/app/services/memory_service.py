# backend/app/services/memory_service.py — SQLite conversation + topic storage

import aiosqlite
from pathlib import Path
from typing import List, Optional, Tuple
import os


def _db_path() -> str:
    p = os.environ.get("TUTOR_DB_PATH")
    if p:
        return p
    base = Path(__file__).resolve().parent.parent.parent.parent
    data = base / "data"
    data.mkdir(parents=True, exist_ok=True)
    return str(data / "tutor.db")


class MemoryService:
    """Store conversation history and weak/strong topics. Single-user MVP."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _db_path()
        self._init_done = False

    async def _ensure_schema(self) -> None:
        if self._init_done:
            return
        schema = (Path(__file__).resolve().parent.parent.parent / "schemas" / "schema.sql").read_text()
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(schema)
            await db.commit()
        self._init_done = True

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        await self._ensure_schema()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            await db.commit()

    async def get_recent_messages(
        self, session_id: str, limit: int = 20
    ) -> List[Tuple[str, str]]:
        """Returns list of (role, content)."""
        await self._ensure_schema()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT role, content FROM conversations
                   WHERE session_id = ? ORDER BY created_at DESC LIMIT ?""",
                (session_id, limit),
            ) as cur:
                rows = await cur.fetchall()
        out = [(r["role"], r["content"]) for r in reversed(rows)]
        return out

    async def upsert_topic(self, name: str, strength: str, concept_summary: Optional[str] = None) -> None:
        await self._ensure_schema()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO topics (name, strength, concept_summary, last_touched_at, updated_at)
                   VALUES (?, ?, ?, datetime('now'), datetime('now'))
                   ON CONFLICT(name) DO UPDATE SET
                     strength = excluded.strength,
                     concept_summary = excluded.concept_summary,
                     last_touched_at = datetime('now'),
                     updated_at = datetime('now')""",
                (name, strength, concept_summary or ""),
            )
            await db.commit()

    async def get_topic(self, name: str) -> Optional[Tuple[str, str]]:
        """Returns (strength, concept_summary) or None."""
        await self._ensure_schema()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT strength, concept_summary FROM topics WHERE name = ?", (name,)
            ) as cur:
                row = await cur.fetchone()
        if row is None:
            return None
        return (row["strength"], row["concept_summary"] or "")

    async def record_turn(
        self,
        session_id: str,
        turn_type: str,
        concept: Optional[str] = None,
        user_answer: Optional[str] = None,
        is_correct: Optional[bool] = None,
    ) -> None:
        await self._ensure_schema()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO teaching_turns (session_id, turn_type, concept, user_answer, is_correct)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, turn_type, concept or "", user_answer or "", 1 if is_correct else 0 if is_correct is not None else None),
            )
            await db.commit()
