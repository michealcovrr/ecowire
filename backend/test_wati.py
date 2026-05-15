import asyncio
from app.config import get_settings
from app.services.otp_service import _dispatch_wati, normalise_phone

async def main():
    phone = normalise_phone("07040684933")
    print(f"Testing WATI for {phone}...")
    success = await _dispatch_wati(phone, "123456")
    print(f"WATI dispatch success: {success}")

if __name__ == "__main__":
    asyncio.run(main())
