import asyncio
from app.config import get_settings
from app.services.otp_service import _get_redis, normalise_phone, _attempts_key, _otp_key

async def main():
    r = _get_redis()
    phone = normalise_phone("07040684933")
    await r.delete(_attempts_key(phone))
    await r.delete(_otp_key(phone))
    print(f"Cleared attempts for {phone}")

if __name__ == "__main__":
    asyncio.run(main())
