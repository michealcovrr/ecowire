"""
Drop all tables and recreate them with the current schema.
Run once: py reset_db.py
"""
import asyncio
from app.database import engine, Base
import app.models.user  # noqa: F401 — registers models with Base


async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("All tables dropped.")
        await conn.run_sync(Base.metadata.create_all)
        print("All tables recreated with current schema.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset())
