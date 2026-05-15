from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Supabase (and most hosted Postgres) requires SSL.
# asyncpg accepts connect_args for SSL options.
# Supabase's pgbouncer (transaction pooler on :6543) does NOT support prepared
# statements, so we disable asyncpg's statement cache and also disable
# SQLAlchemy's compiled-cache lookup-by-statement-name.
_connect_args: dict = {"statement_cache_size": 0}
if "supabase.co" in settings.database_url or "supabase.com" in settings.database_url:
    import ssl as _ssl
    _ctx = _ssl.create_default_context()
    _ctx.check_hostname = False
    _ctx.verify_mode = _ssl.CERT_NONE
    _connect_args["ssl"] = _ctx

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
