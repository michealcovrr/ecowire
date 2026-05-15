import asyncio
from app.config import get_settings
from app.services.otp_service import _dispatch_wasender, send_otp

async def main():
    try:
        settings = get_settings()
        print("Keys:", settings.wasender_api_keys)
        # test send_otp locally
        res = await send_otp("07040684933")
        print("send_otp returned:", res)
        # give it time to finish background task
        await asyncio.sleep(2)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(main())
