"""
One-off: wipe per-user populator output and re-run the enhanced populator
across every user in the DB so they all get jobs-posted, chats, etc.

Idempotent: safe to re-run.
"""
import asyncio
import ssl as _ssl

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.config import get_settings
from app.services.profile_populator import populate_user_profile

settings = get_settings()
_ctx = _ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = _ssl.CERT_NONE
engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"statement_cache_size": 0, "ssl": _ctx},
)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def main():
    import sys

    async with Session() as db:
        users_r = await db.execute(text(
            "SELECT u.user_id, u.full_name "
            "FROM users u "
            "LEFT JOIN ("
            "  SELECT employer_user_id AS uid, COUNT(*) AS c FROM jobs GROUP BY employer_user_id"
            ") jc ON jc.uid = u.user_id "
            "WHERE COALESCE(jc.c, 0) < 1"   # only users with no posted jobs (so far unenhanced)
        ))
        users = users_r.fetchall()
        peer_r = await db.execute(text("SELECT user_id FROM users"))
        peer_ids = [r[0] for r in peer_r.fetchall()]

    print(f"Found {len(users)} users still needing the enhanced populator. peer pool={len(peer_ids)}", flush=True)

    # Fresh session per user — avoids pgbouncer dropping a long-lived connection
    for i, (uid, name) in enumerate(users, 1):
        try:
            async with Session() as db:
                counts = await populate_user_profile(db, uid, peer_user_ids=peer_ids, commit=True)
                print(f"  [{i}/{len(users)}] {uid} ({name}): jobs+={counts['jobs_posted']}+{counts['jobs_applied']}, chats+={counts['chats_with_messages']}, txns+={counts['transactions']}", flush=True)
        except Exception as e:
            print(f"  [{i}/{len(users)}] {uid} FAILED: {type(e).__name__}: {e}", flush=True)
            continue

    print("Done.", flush=True)

    async with Session() as db:
        print("\nFINAL COUNTS")
        for t in ["users", "jobs", "job_chats", "chat_messages", "transactions", "recommendations", "financial_logs"]:
            r = await db.execute(text(f"SELECT COUNT(*) FROM {t}"))
            print(f"  {t}: {r.scalar()}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
