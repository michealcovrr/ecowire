import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def _make_id() -> str:
    chars = string.ascii_uppercase + string.digits
    part1 = "".join(random.choices(chars, k=4))
    part2 = "".join(random.choices(chars, k=4))
    return f"ECO-{part1}-{part2}"


async def generate_unique_user_id(db: AsyncSession) -> str:
    from app.models.user import User

    for _ in range(10):
        candidate = _make_id()
        result = await db.execute(select(User).where(User.user_id == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
    raise RuntimeError("Failed to generate unique user ID after 10 attempts")
