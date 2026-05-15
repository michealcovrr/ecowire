"""
Run this once to create all database tables.
Usage: python -m scripts.init_db
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
import app.models  # noqa: F401 — triggers all model imports so Base knows about them


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
