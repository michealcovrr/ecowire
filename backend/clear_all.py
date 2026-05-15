import asyncio
from app.services.otp_service import _get_redis

async def clear_all():
    r = _get_redis()
    keys = await r.keys("otp*")
    if keys:
        await r.delete(*keys)
        print(f"Cleared keys: {keys}")
    else:
        print("No OTP keys found in Redis.")

if __name__ == "__main__":
    asyncio.run(clear_all())
