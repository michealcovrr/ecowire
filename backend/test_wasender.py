import asyncio
from app.config import get_settings
from app.services.otp_service import _dispatch_wasender, normalise_phone

async def main():
    try:
        phone = normalise_phone("07040684933")
        res = await _dispatch_wasender(phone, "123456")
        print("wasender returned:", res)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(main())
