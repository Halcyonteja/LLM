# backend/scripts/init_db.py — create SQLite schema
import asyncio
import sys
from pathlib import Path

# Add backend to path so "app" resolves (run from project root or backend)
_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from app.services.memory_service import MemoryService


async def main():
    svc = MemoryService()
    await svc._ensure_schema()
    print("DB initialized at", svc.db_path)


if __name__ == "__main__":
    asyncio.run(main())
