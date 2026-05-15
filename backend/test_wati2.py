import asyncio
import json
from app.config import get_settings
from app.services.otp_service import _dispatch_wati, normalise_phone

async def main():
    phone = normalise_phone("07040684933")
    print(f"Testing WATI for {phone}...")
    import httpx
    settings = get_settings()
    message = "Your EcoNet verification code is 123456. Valid for 10 minutes. Do not share."
    headers = {
        "Authorization": f"Bearer {settings.wati_token}",
        "Content-Type": "application/json",
    }
    session_url = f"{settings.wati_api_url}/api/v1/sendSessionMessage/{phone}"
    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        resp = await client.post(session_url, params={"messageText": message}, headers=headers)
    print(resp.status_code)
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
